"""
Tests for our minimal ABNF parser
Starting with the most basic elements
"""

import pytest
from sexp.parser import SExpressionParser
from sexp.gen import sexp_gen
from hypothesis import given


@pytest.mark.parametrize(
    ("method", "character"),
    [
        ("parse_alpha", "é"),
        ("parse_digit", "²"),
        ("parse_digit", "١"),
        ("parse_base_64_char", "é"),
        ("parse_base_64_char", "١"),
    ],
)
def test_abnf_character_classes_reject_out_of_range(method, character):
    parser = SExpressionParser(character)
    assert getattr(parser, method)() is False
    assert parser.index == 0


def test_form_feed_is_whitespace():
    parser = SExpressionParser("\x0c")
    assert parser.parse_whitespace() is True
    assert parser.at_end()
    assert SExpressionParser("|Y\x0cWJj|").parse_base_64() == "abc"
    assert SExpressionParser("#6\x0c1#").parse_hexadecimal() == b"a"


@pytest.mark.parametrize("text", ["|Y\u00a0WJj|", "#6\u00a01#", "|é|"])
def test_encoded_strings_reject_non_abnf_characters(text):
    parser = SExpressionParser(text)
    with pytest.raises(ValueError):
        if text.startswith("|"):
            parser.parse_base_64()
        else:
            parser.parse_hexadecimal()


class TestBasicUtilityMethods:
    """Tests for basic utility methods like consume, peek, at_end"""

    def test_consume_empty_string(self):
        """Test consuming from empty string returns None"""
        parser = SExpressionParser("")
        result = parser.consume()
        assert result is None


class TestParseSpMethod:
    """Tests for parse_sp method (space character parsing)"""

    @given(sexp_gen.sp)
    def test_parse_sp_success(self, s: str):
        """Test parsing a space character successfully"""
        parser = SExpressionParser(s)
        result = parser.parse_sp()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_sp_failure(self, s: str):
        """Test parsing non-space character fails"""
        parser = SExpressionParser(s)
        result = parser.parse_sp()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_sp_empty_string(self):
        """Test parsing space from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_sp()
        assert result is False
        assert parser.at_end()

    def test_parse_sp_multiple_chars(self):
        """Test parsing space when it's first of multiple characters"""
        parser = SExpressionParser(" abc")
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
        parser = SExpressionParser(s)
        result = parser.parse_htab()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_htab_failure(self, s: str):
        """Test parsing non-htab character fails"""
        parser = SExpressionParser(s)
        result = parser.parse_htab()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything


