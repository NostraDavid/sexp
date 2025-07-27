use pyo3::prelude::*;
use pyo3::types::{PyAny, PyBytes, PyList, PyModule, PyString};
use base64::Engine;

/* ---------------- public API ---------------- */

#[pyfunction]
fn parse<'py>(py: Python<'py>, data: &Bound<'py, PyAny>) -> PyResult<PyObject> {
    let buf = to_bytes(data)?;
    let mut p = Parser { buf: &buf, pos: 0 };
    let node = p.parse_one(py)?;
    p.skip_ws().ok();
    Ok(node)
}

#[pyclass]
struct IterParser {
    src: PyObject,
    buf: Vec<u8>,
    pos: usize,
    eof: bool,
}

#[pymethods]
impl IterParser {
    #[new]
    fn new(obj: PyObject) -> PyResult<Self> {
        Ok(Self { src: obj, buf: Vec::new(), pos: 0, eof: false })
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> { slf }

    fn __next__(&mut self, py: Python<'_>) -> PyResult<Option<PyObject>> {
        loop {
            // try parse
            let mut p = Parser { buf: &self.buf, pos: self.pos };
            match p.parse_one(py) {
                Ok(obj) => {
                    self.pos = p.pos;
                    p.skip_ws().ok();
                    self.pos = p.pos;
                    if self.pos > 0 {
                        self.buf.drain(0..self.pos);
                        self.pos = 0;
                    }
                    return Ok(Some(obj));
                }
                Err(_) => {}
            }

            if self.eof {
                return Ok(None);
            }

            // read more
            let chunk = self.src.bind(py).call_method1("read", (65536,))?;
            let b = chunk.downcast::<PyBytes>()?;
            if b.as_bytes().is_empty() {                self.eof = true;
                continue;
            }
            self.buf.extend_from_slice(b.as_bytes());
        }
    }
}

#[pyfunction]
fn dumps_canonical<'py>(py: Python<'py>, node: &Bound<'py, PyAny>) -> PyResult<Py<PyBytes>> {
    let mut out: Vec<u8> = Vec::new();
    write_canonical(py, node, &mut out)?;
    Ok(PyBytes::new(py, &out).unbind())
}

#[pyfunction]
fn dumps_advanced<'py>(py: Python<'py>, node: &Bound<'py, PyAny>) -> PyResult<String> {
    let mut out = String::new();
    write_advanced(py, node, &mut out)?;
    Ok(out)
}

#[pymodule]
fn sexp_native<'py>(_py: Python<'py>, m: &Bound<'py, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse, m)?)?;
    m.add_function(wrap_pyfunction!(dumps_advanced, m)?)?;
    m.add_function(wrap_pyfunction!(dumps_canonical, m)?)?;
    m.add_class::<IterParser>()?;
    Ok(())
}

/* ---------------- internals ---------------- */

struct Parser<'a> { buf: &'a [u8], pos: usize }

impl<'a> Parser<'a> {
    fn parse_one(&mut self, py: Python<'_>) -> PyResult<PyObject> {
        self.skip_ws().ok();
        if self.pos >= self.buf.len() { return Err(err("eof")); }
        match self.buf[self.pos] {
            b'(' => self.parse_list(py),
            b'"' => self.parse_quoted(py),
            b'#' => self.parse_hex(py),
            b'|' => self.parse_b64(py),
            b'0'..=b'9' => {
                let mut i = self.pos;
                while i < self.buf.len() && self.buf[i].is_ascii_digit() { i += 1; }
                if i < self.buf.len() && self.buf[i] == b':' {
                    let len = std::str::from_utf8(&self.buf[self.pos..i]).ok()
                        .and_then(|s| s.parse::<usize>().ok())
                        .ok_or_else(|| err("invalid length prefix"))?;
                    let start = i + 1;
                    let end = start + len;
                    if end > self.buf.len() { return Err(err("need more")); }
                    let slice = &self.buf[start..end];
                    self.pos = end;
                    return Ok(PyBytes::new(py, slice).unbind().into());
                }
                self.parse_symbol(py)
            }
            _ => self.parse_symbol(py),
        }
    }

