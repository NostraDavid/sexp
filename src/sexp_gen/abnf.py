from hypothesis import strategies as st

# Basic ABNF core rules
sp = st.just(" ")
htab = st.just("\t")
cr = st.just("\r")
lf = st.just("\n")
alpha = st.one_of(
    st.characters(min_codepoint=ord("A"), max_codepoint=ord("Z")),
    st.characters(min_codepoint=ord("a"), max_codepoint=ord("z")),
)
digit = st.characters(min_codepoint=ord("0"), max_codepoint=ord("9"))
hexdig = st.one_of(
    digit,
    st.characters(min_codepoint=ord("A"), max_codepoint=ord("F")),
    st.characters(min_codepoint=ord("a"), max_codepoint=ord("f")),
)
dquote = st.just('"')
octet = st.binary(min_size=1, max_size=1)

# S-expression specific basic rules
vtab = st.just("\x0b")
ff = st.just("\x0c")
whitespace = st.one_of(sp, htab, vtab, cr, lf, ff)

# Character sets for specific uses
base_64_char = st.one_of(alpha, digit, st.just("+"), st.just("/"))


# Base64 strings
@st.composite
def _base_64_chars(draw):
    chars = []
    for _ in range(4):
        char = draw(base_64_char)
        ws = draw(st.lists(whitespace, max_size=3))
        chars.append(char + "".join(ws))
    return "".join(chars)


base_64_chars = _base_64_chars()


@st.composite
def _base_64_end(draw):
    choice = draw(st.integers(min_value=0, max_value=2))
    if choice == 0:
        # base-64-chars (4 chars)
        chars = []
        for _ in range(4):
            char = draw(base_64_char)
            ws = draw(st.lists(whitespace, max_size=3))
            chars.append(char + "".join(ws))
        return "".join(chars)
    elif choice == 1:
        # 3 chars + optional "="
        chars = []
        for _ in range(3):
            char = draw(base_64_char)
            ws = draw(st.lists(whitespace, max_size=3))
            chars.append(char + "".join(ws))
        eq_choice = draw(st.booleans())
        if eq_choice:
            ws = draw(st.lists(whitespace, max_size=3))
            return "".join(chars) + "=" + "".join(ws)
        return "".join(chars)
    else:
        # 2 chars + up to 2 "="
        chars = []
        for _ in range(2):
            char = draw(base_64_char)
            ws = draw(st.lists(whitespace, max_size=3))
            chars.append(char + "".join(ws))
        eq_count = draw(st.integers(min_value=0, max_value=2))
        eq_parts = []
        for _ in range(eq_count):
            ws = draw(st.lists(whitespace, max_size=3))
            eq_parts.append("=" + "".join(ws))
        return "".join(chars) + "".join(eq_parts)


base_64_end = _base_64_end()


# Decimal numbers
@st.composite
def _decimal(draw):
    is_zero = draw(st.booleans())
    if is_zero:
        return "0"
    else:
        # Non-zero number: first digit 1-9, then 0-9 digits
        first = draw(st.characters(min_codepoint=ord("1"), max_codepoint=ord("9")))
        rest = draw(st.lists(digit, max_size=10))
        return first + "".join(rest)


decimal = _decimal()


@st.composite
def _base_64(draw):
    # Optional decimal prefix
    has_decimal = draw(st.booleans())
    dec = draw(decimal) if has_decimal else ""

    # Opening whitespace after |
    ws1 = draw(st.lists(whitespace, max_size=5))

    # Base64 character sequences
    chars = draw(st.lists(base_64_chars, max_size=10))

    # Optional base64 end sequence
    has_end = draw(st.booleans())
    end = draw(base_64_end) if has_end else ""

    # Closing whitespace before |
    ws2 = draw(st.lists(whitespace, max_size=5))

    return dec + "|" + "".join(ws1) + "".join(chars) + end + "".join(ws2) + "|"


base_64 = _base_64()


# Hexadecimal strings
@st.composite
def _hexadecimals(draw):
    hex1 = draw(hexdig)
    ws = draw(st.lists(whitespace, max_size=3))
    hex2 = draw(hexdig)
    return hex1 + "".join(ws) + hex2


hexadecimals = _hexadecimals()


@st.composite
def _hexadecimal(draw):
    # Optional decimal prefix
    has_decimal = draw(st.booleans())
    dec = draw(decimal) if has_decimal else ""

    # Opening whitespace after #
    ws1 = draw(st.lists(whitespace, max_size=5))

    # Hexadecimal digit pairs
    hexs = draw(st.lists(hexadecimals, max_size=10))

    # Closing whitespace before #
    ws2 = draw(st.lists(whitespace, max_size=5))

    return dec + "#" + "".join(ws1) + "".join(hexs) + "".join(ws2) + "#"


