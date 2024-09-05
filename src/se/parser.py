import base64
from typing import Any, Callable

# Define types for S-expression components
SExpression = str | list["SExpression"]


class SExpressionParser:
    """
    A parser for S-expressions.

    S-expressions can consist of lists, tokens, verbatim strings,
    hexadecimal strings, base64 strings, or quoted strings.
    This parser handles these types and returns nested Python lists
    or strings based on the parsed S-expression structure.
    """

    def __init__(self, text: str) -> None:
        """
        Initialize the parser with the input text.

        Args:
            text: A string containing the S-expression to be parsed.
        """
        self.text = text.strip()
        self.index = 0

    def _skip_whitespace(self) -> None:
        """
        Move the parser index past any whitespace characters and comments.
        """
        while self.index < len(self.text):
            char = self.text[self.index]

            if char.isspace():
                # Skip whitespace
                self.index += 1
            elif char == ";":
                # Skip comment until the end of the line
                self._consume_until_newline()
            else:
                break

    def _consume_until_newline(self) -> None:
        """
        Consume characters until a newline or the end of the input is reached.
        This is used to skip over comments that start with a semicolon (;).
        """
        while self.index < len(self.text) and self.text[self.index] not in "\n\r":
            self.index += 1

    def _peek(self) -> str:
        """
        Peek at the current character without advancing the parser index.

        Returns:
            The current character at the parser's index.
        """
        self._skip_whitespace()
        return self.text[self.index] if self.index < len(self.text) else ""

    def _consume(self, length: int) -> str:
        """
        Consume a specified number of characters from the input and advance the index.

        Args:
            length: The number of characters to consume.

        Returns:
            The string of consumed characters.
        """
        result = self.text[self.index : self.index + length]
        self.index += length
        return result

    def _consume_while(self, condition: Callable[[Any], bool]) -> str:
        """
        Consume characters while the provided condition function returns True.

        Args:
            condition: A function that takes a character and returns True if it should be consumed.

        Returns:
            A string of all the consumed characters.
        """
        start = self.index
        while self.index < len(self.text) and condition(self.text[self.index]):
            self.index += 1
        return self.text[start : self.index]

    def parse(self) -> SExpression:
        """
        Parse the full input text into an S-expression.

        Returns:
            The parsed S-expression as a nested structure (list or string).
        """
        return self._parse_sexpr()

    def _parse_sexpr(self) -> SExpression:
        """
        Parse a single S-expression, which may be an atom or a list.

        Returns:
            A list if it's a nested S-expression or a string if it's an atom.
        """
        self._skip_whitespace()
        char = self._peek()

        if char == "(":
            return self._parse_list()
        elif char == ")":
            raise ValueError(f"Unexpected closing parenthesis at position {self.index}")
        else:
            return self._parse_atom()

    def _parse_list(self) -> list[SExpression]:
        """
        Parse a list S-expression, which starts with '(' and ends with ')'.

        Returns:
            A list of parsed S-expression elements.
        """
        # Consume the opening parenthesis
        self._consume(1)
        result: list[SExpression] = []
        while self._peek() != ")":
            result.append(self._parse_sexpr())
        # Consume the closing parenthesis
        self._consume(1)
        return result

    def _parse_atom(self) -> SExpression:
        """
        Parse a single atom, which may be a verbatim string, hexadecimal string,
        base64 string, token, or quoted string.

        Returns:
            The parsed atom as a string.

        Raises:
            ValueError: If the atom is not recognized.
        """
        self._skip_whitespace()
        char = self._peek()

        # Handle the single quote for quoting expressions
        if char == "'":
            return self._parse_quoted_expression()

        # Try to parse verbatim string (format: <length>:<string>)
        if char.isdigit():
            return self._parse_number_or_verbatim()

        # Try to parse hexadecimal string (format: #<hex>#)
        if char == "#":
            return self._parse_hexadecimal()

        # Try to parse base-64 string (format: |<base64>|)
        if char == "|":
            return self._parse_base64()

        # Try to parse token
        if char.isalnum() or char in "./_*+=-?":
            return self._parse_token()

        # Parse quoted strings
        if char == '"':
            return self._parse_quoted_string()

        raise ValueError(f"Unknown atom at position {self.index}: '{char}'")

    def _parse_quoted_expression(self) -> SExpression:
        """
        Parse a quoted expression, indicated by a single quote (').
        Quoted expressions are transformed into the form (quote <expression>).

        Returns:
            A list representing the quoted expression.
        """
        self._consume(1)  # Consume the single quote
        quoted_expr = self._parse_sexpr()  # Parse the next S-expression
        return ["quote", quoted_expr]

    def _parse_number_or_verbatim(self) -> SExpression:
        """
        Parse a number or a verbatim string. If the number is followed by a colon,
        it is treated as a verbatim string's length. Otherwise, it is treated as a numeric token.

        Returns:
            The parsed number as a token or the parsed verbatim string.

        Raises:
            ValueError: If the verbatim string format is incorrect.
        """
        number_str = self._consume_while(str.isdigit)
        if self._peek() == ":":
            # Verbatim string case
            self._consume(1)  # Consume the colon
            length = int(number_str)
            value = self._consume(length)
            if len(value) != length:
                raise ValueError(
                    f"Verbatim string length mismatch at position {self.index}: expected {length} characters, but got {len(value)}."
                )
            return value
        else:
            # Numeric token case
            return number_str

    def _parse_hexadecimal(self) -> str:
        """
        Parse a hexadecimal string, which is in the format #<hex>#.

        Returns:
            The decoded hexadecimal string. If decoding to UTF-8 fails, return the raw bytes.

        Raises:
            ValueError: If the format is invalid or if the closing '#' is missing.
        """
        self._consume(1)  # Consume the opening '#'
        start_pos = self.index  # Remember the start position for better error reporting
        hex_string = self._consume_while(lambda c: c in "0123456789abcdefABCDEF")

        # Check if the hex string is empty
        if not hex_string:
            raise ValueError(
                f"Empty hexadecimal string at position {start_pos}. Expected valid hex between '#'."
            )

        if self._peek() != "#":
            raise ValueError(
                f"Expected closing '#' for hexadecimal string at position {self.index}. "
                f"Parsed so far: '{self.text[start_pos:self.index]}'"
            )

        self._consume(1)  # Consume the closing '#'

        try:
            # Try decoding as UTF-8
            return bytes.fromhex(hex_string).decode("utf-8")
        except UnicodeDecodeError:
            # If decoding fails, return the raw bytes
            return bytes.fromhex(hex_string)

    def _parse_base64(self) -> str:
        """
        Parse a base64-encoded string, which is in the format |<base64>|.

        Returns:
            The decoded base64 string. If decoding to UTF-8 fails, return the raw bytes.

        Raises:
            ValueError: If the format is invalid.
        """
        self._consume(1)  # Consume the opening '|'
        base64_string = self._consume_while(
            lambda c: c
            in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
        )

        if self._consume(1) != "|":
            raise ValueError(
                f"Expected closing '|' for base64 string at position {self.index}"
            )

        try:
            # Try decoding as UTF-8
            return base64.b64decode(base64_string).decode("utf-8")
        except UnicodeDecodeError:
            # If decoding fails, return the raw bytes
            return base64.b64decode(base64_string)

    def _parse_token(self) -> str:
        """
        Parse a token, which consists of alphanumeric characters or certain special symbols.

        Returns:
            The parsed token as a string.
        """
        return self._consume_while(lambda c: c.isalnum() or c in "./_*+=-?")

    def _parse_quoted_string(self) -> str:
        """
        Parse a quoted string, handling escape sequences.

        Returns:
            The parsed string with escape sequences resolved.
        """
        self._consume(1)  # Consume the opening quote
        result: list[str] = []
        while (char := self._peek()) != '"':
            if char == "\\":
                # Escape sequences
                self._consume(1)
                next_char = self._consume(1)
                result.append(self._handle_escape(next_char))
            else:
                result.append(self._consume(1))
        self._consume(1)  # Consume the closing quote
        return "".join(result)

    def _handle_escape(self, next_char: str) -> str:
        """
        Handle escape sequences within a quoted string.

        Args:
            next_char: The character following the escape sequence.

        Returns:
            The escaped character or the literal character if no escape is found.
        """
        match next_char:
            case "n":
                return "\n"
            case "t":
                return "\t"
            case "\\":
                return "\\"
            case '"':
                return '"'
            case _:
                return next_char  # Return literal character if not an escape
