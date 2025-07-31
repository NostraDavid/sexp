"""
Tests for our minimal ABNF parser
Starting with the most basic elements
"""

import pytest
from sexp.parser import SexpParser
from sexp.gen import sexp_gen
from hypothesis import given


class TestBasicUtilityMethods:
    """Tests for basic utility methods like consume, peek, at_end"""

    def test_consume_empty_string(self):
        """Test consuming from empty string returns None"""
        parser = SexpParser("")
        result = parser.consume()
        assert result is None


class TestParseSpMethod:
    """Tests for parse_sp method (space character parsing)"""

    @given(sexp_gen.sp)
    def test_parse_sp_success(self, s: str):
        """Test parsing a space character successfully"""
        parser = SexpParser(s)
        result = parser.parse_sp()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_sp_failure(self, s: str):
        """Test parsing non-space character fails"""
        parser = SexpParser(s)
        result = parser.parse_sp()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_sp_empty_string(self):
        """Test parsing space from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_sp()
        assert result is False
        assert parser.at_end()

    def test_parse_sp_multiple_chars(self):
        """Test parsing space when it's first of multiple characters"""
        parser = SexpParser(" abc")
        result = parser.parse_sp()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        # Next character should be 'a'


class TestParseHtabMethod:
    """Tests for parse_htab method (horizontal tab parsing)"""

    @given(sexp_gen.htab)
    def test_parse_htab_success(self, s: str):
        """Test parsing a horizontal tab character successfully"""
        parser = SexpParser(s)
        result = parser.parse_htab()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_htab_failure(self, s: str):
        """Test parsing non-htab character fails"""
        parser = SexpParser(s)
        result = parser.parse_htab()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything


class TestParseCrMethod:
    """Tests for parse_cr method (carriage return parsing)"""

    @given(sexp_gen.cr)
    def test_parse_cr_success(self, s: str):
        """Test parsing a carriage return character successfully"""
        parser = SexpParser(s)
        result = parser.parse_cr()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_cr_failure(self, s: str):
        """Test parsing non-cr character fails"""
        parser = SexpParser(s)
        result = parser.parse_cr()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_cr_empty_string(self):
        """Test parsing cr from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_cr()
        assert result is False
        assert parser.at_end()

    def test_parse_cr_multiple_chars(self):
        """Test parsing cr when it's first of multiple characters"""
        parser = SexpParser("\rabc")
        result = parser.parse_cr()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        # Next character should be 'a'
        assert parser.peek() == "a"


class TestParseLfMethod:
    """Tests for parse_lf method (line feed parsing)"""

    @given(sexp_gen.lf)
    def test_parse_lf_success(self, s: str):
        """Test parsing a line feed character successfully"""
        parser = SexpParser(s)
        result = parser.parse_lf()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_lf_failure(self, s: str):
        """Test parsing non-lf character fails"""
        parser = SexpParser(s)
        result = parser.parse_lf()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_lf_empty_string(self):
        """Test parsing lf from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_lf()
        assert result is False
        assert parser.at_end()

    def test_parse_lf_multiple_chars(self):
        """Test parsing lf when it's first of multiple characters"""
        parser = SexpParser("\nabc")
        result = parser.parse_lf()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        # Next character should be 'a'
        assert parser.peek() == "a"


class TestParseAlphaMethod:
    """Tests for parse_alpha method (alphabetic character parsing)"""

    @given(sexp_gen.alpha)
    def test_parse_alpha_success(self, s: str):
        """Test parsing an alphabetic character successfully"""
        parser = SexpParser(s)
        result = parser.parse_alpha()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.digit)
    def test_parse_alpha_failure(self, s: str):
        """Test parsing non-alpha character fails"""
        parser = SexpParser(s)
        result = parser.parse_alpha()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_alpha_empty_string(self):
        """Test parsing alpha from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_alpha()
        assert result is False
        assert parser.at_end()

    def test_parse_alpha_multiple_chars(self):
        """Test parsing alpha when it's first of multiple characters"""
        parser = SexpParser("abc123")
        result = parser.parse_alpha()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        # Next character should be 'b'
        assert parser.peek() == "b"