    fn parse_list(&mut self, py: Python<'_>) -> PyResult<PyObject> {
        self.pos += 1;
        let pylist = PyList::empty(py);
        loop {
            self.skip_ws().ok();
            if self.pos >= self.buf.len() { return Err(err("need more")); }
            if self.buf[self.pos] == b')' {
                self.pos += 1;
                return Ok(pylist.unbind().into());
            }
            let item = self.parse_one(py)?;
            pylist.append(item)?;
        }
    }

    fn parse_quoted(&mut self, py: Python<'_>) -> PyResult<PyObject> {
        self.pos += 1;
        let mut s = Vec::new();
        loop {
            if self.pos >= self.buf.len() { return Err(err("need more")); }
            let b = self.buf[self.pos]; self.pos += 1;
            match b {
                b'"' => {
                    let st = String::from_utf8(s).map_err(|_| err("utf8"))?;
                    return Ok(PyString::new(py, &st).unbind().into());
                }
                b'\\' => {
                    if self.pos >= self.buf.len() { return Err(err("need more")); }
                    let e = self.buf[self.pos]; self.pos += 1;
                    match e {
                        b'"' | b'\\' => s.push(e),
                        b'n' => s.push(b'\n'),
                        b'r' => s.push(b'\r'),
                        b't' => s.push(b'\t'),
                        b'x' => {
                            if self.pos + 1 >= self.buf.len() { return Err(err("need more")); }
                            let h = &self.buf[self.pos..self.pos+2]; self.pos += 2;
                            let hx = std::str::from_utf8(h).map_err(|_| err("hex"))?;
                            let v = u8::from_str_radix(hx, 16).map_err(|_| err("hex"))?;
                            s.push(v);
                        }
                        _ => return Err(err("escape")),
                    }
                }
                _ => s.push(b),
            }
        }
    }

    fn parse_hex(&mut self, py: Python<'_>) -> PyResult<PyObject> {
        self.pos += 1;
        let start = self.pos;
        loop {
            if self.pos >= self.buf.len() { return Err(err("need more")); }
            if self.buf[self.pos] == b'#' {
                let data = &self.buf[start..self.pos]; self.pos += 1;
                let s = std::str::from_utf8(data).map_err(|_| err("hex"))?;
                let bytes = hex::decode(s).map_err(|_| err("hex"))?;
                return Ok(PyBytes::new(py, &bytes).unbind().into());
            }
            self.pos += 1;
        }
    }

    fn parse_b64(&mut self, py: Python<'_>) -> PyResult<PyObject> {
        self.pos += 1;
        let start = self.pos;
        loop {
            if self.pos >= self.buf.len() { return Err(err("need more")); }
            if self.buf[self.pos] == b'|' {
                let data = &self.buf[start..self.pos]; self.pos += 1;
                let bytes = base64::engine::general_purpose::STANDARD
                    .decode(data)
                    .map_err(|_| err("b64"))?;
                return Ok(PyBytes::new(py, &bytes).unbind().into());
            }
            self.pos += 1;
        }
    }

    fn parse_symbol(&mut self, py: Python<'_>) -> PyResult<PyObject> {
        let start = self.pos;
        while self.pos < self.buf.len() {
            let c = self.buf[self.pos];
            if matches!(c, b'(' | b')' | b'"' | b'|' | b'#' | b';' | b' ' | b'\t' | b'\r' | b'\n') { break; }
            self.pos += 1;
        }
        if self.pos == start { return Err(err("unexpected")); }
        let raw = &self.buf[start..self.pos];
        if let Ok(s) = std::str::from_utf8(raw) {
            return Ok(PyString::new(py, s).unbind().into());
        }
        Ok(PyBytes::new(py, raw).unbind().into())
    }

    fn skip_ws(&mut self) -> Result<(), ()> {
        let n = self.buf.len();
        loop {
            while self.pos < n && matches!(self.buf[self.pos], b' ' | b'\t' | b'\r' | b'\n') { self.pos += 1; }
            if self.pos < n && self.buf[self.pos] == b';' {
                while self.pos < n && !matches!(self.buf[self.pos], b'\r' | b'\n') { self.pos += 1; }
                continue;
            }
            break;
        }
        Ok(())
    }
}