class TestParseCrMethod:
    """Tests for parse_cr method (carriage return parsing)"""

    @given(sexp_gen.cr)
    def test_parse_cr_success(self, s: str):
        """Test parsing a carriage return character successfully"""
        parser = SExpressionParser(s)
        result = parser.parse_cr()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_cr_failure(self, s: str):
        """Test parsing non-cr character fails"""
        parser = SExpressionParser(s)
        result = parser.parse_cr()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_cr_empty_string(self):
        """Test parsing cr from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_cr()
        assert result is False
        assert parser.at_end()

    def test_parse_cr_multiple_chars(self):
        """Test parsing cr when it's first of multiple characters"""
        parser = SExpressionParser("\rabc")
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
        parser = SExpressionParser(s)
        result = parser.parse_lf()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_lf_failure(self, s: str):
        """Test parsing non-lf character fails"""
        parser = SExpressionParser(s)
        result = parser.parse_lf()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_lf_empty_string(self):
        """Test parsing lf from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_lf()
        assert result is False
        assert parser.at_end()

    def test_parse_lf_multiple_chars(self):
        """Test parsing lf when it's first of multiple characters"""
        parser = SExpressionParser("\nabc")
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
        parser = SExpressionParser(s)
        result = parser.parse_alpha()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.digit)
    def test_parse_alpha_failure(self, s: str):
        """Test parsing non-alpha character fails"""
        parser = SExpressionParser(s)
        result = parser.parse_alpha()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_alpha_empty_string(self):
        """Test parsing alpha from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_alpha()
        assert result is False
        assert parser.at_end()

    def test_parse_alpha_multiple_chars(self):
        """Test parsing alpha when it's first of multiple characters"""
        parser = SExpressionParser("abc123")
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
        parser = SExpressionParser(s)
        result = parser.parse_digit()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_digit_failure(self, s: str):
        """Test parsing non-digit character fails"""
        parser = SExpressionParser(s)
        result = parser.parse_digit()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_digit_empty_string(self):
        """Test parsing digit from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_digit()
        assert result is False
        assert parser.at_end()

    def test_parse_digit_multiple_chars(self):
        """Test parsing digit when it's first of multiple characters"""
        parser = SExpressionParser("123abc")
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
        parser = SExpressionParser(s)
        result = parser.parse_hexdigit()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_hexdigit_failure_alpha(self, s: str):
        """Test parsing non-hexdigit alpha character fails"""
        # Filter out valid hex alpha chars
        if s.lower() not in "abcdef":
            parser = SExpressionParser(s)
            result = parser.parse_hexdigit()
            assert result is False
            assert not parser.at_end()
            assert parser.index == 0  # Should not consume anything

    def test_parse_hexdigit_empty_string(self):
        """Test parsing hexdigit from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_hexdigit()
        assert result is False
        assert parser.at_end()

    def test_parse_hexdigit_multiple_chars(self):
        """Test parsing hexdigit when it's first of multiple characters"""
        parser = SExpressionParser("a1b2")
        result = parser.parse_hexdigit()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        # Next character should be '1'
        assert parser.peek() == "1"

    def test_parse_hexdigit_uppercase(self):
        """Test parsing uppercase hex digits"""
        for char in "ABCDEF":
            parser = SExpressionParser(char)
            result = parser.parse_hexdigit()
            assert result is True
            assert parser.at_end()

    def test_parse_hexdigit_lowercase(self):
        """Test parsing lowercase hex digits"""
        for char in "abcdef":
            parser = SExpressionParser(char)
            result = parser.parse_hexdigit()
            assert result is True
            assert parser.at_end()

    def test_parse_hexdigit_digits(self):
        """Test parsing numeric hex digits"""
        for char in "0123456789":
            parser = SExpressionParser(char)
            result = parser.parse_hexdigit()
            assert result is True
            assert parser.at_end()


class TestParseDquoteMethod:
    """Tests for parse_dquote method (double quote parsing)"""

    def test_parse_dquote_success(self):
        """Test parsing double quote character successfully"""
        parser = SExpressionParser('"')
        result = parser.parse_dquote()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_dquote_failure(self, s: str):
        """Test parsing non-dquote character fails"""
        parser = SExpressionParser(s)
        result = parser.parse_dquote()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0  # Should not consume anything

    def test_parse_dquote_empty_string(self):
        """Test parsing dquote from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_dquote()
        assert result is False
        assert parser.at_end()

    def test_parse_dquote_multiple_chars(self):
        """Test parsing dquote when it's first of multiple characters"""
        parser = SExpressionParser('"hello"')
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
        test_chars = ["a", "1", " ", "\t", "\n", "\r", '"', "#", "!", "@"]
        for char in test_chars:
            parser = SExpressionParser(char)
            result = parser.parse_octet()
            assert result is True
            assert parser.at_end()

    def test_parse_octet_empty_string(self):
        """Test parsing octet from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_octet()
        assert result is False
        assert parser.at_end()

    def test_parse_octet_multiple_chars(self):
        """Test parsing octet when it's first of multiple characters"""
        parser = SExpressionParser("abc123")
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
            parser = SExpressionParser(char)
            result = parser.parse_octet()
            assert result is True
            assert parser.index == 1
            assert parser.text_length == len(char.encode("utf-8"))
            assert not parser.at_end()


