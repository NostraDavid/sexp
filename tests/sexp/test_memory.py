"""Behavioral checks for compact, lazily built list frames."""

import platform
import sys

import pytest

from sexp.parser import DisplayString, SExpressionParser


@pytest.mark.parametrize("count", range(9))
def test_list_lengths(count):
    value = SExpressionParser("(" + "a " * count + ")").parse()
    assert type(value) is list
    assert value == [b"a"] * count


@pytest.mark.skipif(
    platform.python_implementation() != "CPython",
    reason="CPython allocation regression",
)
@pytest.mark.parametrize("count", range(9))
def test_small_lists_do_not_retain_more_capacity_than_append(count):
    value = SExpressionParser("(" + "a " * count + ")").parse()
    reference = []
    for _ in range(count):
        reference.append(b"a")
    assert sys.getsizeof(value) <= sys.getsizeof(reference)


@pytest.mark.skipif(
    platform.python_implementation() != "CPython",
    reason="CPython allocation regression",
)
def test_singleton_has_compact_list_capacity():
    value = SExpressionParser("(a)").parse()
    assert sys.getsizeof(value) <= sys.getsizeof([b"a"])


def test_sibling_lists_are_independent():
    value = SExpressionParser("(() () (a) (a))").parse()
    assert isinstance(value, list)
    assert isinstance(value[0], list)
    assert isinstance(value[2], list)
    value[0].append(b"changed")
    value[2].append(b"changed")
    assert value == [[b"changed"], [], [b"a", b"changed"], [b"a"]]


def test_deep_nesting_with_trailing_siblings_and_cursor():
    depth = 5000
    parser = SExpressionParser("(" * depth + "a" + " b)" * depth + " trailing")
    value = parser.parse_value()
    for _ in range(depth):
        assert isinstance(value, list)
        assert len(value) == 2
        assert value[1] == b"b"
        value = value[0]
    assert value == b"a"
    assert parser.text[parser.index :] == " trailing"


@pytest.mark.parametrize("text", ["(", "((a)", "(a (b) "])
def test_missing_close_preserves_eof_cursor(text):
    parser = SExpressionParser(text)
    with pytest.raises(ValueError, match="Missing closing"):
        parser.parse_value()
    assert parser.index == len(text)


def test_canonical_and_display_strings_in_lists():
    value = SExpressionParser(b"((1:a)[4:text]2:\xc3\xa9())").parse_canonical()
    assert value == [[b"a"], DisplayString(b"\xc3\xa9", b"text"), []]
    with pytest.raises(ValueError):
        SExpressionParser("(1:a 1:b)").parse_canonical()