class TestParseDigitMethod:
    """Tests for parse_digit method (digit character parsing)"""

    @given(sexp_gen.digit)
    def test_parse_digit_success(self, s: str):
        """Test parsing a digit character successfully"""
        parser = SexpParser(s)
        result = parser.parse_digit()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_digit_failure(self, s: str):
        """Test parsing non-digit character fails"""
        parser = SexpParser(s)
        result = parser.parse_digit()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_digit_empty_string(self):
        """Test parsing digit from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_digit()
        assert result is False
        assert parser.at_end()

    def test_parse_digit_multiple_chars(self):
        """Test parsing digit when it's first of multiple characters"""
        parser = SexpParser("123abc")
        result = parser.parse_digit()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        # Next character should be '2'
        assert parser.peek() == "2"


class TestParseHexdigitMethod:
    """Tests for parse_hexdigit method (hexadecimal digit parsing)"""

    @given(sexp_gen.hexdig)
    def test_parse_hexdigit_success(self, s: str):
        """Test parsing a hex digit character successfully"""
        parser = SexpParser(s)
        result = parser.parse_hexdigit()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_hexdigit_failure_alpha(self, s: str):
        """Test parsing non-hexdigit alpha character fails"""
        # Filter out valid hex alpha chars
        if s.lower() not in "abcdef":
            parser = SexpParser(s)
            result = parser.parse_hexdigit()
            assert result is False
            assert not parser.at_end()
            assert parser.index == 0  # Should not consume anything

    def test_parse_hexdigit_empty_string(self):
        """Test parsing hexdigit from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_hexdigit()
        assert result is False
        assert parser.at_end()

    def test_parse_hexdigit_multiple_chars(self):
        """Test parsing hexdigit when it's first of multiple characters"""
        parser = SexpParser("a1b2")
        result = parser.parse_hexdigit()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        # Next character should be '1'
        assert parser.peek() == "1"

    def test_parse_hexdigit_uppercase(self):
        """Test parsing uppercase hex digits"""
        for char in "ABCDEF":
            parser = SexpParser(char)
            result = parser.parse_hexdigit()
            assert result is True
            assert parser.at_end()

    def test_parse_hexdigit_lowercase(self):
        """Test parsing lowercase hex digits"""
        for char in "abcdef":
            parser = SexpParser(char)
            result = parser.parse_hexdigit()
            assert result is True
            assert parser.at_end()

    def test_parse_hexdigit_digits(self):
        """Test parsing numeric hex digits"""
        for char in "0123456789":
            parser = SexpParser(char)
            result = parser.parse_hexdigit()
            assert result is True
            assert parser.at_end()


class TestParseDquoteMethod:
    """Tests for parse_dquote method (double quote parsing)"""

    def test_parse_dquote_success(self):
        """Test parsing double quote character successfully"""
        parser = SexpParser('"')
        result = parser.parse_dquote()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_dquote_failure(self, s: str):
        """Test parsing non-dquote character fails"""
        parser = SexpParser(s)
        result = parser.parse_dquote()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_dquote_empty_string(self):
        """Test parsing dquote from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_dquote()
        assert result is False
        assert parser.at_end()

    def test_parse_dquote_multiple_chars(self):
        """Test parsing dquote when it's first of multiple characters"""
        parser = SexpParser('"hello"')
        result = parser.parse_dquote()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        # Next character should be 'h'
        assert parser.peek() == "h"


class TestParseOctetMethod:
    """Tests for parse_octet method (any character parsing)"""

    def test_parse_octet_success(self):
        """Test parsing any character successfully"""
        test_chars = ["a", "1", " ", "\t", "\n", "\r", '"', "#", "!", "@", "€"]
        for char in test_chars:
            parser = SexpParser(char)
            result = parser.parse_octet()
            assert result is True
            assert parser.at_end()

    def test_parse_octet_empty_string(self):
        """Test parsing octet from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_octet()
        assert result is False
        assert parser.at_end()

    def test_parse_octet_multiple_chars(self):
        """Test parsing octet when it's first of multiple characters"""
        parser = SexpParser("abc123")
        result = parser.parse_octet()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        # Next character should be 'b'
        assert parser.peek() == "b"

    def test_parse_octet_unicode(self):
        """Test parsing unicode characters as octets"""
        unicode_chars = ["€", "ñ", "中", "🙂"]
        for char in unicode_chars:
            parser = SexpParser(char)
            result = parser.parse_octet()
            assert result is True


