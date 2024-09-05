import re
from typing import Union

# Define types for S-expression components
SExpression = Union[str, list["SExpression"]]

# Regular expressions for the various string types in S-expressions
TOKEN_RE = re.compile(r"[A-Za-z0-9./_*+=-]+")
VERBATIM_RE = re.compile(r"(\d+):")
HEX_RE = re.compile(r"#([A-Fa-f0-9]+)#")
BASE64_RE = re.compile(r"\|([A-Za-z0-9+/=]+)\|")


class SExpressionParser:
    """
    A parser for S-expressions.
    """

    def __init__(self, text: str):
        self.text = text.strip()
        self.index = 0

    def _skip_whitespace(self):
        while self.index < len(self.text) and self.text[self.index].isspace():
            self.index += 1

    def _peek(self) -> str:
        self._skip_whitespace()
        if self.index < len(self.text):
            return self.text[self.index]
        return ""

    def _consume(self, length: int) -> str:
        result = self.text[self.index : self.index + length]
        self.index += length
        return result

    def parse(self) -> SExpression:
        return self._parse_sexpr()

    def _parse_sexpr(self) -> SExpression:
        self._skip_whitespace()
        char = self._peek()

        if char == "(":
            return self._parse_list()
        else:
            return self._parse_atom()

    def _parse_list(self) -> list[SExpression]:
        # Consume the opening parenthesis
        self._consume(1)
        result: list[SExpression] = []
        while self._peek() != ")":
            result.append(self._parse_sexpr())
        # Consume the closing parenthesis
        self._consume(1)
        return result

    def _parse_atom(self) -> SExpression:
        self._skip_whitespace()
        char = self._peek()

        # Try to parse verbatim string
        verbatim_match = VERBATIM_RE.match(self.text[self.index :])
        if verbatim_match:
            length = int(verbatim_match.group(1))
            self._consume(len(verbatim_match.group(0)))
            value = self._consume(length)
            return value

        # Try to parse hexadecimal string
        hex_match = HEX_RE.match(self.text[self.index :])
        if hex_match:
            self._consume(len(hex_match.group(0)))
            return bytes.fromhex(hex_match.group(1)).decode("utf-8")

        # Try to parse base-64 string
        base64_match = BASE64_RE.match(self.text[self.index :])
        if base64_match:
            import base64

            self._consume(len(base64_match.group(0)))
            return base64.b64decode(base64_match.group(1)).decode("utf-8")

        # Try to parse token
        token_match = TOKEN_RE.match(self.text[self.index :])
        if token_match:
            self._consume(len(token_match.group(0)))
            return token_match.group(0)

        # Parse quoted strings
        if char == '"':
            return self._parse_quoted_string()

        raise ValueError(f"Unknown atom at position {self.index}")

    def _parse_quoted_string(self) -> str:
        # Consume the opening quote
        self._consume(1)
        result: list[str] = []
        while self._peek() != '"':
            if self._peek() == "\\":
                # Escape sequences
                self._consume(1)
                next_char = self._consume(1)
                if next_char == "n":
                    result.append("\n")
                elif next_char == "t":
                    result.append("\t")
                elif next_char == "\\":
                    result.append("\\")
                elif next_char == '"':
                    result.append('"')
                else:
                    result.append(next_char)
            else:
                result.append(self._consume(1))
        # Consume the closing quote
        self._consume(1)
        return "".join(result)