class TestParseVtabMethod:
    """Tests for parse_vtab method (vertical tab parsing)"""

    def test_parse_vtab_success(self):
        """Test parsing vertical tab character successfully"""
        parser = SExpressionParser("\x0b")
        result = parser.parse_vtab()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_vtab_failure(self, s: str):
        """Test parsing non-vtab character fails"""
        parser = SExpressionParser(s)
        result = parser.parse_vtab()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0

    def test_parse_vtab_empty_string(self):
        """Test parsing vtab from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_vtab()
        assert result is False
        assert parser.at_end()

    def test_parse_vtab_multiple_chars(self):
        """Test parsing vtab when it's first of multiple characters"""
        parser = SExpressionParser("\x0babc")
        result = parser.parse_vtab()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        assert parser.peek() == "a"


class TestParseFfMethod:
    """Tests for parse_ff method (form feed parsing)"""

    def test_parse_ff_success(self):
        """Test parsing form feed character successfully"""
        parser = SExpressionParser("\x0c")
        result = parser.parse_ff()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_ff_failure(self, s: str):
        """Test parsing non-ff character fails"""
        parser = SExpressionParser(s)
        result = parser.parse_ff()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0

    def test_parse_ff_empty_string(self):
        """Test parsing ff from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_ff()
        assert result is False
        assert parser.at_end()

    def test_parse_ff_multiple_chars(self):
        """Test parsing ff when it's first of multiple characters"""
        parser = SExpressionParser("\x0cabc")
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
        parser = SExpressionParser(char)
        result = parser.parse_whitespace()
        assert result is True
        assert parser.at_end()

    @given(sexp_gen.alpha)
    def test_parse_whitespace_failure(self, s: str):
        """Test parsing non-whitespace character fails"""
        parser = SExpressionParser(s)
        result = parser.parse_whitespace()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0

    def test_parse_whitespace_empty_string(self):
        """Test parsing whitespace from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_whitespace()
        assert result is False
        assert parser.at_end()

    def test_parse_whitespace_multiple_chars(self):
        """Test parsing whitespace when it's first of multiple characters"""
        parser = SExpressionParser(" \tabc")
        result = parser.parse_whitespace()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1
        assert parser.peek() == "\t"


class TestParseBase64CharMethod:
    """Tests for parse_base_64_char method (base64 character parsing)"""

    @pytest.mark.parametrize(
        "char",
        list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"),
    )
    def test_parse_base_64_char_success(self, char):
        """Test parsing valid base64 character successfully"""
        parser = SExpressionParser(char)
        result = parser.parse_base_64_char()
        assert result is True
        assert parser.at_end()

    @pytest.mark.parametrize("char", ["=", "-", "_", "*", "!", " "])
    def test_parse_base_64_char_failure(self, char):
        """Test parsing invalid base64 character fails"""
        parser = SExpressionParser(char)
        result = parser.parse_base_64_char()
        assert result is False
        assert not parser.at_end()
        assert parser.index == 0

    def test_parse_base_64_char_empty_string(self):
        """Test parsing base64 char from empty string fails"""
        parser = SExpressionParser("")
        result = parser.parse_base_64_char()
        assert result is False
        assert parser.at_end()

    def test_parse_base_64_char_multiple_chars(self):
        """Test parsing base64 char when it's first of multiple characters"""
        parser = SExpressionParser("Qabc")
        result = parser.parse_base_64_char()
        assert result is True
        assert not parser.at_end()
        assert parser.index == 1


