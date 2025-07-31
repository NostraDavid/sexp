"""
Tests for the ABNF rule strategies.
"""

import re
from hypothesis import given
import pytest

from sexp.gen import sexp_gen


# Basic ABNF core rules
@given(sexp_gen.sp)
def test_sp_strategy(s: str):
    """Tests the 'sp' strategy."""
    assert s == " ", "Expected a space character"


@given(sexp_gen.htab)
def test_htab_strategy(s: str):
    """Tests the 'htab' strategy."""
    assert s == "\t", "Expected a horizontal tab character"


@given(sexp_gen.cr)
def test_cr_strategy(s: str):
    """Tests the 'cr' strategy."""
    assert s == "\r", "Expected a carriage return character"


@given(sexp_gen.lf)
def test_lf_strategy(s: str):
    """Tests the 'lf' strategy."""
    assert s == "\n", "Expected a line feed character."


@given(sexp_gen.alpha)
def test_alpha_strategy(s: str):
    """Tests the 'alpha' strategy."""
    assert re.fullmatch(r"[a-zA-Z]", s)


@given(sexp_gen.digit)
def test_digit_strategy(s: str):
    """Tests the 'digit' strategy."""
    assert re.fullmatch(r"[0-9]", s)


@given(sexp_gen.hexdig)
def test_hexdig_strategy(s: str):
    """Tests the 'hexdig' strategy."""
    assert re.fullmatch(r"[0-9a-fA-F]", s)


@given(sexp_gen.dquote)
def test_dquote_strategy(s: str):
    """Tests the 'dquote' strategy."""
    assert s == '"'


@given(sexp_gen.octet)
def test_octet_strategy(b: bytes):
    """Tests the 'octet' strategy."""
    assert isinstance(b, bytes)
    assert len(b) == 1


# S-expression specific basic rules
@given(sexp_gen.vtab)
def test_vtab_strategy(s: str):
    """Tests the 'vtab' strategy."""
    assert s == "\v"


@given(sexp_gen.ff)
def test_ff_strategy(s: str):
    """Tests the 'ff' strategy."""
    assert s == "\f"


@given(sexp_gen.whitespace)
def test_whitespace_strategy(s: str):
    """Tests the 'whitespace' strategy."""
    assert re.fullmatch(r"[\s]", s)
    assert len(s) == 1


@given(sexp_gen.base_64_chars)
def test_base_64_chars_strategy(s: str):
    """Tests the 'base-64-chars' strategy."""
    b64_char_ws = r"[a-zA-Z0-9+/][\s]*"
    b64_chars_re = f"(?:{b64_char_ws}){{4}}"
    assert re.fullmatch(b64_chars_re, s)


@given(sexp_gen.base_64_char)
def test_base_64_char_strategy(s: str):
    """Tests the 'base-64-char' strategy."""
    assert re.fullmatch(r"[a-zA-Z0-9+/]", s)


@given(sexp_gen.base_64_end)
def test_base_64_end_strategy(s: str):
    """Tests the 'base-64-end' strategy."""
    ws = r"[\s]*"
    b64_char_ws = f"[a-zA-Z0-9+/]{ws}"
    # base-64-chars
    part1 = f"(?:{b64_char_ws}){{4}}"
    # 3(base-64-char *whitespace) ["=" *whitespace]
    part2 = f"(?:{b64_char_ws}){{3}}(?:={ws})?"
    # 2(base-64-char *whitespace) *2("=" *whitespace)
    part3 = f"(?:{b64_char_ws}){{2}}(?:={ws}){{0,2}}"
    b64_end_re = f"(?:{part1}|{part2}|{part3})"
    assert re.fullmatch(b64_end_re, s)


@given(sexp_gen.decimal)
def test_decimal_strategy(s: str):
    """Tests the 'decimal' strategy."""
    assert re.fullmatch(r"0|[1-9][0-9]*", s)


@given(sexp_gen.base_64)
def test_base_64_strategy(s: str):
    """Tests the 'base-64' strategy."""
    ws = r"[\s]*"
    b64_char = r"[a-zA-Z0-9+/]"
    b64_char_ws = f"{b64_char}{ws}"
    b64_chars = f"(?:{b64_char_ws}){{4}}"
    # base-64-end parts
    end_part1 = b64_chars
    end_part2 = f"(?:{b64_char_ws}){{3}}(?:={ws})?"
    end_part3 = f"(?:{b64_char_ws}){{2}}(?:={ws}){{0,2}}"
    b64_end = f"(?:{end_part1}|{end_part2}|{end_part3})"
    # Content inside pipes
    content = f"{ws}(?:{b64_chars})*(?:{b64_end})?"
    # Full base-64 regex
    b64_re = f"(?:0|[1-9][0-9]*)?\\|{content}\\|"
    assert re.fullmatch(b64_re, s)


@given(sexp_gen.hexadecimals)
def test_hexadecimals_strategy(s: str):
    """Tests the 'hexadecimals' strategy."""
    ws = r"[\s]*"
    hexdig_ws = f"[0-9a-fA-F]{ws}"
    hexadecimals_re = f"{hexdig_ws}[0-9a-fA-F]"
    assert re.fullmatch(hexadecimals_re, s, re.IGNORECASE)


@given(sexp_gen.hexadecimal)
def test_hexadecimal_strategy(s: str):
    """Tests the 'hexadecimal' strategy."""
    ws = r"[\s]*"
    hexdig_ws = f"[0-9a-fA-F]{ws}"
    hexadecimals = f"({hexdig_ws}{hexdig_ws})*"
    hex_re = f"(0|[1-9][0-9]*)?#{ws}{hexadecimals}#{ws}"
    assert re.fullmatch(hex_re, s, re.IGNORECASE)


