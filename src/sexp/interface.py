import re
from typing import IO
from sexp.parser import SExpressionParser
from sexp.types import SExpression


# A simple regex to identify strings that can be represented as tokens.
# Tokens are contiguous strings of characters that do not include whitespace
# or the special characters '(', ')', '"', ';', '#', '|'.
# This is a conservative choice for serialization.
_TOKEN_RE = re.compile(r"^[a-zA-Z0-9-._+/=]+$")


def _is_token(s: str) -> bool:
    """Checks if a string can be represented as a bare token."""
    return bool(s and _TOKEN_RE.match(s))


def loads(s: str) -> SExpression:
    """
    Parses an S-expression from a string.

    Args:
        s: The string containing the S-expression.

    Returns:
        The parsed Python object (list or string).
    """
    parser = SExpressionParser(s)
    return parser.parse()


def dumps(obj: SExpression) -> str:
    """
    Serializes a Python object into an S-expression string.

    Strings are serialized as tokens if possible, otherwise as quoted strings.
    Lists are serialized into parenthesized, space-separated lists.

    Args:
        obj: The Python object (list or string) to serialize.

    Returns:
        The S-expression string representation.

    Raises:
        TypeError: If the object is not a list or a string.
    """
    if isinstance(obj, str):
        if _is_token(obj):
            return obj
        # Escape backslashes and double quotes for quoted string representation.
        escaped_str = obj.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped_str}"'
    if isinstance(obj, list):
        return f"({' '.join(map(dumps, obj))})"
    raise TypeError(
        f"Object of type {type(obj).__name__} is not S-expression serializable"
    )


def load(fp: IO[str]) -> SExpression:
    """
    Reads and parses an S-expression from a file-like object.

    Args:
        fp: A file-like object opened in text mode.

    Returns:
        The parsed Python object (list or string).
    """
    return loads(fp.read())


def dump(obj: SExpression, fp: IO[str]) -> None:
    """
    Writes the S-expression representation of an object to a file-like object.

    Args:
        obj: The Python object (list or string) to serialize.
        fp: A file-like object opened in text mode for writing.
    """
    fp.write(dumps(obj))