hexadecimal = _hexadecimal()

simple_punc = st.one_of(
    st.just("-"),
    st.just("."),
    st.just("/"),
    st.just("_"),
    st.just(":"),
    st.just("*"),
    st.just("+"),
    st.just("="),
)


@st.composite
def _token(draw):
    # First character: alpha or simple punctuation
    first = draw(st.one_of(alpha, simple_punc))

    # Rest of the characters: alpha, digit, or simple punctuation
    rest = draw(st.lists(st.one_of(alpha, digit, simple_punc), max_size=20))

    return first + "".join(rest)


token = _token()
quote = st.just("'")
backslash = st.just("\\")


# Escaped sequences
@st.composite
def _escaped(draw):
    zero_to_seven = st.characters(min_codepoint=ord("0"), max_codepoint=ord("7"))
    bs = draw(backslash)

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
        char = draw(st.one_of(dquote, quote, backslash))
    elif escape_type == 9:
        # Octal escape: three octal digits
        d1 = draw(zero_to_seven)
        d2 = draw(zero_to_seven)
        d3 = draw(zero_to_seven)
        char = d1 + d2 + d3
    elif escape_type == 10:
        # Hex escape: \x followed by two hex digits
        h1 = draw(hexdig)
        h2 = draw(hexdig)
        char = "\x78" + h1 + h2
    elif escape_type == 11:
        char = draw(cr)
    elif escape_type == 12:
        char = draw(lf)
    else:
        # Line ending combinations: CR+LF or LF+CR
        line_choice = draw(st.booleans())
        if line_choice:
            char = draw(cr) + draw(lf)
        else:
            char = draw(lf) + draw(cr)

    return bs + char


escaped = _escaped()

# Printable characters for quoted strings (excludes " and \)
printable = st.one_of(
    st.characters(min_codepoint=0x20, max_codepoint=0x21),  # space, !
    st.characters(min_codepoint=0x23, max_codepoint=0x5B),  # # to [
    st.characters(min_codepoint=0x5D, max_codepoint=0x7E),  # ] to ~
)


@st.composite
def _quoted_string(draw):
    # Optional decimal prefix
    has_decimal = draw(st.booleans())
    dec = draw(decimal) if has_decimal else ""

    # Content: mix of printable and escaped characters
    content = draw(st.lists(st.one_of(printable, escaped), max_size=50))

    return dec + '"' + "".join(content) + '"'


quoted_string = _quoted_string()


# String types
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


verbatim = _verbatim()


simple_string = st.one_of(verbatim, quoted_string, token, hexadecimal, base_64)


@st.composite
def _display(draw):
    ws1 = draw(st.lists(whitespace, max_size=5))
    simple_str = draw(simple_string)
    ws2 = draw(st.lists(whitespace, max_size=5))
    ws3 = draw(st.lists(whitespace, max_size=5))
    return "[" + "".join(ws1) + simple_str + "".join(ws2) + "]" + "".join(ws3)


display = _display()


@st.composite
def _string(draw):
    has_display = draw(st.booleans())
    if has_display:
        disp = draw(display)
        simple_str = draw(simple_string)
        return disp + simple_str
    else:
        return draw(simple_string)


string = _string()


# Recursive S-expression structures
@st.composite
def _value(draw):
    choice = draw(st.booleans())
    if choice:
        # Generate a string
        return draw(string)
    else:
        # Generate a list: "(" *whitespace *(value / whitespace) *whitespace ")"
        ws1 = draw(st.lists(whitespace, max_size=5))

        # Generate list contents (mix of values and whitespace)
        contents = []
        num_items = draw(st.integers(min_value=0, max_value=10))
        for _ in range(num_items):
            item_choice = draw(st.booleans())
            if item_choice:
                # Add a value (recursive)
                contents.append(draw(st.deferred(lambda: _value())))
            else:
                # Add whitespace
                ws = draw(st.lists(whitespace, min_size=1, max_size=5))
                contents.append("".join(ws))

        ws2 = draw(st.lists(whitespace, max_size=5))
        return "(" + "".join(ws1) + "".join(contents) + "".join(ws2) + ")"


value = _value()


@st.composite
def _sexp(draw):
    ws1 = draw(st.lists(whitespace, max_size=5))
    val = draw(value)
    ws2 = draw(st.lists(whitespace, max_size=5))
    return "".join(ws1) + val + "".join(ws2)


sexp = _sexp()