class TestParseVtabMethod:
    """Tests for parse_vtab method (vertical tab parsing)"""

    def test_parse_vtab_success(self):
        """Test parsing vertical tab character successfully"""
        parser = SexpParser("\x0b")
        result = parser.parse_vtab()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_vtab_failure(self, s: str):
        """Test parsing non-vtab character fails"""
        parser = SexpParser(s)
        result = parser.parse_vtab()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0

    def test_parse_vtab_empty_string(self):
        """Test parsing vtab from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_vtab()
        assert result is False
        assert parser.at_end()

    def test_parse_vtab_multiple_chars(self):
        """Test parsing vtab when it's first of multiple characters"""
        parser = SexpParser("\x0babc")
        result = parser.parse_vtab()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        assert parser.peek() == "a"


class TestParseFfMethod:
    """Tests for parse_ff method (form feed parsing)"""

    def test_parse_ff_success(self):
        """Test parsing form feed character successfully"""
        parser = SexpParser("\x0c")
        result = parser.parse_ff()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_ff_failure(self, s: str):
        """Test parsing non-ff character fails"""
        parser = SexpParser(s)
        result = parser.parse_ff()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0

    def test_parse_ff_empty_string(self):
        """Test parsing ff from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_ff()
        assert result is False
        assert parser.at_end()

    def test_parse_ff_multiple_chars(self):
        """Test parsing ff when it's first of multiple characters"""
        parser = SexpParser("\x0cabc")
        result = parser.parse_ff()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        assert parser.peek() == "a"


class TestParseWhitespaceMethod:
    """Tests for parse_whitespace method (any whitespace character parsing)"""

    @pytest.mark.parametrize("char", [" ", "\t", "\x0b", "\r", "\n"])
    def test_parse_whitespace_success(self, char):
        """Test parsing any whitespace character successfully"""
        parser = SexpParser(char)
        result = parser.parse_whitespace()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_whitespace_failure(self, s: str):
        """Test parsing non-whitespace character fails"""
        parser = SexpParser(s)
        result = parser.parse_whitespace()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0

    def test_parse_whitespace_empty_string(self):
        """Test parsing whitespace from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_whitespace()
        assert result is False
        assert parser.at_end()

    def test_parse_whitespace_multiple_chars(self):
        """Test parsing whitespace when it's first of multiple characters"""
        parser = SexpParser(" \tabc")
        result = parser.parse_whitespace()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        assert parser.peek() == "\t"


class TestParseBase64CharMethod:
    """Tests for parse_base_64_char method (base64 character parsing)"""

    @pytest.mark.parametrize(
        "char", list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/")
    )
    def test_parse_base_64_char_success(self, char):
        """Test parsing valid base64 character successfully"""
        parser = SexpParser(char)
        result = parser.parse_base_64_char()
        assert result is True
        assert parser.at_end()

    @pytest.mark.parametrize("char", ["=", "-", "_", "*", "!", " "])
    def test_parse_base_64_char_failure(self, char):
        """Test parsing invalid base64 character fails"""
        parser = SexpParser(char)
        result = parser.parse_base_64_char()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0

    def test_parse_base_64_char_empty_string(self):
        """Test parsing base64 char from empty string fails"""
        parser = SexpParser("")
        result = parser.parse_base_64_char()
        assert result is False
        assert parser.at_end()

    def test_parse_base_64_char_multiple_chars(self):
        """Test parsing base64 char when it's first of multiple characters"""
        parser = SexpParser("Qabc")
        result = parser.parse_base_64_char()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1


