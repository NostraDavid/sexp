from __future__ import annotations

import base64
import binascii
import io
import logging
from typing import Tuple, Union

from sexp.settings import SexpSettings
from sexp.types import SexpAtom, SexpList, SexpNode

logger = logging.getLogger(__name__)

_whitespace = {ord(" "), ord("\t"), ord("\n"), ord("\r")}
_delims = {ord("("), ord(")")}
_comment = ord(";")  # line comments in advanced/human form


class SexpParseError(ValueError):
    pass


def parse(data: Union[bytes, str], settings: SexpSettings | None = None) -> SexpNode:  # type: ignore[syntax]
    if settings is None:
        settings = SexpSettings()
    buf = data.encode("utf-8") if isinstance(data, str) else data
    node, pos = _parse_one(buf, 0, settings)
    _skip_ws(buf, pos, settings, eof_ok=True)
    return node


def iterparse(source: io.BufferedReader) -> io.BufferedReader:  # type: ignore[no-redef]
    raise TypeError("type hint sentinel")  # never runs, helps some linters


def iterparse(source, settings: SexpSettings | None = None):  # noqa: F811
    if settings is None:
        settings = SexpSettings()
    if not hasattr(source, "read"):
        raise TypeError("iterparse expects a file-like object opened in binary mode")

    buf = bytearray()
    pos = 0
    while True:
        chunk = source.read(64 * 1024)
        if not chunk and pos >= len(buf):
            break
        if chunk:
            buf.extend(chunk)

        while True:
            try:
                node, new_pos = _parse_one(buf, pos, settings)
            except _NeedMore:
                break
            except _AtEnd:
                break
            except SexpParseError:
                raise
            else:
                pos = new_pos
                yield node
                try:
                    pos = _skip_ws(buf, pos, settings, eof_ok=False)
                except _NeedMore:
                    break

        if pos > 0:
            del buf[:pos]
            pos = 0
        if not chunk and pos == 0 and len(buf) == 0:
            break


class _NeedMore(Exception):
    pass


class _AtEnd(Exception):
    pass


def _skip_ws(
    buf: Union[bytearray, bytes], pos: int, settings: SexpSettings, eof_ok: bool
) -> int:
    n = len(buf)
    while True:
        while pos < n and (buf[pos] in _whitespace):
            pos += 1
        if settings.allow_comments and pos < n and buf[pos] == _comment:
            while pos < n and buf[pos] not in (ord("\n"), ord("\r")):
                pos += 1
            continue
        break
    if pos >= n and not eof_ok:
        raise _NeedMore()
    return pos


def _parse_one(
    buf: Union[bytearray, bytes], pos: int, settings: SexpSettings
) -> Tuple[SexpNode, int]:
    pos = _skip_ws(buf, pos, settings, eof_ok=False)
    if pos >= len(buf):
        raise _AtEnd()

    b = buf[pos]
    if b == ord("("):
        return _parse_list(buf, pos + 1, settings)
    if b == ord('"'):
        atom, pos2 = _parse_quoted(buf, pos + 1, settings)
        return atom, pos2
    if b == ord("#"):
        atom, pos2 = _parse_hex(buf, pos + 1, settings)
        return atom, pos2
    if b == ord("|"):
        atom, pos2 = _parse_base64(buf, pos + 1, settings)
        return atom, pos2
    if 48 <= b <= 57:  # '0'..'9' maybe length-prefixed
        pos2 = pos
        while pos2 < len(buf) and 48 <= buf[pos2] <= 57:
            pos2 += 1
        if pos2 >= len(buf):
            raise _NeedMore()
        if buf[pos2] == ord(":"):
            length_bytes = buf[pos:pos2]
            try:
                length = int(length_bytes.decode("ascii"))
            except Exception as exc:
                raise SexpParseError("invalid length prefix") from exc
            start = pos2 + 1
            end = start + length
            if end > len(buf):
                raise _NeedMore()
            chunk = bytes(buf[start:end])
            _maybe_warn_large_atom(chunk, settings)
            return SexpAtom(chunk), end
    return _parse_symbol(buf, pos, settings)


