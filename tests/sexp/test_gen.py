"""
Tests for the ABNF rule strategies.
"""

import base64
import re
import pytest
from hypothesis import given

from sexp.gen import sexp_gen
from sexp import DisplayString, SExpressionParser


def decode_quoted(text: str) -> bytes:
    content = text[text.index('"') + 1 : -1]
    result = bytearray()
    escapes = {"a": 7, "b": 8, "f": 12, "n": 10, "r": 13, "t": 9, "v": 11}
    i = 0
    while i < len(content):
        char = content[i]
        i += 1
        if char != "\\":
            result.append(ord(char))
            continue
        char = content[i]
        i += 1
        if char in "\r\n":
            if i < len(content) and content[i] in "\r\n" and content[i] != char:
                i += 1
        elif char == "x":
            result.append(int(content[i : i + 2], 16))
            i += 2
        elif char in "01234567":
            value = int(char + content[i : i + 2], 8)
            assert value <= 255
            result.append(value)
            i += 2
        else:
            result.append(escapes.get(char, ord(char)))
    return bytes(result)


def canonical_oracle(encoded: bytes):
    """Decode canonical bytes independently, preserving hints as tuples."""

    def atom(pos):
        end = encoded.index(b":", pos)
        digits = encoded[pos:end]
        assert re.fullmatch(rb"0|[1-9][0-9]*", digits)
        size = int(digits)
        value = encoded[end + 1 : end + 1 + size]
        assert len(value) == size
        return value, end + 1 + size

    def value(pos):
        if encoded[pos : pos + 1] == b"(":
            items = []
            pos += 1
            while encoded[pos : pos + 1] != b")":
                item, pos = value(pos)
                items.append(item)
            return items, pos + 1
        if encoded[pos : pos + 1] == b"[":
            hint, pos = atom(pos + 1)
            assert encoded[pos : pos + 1] == b"]"
            data, pos = atom(pos + 1)
            return (data, hint), pos
        return atom(pos)

    result, end = value(0)
    assert end == len(encoded)
    return result


# Basic ABNF core rules
@given(sexp_gen.sp)
def test_sp_strategy(s: str):
    """Tests the 'sp' strategy."""
    assert s == " ", "Expected a space character"


@given(sexp_gen.htab)
def test_htab_strategy(s: str):
    """Tests the 'htab' strategy."""
    assert s == "\t", "Expected a horizontal tab character"


@given(sexp_gen.cr)
def test_cr_strategy(s: str):
    """Tests the 'cr' strategy."""
    assert s == "\r", "Expected a carriage return character"


@given(sexp_gen.lf)
def test_lf_strategy(s: str):
    """Tests the 'lf' strategy."""
    assert s == "\n", "Expected a line feed character."


@given(sexp_gen.alpha)
def test_alpha_strategy(s: str):
    """Tests the 'alpha' strategy."""
    assert re.fullmatch(r"[a-zA-Z]", s)


@given(sexp_gen.digit)
def test_digit_strategy(s: str):
    """Tests the 'digit' strategy."""
    assert re.fullmatch(r"[0-9]", s)


@given(sexp_gen.hexdig)
def test_hexdig_strategy(s: str):
    """Tests the 'hexdig' strategy."""
    assert re.fullmatch(r"[0-9a-fA-F]", s)


@given(sexp_gen.dquote)
def test_dquote_strategy(s: str):
    """Tests the 'dquote' strategy."""
    assert s == '"'


@given(sexp_gen.octet)
def test_octet_strategy(b: bytes):
    """Tests the 'octet' strategy."""
    assert isinstance(b, bytes)
    assert len(b) == 1


# S-expression specific basic rules
@given(sexp_gen.vtab)
def test_vtab_strategy(s: str):
    """Tests the 'vtab' strategy."""
    assert s == "\v"


@given(sexp_gen.ff)
def test_ff_strategy(s: str):
    """Tests the 'ff' strategy."""
    assert s == "\f"


@given(sexp_gen.whitespace)
def test_whitespace_strategy(s: str):
    """Tests the 'whitespace' strategy."""
    assert re.fullmatch(r"[\s]", s)
    assert len(s) == 1


