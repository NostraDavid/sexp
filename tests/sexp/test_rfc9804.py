"""Conformance vectors from RFC 9804, with literal byte-valued expectations.

Source: https://datatracker.ietf.org/doc/html/rfc9804 (June 2025).
The existing expression tests additionally cover malformed input and escapes.
"""

import base64
import string

import pytest

from sexp import DisplayString, SExpressionParser


@pytest.mark.parametrize(
    "source,expected",
    [
        pytest.param(
            '(snicker "abc" (#03# |YWJj|))',
            [b"snicker", b"abc", [b"\x03", b"abc"]],
            id="section-1-introduction",
        ),
        pytest.param(
            '(abc (de #6667#) "ghi jkl")',
            [b"abc", [b"de", b"fg"], b"ghi jkl"],
            id="section-2-list",
        ),
        pytest.param("3:abc", b"abc", id="section-4.1-verbatim-abc"),
        pytest.param("7:subject", b"subject", id="section-4.1-verbatim-subject"),
        pytest.param('4:::":', b'::":', id="section-4.1-verbatim-delimiters"),
        pytest.param(
            "12:hello world!",
            b"hello world!",
            id="section-4.1-verbatim-space",
        ),
        pytest.param("10:abcdefghij", b"abcdefghij", id="section-4.1-verbatim-ten"),
        pytest.param("0:", b"", id="section-4.1-verbatim-empty"),
        pytest.param('"subject"', b"subject", id="section-4.2-quoted-subject"),
        pytest.param('"hi there"', b"hi there", id="section-4.2-quoted-space"),
        pytest.param('7"subject"', b"subject", id="section-4.2-quoted-length"),
        pytest.param(
            r'"\xFE is the same octet as \376"',
            b"\xfe is the same octet as \xfe",
            id="section-4.2-quoted-hex-octal",
        ),
        pytest.param(r'3"\n\n\n"', b"\n\n\n", id="section-4.2-quoted-decoded-length"),
        pytest.param(
            r'"This has\n two lines."',
            b"This has\n two lines.",
            id="section-4.2-quoted-newline",
        ),
        pytest.param(
            '"This has \\\n one line."',
            b"This has  one line.",
            id="section-4.2-quoted-continuation",
        ),
        pytest.param('""', b"", id="section-4.2-quoted-empty"),
        pytest.param("subject", b"subject", id="section-4.3-token-subject"),
        pytest.param("not-before", b"not-before", id="section-4.3-token-hyphen"),
        pytest.param(":=..", b":=..", id="section-4.3-token-punctuation"),
        pytest.param("class-of-1997", b"class-of-1997", id="section-4.3-token-digits"),
        pytest.param(
            "//example.net/names/smith",
            b"//example.net/names/smith",
            id="section-4.3-token-url",
        ),
        pytest.param("*", b"*", id="section-4.3-token-star"),
        pytest.param("#616263#", b"abc", id="section-4.4-hex"),
        pytest.param("3#616263#", b"abc", id="section-4.4-hex-length"),
        pytest.param("# 616\n263 #", b"abc", id="section-4.4-hex-whitespace"),
        pytest.param("##", b"", id="section-4.4-hex-empty"),
        pytest.param("|YWJj|", b"abc", id="section-4.5-base64"),
        pytest.param("| Y W\nJ j |", b"abc", id="section-4.5-base64-whitespace"),
        pytest.param("3|YWJj|", b"abc", id="section-4.5-base64-length"),
        pytest.param("|YWJjZA==|", b"abcd", id="section-4.5-base64-padded"),
        pytest.param("|YWJjZA|", b"abcd", id="section-4.5-base64-unpadded"),
        pytest.param("||", b"", id="section-4.5-base64-empty"),
        pytest.param(
            "[gif] #61626364#",
            DisplayString(b"abcd", b"gif"),
            id="section-9.2.2-hinted-string",
        ),
        pytest.param(
            "(abc [d]ef (g))",
            [b"abc", DisplayString(b"ef", b"d"), [b"g"]],
            id="section-9.2.3-in-memory-list",
        ),
    ],
)
def test_rfc_examples(source, expected):
    assert SExpressionParser(source).parse() == expected


