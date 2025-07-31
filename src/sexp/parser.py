"""
ABNF parser
"""

from typing import Optional
import base64


class SexpParser:
    def __init__(self, text: str):
        self.text = text
        self.text_length = len(text)
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

    # parsing primitives; sexp.abnf definition comes later.
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
        if char and (char.isalpha()):
            self.consume()
            return True
        return False

    def parse_digit(self) -> bool:
        """Parse DIGIT character - %x30-39 (0-9)"""
        char = self.peek()
        if char and char.isdigit():
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
        Parse any whitespace character (SP / HTAB / VTAB / CR / LF)

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
        return False

    def parse_base_64_char(self) -> bool:
        """
        Parse base64 character (A-Z, a-z, 0-9, '+', '/')

        Implements: base-64-char = ALPHA / DIGIT / "+" / "/"
        """
        char = self.peek()
        if char and (char.isalpha() or char.isdigit() or char in "+/"):
            self.consume()
            return True
        return False

    def parse_base_64_chars(self) -> int:
        """
        Parse base64 characters in groups of 4, skipping whitespace. Returns
        count of valid base64 chars.

        Implements: base-64-chars = 4(base-64-char *whitespace)

        That is, parses groups of 4 base64 chars, each possibly followed by
        whitespace. Returns total count of base64 chars parsed. Raises
        ValueError if the number of base64 characters is not divisible by 4.
        """
        count = 0
        while True:
            group_count = 0
            for _ in range(4):
                if self.parse_base_64_char():
                    group_count += 1
                    while self.parse_whitespace():
                        pass
                else:
                    break
            if group_count == 4:
                count += 4
            else:
                break
        if (count + group_count) % 4 != 0:
            raise ValueError(
                f"Invalid base64 character count: {count} (must be multiple of 4)"
            )
        return count + group_count

    def parse_base_64_end(self) -> int:
        """
        Parse base64 end group (with padding) and return count of valid base64
        chars parsed. Returns the count of base64 characters parsed (excluding
        padding). RFC 9804: Only base64 chars are counted, padding '=' is not.

        Implements:
        base-64-end = base-64-chars
            / 3(base-64-char *whitespace) ["=" *whitespace]
            / 2(base-64-char *whitespace) *2("=" *whitespace)
        """
        start_index = self.index
        # Try full group first
        chars = 0
        # Try base-64-chars (multiples of 4)
        try:
            chars = self.parse_base_64_chars()
            if chars > 0 and (chars % 4 == 0):
                return chars
        except ValueError:
            # If it raises, we know it wasn't a full group
            self.index = start_index

        # Try 3(base-64-char *whitespace) ["=" *whitespace]
        try:
            group_start = self.index
            count = 0
            for _ in range(3):
                if self.parse_base_64_char() or self.peek() == "=":
                    count += 1
                    while self.parse_whitespace():
                        pass
                else:
                    break
            if count == 3:
                pad_count = 0
                while self.peek() == "=":
                    self.consume()
                    pad_count += 1
                    while self.parse_whitespace():
                        pass
                # Only one padding allowed for this case
                if pad_count <= 1:
                    return count
        except ValueError:
            # If it raises, we know it wasn't a full group
            self.index = start_index

        try:
            # Try 2(base-64-char *whitespace) *2("=" *whitespace)
            self.index = group_start
            count = 0
            for _ in range(2):
                if self.parse_base_64_char():
                    count += 1
                    while self.parse_whitespace():
                        pass
                else:
                    break
            if count == 2:
                pad_count = 0
                for _ in range(2):
                    if self.peek() == "=":
                        self.consume()
                        pad_count += 1
                        while self.parse_whitespace():
                            pass
                if pad_count == 2:
                    return count
        except ValueError:
            # If it raises, we know it wasn't a full group
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
            return int(self.text[start : self.index])
        return None

    def parse_base_64(self) -> Optional[str]:
        """
        Parse a base64-encoded string (between '|' delimiters).
        Returns the decoded string, or None if not found.

        Implements: base-64 = [decimal] "|" *whitespace *base-64-chars [base-64-end] "|"
        """
        start_index = self.index
        # Optional decimal length (ignored for now)
        self.parse_decimal()

        # Opening delimiter
        if self.peek() != "|":
            raise ValueError(f"Missing opening '|' for base64 at position {self.index}")
        self.consume()

        # Skip any whitespace
        while self.parse_whitespace():
            pass

        # Collect base64 chars (with possible whitespace between)
        b64_chars = []
        while True:
            char = self.peek()
            if char is None or char == "|":
                break
            if char.isspace():
                self.consume()
                continue
            if char in "+/=" or char.isalnum():
                b64_chars.append(char)
                self.consume()
            else:
                # Invalid character in base64
                raise ValueError(
                    f"Invalid base64 character '{char}' at position {self.index}"
                )

        # Closing delimiter
        if self.peek() != "|":
            raise ValueError(f"Missing closing '|' for base64 at position {self.index}")
        self.consume()

        # Join and decode
        b64_str = "".join(b64_chars)
        if not b64_str:
            return ""
        try:
            decoded = base64.b64decode(b64_str, validate=True)
            # Try to decode as UTF-8, fallback to bytes
            try:
                return decoded.decode("utf-8")
            except UnicodeDecodeError:
                return decoded
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding at position {start_index}: {e}")

    def parse_hexadecimals(self) -> str:
        """
        Parse a sequence of hexadecimal digits and return as a string.
        Returns empty string if no hex digits found.
        """
        start = self.index
        while self.parse_hexdigit():
            pass
        return self.text[start : self.index]

    def parse_hexadecimal(self) -> Optional[int]:
        """
        Parse a sequence of hexadecimal digits and return as int.
        Returns None if no hex digits found.
        """
        start = self.index
        while self.parse_hexdigit():
            pass
        if self.index > start:
            return int(self.text[start : self.index], 16)
        return None
