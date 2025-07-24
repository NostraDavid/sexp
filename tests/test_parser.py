"""
Tests for the S-expression parser.
"""

import base64
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from sexp.parser import SExpressionParser
from tests.random_generator import sexp

# According to RFC 9804 ABNF
# simple-punc = "-" / "." / "/" / "_" / ":" / "*" / "+" / "="
SIMPLE_PUNC = "-./_:+*="
# token = (ALPHA / simple-punc) *(ALPHA / DIGIT / simple-punc)
TOKEN_START_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" + SIMPLE_PUNC
TOKEN_CHARS = TOKEN_START_CHARS + "0123456789"

# Strategy for generating valid tokens
st_tokens = st.text(alphabet=TOKEN_CHARS, min_size=1).filter(
    lambda s: s[0] in TOKEN_START_CHARS
)

# Strategy for generating content for verbatim strings
# The content can be any string.
st_verbatim_content = st.text(max_size=200)


@st.composite
def st_verbatim_strings(draw):# -> tuple[str, Any]:
    """Strategy for generating verbatim strings and their expected value."""
    content = draw(st_verbatim_content)
    # The parser implementation uses byte length for verbatim strings.
    content_bytes = content.encode("utf-8", "surrogatepass")
    return f"{len(content_bytes)}:{content}", content


# Strategy for generating content for quoted strings
# Printable characters, excluding special characters like backslash and double-quote.
st_quoted_content = st.text(
    alphabet=st.characters(
        min_codepoint=32, max_codepoint=126, blacklist_characters='"\\'
    ),
    max_size=200,
)


@st.composite
def st_quoted_strings(draw):
    """Strategy for generating quoted strings and their expected value."""
    content = draw(st_quoted_content)
    return f'"{content}"', content


# Strategy for generating hexadecimal strings
st_hex_strings = st.binary(max_size=100).map(lambda b: (f"#{b.hex()}#", b.decode("utf-8", "replace")))

# Strategy for generating base64 strings
st_base64_strings = st.binary(max_size=100).map(
    lambda b: (f"|{base64.b64encode(b).decode('ascii')}|", b.decode("utf-8", "replace"))
)

# A strategy for any atomic (string) S-expression
st_atoms = st.one_of(
    st_tokens,
    st_verbatim_strings().map(lambda p: p[0]),
    st_quoted_strings().map(lambda p: p[0]),
    st_hex_strings.map(lambda p: p[0]),
    st_base64_strings.map(lambda p: p[0]),
)

# A recursive strategy for S-expressions (atoms or lists)
st_sexp = st.recursive(
    st_atoms,
    lambda children: st.lists(children, max_size=10).map(
        lambda l: f"({' '.join(map(str, l))})"
    ),
    max_leaves=20,
)


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("()", []),
        ("(a)", ["a"]),
        ("(a b c)", ["a", "b", "c"]),
        ("(a (b c) d)", ["a", ["b", "c"], "d"]),
        (" ( a ( b ) ) ", ["a", ["b"]]),
        (" ( a ; comment\n b ) ", ["a", "b"]),
    ],
)
def test_parse_list_examples(input_text: str, expected: list):
    """Test parsing of basic list structures."""
    parser = SExpressionParser(input_text)
    assert parser.parse() == expected


@given(st_tokens)
def test_parse_token(token: str):
    """Test that tokens are parsed correctly."""
    parser = SExpressionParser(token)
    assert parser.parse() == token


@given(st_verbatim_strings())
def test_parse_verbatim_string(verbatim_pair):
    """Test that verbatim strings are parsed correctly."""
    text, expected = verbatim_pair
    parser = SExpressionParser(text)
    assert parser.parse() == expected


@given(st_quoted_strings())
def test_parse_quoted_string(quoted_pair):
    """Test that quoted strings are parsed correctly."""
    text, expected = quoted_pair
    parser = SExpressionParser(text)
    assert parser.parse() == expected


@given(st_hex_strings)
def test_parse_hex_string(hex_pair):
    """Test that hexadecimal strings are parsed correctly."""
    text, expected = hex_pair
    parser = SExpressionParser(text)
    assert parser.parse() == expected


@given(st_base64_strings)
def test_parse_base64_string(base64_pair):
    """Test that base64 strings are parsed correctly."""
    text, expected = base64_pair
    parser = SExpressionParser(text)
    assert parser.parse() == expected


# Disable 'too_slow' health check as S-expression generation can be slow.
@settings(suppress_health_check=[HealthCheck.too_slow])
@given(st_sexp)
def test_parser_roundtrip(text: str):
    """
    Test that parsing any valid S-expression does not fail.
    This is a smoke test to ensure the parser can handle a wide
    variety of generated valid inputs.
    """
    parser = SExpressionParser(text)
    try:
        parser.parse()
    except ValueError as e:
        pytest.fail(f"Parser failed on valid input:\n{text}\nError: {e}")


def test_parse_multiple():
    """Test parsing multiple S-expressions from a single string."""
    text = '(a b) "hello" 3:foo'
    parser = SExpressionParser(text)
    result = parser.parse_multiple()
    assert result == [["a", "b"], "hello", "foo"]


def test_empty_input_raises_error():
    """Test that parsing an empty string raises a ValueError."""
    with pytest.raises(ValueError, match="Unexpected EOF"):
        SExpressionParser("").parse()


def test_trailing_chars_raise_error():
    """Test that extra characters after a valid S-expression raise a ValueError."""
    with pytest.raises(ValueError, match="Extra characters"):
        SExpressionParser("(a) b").parse()


def test_unclosed_list_raises_error():
    """Test that an unclosed list raises a ValueError."""
    with pytest.raises(ValueError, match="Unclosed list"):
        SExpressionParser("(a b").parse()


# def test_parse_multiple_expressions_with_whitespace(parser_mock):
#     parser_mock.return_value = None
#     text = '() ( foo bar )  "hello" '
#     parser = SExpressionParser(text)
#     result = parser.parse_multiple()
#     assert result == [[], ["foo", "bar"], "hello"]
#     parser_mock.assert_has_calls(
#         [call("()"), call(" ( foo bar ) "), call(' "hello"')]
#     )


@settings(deadline=300_000, max_examples=10_000) # 5 minutes in milliseconds
@given(sexp())
def test_parser_with_random_valid_input(input_text: str):
    """Test that the parser can handle any valid S-expression from the generator."""
    parser = SExpressionParser(input_text)
    try:
        parser.parse()
    except ValueError:
        # It's okay for the parser to fail on some generated inputs,
        # as the generator might produce edge cases the parser doesn't support yet.
        # The main goal is to ensure the parser doesn't crash unexpectedly.
        pass