class TestParseBase64CharsMethod:
    """One RFC base-64-chars group contains exactly four characters."""

    @pytest.mark.parametrize(
        "input_str, expected_count",
        [
            ("ABCD", 4),
            ("ABCDWXYZ", 4),
            ("ABCD WXYZ", 4),  # whitespace between groups
            ("A B C D", 4),  # whitespace between chars
            ("ABCD\tWXYZ", 4),  # tab as whitespace
            ("ABCD\nWXYZ", 4),  # newline as whitespace
            ("ABCD", 4),
            ("", 0),
            ("ABCD WXYZ1234", 4),  # leave subsequent groups unread
            ("ABCD WXYZ 1234", 4),
        ],
    )
    def test_parse_base_64_chars_various(self, input_str, expected_count):
        parser = SExpressionParser(input_str)
        count = parser.parse_base_64_chars()
        assert count == expected_count
        # Should consume only the valid base64 chars and whitespace
        # If expected_count == 0, index should be 0
        if expected_count == 0:
            assert parser.index == 0
        else:
            # Consume one group, including following RFC whitespace.
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
            assert parser.index == i

    def test_parse_base_64_chars_with_extra_non_base64(self):
        parser = SExpressionParser("ABCD!WXYZ")
        count = parser.parse_base_64_chars()
        assert count == 4  # Only first group is valid
        assert parser.index == 4  # Stops at '!' (non-base64 char)

    def test_parse_base_64_chars_only_whitespace(self):
        parser = SExpressionParser("    ")
        count = parser.parse_base_64_chars()
        assert count == 0
        assert parser.index == 0

    def test_parse_base_64_chars_partial_group(self):
        s = "ABC"
        parser = SExpressionParser(s)
        with pytest.raises(ValueError) as excinfo:
            parser.parse_base_64_chars()
        assert "Invalid base64 character count" in str(excinfo.value)
        assert parser.index == len(s)

    def test_parse_base_64_chars_multiple_groups_with_whitespace(self):
        parser = SExpressionParser("ABCD \tWXYZ\n1234")
        assert [parser.parse_base_64_chars() for _ in range(3)] == [4, 4, 4]
        assert parser.index == len("ABCD \tWXYZ\n1234")


class TestParseBase64EndMethod:
    """Tests for parse_base_64_end method (base64 end parsing according to RFC 9804)"""

    @pytest.mark.parametrize(
        "input_str, expected_count",
        [
            ("ABCD", 4),  # base-64-chars: full group
            ("ABCDWXYZ", 4),  # leave the second group unread
            ("ABCD WXYZ", 4),
            ("ABCDE", 4),
        ],
    )
    def test_parse_base_64_end_full_group(self, input_str, expected_count):
        parser = SExpressionParser(input_str)
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
        parser = SExpressionParser(input_str)
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
        parser = SExpressionParser(input_str)
        count = parser.parse_base_64_end()
        assert count == expected_count
        assert parser.index >= len(input_str.rstrip())

    def test_parse_base_64_end_with_whitespace(self):
        parser = SExpressionParser("ABCD \t\n")
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
            ("42abc", 42),
            ("9", 9),
            ("", None),
            ("abc", None),
            (" 123", None),
        ],
    )
    def test_parse_decimal_various(self, input_str, expected):
        parser = SExpressionParser(input_str)
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
        parser = SExpressionParser("123abc456")
        result = parser.parse_decimal()
        assert result == 123
        assert parser.index == 3
        assert parser.peek() == "a"

    def test_parse_decimal_empty(self):
        parser = SExpressionParser("")
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
        parser = SExpressionParser(input_str)
        result = parser.parse_base_64()
        assert result == expected
        assert parser.at_end()

    def test_parse_base_64_with_trailing(self):
        parser = SExpressionParser("|YWJj|foo")
        result = parser.parse_base_64()
        assert result == "abc"
        assert parser.index == 6
        assert parser.peek() == "f"

    def test_parse_base_64_invalid_start(self):
        parser = SExpressionParser("YWJj|")
        with pytest.raises(ValueError) as excinfo:
            parser.parse_base_64()
        assert "Missing opening '|'" in str(
            excinfo.value,
        ) or "Missing closing '|'" in str(excinfo.value)
        assert parser.index == 0

    def test_parse_base_64_unterminated(self):
        parser = SExpressionParser("|YWJj")
        with pytest.raises(ValueError) as excinfo:
            parser.parse_base_64()
        assert "Missing closing '|' for base64 at position" in str(excinfo.value)

    def test_parse_base_64_invalid_char(self):
        parser = SExpressionParser("|YWJ!j|")
        with pytest.raises(ValueError) as excinfo:
            parser.parse_base_64()
        assert "Invalid base64 character" in str(excinfo.value)

    def test_parse_base_64_decode_error(self):
        # Invalid base64 padding
        parser = SExpressionParser("|YWJj===")
        with pytest.raises(ValueError) as excinfo:
            parser.parse_base_64()
        assert "Missing closing '|' for base64 at position" in str(excinfo.value)


