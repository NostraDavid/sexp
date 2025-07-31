from hypothesis import strategies as st


# Basic ABNF core rules
class SExpressionGenerator:
    """ABNF strategy generators for S-expressions based on RFC 9804.

    This class was created so I as actually able to tell which properties have
    been tested, while I was writing tests.
    """

    # Basic ABNF core rules
    @property
    def sp(self):
        return st.just(" ")

    @property
    def htab(self):
        return st.just("\t")

    @property
    def cr(self):
        return st.just("\r")

    @property
    def lf(self):
        return st.just("\n")

    @property
    def alpha(self):
        return st.one_of(
            st.characters(min_codepoint=ord("A"), max_codepoint=ord("Z")),
            st.characters(min_codepoint=ord("a"), max_codepoint=ord("z")),
        )

    @property
    def digit(self):
        return st.characters(min_codepoint=ord("0"), max_codepoint=ord("9"))

    @property
    def hexdig(self):
        return st.one_of(
            self.digit,
            st.characters(min_codepoint=ord("A"), max_codepoint=ord("F")),
            st.characters(min_codepoint=ord("a"), max_codepoint=ord("f")),
        )

    @property
    def dquote(self):
        return st.just('"')

    @property
    def octet(self):
        return st.binary(min_size=1, max_size=1)

    # S-expression specific basic rules
    @property
    def vtab(self):
        return st.just("\x0b")

    @property
    def ff(self):
        return st.just("\x0c")

    @property
    def whitespace(self):
        return st.one_of(self.sp, self.htab, self.vtab, self.cr, self.lf, self.ff)

    # Character sets for specific uses
    @property
    def base_64_char(self):
        return st.one_of(self.alpha, self.digit, st.just("+"), st.just("/"))

    # Base64 strings
    @property
    def base_64_chars(self):
        @st.composite
        def _base_64_chars(draw):
            chars = []
            for _ in range(4):
                char = draw(self.base_64_char)
                ws = draw(st.lists(self.whitespace, max_size=3))
                chars.append(char + "".join(ws))
            return "".join(chars)

        return _base_64_chars()

    @property
    def base_64_end(self):
        @st.composite
        def _base_64_end(draw):
            choice = draw(st.integers(min_value=0, max_value=2))
            if choice == 0:
                # base-64-chars (4 chars)
                chars = []
                for _ in range(4):
                    char = draw(self.base_64_char)
                    ws = draw(st.lists(self.whitespace, max_size=3))
                    chars.append(char + "".join(ws))
                return "".join(chars)
            elif choice == 1:
                # 3 chars + optional "="
                chars = []
                for _ in range(3):
                    char = draw(self.base_64_char)
                    ws = draw(st.lists(self.whitespace, max_size=3))
                    chars.append(char + "".join(ws))
                eq_choice = draw(st.booleans())
                if eq_choice:
                    ws = draw(st.lists(self.whitespace, max_size=3))
                    return "".join(chars) + "=" + "".join(ws)
                return "".join(chars)
            else:
                # 2 chars + up to 2 "="
                chars = []
                for _ in range(2):
                    char = draw(self.base_64_char)
                    ws = draw(st.lists(self.whitespace, max_size=3))
                    chars.append(char + "".join(ws))
                eq_count = draw(st.integers(min_value=0, max_value=2))
                eq_parts = []
                for _ in range(eq_count):
                    ws = draw(st.lists(self.whitespace, max_size=3))
                    eq_parts.append("=" + "".join(ws))
                return "".join(chars) + "".join(eq_parts)

        return _base_64_end()

    # Decimal numbers
    @property
    def decimal(self):
        @st.composite
        def _decimal(draw):
            is_zero = draw(st.booleans())
            if is_zero:
                return "0"
            else:
                # Non-zero number: first digit 1-9, then 0-9 digits
                first = draw(
                    st.characters(min_codepoint=ord("1"), max_codepoint=ord("9"))
                )
                rest = draw(st.lists(self.digit, max_size=10))
                return first + "".join(rest)

        return _decimal()

    @property
    def base_64(self):
        @st.composite
        def _base_64(draw):
            # Optional decimal prefix
            has_decimal = draw(st.booleans())
            dec = draw(self.decimal) if has_decimal else ""

            # Opening whitespace after |
            ws1 = draw(st.lists(self.whitespace, max_size=5))

            # Base64 character sequences
            chars = draw(st.lists(self.base_64_chars, max_size=10))

            # Optional base64 end sequence
            has_end = draw(st.booleans())
            end = draw(self.base_64_end) if has_end else ""

            # Closing whitespace before |
            ws2 = draw(st.lists(self.whitespace, max_size=5))

            return dec + "|" + "".join(ws1) + "".join(chars) + end + "".join(ws2) + "|"

        return _base_64()

    # Hexadecimal strings
    @property
    def hexadecimals(self):
        @st.composite
        def _hexadecimals(draw):
            hex1 = draw(self.hexdig)
            ws = draw(st.lists(self.whitespace, max_size=3))
            hex2 = draw(self.hexdig)
            return hex1 + "".join(ws) + hex2

        return _hexadecimals()

    @property
    def hexadecimal(self):
        @st.composite
        def _hexadecimal(draw):
            # Optional decimal prefix
            has_decimal = draw(st.booleans())
            dec = draw(self.decimal) if has_decimal else ""

            # Opening whitespace after #
            ws1 = draw(st.lists(self.whitespace, max_size=5))

            # Hexadecimal digit pairs
            hexs = draw(st.lists(self.hexadecimals, max_size=10))

            # Closing whitespace before #
            ws2 = draw(st.lists(self.whitespace, max_size=5))

            return dec + "#" + "".join(ws1) + "".join(hexs) + "".join(ws2) + "#"

        return _hexadecimal()

    @property
    def simple_punc(self):
        return st.one_of(
            st.just("-"),
            st.just("."),
            st.just("/"),
            st.just("_"),
            st.just(":"),
            st.just("*"),
            st.just("+"),
            st.just("="),
        )

    @property
    def token(self):
        @st.composite
        def _token(draw):
            # First character: alpha or simple punctuation
            first = draw(st.one_of(self.alpha, self.simple_punc))

            # Rest of the characters: alpha, digit, or simple punctuation
            rest = draw(
                st.lists(
                    st.one_of(self.alpha, self.digit, self.simple_punc), max_size=20
                )
            )

            return first + "".join(rest)

        return _token()

    @property
    def quote(self):
        return st.just("'")

    @property
    def backslash(self):
        return st.just("\\")

    @property
    def escaped(self):
        @st.composite
        def _escaped(draw):
            zero_to_seven = st.characters(
                min_codepoint=ord("0"), max_codepoint=ord("7")
            )
            bs = draw(self.backslash)

            # Choose which type of escape sequence to generate
            escape_type = draw(st.integers(min_value=0, max_value=13))

            if escape_type == 0:
                char = "\x3f"  # ?
            elif escape_type == 1:
                char = "\x61"  # a
            elif escape_type == 2:
                char = "\x62"  # b
            elif escape_type == 3:
                char = "\x66"  # f
            elif escape_type == 4:
                char = "\x6e"  # n
            elif escape_type == 5:
                char = "\x72"  # r
            elif escape_type == 6:
                char = "\x74"  # t
            elif escape_type == 7:
                char = "\x76"  # v
            elif escape_type == 8:
                char = draw(st.one_of(self.dquote, self.quote, self.backslash))
            elif escape_type == 9:
                # Octal escape: three octal digits
                d1 = draw(zero_to_seven)
                d2 = draw(zero_to_seven)
                d3 = draw(zero_to_seven)
                char = d1 + d2 + d3
            elif escape_type == 10:
                # Hex escape: \x followed by two hex digits
                h1 = draw(self.hexdig)
                h2 = draw(self.hexdig)
                char = "\x78" + h1 + h2
            elif escape_type == 11:
                char = draw(self.cr)
            elif escape_type == 12:
                char = draw(self.lf)
            else:
                # Line ending combinations: CR+LF or LF+CR
                line_choice = draw(st.booleans())
                if line_choice:
                    char = draw(self.cr) + draw(self.lf)
                else:
                    char = draw(self.lf) + draw(self.cr)

            return bs + char

        return _escaped()

    # Printable characters for quoted strings (excludes " and \)
    @property
    def printable(self):
        return st.one_of(
            st.characters(min_codepoint=0x20, max_codepoint=0x21),  # space, !
            st.characters(min_codepoint=0x23, max_codepoint=0x5B),  # # to [
            st.characters(min_codepoint=0x5D, max_codepoint=0x7E),  # ] to ~
        )

    @property
    def quoted_string(self):
        @st.composite
        def _quoted_string(draw):
            # Optional decimal prefix
            has_decimal = draw(st.booleans())
            dec = draw(self.decimal) if has_decimal else ""

            # Content: mix of printable and escaped characters
            content = draw(
                st.lists(st.one_of(self.printable, self.escaped), max_size=50)
            )

            return dec + '"' + "".join(content) + '"'

        return _quoted_string()

    @property
    def verbatim(self):
        @st.composite
        def _verbatim(draw):
            content = draw(
                st.text(
                    alphabet=st.characters(min_codepoint=0x00, max_codepoint=0x7F),
                    max_size=99,
                )
            )
            length = len(content.encode("utf-8"))
            return f"{length}:{content}"

        return _verbatim()

    @property
    def simple_string(self):
        return st.one_of(
            self.verbatim,
            self.quoted_string,
            self.token,
            self.hexadecimal,
            self.base_64,
        )

    @property
    def display(self):
        @st.composite
        def _display(draw):
            ws1 = draw(st.lists(self.whitespace, max_size=5))
            simple_str = draw(self.simple_string)
            ws2 = draw(st.lists(self.whitespace, max_size=5))
            ws3 = draw(st.lists(self.whitespace, max_size=5))
            return "[" + "".join(ws1) + simple_str + "".join(ws2) + "]" + "".join(ws3)

        return _display()

    @property
    def string(self):
        @st.composite
        def _string(draw):
            has_display = draw(st.booleans())
            if has_display:
                disp = draw(self.display)
                simple_str = draw(self.simple_string)
                return disp + simple_str
            else:
                return draw(self.simple_string)

        return _string()

    @property
    def value(self):
        @st.composite
        def _value(draw):
            choice = draw(st.booleans())
            if choice:
                # Generate a string
                return draw(self.string)
            else:
                # Generate a list: "(" *whitespace *(value / whitespace) *whitespace ")"
                ws1 = draw(st.lists(self.whitespace, max_size=5))

                # Generate list contents (mix of values and whitespace)
                contents = []
                num_items = draw(st.integers(min_value=0, max_value=10))
                for _ in range(num_items):
                    item_choice = draw(st.booleans())
                    if item_choice:
                        # Add a value (recursive)
                        contents.append(draw(st.deferred(lambda: self.value)))
                    else:
                        # Add whitespace
                        ws = draw(st.lists(self.whitespace, min_size=1, max_size=5))
                        contents.append("".join(ws))

                ws2 = draw(st.lists(self.whitespace, max_size=5))
                return "(" + "".join(ws1) + "".join(contents) + "".join(ws2) + ")"

        return _value()

    @property
    def sexp(self):
        @st.composite
        def _sexp(draw):
            ws1 = draw(st.lists(self.whitespace, max_size=5))
            val = draw(self.value)
            ws2 = draw(st.lists(self.whitespace, max_size=5))
            return "".join(ws1) + val + "".join(ws2)

        return _sexp()


sexp_gen = SExpressionGenerator()