@given(sexp_gen.base_64_chars)
def test_base_64_chars_strategy(s: str):
    """Tests the 'base-64-chars' strategy."""
    b64_char_ws = r"[a-zA-Z0-9+/][\s]*"
    b64_chars_re = f"(?:{b64_char_ws}){{4}}"
    assert re.fullmatch(b64_chars_re, s)
    parser = SExpressionParser(s)
    assert parser.parse_base_64_chars() == 4
    assert parser.at_end()


@given(sexp_gen.base_64_char)
def test_base_64_char_strategy(s: str):
    """Tests the 'base-64-char' strategy."""
    assert re.fullmatch(r"[a-zA-Z0-9+/]", s)


@given(sexp_gen.base_64_end)
def test_base_64_end_strategy(s: str):
    """Tests the 'base-64-end' strategy."""
    ws = r"[\s]*"
    b64_char_ws = f"[a-zA-Z0-9+/]{ws}"
    # base-64-chars
    part1 = f"(?:{b64_char_ws}){{4}}"
    # 3(base-64-char *whitespace) ["=" *whitespace]
    part2 = f"(?:{b64_char_ws}){{3}}(?:={ws})?"
    # 2(base-64-char *whitespace) *2("=" *whitespace)
    part3 = f"(?:{b64_char_ws}){{2}}(?:={ws}){{0,2}}"
    b64_end_re = f"(?:{part1}|{part2}|{part3})"
    assert re.fullmatch(b64_end_re, s)
    parser = SExpressionParser(s)
    assert parser.parse_base_64_end() == len("".join(s.split()).rstrip("="))
    assert parser.at_end()


@given(sexp_gen.decimal)
def test_decimal_strategy(s: str):
    """Tests the 'decimal' strategy."""
    assert re.fullmatch(r"0|[1-9][0-9]*", s)


@given(sexp_gen.base_64)
def test_base_64_strategy(s: str):
    """Tests the 'base-64' strategy."""
    ws = r"[\s]*"
    b64_char = r"[a-zA-Z0-9+/]"
    b64_char_ws = f"{b64_char}{ws}"
    b64_chars = f"(?:{b64_char_ws}){{4}}"
    # base-64-end parts
    end_part1 = b64_chars
    end_part2 = f"(?:{b64_char_ws}){{3}}(?:={ws})?"
    end_part3 = f"(?:{b64_char_ws}){{2}}(?:={ws}){{0,2}}"
    b64_end = f"(?:{end_part1}|{end_part2}|{end_part3})"
    # Content inside pipes
    content = f"{ws}(?:{b64_chars})*(?:{b64_end})?"
    # Full base-64 regex
    b64_re = f"(?:0|[1-9][0-9]*)?\\|{content}\\|"
    assert re.fullmatch(b64_re, s)
    prefix, content, _ = s.split("|")
    decoded = base64.b64decode("".join(content.split()), validate=True)
    assert not prefix or int(prefix) == len(decoded)
    assert "".join(content.split()) == base64.b64encode(decoded).decode("ascii")
    assert SExpressionParser(s).parse() == decoded


@given(sexp_gen.hexadecimals)
def test_hexadecimals_strategy(s: str):
    """Tests the 'hexadecimals' strategy."""
    ws = r"[\s]*"
    hexdig_ws = f"[0-9a-fA-F]{ws}"
    hexadecimals_re = f"{hexdig_ws}[0-9a-fA-F]"
    assert re.fullmatch(hexadecimals_re, s, re.IGNORECASE)
    parser = SExpressionParser(s)
    assert parser.parse_hexadecimals() == "".join(s.split())
    assert parser.at_end()


@given(sexp_gen.hexadecimal)
def test_hexadecimal_strategy(s: str):
    """Tests the 'hexadecimal' strategy."""
    ws = r"[\s]*"
    hexdig_ws = f"[0-9a-fA-F]{ws}"
    hexadecimals = f"({hexdig_ws}{hexdig_ws})*"
    hex_re = f"(0|[1-9][0-9]*)?#{ws}{hexadecimals}#{ws}"
    assert re.fullmatch(hex_re, s, re.IGNORECASE)
    prefix, content, _ = s.split("#")
    decoded = bytes.fromhex("".join(content.split()))
    assert not prefix or int(prefix) == len(decoded)
    assert SExpressionParser(s).parse() == decoded