@pytest.mark.parametrize(
    "source,expected",
    [
        ("(6:issuer3:bob)", [b"issuer", b"bob"]),
        (
            "(4:icon[12:image/bitmap]9:xxxxxxxxx)",
            [b"icon", DisplayString(b"xxxxxxxxx", b"image/bitmap")],
        ),
        (
            "(7:subject(3:ref5:alice6:mother))",
            [b"subject", [b"ref", b"alice", b"mother"]],
        ),
        ("10:foo)]}>bar", b"foo)]}>bar"),
        ("0:", b""),
        ("(1:a1:b1:c)", [b"a", b"b", b"c"]),
    ],
)
def test_sections_6_and_7_mandatory_canonical_and_basic(source, expected):
    assert SExpressionParser(source).parse_canonical() == expected
    assert SExpressionParser(source).parse() == expected
    encoded = base64.b64encode(source.encode("ascii"))
    for padding_removed in range(len(encoded) - len(encoded.rstrip(b"=")) + 1):
        body = encoded[: len(encoded) - padding_removed]
        assert SExpressionParser(b"{" + body + b"}").parse() == expected
        for whitespace in b" \t\r\n\v\f":
            separator = bytes([whitespace])
            spaced = (
                separator + separator.join(bytes([byte]) for byte in body) + separator
            )
            assert SExpressionParser(b"{" + spaced + b"}").parse() == expected


@pytest.mark.parametrize(
    "method,alphabet",
    [
        ("parse_alpha", string.ascii_letters.encode()),
        ("parse_digit", string.digits.encode()),
        ("parse_hexdigit", string.hexdigits.encode()),
        ("parse_base_64_char", (string.ascii_letters + string.digits + "+/").encode()),
        ("parse_whitespace", b" \t\r\n\v\f"),
        (
            "parse_printable",
            bytes(byte for byte in range(32, 127) if byte not in b'"\\'),
        ),
        ("parse_simple_punc", b"-./_:*+="),
        ("parse_octet", bytes(range(256))),
    ],
)
def test_sections_3_and_7_character_classes_for_every_octet(method, alphabet):
    for byte in range(256):
        parser = SExpressionParser(bytes([byte]))
        expected = byte in alphabet
        assert getattr(parser, method)() is expected, (method, byte)
        assert parser.index == int(expected)


@pytest.mark.parametrize(
    "method,source,expected,remaining",
    [
        ("parse_base_64_chars", "YWJjZGVm", 4, "ZGVm"),
        ("parse_base_64_end", "YWJjZGVm", 4, "ZGVm"),
        ("parse_hexadecimals", "616263", "61", "6263"),
    ],
)
def test_section_7_helpers_consume_one_abnf_group(method, source, expected, remaining):
    parser = SExpressionParser(source)
    assert getattr(parser, method)() == expected
    assert parser.text[parser.index :] == remaining


def test_section_4_6_literal_utf8_example_is_not_silently_corrected():
    # The RFC prose says ö, but its literal C3 B7 bytes encode ÷, not C3 B6 (ö).
    literal = r'["text/plain; charset=utf-8"]"b\xC3\xB7b\xE2\x98\xBA"'
    value = SExpressionParser(literal).parse()
    assert value == DisplayString("b÷b☺".encode(), b"text/plain; charset=utf-8")
    corrected = literal.replace(r"\xB7", r"\xB6")
    assert SExpressionParser(corrected).parse() == DisplayString(
        "böb☺".encode(),
        value.display_hint,
    )


def test_section_4_6_explicit_default_hint_is_preserved():
    plain = SExpressionParser("abc").parse()
    hinted = SExpressionParser("[application/octet-stream]abc").parse()
    assert plain == b"abc"
    assert hinted == DisplayString(b"abc", b"application/octet-stream")
    assert SExpressionParser("[0:]abc").parse() == DisplayString(b"abc", b"")


@pytest.mark.parametrize(
    "data,encoded",
    [
        (b"", ""),
        (b"f", "Zg=="),
        (b"fo", "Zm8="),
        (b"foo", "Zm9v"),
        (b"foob", "Zm9vYg=="),
        (b"fooba", "Zm9vYmE="),
        (b"foobar", "Zm9vYmFy"),
    ],
)
def test_rfc4648_section_10_base64_vectors(data, encoded):
    assert SExpressionParser("|" + encoded + "|").parse() == data
    assert SExpressionParser(str(len(data)) + "|" + encoded + "|").parse() == data
