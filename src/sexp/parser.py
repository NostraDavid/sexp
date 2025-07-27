import base64
import binascii
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from parsimonious.exceptions import ParseError
from pathlib import Path

_abnf_path = Path(__file__).parent / "rfc9804.peg"
with open(_abnf_path, "r", encoding="utf-8") as f:
    _abnf_content = f.read()

# Parsimonious doesn't support ABNF comments (starting with ';').
# We filter them out.
_abnf_lines = [
    line for line in _abnf_content.splitlines() if not line.strip().startswith(";")
]
_processed_abnf = "\n".join(_abnf_lines)


RFC9804_GRAMMAR = Grammar(_processed_abnf)


class SExpressionVisitor(NodeVisitor):
    """
    Transforms the parsimonious parse tree into Python objects.
    This visitor handles the "advanced transport" representation.
    """

    def __init__(self, text):
        self.text = text
        self.index = 0

    def visit_sexp(self, node, visited_children):
        _, value, _ = visited_children
        return value

    def visit_value(self, node, visited_children):
        return visited_children[0]

    def visit_list(self, node, visited_children):
        _, children, _ = visited_children
        # Filter out whitespace nodes
        return [
            child
            for child in children
            if not isinstance(child, str) or not child.isspace()
        ]

    def visit_string(self, node, visited_children):
        # Ignores display hints for now as per project spec (string | list)
        _display, simple_string = visited_children
        return simple_string

    def visit_simple_string(self, node, visited_children):
        return visited_children[0]

    def visit_token(self, node, visited_children):
        return node.text

    def visit_verbatim(self, node, visited_children):
        length_str, _ = visited_children
        length = int(length_str)
        # Manually consume from original text
        start = node.end
        end = start + length
        if end > len(self.text):
            raise ValueError(
                f"Verbatim string at position {node.start} expects {length} bytes, but not enough data remains."
            )
        data = self.text[start:end]
        # This is a bit of a hack to tell the top-level parser how much we consumed
        self.index = end
        return data

    def visit_quoted_string(self, node, visited_children):
        # Using `codecs.escape_decode` is a robust way to handle C-style escapes
        return binascii.unhexlify(
            node.text[1:-1]
            .encode("utf-8")
            .decode("unicode_escape")
            .encode("latin1")
            .hex()
        ).decode("utf-8")

    def visit_hex_str(self, node, visited_children):
        content = node.text.strip()
        if content.startswith("#"):  # No length prefix
            hex_data = content[1:-1]
        else:  # Length prefix
            hex_data = content[content.find("#") + 1 : -1]

        hex_data = "".join(hex_data.split())  # remove whitespace
        if len(hex_data) % 2 != 0:
            raise ValueError(
                f"Invalid hex string at {node.start}: odd number of hex digits."
            )
        return binascii.unhexlify(hex_data).decode("utf-8", errors="replace")

    def visit_base64_str(self, node, visited_children):
        content = node.text.strip()
        if content.startswith("|"):  # No length prefix
            b64_data = content[1:-1]
        else:
            b64_data = content[content.find("|") + 1 : -1]

        b64_data = "".join(b64_data.split())  # remove whitespace
        # Add padding if missing
        missing_padding = len(b64_data) % 4
        if missing_padding:
            b64_data += "=" * (4 - missing_padding)
        return base64.b64decode(b64_data).decode("utf-8", errors="replace")

    def generic_visit(self, node, visited_children):
        return visited_children or node.text


def loads(s: str):
    """Parse a string into a list of S-expressions."""
    results = []
    index = 0
    s = s.strip()
    while index < len(s):
        try:
            # We can't use the grammar directly for verbatim strings, so we check first.
            is_verbatim = False
            if s[index].isdigit():
                colon_pos = s.find(":", index)
                if colon_pos > index:
                    try:
                        length = int(s[index:colon_pos])
                        is_verbatim = True
                        data_start = colon_pos + 1
                        data_end = data_start + length
                        results.append(s[data_start:data_end])
                        index = data_end
                        # Skip trailing whitespace for next iteration
                        while index < len(s) and s[index].isspace():
                            index += 1
                        continue
                    except (ValueError, IndexError):
                        is_verbatim = False  # Not a valid verbatim string start

            tree = RFC9804_GRAMMAR.parse(s[index:])
            visitor = SExpressionVisitor(s)
            result = visitor.visit(tree)
            results.append(result)
            # The visitor might have advanced the index for verbatim strings
            index += tree.end
            # Skip trailing whitespace for next iteration
            while index < len(s) and s[index].isspace():
                index += 1

        except ParseError as e:
            raise ValueError(
                f"Failed to parse S-expression at position {index + e.pos}: {e.text[e.pos : e.pos + 30]}..."
            ) from e
    return results[0] if len(results) == 1 else results


def load(f):
    """Parse a file-like object into an S-expression."""
    return loads(f.read())


def _dumps_canonical(node):
    if isinstance(node, str):
        return f"{len(node.encode('utf-8'))}:{node}"
    elif isinstance(node, list):
        return f"({''.join(_dumps_canonical(n) for n in node)})"
    else:
        raise TypeError(
            f"Object of type {type(node).__name__} is not serializable to S-expression"
        )


def _dumps_advanced(node):
    if isinstance(node, str):
        # Simple heuristic: if it's a valid token, print as token, otherwise as quoted string.
        try:
            RFC9804_GRAMMAR["token"].parse(node)
            return node
        except ParseError:
            # Simple quoting, does not handle all escapes but is reasonable.
            return '"' + node.replace("\\", "\\\\").replace('"', '\\"') + '"'
    elif isinstance(node, list):
        return f"({' '.join(_dumps_advanced(n) for n in node)})"
    else:
        raise TypeError(
            f"Object of type {type(node).__name__} is not serializable to S-expression"
        )


def dumps(node, *, advanced: bool = False):
    """Serialize an S-expression node to a string."""
    if advanced:
        return _dumps_advanced(node)
    return _dumps_canonical(node)


def dump(node, f, *, advanced: bool = False):
    """Serialize an S-expression node to a file-like object."""
    f.write(dumps(node, advanced=advanced))