class TestParseHexadecimalsMethod:
    """One RFC hexadecimals group contains exactly two digits."""

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("abc123", "ab"),
            ("ABCDEF", "AB"),
            ("0123456789abcdef", "01"),
            ("a1b2c3xyz", "a1"),
        ],
    )
    def test_parse_hexadecimals_various(self, input_str, expected):
        parser = SExpressionParser(input_str)
        result = parser.parse_hexadecimals()
        assert result == expected
        assert parser.index == len(expected)

    def test_parse_hexadecimals_empty(self):
        parser = SExpressionParser("")
        with pytest.raises(ValueError) as excinfo:
            parser.parse_hexadecimals()
        assert "Expected HEXDIG at position" in str(excinfo.value)
        assert parser.at_end()

    def test_parse_hexadecimals_partial(self):
        parser = SExpressionParser("deadbeef!")
        result = parser.parse_hexadecimals()
        assert result == "de"
        assert parser.index == 2
        assert parser.peek() == "a"


class TestParseHexadecimalMethod:
    """RFC 9804 section 4.4 encodes octets as pairs of hexadecimal digits."""

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("#1a#", b"\x1a"),
            ("#00#", b"\x00"),
            ("#deadBEEF#", b"\xde\xad\xbe\xef"),
            ("#ABCD#", b"\xab\xcd"),
            ("##", b""),
            ("# 61 62 63 #", b"abc"),
            ("3#616263#", b"abc"),
        ],
    )
    def test_parse_hexadecimal_various(self, input_str, expected):
        parser = SExpressionParser(input_str)
        assert parser.parse_hexadecimal() == expected
        assert parser.at_end()

    @pytest.mark.parametrize("input_str", ["#0#", "#ABC#", "#g123#", "#123xyz#", "#12"])
    def test_parse_hexadecimal_invalid(self, input_str):
        with pytest.raises(ValueError):
            SExpressionParser(input_str).parse_hexadecimal()

    def test_parse_hexadecimal_empty(self):
        parser = SExpressionParser("")
        assert parser.parse_hexadecimal() is None
        assert parser.at_end()

    def test_parse_hexadecimal_partial(self):
        parser = SExpressionParser("#beef#!foo")
        assert parser.parse_hexadecimal() == b"\xbe\xef"
        assert parser.index == 6
        assert parser.peek() == "!"

    def test_parse_hexadecimal_missing_delimiter(self):
        parser = SExpressionParser("beef!foo")
        assert parser.parse_hexadecimal() is None
        assert parser.index == 0


@pytest.mark.parametrize(
    "text, expected",
    [("AB", 2), ("AB=", 2), ("AB==", 2), ("ABC", 3), ("ABC=", 3), ("A B = = ", 2)],
)
def test_base64_end_optional_padding(text, expected):
    parser = SExpressionParser(text)
    assert parser.parse_base_64_end() == expected
    assert parser.at_end()


@pytest.mark.parametrize(
    "text",
    ["", "!", "A", "=", "AB===", "ABC==", "ABCD="],
)
def test_base64_end_invalid_group(text):
    parser = SExpressionParser(text)
    assert parser.parse_base_64_end() == 0
    assert parser.index == 0


@pytest.mark.parametrize("text, expected", [("|/w==|", b"\xff"), ("|Y W J j |", "abc")])
def test_base64_octets_and_internal_whitespace(text, expected):
    assert SExpressionParser(text).parse_base_64() == expected


def test_base64_invalid_padding():
    with pytest.raises(ValueError, match="Invalid base64 encoding"):
        SExpressionParser("|A|").parse_base_64()