class TestParseBase64CharsMethod:
    """Tests for parse_base_64_chars method (sequence of base64 characters in groups of 4)"""

    @pytest.mark.parametrize(
        "input_str, expected_count",
        [
            ("ABCD", 4),
            ("ABCDWXYZ", 8),
            ("ABCD WXYZ", 8),  # whitespace between groups
            ("A B C D", 4),  # whitespace between chars
            ("ABCD\tWXYZ", 8),  # tab as whitespace
            ("ABCD\nWXYZ", 8),  # newline as whitespace
            ("ABCD", 4),
            ("", 0),
            ("ABCD WXYZ1234", 12),  # three groups
            ("ABCD WXYZ 1234", 12),  # three groups with whitespace
        ],
    )
    def test_parse_base_64_chars_various(self, input_str, expected_count):
        parser = SexpParser(input_str)
        count = parser.parse_base_64_chars()
        assert count == expected_count
        # Should consume only the valid base64 chars and whitespace
        # If expected_count == 0, index should be 0
        if expected_count == 0:
            assert parser.index == 0
        else:
            # Should consume up to the last valid group
            # Find where parsing should stop
            i = 0
            chars = 0
            while i < len(input_str) and chars < expected_count:
                if (
                    input_str[i]
                    in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
                ):
                    chars += 1
                i += 1
            # Allow for whitespace after each base64 char
            while i < len(input_str) and input_str[i].isspace():
                i += 1
            assert parser.index >= expected_count

    def test_parse_base_64_chars_with_extra_non_base64(self):
        parser = SexpParser("ABCD!WXYZ")
        count = parser.parse_base_64_chars()
        assert count == 4  # Only first group is valid
        assert parser.index == 4  # Stops at '!' (non-base64 char)

    def test_parse_base_64_chars_only_whitespace(self):
        parser = SexpParser("    ")
        count = parser.parse_base_64_chars()
        assert count == 0
        assert parser.index == 0

    def test_parse_base_64_chars_partial_group(self):
        s = "ABC"
        parser = SexpParser(s)
        with pytest.raises(ValueError) as excinfo:
            parser.parse_base_64_chars()
        assert "Invalid base64 character count" in str(excinfo.value)
        assert parser.index == len(s)

    def test_parse_base_64_chars_multiple_groups_with_whitespace(self):
        parser = SexpParser("ABCD \tWXYZ\n1234")
        count = parser.parse_base_64_chars()
        assert count == 12
        assert parser.index == len("ABCD \tWXYZ\n1234")


class TestParseBase64EndMethod:
    """Tests for parse_base_64_end method (base64 end parsing according to RFC 9804)"""

    @pytest.mark.parametrize(
        "input_str, expected_count",
        [
            ("ABCD", 4),  # base-64-chars: full group
            ("ABCDWXYZ", 8),  # two full groups
            ("ABCD WXYZ", 8),  # whitespace between groups
        ],
    )
    def test_parse_base_64_end_full_group(self, input_str, expected_count):
        parser = SexpParser(input_str)
        count = parser.parse_base_64_end()
        assert count == expected_count
        assert parser.index >= expected_count

    @pytest.mark.parametrize(
        "input_str, expected_count",
        [
            ("ABC=", 3),  # 3 chars + 1 padding
            ("ABC= ", 3),  # 3 chars + 1 padding + whitespace
            ("A B C =", 3),  # whitespace between chars and padding
        ],
    )
    def test_parse_base_64_end_three_chars_one_padding(self, input_str, expected_count):
        parser = SexpParser(input_str)
        count = parser.parse_base_64_end()
        assert count == expected_count
        # Should consume up to the padding
        assert parser.index >= len(input_str.rstrip())

    @pytest.mark.parametrize(
        "input_str, expected_count",
        [
            ("AB==", 2),  # 2 chars + 2 padding
            ("A B = =", 2),  # whitespace between chars and paddings
            ("AB== ", 2),  # trailing whitespace
        ],
    )
    def test_parse_base_64_end_two_chars_two_padding(self, input_str, expected_count):
        parser = SexpParser(input_str)
        count = parser.parse_base_64_end()
        assert count == expected_count
        assert parser.index >= len(input_str.rstrip())

    def test_parse_base_64_end_with_whitespace(self):
        parser = SexpParser("ABCD \t\n")
        count = parser.parse_base_64_end()
        assert count == 4
        # Should consume all base64 chars and whitespace
        assert parser.index == len("ABCD \t\n")


class TestParseDecimalMethod:
    """Tests for parse_decimal method (sequence of decimal digits as int)"""

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("123", 123),
            ("0", 0),
            ("00123", 123),
            ("42abc", 42),
            ("9", 9),
            ("", None),
            ("abc", None),
            (" 123", None),
        ],
    )
    def test_parse_decimal_various(self, input_str, expected):
        parser = SexpParser(input_str)
        result = parser.parse_decimal()
        assert result == expected
        if expected is not None:
            # Should consume all contiguous digit characters
            digit_count = 0
            for c in input_str:
                if c.isdigit():
                    digit_count += 1
                else:
                    break
            assert parser.index == digit_count
        else:
            assert parser.index == 0

    def test_parse_decimal_partial(self):
        parser = SexpParser("123abc456")
        result = parser.parse_decimal()
        assert result == 123
        assert parser.index == 3
        assert parser.peek() == "a"

    def test_parse_decimal_empty(self):
        parser = SexpParser("")
        result = parser.parse_decimal()
        assert result is None
        assert parser.at_end()


