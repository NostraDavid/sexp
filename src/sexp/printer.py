from __future__ import annotations

import io
import string
from typing import Optional

from sexp.settings import SexpSettings
from sexp.types import SexpAtom, SexpList, SexpNode


def dumps_advanced(node: SexpNode, settings: Optional[SexpSettings] = None) -> str:
    if settings is None:
        settings = SexpSettings()
    buf = io.StringIO()
    _write_adv(node, buf, settings, depth=0)
    return buf.getvalue()


def dumps_canonical(node: SexpNode) -> bytes:
    out = io.BytesIO()
    _write_canon(node, out)
    return out.getvalue()


def _write_adv(
    node: SexpNode, out: io.StringIO, settings: SexpSettings, depth: int
) -> None:
    indent = settings.pretty_indent
    if isinstance(node, SexpList):
        out.write("(")
        for i, it in enumerate(node.items):
            if i > 0:
                out.write(" ")
            if indent is not None:
                if isinstance(it, SexpList) and it.items:
                    out.write("\n" + " " * (depth + indent))
            _write_adv(it, out, settings, depth + (indent or 0))
        out.write(")")
        return

    assert isinstance(node, SexpAtom)
    if isinstance(node.value, str):
        if _is_symbol(node.value):
            out.write(node.value)
        else:
            out.write(_quote(node.value))
        return

    data = node.value
    try:
        s = data.decode("utf-8")
        if _is_printable(s):
            out.write(_quote(s))
            return
    except Exception:
        pass

    if len(data) >= (settings.prefer_base64_min_len or 48):
        import base64

        out.write("|")
        out.write(base64.b64encode(data).decode("ascii"))
        out.write("|")
    else:
        out.write("#")
        out.write(data.hex())
        out.write("#")


def _write_canon(node: SexpNode, out: io.BytesIO) -> None:
    if isinstance(node, SexpList):
        out.write(b"(")
        first = True
        for it in node.items:
            if not first:
                out.write(b" ")
            _write_canon(it, out)
            first = False
        out.write(b")")
        return

    assert isinstance(node, SexpAtom)
    b = node.value.encode("utf-8") if isinstance(node.value, str) else node.value
    out.write(str(len(b)).encode("ascii"))
    out.write(b":")
    out.write(b)


def _is_symbol(s: str) -> bool:
    if not s:
        return False
    for ch in s:
        if ch in '()"|#; \t\r\n':
            return False
    return True


def _is_printable(s: str) -> bool:
    for ch in s:
        if ch in '"\\\n\r\t':
            return False
        if ch not in string.printable:
            return False
    return True


def _quote(s: str) -> str:
    s = (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return '"' + s + '"'