@given(sexp_gen.simple_punc)
def test_simple_punc_strategy(s: str):
    """Tests the 'simple_punc' strategy."""
    assert re.fullmatch(r"[-./_:*+=]", s)


@given(sexp_gen.token)
def test_token_strategy(s: str):
    """Tests the 'token' strategy."""
    assert re.fullmatch(r"[a-zA-Z-./_:*+=][a-zA-Z0-9-./_:*+=]*", s)


@given(sexp_gen.quote)
def test_quote_strategy(s: str):
    """Tests the 'quote' strategy."""
    assert s == "'"


@given(sexp_gen.backslash)
def test_backslash_strategy(s: str):
    """Tests the 'backslash' strategy."""
    assert s == "\\"


@given(sexp_gen.escaped)
def test_escaped_strategy(s: str):
    """Tests the 'escaped' strategy."""
    escaped_re = r"""
    \\(?:
        [?abfnrtv"'\\] |          # Simple escapes
        [0-7]{3} |                # Octal escape
        x[0-9a-fA-F]{2} |         # Hex escape
        \r\n? |                   # Carriage return
        \n\r?                     # Line feed
    )
    """
    assert re.fullmatch(escaped_re, s, re.VERBOSE)


@given(sexp_gen.printable)
def test_printable_strategy(s: str):
    """Tests the 'printable' strategy."""
    assert re.fullmatch(r"[\x20-\x21\x23-\x5B\x5D-\x7E]", s)


@given(sexp_gen.quoted_string)
def test_quoted_string_strategy(s: str):
    """Tests the 'quoted_string' strategy."""
    printable_char = r"[\x20-\x21\x23-\x5B\x5D-\x7E]"
    escaped_char = r"""\\(?:[?abfnrtv"'\\]|[0-7]{3}|x[0-9a-fA-F]{2}|\r\n?|\n\r?)"""
    quoted_re = f'(0|[1-9][0-9]*)?"(?:{printable_char}|{escaped_char})*"'
    assert re.fullmatch(quoted_re, s)


@given(sexp_gen.verbatim)
def test_verbatim_strategy(s: str):
    """Tests the 'verbatim' strategy."""
    match = re.match(r"([0-9]+):", s)
    assert match
    length_str = match.group(1)
    length = int(length_str)
    header = f"{length_str}:"
    content = s[len(header) :]
    assert len(content.encode("utf-8")) == length


@given(sexp_gen.simple_string)
def test_simple_string_strategy(s: str):
    """Tests the 'simple_string' strategy."""
    assert isinstance(s, str)


@given(sexp_gen.display)
def test_display_strategy(s: str):
    """Tests the 'display' strategy."""
    assert s.startswith("[") and s.strip().endswith("]")


@given(sexp_gen.string)
def test_string_strategy(s: str):
    """Tests the 'string' strategy."""
    assert isinstance(s, str)


@given(sexp_gen.value)
def test_value_strategy(s: str):
    """Tests the 'value' strategy."""
    assert isinstance(s, str)


@given(sexp_gen.sexp)
def test_sexp_strategy(s: str):
    """Tests the 'sexp' strategy."""
    assert isinstance(s, str)


def check_balanced_parentheses(s: str):
    """
    Checks if the parentheses in a string are balanced, ignoring those inside
    quoted strings.
    """
    balance = 0
    i = 0
    while i < len(s):
        char = s[i]

        # Handle verbatim strings
        if char.isdigit():
            s_match = s[i:]
            match = re.match(r"([0-9]+):", s_match)
            if match:
                length_str = match.group(1)
                length = int(length_str)
                header_len = len(length_str) + 1
                i += header_len + length
                continue

        # Handle quoted strings
        if char == '"':
            i += 1
            while i < len(s):
                if s[i] == "\\":
                    i += 2
                    continue
                if s[i] == '"':
                    break
                i += 1
            i += 1
            continue

        # Handle parentheses
        if char == "(":
            balance += 1
        elif char == ")":
            balance -= 1

        if balance < 0:
            return False

        i += 1

    return balance == 0


@pytest.mark.parametrize(
    "input_string, expected",
    [
        # Balanced cases
        ("", True),
        ("()", True),
        ("(abc)", True),
        ("(a(b)c)", True),
        ("()()", True),
        ("text without parens", True),
        ("(1:2)", True),
        ("(0:)", True),
        # verbatims are like quoted strings
        ("1:(", True),
        ("1:)", True),
        ("3:(()", True),
        ("3:())", True),
        ("2:)(", True),
        # Unbalanced cases
        ("(", False),
        (")", False),
        ("(()", False),
        ("())", False),
        (")(", False),
        # Parentheses inside quotes (should be ignored)
        ('"()"', True),
        ('a(b"c()d")e', True),
        # Escaped quotes
        (r'a(b"c\"d()")e', True),
        (r'("a\"b(c)")', True),
        # Mixed content
        ('a(b)c"d(e"f(g)h', True),
        # Unbalanced outside quotes
        ('a(b"c)d"', False),
        # Unclosed quote - the logic should handle this correctly
        ('a(b"c', False),  # `(` is unbalanced, `"` starts quote, rest is ignored
        ('a(b"c)', False),  # `(` is balanced, `)` is inside unclosed quote
        ('a)b"c(', False),  # `)` is encountered before `(`, unbalanced
        ("(:2:)", False),  # Unbalanced parentheses with verbatim
        ("(:10:)", False),  # Unbalanced parentheses with verbatim
        ("(:10:())", False),  # Unbalanced parentheses with verbatim
        ("(:10:())(:5:)", False),  # Multiple unbalanced verbatim sections
    ],
)
def test_check_balanced_parentheses(input_string: str, expected: bool):
    """Tests the 'check_balanced_parentheses' helper function."""
    assert check_balanced_parentheses(input_string) == expected
