"""
Tests for our minimal ABNF parser
Starting with the most basic elements
"""

from sexp.parser import SexpParser


def test_parse_sp_success():
    """Test parsing a space character successfully"""
    parser = SexpParser(" ")
    result = parser.parse_sp()
    assert result is True
    assert parser.at_end()


def test_parse_sp_failure():
    """Test parsing non-space character fails"""
    parser = SexpParser("a")
    result = parser.parse_sp()
    assert result is False
    assert not parser.at_end()
    assert parser.index == 0  # Should not consume anything


def test_parse_sp_empty_string():
    """Test parsing space from empty string fails"""
    parser = SexpParser("")
    result = parser.parse_sp()
    assert result is False
    assert parser.at_end()


def test_parse_sp_multiple_chars():
    """Test parsing space when it's first of multiple characters"""
    parser = SexpParser(" abc")
    result = parser.parse_sp()
    assert result is True
    assert not parser.at_end()
    assert parser.index == 1
    # Next character should be 'a'
    assert parser.peek() == "a"
