# Public API Interface

This document outlines the public-facing API for the `sexp` library. The library provides simple, high-level functions for serializing Python objects into S-expression strings and deserializing S-expression strings back into Python objects, following the conventions of standard Python libraries like `json`.

## Core Functions

The library exposes four main functions for S-expression processing:

- `loads(s: str) -> list | str`: Parses an S-expression from a string.
- `dumps(obj: list | str) -> str`: Serializes a Python object into an S-expression string.
- `load(fp: IO[str]) -> list | str`: Reads and parses an S-expression from a file-like object.
- `dump(obj: list | str, fp: IO[str])`: Writes the S-expression representation of an object to a file-like object.

---

### `sexp.loads(s)`

Converts an S-expression string `s` into a Python object.

**Parameters:**
- `s` (`str`): The S-expression string to parse.

**Returns:**
- `list | str`: The corresponding Python object, typically a nested structure of lists and strings.

**Example:**
```python
import sexp

sexp_string = '(data "Hello, World!" (version 1))'
python_obj = sexp.loads(sexp_string)
# python_obj is now ['data', 'Hello, World!', ['version', '1']]
```

---

### `sexp.dumps(obj)`

Converts a Python object `obj` (composed of lists and strings) into its canonical S-expression string representation.

**Parameters:**
- `obj` (`list | str`): The Python object to serialize.

**Returns:**
- `str`: The S-expression string representation.

**Example:**
```python
import sexp

python_obj = ['person', ['name', 'Alice'], ['age', '30']]
sexp_string = sexp.dumps(python_obj)
# sexp_string is now '(person (name "Alice") (age "30"))'
```
*Note: Atoms that require quoting (e.g., containing spaces or special characters) will be automatically converted to quoted strings.*

---

### `sexp.load(fp)`

Reads and parses an S-expression from a file-like object `fp` (which supports a `.read()` method).

**Parameters:**
- `fp` (`IO[str]`): A text file or file-like object.

**Returns:**
- `list | str`: The corresponding Python object.

**Example:**
```python
import sexp
from io import StringIO

file_content = '(config (host "localhost") (port 8080))'
with StringIO(file_content) as f:
    config = sexp.load(f)
    # config is now ['config', ['host', 'localhost'], ['port', '8080']]
```

---

### `sexp.dump(obj, fp)`

Writes the S-expression string representation of a Python object `obj` to a file-like object `fp` (which supports a `.write()` method).

**Parameters:**
- `obj` (`list | str`): The Python object to serialize.
- `fp` (`IO[str]`): A writable text file or file-like object.

**Example:**
```python
import sexp
from io import StringIO

data = ['log', ['level', 'info'], ['message', 'System startup']]
with StringIO() as f:
    sexp.dump(data, f)
    f.seek(0)
    content = f.read()
    # content is now '(log (level "info") (message "System startup"))'
```
