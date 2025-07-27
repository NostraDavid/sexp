from parsimonious import Grammar
import pytest
from sexp.parser import dumps, loads


def test_grammar():
    g = Grammar("""
    polite_greeting = greeting ", my good " title
    greeting        = "Hi" / "Hello"
    title           = "madam" / "sir"
    """)
    g.parse("Hello, my good sir")


def test_loads_valid_sexp123():
    assert loads("# comment") is None


@pytest.mark.parametrize(
    "input_sexp, expected_obj",
    [
        # Basic atoms
        ("#comment", None),
        ("token", "token"),
        ('"a quoted string"', "a quoted string"),
        ("5:hello", "hello"),
        ("#68656c6c6f#", "hello"),
        ("|aGVsbG8=|", "hello"),
        # Booleans
        ("#t", True),
        ("#f", False),
        # Empty cases
        ("()", []),
        ('""', ""),
        ("0:", ""),
        ("##", ""),
        ("||", ""),
        # Lists
        ("(a b c)", ["a", "b", "c"]),
        ("(a (b c) d)", ["a", ["b", "c"], "d"]),
        (
            '( "a" 1:b #63# |ZA==| #t )',
            ["a", "b", "c", "d", True],
        ),
        # Whitespace and comments
        (" ( a\n b\t c) # comment", ["a", "b", "c"]),
        (
            """
            (list-of-items
                # this is a comment
                item1
                "item 2 with spaces"
                (nested list)
            )
            """,
            ["list-of-items", "item1", "item 2 with spaces", ["nested", "list"]],
        ),
    ],
)
def test_loads_valid_sexp(input_sexp: str, expected_obj):
    """
    Tests that `loads` correctly parses various valid S-expression strings.
    """
    assert loads(input_sexp) == expected_obj


@pytest.mark.parametrize(
    "invalid_sexp, error_message_part",
    [
        ("(", "Unexpected EOF while parsing list"),
        (")", "Unexpected ')'"),
        ("(a b", "Unexpected EOF while parsing list"),
        ("4:abc", "Invalid length for verbatim string"),
        ('"abc', "Unterminated quoted string"),
        ("#616g#", "Invalid hex character 'g'"),
        ("|YWJj", "Incorrect padding"),
        ("#z", "Invalid token starting with '#'"),
        ("a b", "Extra content found after S-expression"),
    ],
)
def test_loads_invalid_sexp(invalid_sexp: str, error_message_part: str):
    """
    Tests that `loads` raises a ValueError for invalid S-expression strings.
    """
    with pytest.raises(ValueError, match=error_message_part):
        loads(invalid_sexp)


@pytest.mark.parametrize(
    "obj, expected_sexp",
    [
        # Basic atoms
        ("token", "token"),
        ("a simple string", '"a simple string"'),
        ("string-with-hyphen", "string-with-hyphen"),
        ("string with (parens)", '"string with (parens)"'),
        ('string with "quotes"', '"string with \\"quotes\\""'),
        # Booleans
        (True, "#t"),
        (False, "#f"),
        # Empty cases
        ([], "()"),
        ("", '""'),
        # Lists
        (["a", "b", "c"], "(a b c)"),
        (["a", ["b", "c"], "d"], "(a (b c) d)"),
        (
            ["a", "b c", True, ["d", False]],
            '(a "b c" #t (d #f))',
        ),
    ],
)
def test_dumps_valid_objects(obj, expected_sexp: str):
    """
    Tests that `dumps` correctly serializes various Python objects to S-expressions.
    """
    assert dumps(obj) == expected_sexp


@pytest.mark.parametrize(
    "invalid_obj",
    [
        123,
        12.34,
        b"bytes",
        {"a": 1},
        None,
    ],
)
def test_dumps_invalid_objects(invalid_obj):
    """
    Tests that `dumps` raises a TypeError for unsupported Python types.
    """
    with pytest.raises(
        TypeError, match="Unsupported type for S-expression serialization"
    ):
        dumps(invalid_obj)


@pytest.mark.parametrize(
    "obj",
    [
        "simple",
        "a string with spaces",
        True,
        False,
        [],
        ["a", "b", "c"],
        ["a", ["b", "c"], True, "d e f"],
    ],
)
def test_loads_dumps_roundtrip(obj):
    """
    Tests that `loads(dumps(obj))` returns the original object.
    """
    sexp_str = dumps(obj)
    new_obj = loads(sexp_str)
    assert new_obj == obj
