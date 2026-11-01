"""Byte-oriented parser for RFC 9804 S-expressions."""

import base64
import binascii
from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass(frozen=True)
class DisplayString:
    """An octet-string with its explicit RFC 9804 display-hint."""

    data: bytes
    display_hint: bytes


SExpression = Union[bytes, DisplayString, List["SExpression"]]

_WHITESPACE = " \t\v\r\n\f"
_TOKEN_START = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-./_:*+="
_TOKEN_CHARS = _TOKEN_START + "0123456789"
_HEX = "0123456789abcdefABCDEF"
_BASE64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
_ESCAPES = {
    "a": b"\a",
    "b": b"\b",
    "t": b"\t",
    "v": b"\v",
    "n": b"\n",
    "f": b"\f",
    "r": b"\r",
    '"': b'"',
    "'": b"'",
    "?": b"?",
    "\\": b"\\",
}


class SExpressionParser:
    """Parse one complete expression; atoms are bytes and lists are Python lists.

    Text input is encoded as UTF-8. Cursor positions and length fields count
    bytes, not Unicode characters. Use bytes input for arbitrary binary data.
    """

    def __init__(self, text: Union[str, bytes]):
        if isinstance(text, str):
            text = text.encode("utf-8")
        if not isinstance(text, bytes):
            raise TypeError("S-expression input must be str or bytes")
        # Latin-1 provides a one-character-per-byte view for the ABNF primitives.
        self.text = text.decode("latin-1")
        self.text_length = len(self.text)
        self.index = 0

    def at_end(self) -> bool:
        """Check if we've reached the end of input"""
        return self.index >= self.text_length

    def peek(self) -> Optional[str]:
        """Look at current character without consuming it"""
        if self.at_end():
            return None
        return self.text[self.index]

    def consume(self) -> Optional[str]:
        """Consume and return current character"""
        if self.at_end():
            return None
        char = self.text[self.index]
        self.index += 1
        return char

    # ABNF core rules.
    def parse_sp(self) -> bool:
        """Parse SP (space character) - %x20"""
        if self.peek() == " ":
            self.consume()
            return True
        return False

    def parse_htab(self) -> bool:
        """Parse HTAB (horizontal tab character) - %x09"""
        if self.peek() == "\t":
            self.consume()
            return True
        return False

    def parse_cr(self) -> bool:
        """Parse CR (carriage return character) - %x0D"""
        if self.peek() == "\r":
            self.consume()
            return True
        return False

    def parse_lf(self) -> bool:
        """Parse LF (line feed character) - %x0A"""
        if self.peek() == "\n":
            self.consume()
            return True
        return False

    def parse_alpha(self) -> bool:
        """Parse ALPHA character - %x41-5A / %x61-7A (A-Z / a-z)"""
        char = self.peek()
        if char and char.isascii() and char.isalpha():
            self.consume()
            return True
        return False

    def parse_digit(self) -> bool:
        """Parse DIGIT character - %x30-39 (0-9)"""
        char = self.peek()
        if char and char in "0123456789":
            self.consume()
            return True
        return False

    def parse_hexdigit(self) -> bool:
        """Parse HEXDIG character - DIGIT / "A" / "B" / "C" / "D" / "E" / "F" / "a" / "b" / "c" / "d" / "e" / "f"""
        char = self.peek()
        if char and char.lower() in "0123456789abcdef":
            self.consume()
            return True
        return False

    def parse_dquote(self) -> bool:
        """Parse DQUOTE (double quote character) - %x22"""
        if self.peek() == '"':
            self.consume()
            return True
        return False

    def parse_octet(self) -> bool:
        """Parse OCTET (any 8-bit byte) - %x00-FF"""
        char = self.peek()
        if char is not None:
            self.consume()
            return True
        return False

    # start of sexp.abnf
    def parse_ff(self) -> bool:
        """
        Parse FF (ASCII 0x0C, Form Feed)

        Implements:ff = %x0C   ; form feed
        """
        if self.peek() == "\x0c":
            self.consume()
            return True
        return False

    def parse_vtab(self) -> bool:
        """
        Parse VTAB (vertical tab character) - %x0B

        vtab = %x0B   ; vertical tab
        """
        if self.peek() == "\x0b":
            self.consume()
            return True
        return False

    def parse_whitespace(self) -> bool:
        """
        Parse any whitespace character (SP / HTAB / VTAB / CR / LF / FF)

        Implements: whitespace = SP / HTAB / vtab / CR / LF / ff
        """
        if self.parse_sp():
            return True
        if self.parse_htab():
            return True
        if self.parse_vtab():
            return True
        if self.parse_cr():
            return True
        if self.parse_lf():
            return True
        if self.parse_ff():
            return True
        return False

    def parse_base_64_char(self) -> bool:
        """
        Parse base64 character (A-Z, a-z, 0-9, '+', '/')

        Implements: base-64-char = ALPHA / DIGIT / "+" / "/"
        """
        char = self.peek()
        if char and char.isascii() and (char.isalnum() or char in "+/"):
            self.consume()
            return True
        return False

    def parse_base_64_chars(self) -> int:
        """Read one base-64-chars group: 4(base-64-char *whitespace).

        Return 4 on success, 0 on no match; raise ValueError for a partial group.
        Subsequent groups are left unread.
        """
        count = 0
        while count < 4 and self.parse_base_64_char():
            count += 1
            self._skip_whitespace()
        if count not in (0, 4):
            raise ValueError(
                f"Invalid base64 character count: {count} (expected 4)",
            )
        return count

    def parse_base_64_end(self) -> int:
        """Parse an RFC 9804 base64 group and optional padding, or leave it unread."""
        start_index = self.index
        count = 0
        while count < 4 and self.parse_base_64_char():
            count += 1
            while self.parse_whitespace():
                pass

        padding = 0
        while self.peek() == "=":
            self.consume()
            padding += 1
            while self.parse_whitespace():
                pass

        if count == 4 and padding == 0:
            return count
        if count in (2, 3) and padding <= 4 - count:
            return count
        self.index = start_index
        return 0

    def parse_decimal(self) -> Optional[int]:
        """
        Parse a sequence of decimal digits and return as int.
        Returns None if no digits found.
        """
        start = self.index
        while self.parse_digit():
            pass
        if self.index > start:
            digits = self.text[start : self.index]
            if len(digits) > 1 and digits[0] == "0":
                raise ValueError(f"Leading zero in decimal at position {start}")
            return int(digits)
        return None

    def parse_base_64(self) -> Union[str, bytes]:
        """Legacy primitive: return UTF-8 text if possible, otherwise bytes.

        Full-expression methods always return byte-valued atoms instead.
        """
        length = self.parse_decimal()
        if self.peek() != "|":
            raise ValueError(f"Missing opening '|' for base64 at position {self.index}")
        decoded = self._check_length(self._read_base64("|", "|"), length)
        try:
            return decoded.decode("utf-8")
        except UnicodeDecodeError:
            return decoded

    def parse_hexadecimals(self) -> str:
        """Read exactly one hexadecimals group: 2(HEXDIG *whitespace)."""
        hex_digits = []
        for _ in range(2):
            if not self.parse_hexdigit():
                raise ValueError(f"Expected HEXDIG at position {self.index}")
            hex_digits.append(self.text[self.index - 1])
            while self.parse_whitespace():
                pass
        return "".join(hex_digits)

    def parse_hexadecimal(self) -> Optional[bytes]:
        """Parse a hexadecimal string, or return None without consuming input."""
        start_index = self.index
        length = self.parse_decimal()
        if self.peek() != "#":
            self.index = start_index
            return None
        return self._check_length(self._read_hexadecimal(), length)

    def _read_encoded(
        self,
        opening: str,
        closing: str,
        alphabet: str,
        label: str,
    ) -> str:
        self._expect(opening)
        chars = bytearray()
        while (char := self.peek()) != closing:
            if char is None:
                raise ValueError(
                    f"Missing closing '{closing}' for {label} at position {self.index}",
                )
            if char in _WHITESPACE:
                self.consume()
            elif char in alphabet:
                chars.append(ord(char))
                self.consume()
            else:
                raise ValueError(
                    f"Invalid {label} character {char!r} at position {self.index}",
                )
        self.consume()
        return chars.decode("ascii")

    def _read_base64(self, opening: str, closing: str) -> bytes:
        encoded = self._read_encoded(opening, closing, _BASE64, "base64")
        data = encoded.rstrip("=")
        padding = len(encoded) - len(data)
        required = -len(data) % 4
        if required == 3 or padding > required:
            raise ValueError(f"Invalid base64 encoding at position {self.index}")
        try:
            return base64.b64decode(encoded + "=" * (required - padding), validate=True)
        except binascii.Error as exc:
            raise ValueError(
                f"Invalid base64 encoding at position {self.index}: {exc}",
            ) from exc

    def _read_hexadecimal(self) -> bytes:
        encoded = self._read_encoded("#", "#", _HEX, "hexadecimal")
        if len(encoded) % 2:
            raise ValueError(f"Odd hexadecimal digit count at position {self.index}")
        return bytes.fromhex(encoded)

    def _expect(self, character: str) -> None:
        if self.peek() != character:
            raise ValueError(f"Expected {character!r} at position {self.index}")
        self.consume()

    def _skip_whitespace(self) -> None:
        while self.parse_whitespace():
            pass

    def _check_length(self, data: bytes, length: Optional[int]) -> bytes:
        if length is not None and length != len(data):
            raise ValueError(
                f"Length mismatch at position {self.index}: expected {length} bytes, "
                f"got {len(data)}",
            )
        return data

    def parse_simple_punc(self) -> bool:
        char = self.peek()
        if char is not None and char in "-./_:*+=":
            self.consume()
            return True
        return False

    def parse_token(self) -> bytes:
        """Read an ASCII token; numbers are length prefixes, not numeric atoms."""
        start = self.index
        char = self.peek()
        if char is None or char not in _TOKEN_START:
            raise ValueError(f"Expected token at position {self.index}")
        while (char := self.peek()) is not None and char in _TOKEN_CHARS:
            self.consume()
        return self.text[start : self.index].encode("latin-1")

    def parse_quote(self) -> bool:
        if self.peek() == "'":
            self.consume()
            return True
        return False

    def parse_backslash(self) -> bool:
        if self.peek() == "\\":
            self.consume()
            return True
        return False

    def parse_printable(self) -> bool:
        char = self.peek()
        if char is not None and " " <= char <= "~" and char not in '\\"':
            self.consume()
            return True
        return False

    def parse_escaped(self) -> bytes:
        """Decode one C escape, including RFC 9804 line continuations."""
        self._expect("\\")
        char = self.consume()
        if char in _ESCAPES:
            return _ESCAPES[char]
        if char in ("\r", "\n"):
            other = "\n" if char == "\r" else "\r"
            if self.peek() == other:
                self.consume()
            return b""
        if char == "x":
            count, base, alphabet = 2, 16, _HEX
        elif char is not None and char in "01234567":
            self.index -= 1
            count, base, alphabet = 3, 8, "01234567"
        else:
            raise ValueError(f"Invalid escape at position {self.index}")
        digits = self.text[self.index : self.index + count]
        if len(digits) != count or any(digit not in alphabet for digit in digits):
            raise ValueError(f"Invalid escape digits at position {self.index}")
        self.index += count
        value = int(digits, base)
        if value > 255:
            raise ValueError(f"Octal escape exceeds one octet at position {self.index}")
        return bytes([value])

    def _read_quoted_string(self) -> bytes:
        self._expect('"')
        result = bytearray()
        while self.peek() != '"':
            if self.peek() == "\\":
                result.extend(self.parse_escaped())
            elif self.parse_printable():
                result.append(ord(self.text[self.index - 1]))
            else:
                raise ValueError(
                    f"Expected printable character or escape at position {self.index}",
                )
        self.consume()
        return bytes(result)

    def parse_quoted_string(self) -> bytes:
        length = self.parse_decimal()
        return self._check_length(self._read_quoted_string(), length)

    def _read_verbatim(self, length: int) -> bytes:
        self._expect(":")
        end = self.index + length
        if end > self.text_length:
            raise ValueError(f"Truncated verbatim string at position {self.index}")
        data = self.text[self.index : end].encode("latin-1")
        self.index = end
        return data

    def parse_verbatim(self) -> bytes:
        length = self.parse_decimal()
        if length is None:
            raise ValueError(f"Expected verbatim length at position {self.index}")
        return self._read_verbatim(length)

    def _parse_simple_string(self, canonical: bool) -> bytes:
        length = self.parse_decimal()
        char = self.peek()
        if length is not None and char == ":":
            return self._read_verbatim(length)
        if canonical:
            raise ValueError(
                f"Expected canonical verbatim string at position {self.index}",
            )
        if char == '"':
            data = self._read_quoted_string()
        elif char == "#":
            data = self._read_hexadecimal()
        elif char == "|":
            data = self._read_base64("|", "|")
        elif length is None:
            return self.parse_token()
        else:
            raise ValueError(
                f"Expected string delimiter after length at position {self.index}",
            )
        return self._check_length(data, length)

    def parse_simple_string(self) -> bytes:
        return self._parse_simple_string(canonical=False)

    def _parse_display(self, canonical: bool) -> bytes:
        self._expect("[")
        if not canonical:
            self._skip_whitespace()
        hint = self._parse_simple_string(canonical)
        if not canonical:
            self._skip_whitespace()
        self._expect("]")
        if not canonical:
            self._skip_whitespace()
        return hint

    def parse_display(self) -> bytes:
        """Read one non-nested display-hint and its following whitespace."""
        return self._parse_display(canonical=False)

    def _parse_string(self, canonical: bool) -> Union[bytes, DisplayString]:
        if self.peek() == "[":
            hint = self._parse_display(canonical)
            return DisplayString(self._parse_simple_string(canonical), hint)
        return self._parse_simple_string(canonical)

    def parse_string(self) -> Union[bytes, DisplayString]:
        return self._parse_string(canonical=False)

    def _parse_value(self, canonical: bool) -> SExpression:
        # An explicit stack also handles untrusted lists deeper than Python's recursion limit.
        stack: List[Optional[List[SExpression]]] = []
        while True:
            if stack and not canonical:
                self._skip_whitespace()
            char = self.peek()
            if char == "(":
                self.consume()
                stack.append(None)
                continue
            if char == ")" and stack:
                self.consume()
                children = stack.pop()
                if children is None:
                    node: SExpression = []
                elif 3 <= len(children) <= 4:
                    # Trim the growth caused by appending to a compact pair.
                    node = children[:]
                else:
                    node = children
            elif char is None and stack:
                raise ValueError(f"Missing closing ')' at position {self.index}")
            else:
                node = self._parse_string(canonical)
            if not stack:
                return node
            children = stack[-1]
            if children is None:
                stack[-1] = [node]
            elif len(children) == 1:
                stack[-1] = [children[0], node]
            else:
                children.append(node)

    def parse_value(self) -> SExpression:
        """Read one advanced value, leaving subsequent input unread."""
        return self._parse_value(canonical=False)

    def _require_end(self) -> None:
        if not self.at_end():
            raise ValueError(f"Unexpected trailing input at position {self.index}")

    def parse_canonical(self) -> SExpression:
        """Read exactly one canonical expression, without structural whitespace."""
        value = self._parse_value(canonical=True)
        self._require_end()
        return value

    def parse(self) -> SExpression:
        """Read exactly one canonical, basic transport or advanced expression."""
        self._skip_whitespace()
        if self.peek() == "{":
            decoded = self._read_base64("{", "}")
            value = SExpressionParser(decoded).parse_canonical()
        else:
            value = self.parse_value()
        self._skip_whitespace()
        self._require_end()
        return value

    def parse_sexp(self) -> SExpression:
        return self.parse()


# Compatibility with the original primitive parser's public name.
SexpParser = SExpressionParser