class TestParseBase64Method:
    """Tests for parse_base_64 method (base64-encoded string between '|')"""

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("|YWJj|", "abc"),
            ("|QQ==|", "A"),
            ("|SGVsbG8gd29ybGQ=|", "Hello world"),
            ("|MTIzNDU2|", "123456"),
            ("||", ""),  # empty base64
        ],
    )
    def test_parse_base_64_success(self, input_str, expected):
        parser = SexpParser(input_str)
        result = parser.parse_base_64()
        assert result == expected
        assert parser.at_end()

    def test_parse_base_64_with_trailing(self):
        parser = SexpParser("|YWJj|foo")
        result = parser.parse_base_64()
        assert result == "abc"
        assert parser.index == 6
        assert parser.peek() == "f"

    def test_parse_base_64_invalid_start(self):
        parser = SexpParser("YWJj|")
        with pytest.raises(ValueError) as excinfo:
            parser.parse_base_64()
        assert "Missing opening '|'" in str(
            excinfo.value
        ) or "Missing closing '|'" in str(excinfo.value)
        assert parser.index == 0

    def test_parse_base_64_unterminated(self):
        parser = SexpParser("|YWJj")
        with pytest.raises(ValueError) as excinfo:
            parser.parse_base_64()
        assert "Missing closing '|' for base64 at position" in str(excinfo.value)

    def test_parse_base_64_invalid_char(self):
        parser = SexpParser("|YWJ!j|")
        with pytest.raises(ValueError) as excinfo:
            parser.parse_base_64()
        assert "Invalid base64 character" in str(excinfo.value)

    def test_parse_base_64_decode_error(self):
        # Invalid base64 padding
        parser = SexpParser("|YWJj===")
        with pytest.raises(ValueError) as excinfo:
            parser.parse_base_64()
        assert "Missing closing '|' for base64 at position" in str(excinfo.value)


class TestParseHexadecimalsMethod:
    """Tests for parse_hexadecimals method (sequence of hex digits as string)"""

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("abc123", "abc123"),
            ("ABCDEF", "ABCDEF"),
            ("0123456789abcdef", "0123456789abcdef"),
            ("", ""),
            ("g123", ""),  # 'g' is not a hex digit
            ("a1b2c3xyz", "a1b2c3"),
        ],
    )
    def test_parse_hexadecimals_various(self, input_str, expected):
        parser = SexpParser(input_str)
        result = parser.parse_hexadecimals()
        assert result == expected
        assert parser.index == len(expected)

    def test_parse_hexadecimals_empty(self):
        parser = SexpParser("")
        result = parser.parse_hexadecimals()
        assert result == ""
        assert parser.at_end()

    def test_parse_hexadecimals_partial(self):
        parser = SexpParser("deadbeef!")
        result = parser.parse_hexadecimals()
        assert result == "deadbeef"
        assert parser.index == 8
        assert parser.peek() == "!"


class TestParseHexadecimalMethod:
    """Tests for parse_hexadecimal method (sequence of hex digits as int)"""

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("1a", 0x1A),
            ("0", 0),
            ("deadBEEF", 0xDEADBEEF),
            ("ABC", 0xABC),
            ("", None),
            ("g123", None),
            ("123xyz", 0x123),
        ],
    )
    def test_parse_hexadecimal_various(self, input_str, expected):
        parser = SexpParser(input_str)
        result = parser.parse_hexadecimal()
        assert result == expected
        if expected is not None:
            # Should consume only the hex digits
            hex_part = ""
            for c in input_str:
                if c.lower() in "0123456789abcdef":
                    hex_part += c
                else:
                    break
            assert parser.index == len(hex_part)
        else:
            assert parser.index == 0

    def test_parse_hexadecimal_empty(self):
        parser = SexpParser("")
        result = parser.parse_hexadecimal()
        assert result is None
        assert parser.at_end()

    def test_parse_hexadecimal_partial(self):
        parser = SexpParser("beef!foo")
        result = parser.parse_hexadecimal()
        assert result == 0xBEEF
        assert parser.index == 4
        assert parser.peek() == "!"