@given(sexp_gen.simple_punc)
def test_simple_punc_strategy(s: str):
    """Tests the 'simple_punc' strategy."""
    assert re.fullmatch(r"[-./_:*+=]", s)


@given(sexp_gen.token)
def test_token_strategy(s: str):
    """Tests the 'token' strategy."""
    assert re.fullmatch(r"[a-zA-Z-./_:*+=][a-zA-Z0-9-./_:*+=]*", s)
    assert SExpressionParser(s).parse() == s.encode("ascii")


@given(sexp_gen.quote)
def test_quote_strategy(s: str):
    """Tests the 'quote' strategy."""
    assert s == "'"


@given(sexp_gen.backslash)
def test_backslash_strategy(s: str):
    """Tests the 'backslash' strategy."""
    assert s == "\\"


@given(sexp_gen.escaped)
def test_escaped_strategy(s: str):
    """Tests the 'escaped' strategy."""
    escaped_re = r"""
    \\(?:
        [?abfnrtv"'\\] |          # Simple escapes
        [0-7]{3} |                # Octal escape
        x[0-9a-fA-F]{2} |         # Hex escape
        \r\n? |                   # Carriage return
        \n\r?                     # Line feed
    )
    """
    assert re.fullmatch(escaped_re, s, re.VERBOSE)
    if re.fullmatch(r"\\[0-7]{3}", s):
        assert int(s[1:], 8) <= 255


@given(sexp_gen.printable)
def test_printable_strategy(s: str):
    """Tests the 'printable' strategy."""
    assert re.fullmatch(r"[\x20-\x21\x23-\x5B\x5D-\x7E]", s)


@given(sexp_gen.quoted_string)
def test_quoted_string_strategy(s: str):
    """Tests the 'quoted_string' strategy."""
    printable_char = r"[\x20-\x21\x23-\x5B\x5D-\x7E]"
    escaped_char = r"""\\(?:[?abfnrtv"'\\]|[0-7]{3}|x[0-9a-fA-F]{2}|\r\n?|\n\r?)"""
    quoted_re = f'(0|[1-9][0-9]*)?"(?:{printable_char}|{escaped_char})*"'
    assert re.fullmatch(quoted_re, s)
    prefix = s[: s.index('"')]
    decoded = decode_quoted(s)
    assert not prefix or int(prefix) == len(decoded)
    assert SExpressionParser(s).parse() == decoded


@given(sexp_gen.verbatim)
def test_verbatim_strategy(s: str):
    """Tests the 'verbatim' strategy."""
    match = re.match(r"([0-9]+):", s)
    assert match
    length_str = match.group(1)
    length = int(length_str)
    header = f"{length_str}:"
    content = s[len(header) :]
    assert len(content.encode("utf-8")) == length
    assert SExpressionParser(s).parse() == content.encode("utf-8")


@given(sexp_gen.simple_string)
def test_simple_string_strategy(s: str):
    """Tests the 'simple_string' strategy."""
    assert isinstance(s, str)


@given(sexp_gen.display)
def test_display_strategy(s: str):
    """Tests the 'display' strategy."""
    assert s.startswith("[") and s.strip().endswith("]")


@given(sexp_gen.string)
def test_string_strategy(s: str):
    """Tests the 'string' strategy."""
    assert isinstance(s, str)


@given(sexp_gen.value)
def test_value_strategy(s: str):
    """Tests the 'value' strategy."""
    assert isinstance(s, str)


@given(sexp_gen.sexp)
def test_sexp_strategy(s: str):
    """Tests the 'sexp' strategy."""
    assert isinstance(s, str)


@given(sexp_gen.canonical)
def test_canonical_strategy(encoded: bytes):
    canonical_oracle(encoded)


@given(sexp_gen.basic_transport)
def test_basic_transport_strategy(encoded: bytes):
    if encoded.startswith(b"{"):
        assert encoded.endswith(b"}")
        body = b"".join(encoded[1:-1].split())
        encoded = base64.b64decode(body, validate=True)
        assert base64.b64encode(encoded) == body
    canonical_oracle(encoded)


def canonical_expected(value):
    if isinstance(value, list):
        return [canonical_expected(item) for item in value]
    if isinstance(value, tuple):
        return DisplayString(data=value[0], display_hint=value[1])
    return value


