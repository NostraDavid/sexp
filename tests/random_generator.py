import base64
import re
from hypothesis import strategies as st

# Character sets from the grammar
SP = st.just(" ")
HTAB = st.just("\t")
VTAB = st.just("\x0b")
CR = st.just("\r")
LF = st.just("\n")
FF = st.just("\x0c")

WHITESPACE_CHAR = st.one_of(SP, HTAB, VTAB, CR, LF, FF)
WHITESPACE = st.text(WHITESPACE_CHAR, min_size=0, max_size=5)

DIGIT = st.characters(min_codepoint=ord("0"), max_codepoint=ord("9"))
ALPHA = st.characters(min_codepoint=ord("a"), max_codepoint=ord("z")) | st.characters(
    min_codepoint=ord("A"), max_codepoint=ord("Z")
)
HEXDIG = st.sampled_from("0123456789abcdefABCDEF")

SIMPLE_PUNC = st.sampled_from("-./_:*+=")
TOKEN_START_CHAR = ALPHA | SIMPLE_PUNC
TOKEN_BODY_CHAR = ALPHA | DIGIT | SIMPLE_PUNC

# --- Atom Strategies ---


@st.composite
def tokens(draw):
    """Strategy for tokens."""
    start = draw(TOKEN_START_CHAR)
    body = draw(st.text(TOKEN_BODY_CHAR, min_size=0, max_size=10))
    return start + body


@st.composite
def verbatim_strings(draw):
    """Strategy for verbatim strings, e.g., '5:hello'."""
    data = draw(st.binary(max_size=20))
    # The parser expects UTF-8, but verbatim can be any octet.
    # We'll generate valid UTF-8 here for compatibility with Python strings.
    # For raw bytes, a different handling would be needed.
    try:
        text_content = data.decode("utf-8")
    except UnicodeDecodeError:
        # Fallback for invalid utf-8 sequences if needed, but we'll generate valid ones.
        text_content = data.decode("latin-1")
    return f"{len(data)}:{text_content}"


@st.composite
def quoted_strings(draw):
    """Strategy for quoted strings, e.g., '"hello\\nworld"'."""
    # Printable characters excluding " and \
    printable = st.characters(
        min_codepoint=0x20, max_codepoint=0x7E, blacklist_characters='"\\'
    )
    # Simple escape sequences
    escaped_char = st.sampled_from(['\\"', "\\\\", "\\n", "\\t", "\\r"])
    content_list = draw(st.lists(st.one_of(printable, escaped_char), max_size=20))
    content = "".join(content_list)
    return f'"{content}"'


@st.composite
def hex_strings(draw):
    """Strategy for hex strings, e.g., '#68656c6c6f#'."""
    data = draw(st.binary(max_size=10))
    hex_content = data.hex()
    return f"#{hex_content}#"


@st.composite
def base64_strings(draw):
    """Strategy for base64 strings, e.g., '|aGVsbG8=|'."""
    data = draw(st.binary(max_size=15))
    b64_content = base64.b64encode(data).decode("ascii")
    # The RFC allows whitespace, but the current parser is strict.
    return f"|{b64_content}|"


# --- Composite Strategies ---

# A simple-string is one of the atomic types.
simple_string = st.one_of(
    tokens(),
    verbatim_strings(),
    quoted_strings(),
    hex_strings(),
    base64_strings(),
)

# The main recursive strategy for a single S-expression value.
# We use st.deferred() to allow recursion.
value = st.deferred(lambda: st.one_of(simple_string, lists()))


@st.composite
def lists(draw):
    """Strategy for lists, e.g., '(a (b c) "d")'."""
    # Generate a list of values, interspersed with optional whitespace.
    list_items = draw(st.lists(st.tuples(value, WHITESPACE), max_size=4))
    # Join the items together.
    content = "".join([item + ws for item, ws in list_items])
    return f"({content})"


@st.composite
def sexp(draw):
    """Top-level strategy for a complete S-expression."""
    ws_before = draw(WHITESPACE)
    ws_after = draw(WHITESPACE)
    s_expression_value = draw(value)
    return f"{ws_before}{s_expression_value}{ws_after}"


# Example of how to use the strategy with Hypothesis
# You would typically use this inside a @given decorator in a pytest test.
if __name__ == "__main__":
    output_filename = "data/random_sexp.lisp"
    num_examples = 20
    with open(output_filename, "w", encoding="utf-8") as f:
        print(f"Generating {num_examples} random S-expressions to {output_filename}...")
        for _ in range(num_examples):
            example = sexp().example()
            f.write(example)
            f.write("\n")  # Add a newline for better readability
    print("Done.")
