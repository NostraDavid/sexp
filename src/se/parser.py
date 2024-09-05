import re
import base64

# Define types for S-expression components
SExpression = str | list["SExpression"]

# Regular expressions for the various string types in S-expressions
TOKEN_RE = re.compile(r"[A-Za-z0-9./_*+=-]+")
VERBATIM_RE = re.compile(r"(\d+):")
HEX_RE = re.compile(r"#([A-Fa-f0-9]+)#")
BASE64_RE = re.compile(r"\|([A-Za-z0-9+/=]+)\|")


class SExpressionParser:
    """
    A parser for S-expressions.
    """

    def __init__(self, text: str) -> None:
        self.text = text.strip()
        self.index = 0

    def _skip_whitespace(self) -> None:
        while self.index < len(self.text) and self.text[self.index].isspace():
            self.index += 1

    def _peek(self) -> str:
        self._skip_whitespace()
        return self.text[self.index] if self.index < len(self.text) else ""

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

        # Cache the substring from current index to the end for efficiency
        remaining_text = self.text[self.index :]

        # Try to parse verbatim string
        verbatim_match: re.Match[str] | None = VERBATIM_RE.match(remaining_text)
        if verbatim_match:
            length = int(verbatim_match.group(1))
            self._consume(len(verbatim_match.group(0)))
            value = self._consume(length)
            return value

        # Try to parse hexadecimal string
        hex_match: re.Match[str] | None = HEX_RE.match(remaining_text)
        if hex_match:
            self._consume(len(hex_match.group(0)))
            return bytes.fromhex(hex_match.group(1)).decode("utf-8")

        # Try to parse base-64 string
        base64_match: re.Match[str] | None = BASE64_RE.match(remaining_text)
        if base64_match:
            self._consume(len(base64_match.group(0)))
            return base64.b64decode(base64_match.group(1)).decode("utf-8")

        # Try to parse token
        token_match: re.Match[str] | None = TOKEN_RE.match(remaining_text)
        if token_match:
            self._consume(len(token_match.group(0)))
            return token_match.group(0)

        # Parse quoted strings
        if self._peek() == '"':
            return self._parse_quoted_string()

        raise ValueError(f"Unknown atom at position {self.index}")

    def _parse_quoted_string(self) -> str:
        # Consume the opening quote
        self._consume(1)
        result: list[str] = []
        while (char := self._peek()) != '"':
            if char == "\\":
                # Escape sequences
                self._consume(1)
                next_char = self._consume(1)
                result.append(self._handle_escape(next_char))
            else:
                result.append(self._consume(1))
        # Consume the closing quote
        self._consume(1)
        return "".join(result)

    def _handle_escape(self, next_char: str) -> str:
        if next_char == "n":
            return "\n"
        elif next_char == "t":
            return "\t"
        elif next_char == "\\":
            return "\\"
        elif next_char == '"':
            return '"'
        else:
            return next_char  # Return literal character if not an escape
