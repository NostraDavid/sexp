import pytest
from sexp.parser import dumps, loads


@pytest.mark.parametrize(
    "input_sexp, expected_obj",
    [
        # Basic atoms
        ("token", "token"),
        ('"a quoted string"', "a quoted string"),
        ("5:hello", "hello"),
        ("#t", True),
        ("#f", False),
        # Empty cases
        ("()", []),
        ('""', ""),
        ("0:", ""),
        # Lists
        ("(a b c)", ["a", "b", "c"]),
        ("(a (b c) d)", ["a", ["b", "c"], "d"]),
        # Whitespace handling
        (" ( a\n b\t c) ", ["a", "b", "c"]),
        (
            """
            (list-of-items
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
        ("(", "Failed to parse S-expression"),
        (")", "Failed to parse S-expression"),
        ("(a b", "Failed to parse S-expression"),
        ("4:abc", "Failed to parse S-expression"),
        ('"abc', "Failed to parse S-expression"),
        ("a b", "Failed to parse S-expression"),
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
        ("token", "5:token"),
        ("a simple string", "15:a simple string"),
        ("string-with-hyphen", "18:string-with-hyphen"),
        ("string with (parens)", "20:string with (parens)"),
        ('string with "quotes"', '20:string with "quotes"'),
        # Empty cases
        ([], "()"),
        ("", "0:"),
        # Lists
        (["a", "b", "c"], "(1:a1:b1:c)"),
        (["a", ["b", "c"], "d"], "(1:a(1:b1:c)1:d)"),
        (
            ["a", "b c", "d"],
            "(1:a3:b c1:d)",
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
        TypeError, match="Object of type .* is not serializable to S-expression"
    ):
        dumps(invalid_obj)


@pytest.mark.parametrize(
    "obj",
    [
        "simple",
        "a string with spaces",
        [],
        ["a", "b", "c"],
        ["a", ["b", "c"], "d e f"],
    ],
)
def test_loads_dumps_roundtrip(obj):
    """
    Tests that `loads(dumps(obj))` returns the original object.
    """
    sexp_str = dumps(obj)
    new_obj = loads(sexp_str)
    assert new_obj == obj
