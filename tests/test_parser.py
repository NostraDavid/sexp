import pytest
from s_expression import SExpressionParser

@pytest.mark.parametrize("input_text, expected", [
    ("()", []),  # Empty list
    ("(foo)", ["foo"]),  # Simple list with one atom
    ("(foo bar)", ["foo", "bar"]),  # Simple list with two atoms
    ("((foo) (bar))", [["foo"], ["bar"]]),  # Nested list
    ("(foo (bar baz))", ["foo", ["bar", "baz"]]),  # Mixed atoms and list
])
def test_parse_list(input_text: str, expected: list):
    """
    Test parsing lists, including nested lists and combinations of atoms and lists.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected

@pytest.mark.parametrize("input_text, expected", [
    ("#t", True),  # Boolean true
    ("#f", False),  # Boolean false
])
def test_parse_boolean(input_text: str, expected: bool):
    """
    Test parsing boolean literals.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected

@pytest.mark.parametrize("input_text, expected", [
    ("'foo", ["quote", "foo"]),  # Quoted atom
    ("'(foo bar)", ["quote", ["foo", "bar"]]),  # Quoted list
])
def test_parse_quoted_expression(input_text: str, expected: list):
    """
    Test parsing quoted expressions.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected

@pytest.mark.parametrize("input_text, expected", [
    ("#1A2B#", "+")  # Hexadecimal string
])
def test_parse_hexadecimal(input_text: str, expected: str):
    """
    Test parsing hexadecimal strings.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected

@pytest.mark.parametrize("input_text, expected", [
    ("|SGVsbG8gd29ybGQ=|", "Hello world"),  # Base64 string
    ("|c3VwZXI=|", "super"),  # Base64 string with decoding
])
def test_parse_base64(input_text: str, expected: str):
    """
    Test parsing base64-encoded strings.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected

@pytest.mark.parametrize("input_text, expected", [
    ("5:hello", "hello"),  # Verbatim string
    ("42", "42"),  # Numeric token
])
def test_parse_number_or_verbatim(input_text: str, expected: str):
    """
    Test parsing numbers or verbatim strings.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected

@pytest.mark.parametrize("input_text, expected", [
    ("(foo ; this is a comment\nbar)", ["foo", "bar"]),  # Ignoring comment
    ("; entire line comment\n(foo)", ["foo"]),  # Comment before S-expression
])
def test_parse_ignore_comments(input_text: str, expected: list):
    """
    Test that comments are correctly ignored during parsing.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected

@pytest.mark.parametrize("input_text, expected", [
    (r"(foo \"quoted\" bar)", ["foo", "quoted", "bar"]),  # Quoted strings with double quotes
    (r"(foo \"hello \\\\world\" bar)", ["foo", "hello \\world", "bar"]),  # Properly escaped backslash within quoted string
])
def test_parse_quoted_strings(input_text: str, expected: list):
    """
    Test parsing quoted strings, including handling of escape sequences.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected

@pytest.mark.parametrize("input_text, expected", [
    ("(foo >= bar)", ["foo", ">=", "bar"]),  # Comparison operators
    ("(foo <= bar)", ["foo", "<=", "bar"]),
])
def test_parse_comparison_operators(input_text: str, expected: list):
    """
    Test parsing comparison operators.
    """
    parser = SExpressionParser(input_text)
    result = parser.parse()
    assert result == expected