def advanced_oracle(text: str):
    """Decode generated advanced expressions without the production parser."""
    encoded = text.encode("utf-8")
    whitespace = b" \t\v\r\n\f"

    def skip(pos):
        while pos < len(encoded) and encoded[pos] in whitespace:
            pos += 1
        return pos

    def atom(pos):
        prefix = re.match(rb"(?:0|[1-9][0-9]*)", encoded[pos:])
        size = int(prefix.group()) if prefix else None
        if prefix:
            pos += len(prefix.group())
        marker = encoded[pos : pos + 1]
        if marker == b":" and size is not None:
            start = pos + 1
            data = encoded[start : start + size]
            assert len(data) == size
            return data, start + size
        if marker == b'"':
            match = re.match(
                rb'''"(?:[\x20-\x21\x23-\x5b\x5d-\x7e]|\\(?:[?abfnrtv"'\\]|[0-7]{3}|x[0-9a-fA-F]{2}|\r\n?|\n\r?))*"''',
                encoded[pos:],
            )
            assert match
            data = decode_quoted(match.group().decode("ascii"))
            end = pos + len(match.group())
        elif marker in (b"#", b"|"):
            end = encoded.index(marker, pos + 1)
            content = encoded[pos + 1 : end]
            if marker == b"#":
                assert re.fullmatch(rb"[0-9a-fA-F\x20\t\v\r\n\f]*", content)
                data = bytes.fromhex(b"".join(content.split()).decode("ascii"))
            else:
                assert re.fullmatch(rb"[a-zA-Z0-9+/=\x20\t\v\r\n\f]*", content)
                data = base64.b64decode(b"".join(content.split()), validate=True)
            end += 1
        else:
            assert size is None
            match = re.match(rb"[a-zA-Z./_:*+=-][a-zA-Z0-9./_:*+=-]*", encoded[pos:])
            assert match
            return match.group(), pos + len(match.group())
        assert size is None or size == len(data)
        return data, end

    def value(pos):
        if encoded[pos : pos + 1] == b"(":
            items = []
            pos = skip(pos + 1)
            while encoded[pos : pos + 1] != b")":
                item, pos = value(pos)
                items.append(item)
                next_pos = skip(pos)
                assert next_pos > pos or encoded[pos : pos + 1] == b")"
                pos = next_pos
            return items, pos + 1
        if encoded[pos : pos + 1] == b"[":
            hint, pos = atom(skip(pos + 1))
            pos = skip(pos)
            assert encoded[pos : pos + 1] == b"]"
            data, pos = atom(skip(pos + 1))
            return (data, hint), pos
        return atom(pos)

    result, end = value(skip(0))
    assert skip(end) == len(encoded)
    return result


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [
        (
            '([hint]2:é 1"\\x41" #4 2# |Qw==| ())',
            [(b"\xc3\xa9", b"hint"), b"A", b"B", b"C", []],
        ),
        ('[1:h]1"\\n"', (b"\n", b"h")),
    ],
)
def test_advanced_oracle_examples(encoded, expected):
    assert advanced_oracle(encoded) == expected


@pytest.mark.parametrize(
    "encoded",
    ["(a [h]x[y]z)", "[ [h]x ]y", "2:éx", '2"x"', "a trailing"],
)
def test_advanced_oracle_rejects_invalid_or_unseparated(encoded):
    with pytest.raises((AssertionError, ValueError)):
        advanced_oracle(encoded)


@given(sexp_gen.canonical)
def test_canonical_parser_interoperability(encoded: bytes):
    expected = canonical_expected(canonical_oracle(encoded))
    assert SExpressionParser(encoded).parse_canonical() == expected
    assert SExpressionParser(encoded).parse() == expected


@given(sexp_gen.basic_transport)
def test_basic_transport_parser_interoperability(encoded: bytes):
    canonical = encoded
    if encoded.startswith(b"{"):
        canonical = base64.b64decode(b"".join(encoded[1:-1].split()), validate=True)

    assert SExpressionParser(encoded).parse() == canonical_expected(
        canonical_oracle(canonical),
    )


@given(sexp_gen.sexp | sexp_gen.value)
def test_advanced_parser_interoperability(encoded: str):
    expected = canonical_expected(advanced_oracle(encoded))
    assert SExpressionParser(encoded).parse() == expected
    assert SExpressionParser(encoded.encode("utf-8")).parse() == expected
