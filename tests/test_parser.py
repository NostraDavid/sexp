import base64
import pytest
from s_expression import SExpressionParser


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("()", []),  # Empty list
        ("(foo)", ["foo"]),  # Simple list with one atom
        ("(foo bar)", ["foo", "bar"]),  # Simple list with two atoms
        ("((foo) (bar))", [["foo"], ["bar"]]),  # Nested list
        ("(foo (bar baz))", ["foo", ["bar", "baz"]]),  # Mixed atoms and list
    ],
)
def test_parse_list(input_text: str, expected: list):
    """
    Test parsing lists, including nested lists and combinations of atoms and lists.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("#t", True),  # Boolean true
        ("#f", False),  # Boolean false
    ],
)
def test_parse_boolean(input_text: str, expected: bool):
    """
    Test parsing boolean literals.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("'foo", ["quote", "foo"]),  # Quoted atom
        ("'(foo bar)", ["quote", ["foo", "bar"]]),  # Quoted list
    ],
)
def test_parse_quoted_expression(input_text: str, expected: list):
    """
    Test parsing quoted expressions.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("#1A2B#", "+")  # Hexadecimal string
    ],
)
def test_parse_hexadecimal(input_text: str, expected: str):
    """
    Test parsing hexadecimal strings.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected


def test_empty_hexadecimal_string():
    """
    Test _parse_hexadecimal handles an empty hexadecimal string (##) without error.
    """
    instance = SExpressionParser(text="##")
    result = instance._parse_hexadecimal()
    assert result == ""


def test_invalid_hexadecimal_format():
    """
    Test _parse_hexadecimal raises ValueError for invalid hexadecimal format (missing closing '#').
    """
    instance = SExpressionParser(text="#1f4a9")  # Missing closing '#'
    with pytest.raises(
        ValueError, match="Expected closing '#' for hexadecimal string at position "
    ):
        instance._parse_hexadecimal()


def test_hexadecimal_unicode_decode_error():
    """
    Test _parse_hexadecimal handles UnicodeDecodeError by returning raw bytes.
    """
    # Hexadecimal encoding of invalid UTF-8 byte sequence
    invalid_utf8_hex = "fffefd"
    instance = SExpressionParser(text=f"#{invalid_utf8_hex}#")
    result = instance._parse_hexadecimal()
    assert result == b"\xff\xfe\xfd"


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("|SGVsbG8gd29ybGQ=|", "Hello world"),  # Base64 string
        ("|c3VwZXI=|", "super"),  # Base64 string with decoding
    ],
)
def test_parse_base64(input_text: str, expected: str):
    """
    Test parsing base64-encoded strings.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected


def test_invalid_base64_format():
    """
    Test _parse_base64 raises ValueError for invalid base64 format (missing closing '|').
    """
    instance = SExpressionParser(text="|SGVsbG8gd29ybGQ")  # Missing closing '|'
    with pytest.raises(
        ValueError, match="Expected closing '\|' for base64 string at position "
    ):
        instance._parse_base64()


def test_base64_unicode_decode_error():
    """
    Test _parse_base64 handles UnicodeDecodeError by returning raw bytes.
    """
    # Base64 encoding of invalid UTF-8 byte sequence
    invalid_utf8_base64 = base64.b64encode(b"\xff\xfe\xfd").decode("ascii")
    instance = SExpressionParser(text=f"|{invalid_utf8_base64}|")
    result = instance._parse_base64()
    assert result == b"\xff\xfe\xfd"


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("5:hello", "hello"),  # Verbatim string
        ("42", "42"),  # Numeric token
    ],
)
def test_parse_number_or_verbatim(input_text: str, expected: str):
    """
    Test parsing numbers or verbatim strings.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected


def test_verbatim_string_length_mismatch():
    """
    Test _parse_number_or_verbatim raises ValueError if the verbatim string length is incorrect.
    """
    instance = SExpressionParser(text="5:abcd")  # Length is 5, but only 4 characters provided
    with pytest.raises(ValueError, match="Verbatim string length mismatch at position "):
        instance._parse_number_or_verbatim()

@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("(foo ; this is a comment\nbar)", ["foo", "bar"]),  # Ignoring comment
        ("; entire line comment\n(foo)", ["foo"]),  # Comment before S-expression
    ],
)
def test_parse_ignore_comments(input_text: str, expected: list):
    """
    Test that comments are correctly ignored during parsing.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        (
            '(foo "quoted" bar)',
            ["foo", "quoted", "bar"],
        ),  # Quoted strings with double quotes
        (
            '(foo "hello \\\\world" bar)',
            ["foo", "hello \\world", "bar"],
        ),  # Properly escaped backslash within quoted string
    ],
)
def test_parse_quoted_strings(input_text: str, expected: list):
    """
    Test parsing quoted strings, including handling of escape sequences.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected


def test_unterminated_quoted_string():
    """
    Test _parse_quoted_string raises ValueError for unterminated quoted string.
    """
    instance = SExpressionParser(text='"unterminated')
    with pytest.raises(ValueError, match="Unterminated quoted string at end of input."):
        instance._parse_quoted_string()


def test_unknown_escape_sequence():
    """
    Test _parse_quoted_string handles unknown escape sequences as literal characters.
    """
    instance = SExpressionParser(text='"This is a test with \\x escape"')
    result = instance._parse_quoted_string()
    assert result == "This is a test with \\x escape"


def test_parse_quoted_minimal_strings():
    """
    This tiny example was failing.
    """
    parser = SExpressionParser('"a b"')
    result = parser.parse()
    assert result == "a b"


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("(foo >= bar)", ["foo", ">=", "bar"]),  # Comparison operators
        ("(foo <= bar)", ["foo", "<=", "bar"]),
    ],
)
def test_parse_comparison_operators(input_text: str, expected: list):
    """
    Test parsing comparison operators.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected


@pytest.mark.parametrize(
    "input_char, expected_output",
    [
        ("n", "\n"),
        ("t", "\t"),
        ("\\", "\\"),
        ('"', '"'),
        (" ", " "),
        ("a", "a"),  # No special escape, should return itself
        ("1", "1"),  # No special escape, should return itself
    ],
)
def test_handle_escape(input_char: str, expected_output: str, mocker):
    """
    Test _handle_escape with various escape and non-escape characters.
    """
    instance = SExpressionParser(
        text="dummy_text"
    )  # Replace with the correct class instantiation
    result = instance._handle_escape(input_char)
    assert result == expected_output
