from __future__ import annotations

import os
from typing import Iterator

from sexp.settings import SexpSettings
from sexp.types import SexpNode
from sexp import parser as py_parser
from sexp import printer as py_printer

# Set SEXP_FORCE_PY=1 to force pure Python (useful in CI/tests)
_USE_NATIVE = os.getenv("SEXP_FORCE_PY") not in ("1", "true", "yes")

_native_ok = False
if _USE_NATIVE:
    try:
        from sexp._native import parse as _n_parse
        from sexp._native import dumps_advanced as _n_dumps_advanced
        from sexp._native import dumps_canonical as _n_dumps_canonical
        from sexp._native import IterParser as _NIterParser

        _native_ok = True
    except Exception:
        _native_ok = False


def parse(data: bytes | str, settings: SexpSettings | None = None) -> SexpNode:  # type: ignore[syntax]
    # Py3.9 note: if your linter complains about "|", change to Union[...] below.
    if _native_ok and settings is None:
        return _n_parse(data)
    return py_parser.parse(data, settings)


def iterparse(source, settings: SexpSettings | None = None) -> Iterator[SexpNode]:  # type: ignore[syntax]
    if _native_ok and settings is None:
        return _NIterParser(source)  # type: ignore[return-value]
    return py_parser.iterparse(source, settings)


def dumps_advanced(node: SexpNode, settings: SexpSettings | None = None) -> str:  # type: ignore[syntax]
    if _native_ok and settings is None:
        return _n_dumps_advanced(node)
    return py_printer.dumps_advanced(node, settings)


def dumps_canonical(node: SexpNode) -> bytes:
    if _native_ok:
        return _n_dumps_canonical(node)
    return py_printer.dumps_canonical(node)
