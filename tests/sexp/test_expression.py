"""RFC examples, malformed inputs, binary/UTF-8 and complete-expression tests."""

import base64

from hypothesis import given, strategies as st
import pytest

from sexp import DisplayString, SExpressionParser, SexpParser


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("subject", b"subject"),
        ("//example.net/names/smith", b"//example.net/names/smith"),
        (":=..", b":=.."),
        ("-42", b"-42"),
        ("0:", b""),
        ('3:::"', b'::"'),
        ('3"abc"', b"abc"),
        ('3"\\n\\n\\n"', b"\n\n\n"),
        ('""', b""),
        ("# 616\n263 #", b"abc"),
        ("3|YWJj|", b"abc"),
        ("|YWJjZA|", b"abcd"),
        ("|YQ=|", b"a"),
        ("||", b""),
        ("()", []),
        (" \t\v\r\n\f( \t\v\r\n\f)\r\n", []),
        ("(a bob c)", [b"a", b"bob", b"c"]),
        (
            "( a ( bob c ) ( ( d e ) ( e f ) )  )",
            [b"a", [b"bob", b"c"], [[b"d", b"e"], [b"e", b"f"]]],
        ),
        (
            "(11:certificate(6:issuer3:bob)(7:subject5:alice))",
            [b"certificate", [b"issuer", b"bob"], [b"subject", b"alice"]],
        ),
        (
            '(|ODpFeGFtcGxlIQ==| "1997" murphy 3:XC+)',
            [b"8:Example!", b"1997", b"murphy", b"XC+"],
        ),
        ("(a()b)", [b"a", [], b"b"]),
        ("(3:abc3:def)", [b"abc", b"def"]),
        ('(a"b"#63#|ZA==|)', [b"a", b"b", b"c", b"d"]),
        ("(a1:b)", [b"a1:b"]),
        ("[image/gif]#474946#", DisplayString(b"GIF", b"image/gif")),
        (
            '[ "text/plain; charset=utf-8" ] 7:hél lo',
            DisplayString("hél lo".encode(), b"text/plain; charset=utf-8"),
        ),
        ("[0:]0:", DisplayString(b"", b"")),
        ("([a]b[0:]c)", [DisplayString(b"b", b"a"), DisplayString(b"c", b"")]),
        (b"3:\x00\xff)", b"\x00\xff)"),
        (b"[1:\xff]1:\xfe", DisplayString(b"\xfe", b"\xff")),
        ("6:héllo", "héllo".encode()),
        ("4:🙂", "🙂".encode()),
        (r'"h\xC3\xA9llo"', "héllo".encode()),
        ("|aMOpbGxv|", "héllo".encode()),
    ],
)
def test_complete_expression(source, expected):
    parser = SExpressionParser(source)
    assert parser.parse() == expected
    assert parser.at_end()


@pytest.mark.parametrize(
    ("escape", "expected"),
    [
        (r"\a", b"\a"),
        (r"\b", b"\b"),
        (r"\t", b"\t"),
        (r"\v", b"\v"),
        (r"\n", b"\n"),
        (r"\f", b"\f"),
        (r"\r", b"\r"),
        (r"\"", b'"'),
        (r"\'", b"'"),
        (r"\?", b"?"),
        (r"\\", b"\\"),
        (r"\000", b"\x00"),
        (r"\377", b"\xff"),
        (r"\xFe", b"\xfe"),
        ("\\\r", b""),
        ("\\\n", b""),
        ("\\\r\n", b""),
        ("\\\n\r", b""),
    ],
)
def test_escape_sequences(escape, expected):
    parser = SExpressionParser(escape)
    assert parser.parse_escaped() == expected
    assert parser.at_end()
    assert SExpressionParser(f'{len(expected)}"{escape}"').parse() == expected


@pytest.mark.parametrize(
    "source",
    [
        "",
        " \n",
        "(",
        ")",
        "(()",
        "())",
        "()()",
        "a b",
        "0:0:",
        "123",
        "01:a",
        "00:",
        '01"a"',
        "01#61#",
        "01|YQ==|",
        "1 :a",
        "1:a!",
        "2:a",
        "-1:a b",
        "[a]",
        "[]b",
        "[a b]c",
        "[[a]b]c",
        "[a]()",
        "[a][b]c",
        "[a",
        "[a)b",
        "[a]1:",
        '"unterminated',
        '"raw\nnewline"',
        '"raw\x00NUL"',
        '"é"',
        "é",
        r'"\q"',
        '"trailing\\',
        r'"\0"',
        r'"\00"',
        r'"\008"',
        r'"\400"',
        r'"\777"',
        r'"\x"',
        r'"\x0"',
        r'"\x0G"',
        '2"a"',
        '0"a"',
        "2#61#",
        "0#61#",
        "2|YQ==|",
        "0|YQ==|",
        "#0#",
        "#aa",
        "#g0#",
        "#\u00a061#",
        "|Y\u00a0Q==|",
        "|A|",
        "|=|",
        "|====|",
        "|AAAA=|",
        "|AA===|",
        "|AA=A|",
        "|AA!|",
        "{",
        "{}",
        "{eA==}",
        "{MDo=}{MDo=}",
        "({MDo=})",
        "{KCAp}",
        "{KGEp}",
        "{ezBEbz19}",
    ],
)
def test_malformed_expression(source):
    with pytest.raises(ValueError):
        SExpressionParser(source).parse()


@pytest.mark.parametrize("source", [None, 123, bytearray(b"0:")])
def test_input_type(source):
    with pytest.raises(TypeError, match="str or bytes"):
        SExpressionParser(source)