def _parse_list(
    buf: Union[bytearray, bytes], pos: int, settings: SexpSettings
) -> Tuple[SexpNode, int]:
    items: list[SexpNode] = []
    while True:
        pos = _skip_ws(buf, pos, settings, eof_ok=False)
        if pos >= len(buf):
            raise _NeedMore()
        if buf[pos] == ord(")"):
            return SexpList(items), pos + 1
        node, pos = _parse_one(buf, pos, settings)
        items.append(node)


def _parse_quoted(
    buf: Union[bytearray, bytes], pos: int, settings: SexpSettings
) -> Tuple[SexpAtom, int]:
    out = bytearray()
    n = len(buf)
    while True:
        if pos >= n:
            raise _NeedMore()
        b = buf[pos]
        pos += 1
        if b == ord('"'):
            s = out.decode("utf-8")
            return SexpAtom(s), pos
        if b == ord("\\"):
            if pos >= n:
                raise _NeedMore()
            esc = buf[pos]
            pos += 1
            if esc in (ord('"'), ord("\\")):
                out.append(esc)
            elif esc == ord("n"):
                out.append(ord("\n"))
            elif esc == ord("r"):
                out.append(ord("\r"))
            elif esc == ord("t"):
                out.append(ord("\t"))
            elif esc == ord("x"):
                if pos + 1 >= n:
                    raise _NeedMore()
                h1, h2 = buf[pos], buf[pos + 1]
                pos += 2
                try:
                    out.append(int(bytes([h1, h2]).decode("ascii"), 16))
                except Exception as exc:
                    raise SexpParseError("invalid \\x escape") from exc
            else:
                raise SexpParseError("invalid escape")
        else:
            out.append(b)


def _parse_hex(
    buf: Union[bytearray, bytes], pos: int, settings: SexpSettings
) -> Tuple[SexpAtom, int]:
    start = pos
    while True:
        if pos >= len(buf):
            raise _NeedMore()
        if buf[pos] == ord("#"):
            data = buf[start:pos]
            try:
                val = binascii.unhexlify(bytes(data))
            except Exception as exc:
                raise SexpParseError("invalid hex data") from exc
            _maybe_warn_large_atom(val, settings)
            return SexpAtom(val), pos + 1
        pos += 1


def _parse_base64(
    buf: Union[bytearray, bytes], pos: int, settings: SexpSettings
) -> Tuple[SexpAtom, int]:
    start = pos
    while True:
        if pos >= len(buf):
            raise _NeedMore()
        if buf[pos] == ord("|"):
            data = buf[start:pos]
            try:
                val = base64.b64decode(bytes(data), validate=True)
            except Exception as exc:
                raise SexpParseError("invalid base64 data") from exc
            _maybe_warn_large_atom(val, settings)
            return SexpAtom(val), pos + 1
        pos += 1


def _parse_symbol(
    buf: Union[bytearray, bytes], pos: int, settings: SexpSettings
) -> Tuple[SexpAtom, int]:
    start = pos
    n = len(buf)
    while (
        pos < n
        and (buf[pos] not in _whitespace)
        and (buf[pos] not in _delims)
        and buf[pos] != _comment
    ):
        pos += 1
    if pos == start:
        raise SexpParseError("unexpected character")
    raw = bytes(buf[start:pos])
    try:
        s = raw.decode("utf-8")
        return SexpAtom(s), pos
    except UnicodeDecodeError:
        _maybe_warn_large_atom(raw, settings)
        return SexpAtom(raw), pos


def _maybe_warn_large_atom(val: bytes, settings: SexpSettings) -> None:
    if (
        settings.warn_on_large_atom
        and isinstance(val, (bytes, bytearray))
        and len(val) >= settings.large_atom_threshold
    ):
        logger.warning("large atom: %d bytes", len(val))