fn write_canonical<'py>(py: Python<'py>, node: &Bound<'py, PyAny>, out: &mut Vec<u8>) -> PyResult<()> {
    if let Ok(list) = node.downcast::<PyList>() {
        out.extend_from_slice(b"(");
        for (i, item) in list.iter().enumerate() {
            if i > 0 { out.push(b' '); }
            write_canonical(py, &item, out)?;
        }
        out.extend_from_slice(b")");
        return Ok(());
    }
    if let Ok(s) = node.downcast::<PyString>() {
        let b = s.to_string_lossy().into_owned().into_bytes();
        out.extend_from_slice(b.len().to_string().as_bytes());
        out.push(b':'); out.extend_from_slice(&b); return Ok(());
    }
    if let Ok(b) = node.downcast::<PyBytes>() {
        let bytes = b.as_bytes();
        out.extend_from_slice(bytes.len().to_string().as_bytes());
        out.push(b':'); out.extend_from_slice(bytes); return Ok(());
    }
    Err(err("unsupported node"))
}

fn write_advanced<'py>(py: Python<'py>, node: &Bound<'py, PyAny>, out: &mut String) -> PyResult<()> {
    if let Ok(list) = node.downcast::<PyList>() {
        out.push('(');
        for (i, item) in list.iter().enumerate() {
            if i > 0 { out.push(' '); }
            write_advanced(py, &item, out)?;
        }
        out.push(')'); return Ok(());
    }
    if let Ok(s) = node.downcast::<PyString>() {
        let st = s.to_string_lossy().into_owned();
        if is_symbol(&st) { out.push_str(&st); }
        else { out.push('"'); out.push_str(&escape(&st)); out.push('"'); }
        return Ok(());
    }
    if let Ok(b) = node.downcast::<PyBytes>() {
        let bytes = b.as_bytes();
        if looks_printable(bytes) {
            let st = String::from_utf8(bytes.to_vec()).unwrap_or_default();
            out.push('"'); out.push_str(&escape(&st)); out.push('"');
        } else if bytes.len() >= 48 {
            let enc = base64::engine::general_purpose::STANDARD.encode(bytes);
            out.push('|'); out.push_str(&enc); out.push('|');
        } else {
            out.push('#'); out.push_str(&hex::encode(bytes)); out.push('#');
        }
        return Ok(());
    }
    Err(err("unsupported node"))
}

fn to_bytes<'py>(data: &Bound<'py, PyAny>) -> PyResult<Vec<u8>> {
    if let Ok(s) = data.extract::<&str>() {
        return Ok(s.as_bytes().to_vec());
    }
    if let Ok(b) = data.downcast::<PyBytes>() {
        return Ok(b.as_bytes().to_vec());
    }
    let pybytes = data
        .call_method0("__bytes__")
        .or_else(|_| {
            // builtins.bytes(data)
            let builtins = PyModule::import(data.py(), "builtins")?;
            builtins.getattr("bytes")?.call1((data,))
        })?;    let b = pybytes.downcast::<PyBytes>()?;
    Ok(b.as_bytes().to_vec())
}

fn err(msg: &str) -> PyErr {
    PyErr::new::<pyo3::exceptions::PyValueError, _>(msg.to_string())
}

/* ---------------- helpers ---------------- */

fn is_symbol(s: &str) -> bool {
    !s.is_empty() && !s.chars().any(|c| "()\"|#; \t\r\n".contains(c))
}

fn looks_printable(bytes: &[u8]) -> bool {
    if let Ok(s) = std::str::from_utf8(bytes) {
        !s.chars().any(|c| "\"\\\n\r\t".contains(c)) && s.chars().all(|c| !c.is_control())
    } else {
        false
    }
}

fn escape(s: &str) -> String {
    s.chars()
        .flat_map(|c| match c {
            '\\' => "\\\\".chars().collect::<Vec<_>>(),
            '\"' => "\\\"".chars().collect::<Vec<_>>(),
            '\n' => "\\n".chars().collect::<Vec<_>>(),
            '\r' => "\\r".chars().collect::<Vec<_>>(),
            '\t' => "\\t".chars().collect::<Vec<_>>(),
            _ => vec![c],
        })
        .collect()
}