@pytest.mark.parametrize(
    "source",
    ["0:", "()", "(6:issuer3:bob)", "(4:icon[12:image/bitmap]9:xxxxxxxxx)", "[0:]0:"],
)
def test_canonical_expression(source):
    assert (
        SExpressionParser(source).parse_canonical() == SExpressionParser(source).parse()
    )


@pytest.mark.parametrize(
    "source",
    [
        "a",
        '"a"',
        "#61#",
        "|YQ==|",
        " 0:",
        "0: ",
        "( 0:)",
        "(0: )",
        "[ 0:]0:",
        "[0: ]0:",
        "[0:] 0:",
        "[a]0:",
        "[0:]a",
        "01:a",
        "()()",
        "{MDo=}",
    ],
)
def test_reject_noncanonical_expression(source):
    with pytest.raises(ValueError):
        SExpressionParser(source).parse_canonical()


@pytest.mark.parametrize("source", ["{KDE6YTE6YjE\n6Yyk= }", " { KDE6YTE6YjE6Yyk }\n"])
def test_basic_transport_rfc_example(source):
    assert SExpressionParser(source).parse() == [b"a", b"b", b"c"]


def test_cursor_counts_utf8_bytes():
    parser = SExpressionParser("(2:é4:🙂)")
    assert parser.parse() == ["é".encode(), "🙂".encode()]
    assert parser.index == len("(2:é4:🙂)".encode())
    assert SExpressionParser("1:é").parse_value() == b"\xc3"
    with pytest.raises(ValueError, match="trailing input"):
        SExpressionParser("1:é").parse()


def test_binary_delimiters_are_not_syntax():
    data = bytes(range(256))
    encoded = b"[4:a]b[]256:" + data
    assert SExpressionParser(encoded).parse() == DisplayString(data, b"a]b[")


def test_partial_grammar_methods():
    parser = SExpressionParser("(a) b")
    assert parser.parse_value() == [b"a"]
    assert parser.index == 3
    assert parser.parse_whitespace()
    assert parser.parse_value() == b"b"
    assert SExpressionParser('"abc"').parse_quoted_string() == b"abc"
    assert SExpressionParser("[a]\t").parse_display() == b"a"
    assert SExpressionParser("[a]b").parse_string() == DisplayString(b"b", b"a")
    assert SExpressionParser("a").parse_string() == b"a"
    assert SExpressionParser("2:ab").parse_verbatim() == b"ab"
    assert SExpressionParser("a").parse_simple_string() == b"a"
    assert SExpressionParser("a").parse_sexp() == b"a"


@pytest.mark.parametrize(
    "method,source",
    [
        ("parse_verbatim", "a"),
        ("parse_verbatim", "2a"),
        ("parse_quoted_string", "a"),
        ("parse_display", "a"),
        ("parse_escaped", "a"),
    ],
)
def test_primitive_requires_its_delimiter(method, source):
    with pytest.raises(ValueError):
        getattr(SExpressionParser(source), method)()


@pytest.mark.parametrize(
    "method,character",
    [
        ("parse_simple_punc", ":"),
        ("parse_quote", "'"),
        ("parse_backslash", "\\"),
        ("parse_printable", "!"),
    ],
)
def test_character_primitives(method, character):
    for source, expected in [(character, True), ("", False), ("\x00", False)]:
        parser = SExpressionParser(source)
        assert getattr(parser, method)() is expected
        assert parser.index == int(expected)


def test_hexadecimal_no_match_preserves_length_prefix():
    parser = SExpressionParser("3:abc")
    assert parser.parse_hexadecimal() is None
    assert parser.index == 0


@pytest.mark.parametrize(
    "method,source",
    [
        ("parse_base_64", "2|YQ==|"),
        ("parse_hexadecimal", "2#61#"),
        ("parse_quoted_string", '2"a"'),
    ],
)
def test_primitive_length_mismatch(method, source):
    with pytest.raises(ValueError, match="Length mismatch"):
        getattr(SExpressionParser(source), method)()


def test_legacy_name():
    assert SexpParser is SExpressionParser
    assert SexpParser("(a)").parse() == [b"a"]


def test_deep_and_long_lists():
    depth = 5000
    result = SExpressionParser("(" * depth + "a" + ")" * depth).parse()
    for _ in range(depth):
        assert isinstance(result, list)
        assert len(result) == 1
        result = result[0]
    assert result == b"a"
    with pytest.raises(ValueError, match="Missing closing"):
        SExpressionParser("(" * depth).parse()
    assert SExpressionParser("(" + "1:a" * 5000 + ")").parse() == [b"a"] * 5000


@given(st.binary(max_size=100))
def test_equivalent_octet_encodings(data):
    prefix = str(len(data)).encode()
    verbatim = prefix + b":" + data
    quoted = b'"' + b"".join(f"\\x{byte:02x}".encode() for byte in data) + b'"'
    hexadecimal = b"#" + data.hex().encode() + b"#"
    encoded = base64.b64encode(data)
    for source in (
        verbatim,
        quoted,
        hexadecimal,
        b"|" + encoded + b"|",
        b"|" + encoded.rstrip(b"=") + b"|",
    ):
        assert SExpressionParser(source).parse() == data
    for source in (quoted, hexadecimal, b"|" + encoded + b"|"):
        assert SExpressionParser(prefix + source).parse() == data
    transport = b"{" + base64.b64encode(verbatim) + b"}"
    assert SExpressionParser(transport).parse() == data


@given(st.binary(max_size=100))
def test_arbitrary_input_never_leaks_internal_errors(data):
    try:
        SExpressionParser(data).parse()
    except ValueError:
        pass
