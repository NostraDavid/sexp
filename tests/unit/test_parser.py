import base64
import re
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sexp.parser import SExpressionParser

from tests.unit.random_generator import (
    base64_strings,
    hex_strings,
    lists,
    quoted_strings,
    sexp,
    tokens,
    verbatim_strings,
)


@given(token_str=tokens())
def test_parse_token_hypothesis(token_str: str):
    """Verify that valid tokens are parsed correctly."""
    parser = SExpressionParser(token_str)
    result = parser.parse()
    assert result == token_str


@given(verbatim_str=verbatim_strings())
def test_parse_verbatim_string_hypothesis(verbatim_str: str):
    """Verify that valid verbatim strings are parsed correctly."""
    parser = SExpressionParser(verbatim_str)
    result = parser.parse()
    # Extract expected content from 'length:content'
    _, expected_content = verbatim_str.split(":", 1)
    assert result == expected_content


@given(quoted_str=quoted_strings())
def test_parse_quoted_string_hypothesis(quoted_str: str):
    """Verify that valid quoted strings are parsed correctly."""
    parser = SExpressionParser(quoted_str)
    result = parser.parse()
    # Manually unescape to get the expected result
    expected = (
        quoted_str[1:-1]
        .replace("\\\\", "\\")
        .replace('\\"', '"')
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\r", "\r")
    )
    assert result == expected


@given(hex_str=hex_strings())
def test_parse_hex_string_hypothesis(hex_str: str):
    """Verify that valid hex strings are parsed correctly."""
    parser = SExpressionParser(hex_str)
    result = parser.parse()
    # Extract hex content from '#content#'
    hex_content = hex_str[1:-1]
    if not hex_content:
        assert result == ""
    else:
        expected = bytes.fromhex(hex_content).decode("utf-8", errors="replace")
        assert result == expected


@given(b64_str=base64_strings())
def test_parse_base64_string_hypothesis(b64_str: str):
    """Verify that valid base64 strings are parsed correctly."""
    parser = SExpressionParser(b64_str)
    result = parser.parse()
    # Extract base64 content from '|content|'
    b64_content = b64_str[1:-1]
    expected = base64.b64decode(b64_content).decode("utf-8", errors="replace")
    assert result == expected


@given(list_str=lists())
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_parse_list_hypothesis(list_str: str):
    """Verify that valid lists can be parsed without error."""
    parser = SExpressionParser(list_str)
    result = parser.parse()
    assert isinstance(result, list)


@given(sexp_str=sexp())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=500)
def test_parse_sexp_does_not_raise_hypothesis(sexp_str: str):
    """Verify that any valid generated S-expression can be parsed without error."""
    # This test ensures the parser is robust against a wide variety of
    # valid inputs, including complex nested structures.
    parser = SExpressionParser(sexp_str)
    try:
        parser.parse()
    except ValueError as e:
        pytest.fail(f"Parser failed on valid input:\n{sexp_str}\nError: {e}")


@given(data=st.text())
def test_parse_multiple_hypothesis(data: str):
    """Test parsing multiple S-expressions from a single string."""
    # Create a string of multiple S-expressions separated by spaces
    token1 = "token1"
    token2 = "another-token"
    list1 = "(a b)"
    # Use a generated string, but clean it to be a valid token
    safe_data = re.sub(r"[\s\(\)#|;]", "_", data).strip()
    if not safe_data:
        safe_data = "safe"

    sexp_list = [token1, token2, list1, safe_data]
    input_str = " ".join(sexp_list)

    parser = SExpressionParser(input_str)
    result = parser.parse_multiple()

    assert len(result) == 4
    assert result[0] == token1
    assert result[1] == token2
    assert result[2] == ["a", "b"]
    assert result[3] == safe_data
