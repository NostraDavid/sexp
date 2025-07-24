"""
S-expression parser for RFC 9804.
"""

import base64
from typing import List, Union

# An S-expression is either a string (atom) or a list of S-expressions.
SExpression = Union[str, List["SExpression"]]


class SExpressionParser:
    """
    A stateful parser for S-expressions as defined in RFC 9804.

    This parser consumes the input text from left to right, building the
    corresponding Python objects (strings and lists). It handles various
    string representations (verbatim, quoted, hex, base64, tokens) and
    nested list structures.

    The implementation is guided by the ABNF specification in RFC 9804.
    """

    def __init__(self, text: str):
        """
        Initializes the parser with the input text.

        Args:
            text: The string containing the S-expression(s).
        """
        self.text = text
        self.index = 0

    def parse(self) -> SExpression:
        """
        Parses a single S-expression from the input string.

        It expects the string to contain exactly one S-expression,
        surrounded by optional whitespace.

        Returns:
            The parsed S-expression as a Python object.

        Raises:
            ValueError: If the input is empty, contains more than one
                        S-expression, or has syntax errors.
        """
        self._skip_whitespace()
        if self.index >= len(self.text):
            raise ValueError(
                "Unexpected EOF: input is empty or contains only whitespace."
            )
        value = self._parse_sexpr()
        self._skip_whitespace()
        if self.index < len(self.text):
            raise ValueError(
                f"Extra characters after end of S-expression at position {self.index}"
            )
        return value

    def parse_multiple(self) -> List[SExpression]:
        """
        Parses a sequence of S-expressions from the input string.

        This method is useful for files containing multiple S-expressions.

        Returns:
            A list of parsed S-expressions.
        """
        expressions = []
        while True:
            self._skip_whitespace()
            if self.index >= len(self.text):
                break
            expressions.append(self._parse_sexpr())
        return expressions

    def _peek(self) -> str:
        """Returns the character at the current parsing position without advancing."""
        return self.text[self.index] if self.index < len(self.text) else ""

    def _consume(self) -> str:
        """Consumes and returns the character at the current position, advancing the index."""
        if self.index >= len(self.text):
            raise ValueError("Unexpected EOF while consuming character")
        char = self.text[self.index]
        self.index += 1
        return char

    def _consume_while(self, predicate) -> str:
        """Consumes characters as long as the predicate function returns true."""
        start = self.index
        while self.index < len(self.text) and predicate(self.text[self.index]):
            self.index += 1
        return self.text[start : self.index]

    def _skip_whitespace(self):
        """
        Skips over whitespace characters and comments.
        ABNF: whitespace = SP / HTAB / vtab / CR / LF / ff
        Also handles Lisp-style comments starting with ';'.
        """
        while self.index < len(self.text):
            char = self.text[self.index]
            if char in " \t\r\n\v\f":  # vtab=%x0B, ff=%x0C
                self.index += 1
            elif char == ";":
                # Comment runs to the end of the line
                while self.index < len(self.text) and self.text[self.index] != "\n":
                    self.index += 1
            else:
                break

    def _parse_sexpr(self) -> SExpression:
        """
        Parses a single S-expression value, which can be a list or an atom.
        ABNF: value = string / ("(" *(value / whitespace) ")")
        """
        self._skip_whitespace()
        if self._peek() == "(":
            return self._parse_list()
        else:
            # ABNF: string = [display] simple-string
            # We ignore the display hint.
            return self._parse_simple_string()

    def _parse_list(self) -> List[SExpression]:
        """Parses a list S-expression: "(" *(value / whitespace) ")"."""
        self._consume()  # Consume '('
        items = []
        while True:
            self._skip_whitespace()
            peeked = self._peek()
            if peeked == "" or peeked == ")":
                break
            items.append(self._parse_sexpr())

        if self.index >= len(self.text) or self._consume() != ")":
            raise ValueError(f"Unclosed list starting at position {self.index}")
        return items

    def _parse_simple_string(self) -> str:
        """
        Parses an atomic S-expression (simple-string).
        ABNF: simple-string = verbatim / quoted-string / token / hexadecimal / base-64
        """
        char = self._peek()
        if char.isdigit():
            return self._parse_verbatim()
        elif char == '"':
            return self._parse_quoted_string()
        elif char == "#":
            return self._parse_hexadecimal()
        elif char == "|":
            return self._parse_base64()
        else:
            return self._parse_token()

    def _parse_decimal(self) -> int:
        """
        Parses a non-zero-prefixed decimal number.
        ABNF: decimal = %x30 / (%x31-39 *DIGIT)
        """
        if not self._peek().isdigit():
            raise ValueError(f"Expected a digit at position {self.index}")
        num_str = self._consume_while(str.isdigit)
        if len(num_str) > 1 and num_str.startswith("0"):
            raise ValueError(f"Invalid decimal: leading zero is not allowed: {num_str}")
        return int(num_str)

    def _parse_verbatim(self) -> str:
        """Parses a verbatim string like '5:hello'."""
        match = self._consume_while(lambda char: char.isdigit())
        if not match:
            raise ValueError("Invalid verbatim string format: missing length")

        length = int(match)
        if self._peek() != ":":
            raise ValueError("Invalid verbatim string format: missing colon")
        self._consume()  # Skip the colon

        # The rest of the text from the current index
        remaining_text = self.text[self.index :]
        # Encode to bytes to correctly handle multi-byte characters
        remaining_bytes = remaining_text.encode("utf-8")

        if length > len(remaining_bytes):
            raise ValueError("Verbatim string length exceeds input size")

        # Get the verbatim content in bytes
        verbatim_bytes = remaining_bytes[:length]
        # Decode back to a string
        content = verbatim_bytes.decode("utf-8")

        # Advance the index by the number of characters in the decoded content
        self.index += len(content)

        return content

    def _parse_quoted_string(self) -> str:
        """
        Parses a quoted string.
        ABNF: quoted-string = [decimal] DQUOTE *(printable / escaped) DQUOTE
        Ignoring optional decimal length prefix.
        """
        self._consume()  # Consume initial DQUOTE
        result = []
        while self._peek() != '"':
            if self.index >= len(self.text):
                raise ValueError("Unterminated quoted string")
            char = self._consume()
            if char == "\\":  # backslash
                if self.index >= len(self.text):
                    raise ValueError("Unterminated escape sequence in quoted string")
                escaped_char = self._consume()
                # ABNF for escaped is complex, implementing a subset.
                if escaped_char == "n":
                    result.append("\n")
                elif escaped_char == "r":
                    result.append("\r")
                elif escaped_char == "t":
                    result.append("\t")
                elif escaped_char in "\"\\'":  # DQUOTE / backslash / quote
                    result.append(escaped_char)
                else:
                    raise ValueError(f"Unsupported escape sequence: \\{escaped_char}")
            else:
                result.append(char)
        self._consume()  # Consume final DQUOTE
        return "".join(result)

    def _parse_hexadecimal(self) -> str:
        """
        Parses a hexadecimal string.
        ABNF: hexadecimal = [decimal] "#" *whitespace *hexadecimals "#"
        Ignoring optional decimal length prefix.
        """
        self._consume()  # Consume '#'
        self._skip_whitespace()
        hex_chars = []
        while self._peek() != "#":
            if self.index >= len(self.text):
                raise ValueError("Unterminated hexadecimal string")
            char = self._consume()
            if not char.isspace():
                if not ("0" <= char <= "9" or "a" <= char.lower() <= "f"):
                    raise ValueError(
                        f"Invalid hex character '{char}' at position {self.index - 1}"
                    )
                hex_chars.append(char)
        self._consume()  # Consume final '#'

        hex_str = "".join(hex_chars)
        # ABNF: hexadecimals = 2(HEXDIG *whitespace)
        # This implies pairs of hexdigits. My simple join doesn't enforce the space between pairs,
        # but it should be fine for decoding.
        if len(hex_str) % 2 != 0:
            raise ValueError(f"Odd number of hex digits: {hex_str}")
        try:
            # Per RFC, hex is raw bytes. We decode to string for type consistency.
            return bytes.fromhex(hex_str).decode("utf-8", errors="replace")
        except ValueError as e:
            raise ValueError(f"Invalid hexadecimal string: {e}") from e

    def _parse_base64(self) -> str:
        """
        Parses a base64 string.
        ABNF: base-64 = [decimal] "|" *whitespace *base-64-chars [base-64-end] "|"
        Ignoring optional decimal length prefix.
        """
        self._consume()  # Consume '|'
        self._skip_whitespace()
        b64_chars = []
        while self._peek() != "|":
            if self.index >= len(self.text):
                raise ValueError("Unterminated base64 string")
            char = self._consume()
            if not char.isspace():
                b64_chars.append(char)
        self._consume()  # Consume final '|'

        b64_str = "".join(b64_chars)
        # Add padding if necessary for decoding.
        padding = len(b64_str) % 4
        if padding != 0:
            b64_str += "=" * (4 - padding)

        try:
            # Per RFC, base64 is raw bytes. We decode to string for type consistency.
            return base64.b64decode(b64_str).decode("utf-8", errors="replace")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid base64 string: {e}") from e

    def _parse_token(self) -> str:
        """
        Parses a token.
        ABNF: token = (ALPHA / simple-punc) *(ALPHA / DIGIT / simple-punc)
        simple-punc = "-" / "." / "/" / "_" / ":" / "*" / "+" / "="
        """
        SIMPLE_PUNC = "-./_:+*="

        def is_token_start_char(char: str):
            return char.isalpha() or char in SIMPLE_PUNC

        def is_token_char(char: str):
            return char.isalnum() or char in SIMPLE_PUNC

        if not self._peek() or not is_token_start_char(self._peek()):
            raise ValueError(
                f"Invalid token start character at {self.index}: '{self._peek()}'"
            )

        return self._consume_while(is_token_char)
