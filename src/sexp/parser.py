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
        # Debug print to understand structure
        # print(f"visit_value: {visited_children}")

        if len(visited_children) == 1:
            child = visited_children[0]
            if isinstance(child, list) and len(child) == 3:
                # It's a nested group like [['(', [['a']], ')']]
                left_paren, content, right_paren = child
                if left_paren == "(" and right_paren == ")":
                    if not content:  # Empty list
                        return []
                    if isinstance(content, list):
                        # Filter out whitespace and flatten
                        result = []
                        for item in content:
                            if isinstance(item, list) and len(item) == 1:
                                # Unwrap single-item lists (result of whitespace filtering)
                                inner = item[0]
                                if isinstance(inner, list) and len(inner) == 1:
                                    # Double wrapped like [[' ']]
                                    if not (
                                        isinstance(inner[0], str) and inner[0].isspace()
                                    ):
                                        result.append(inner[0])
                                elif not (isinstance(inner, str) and inner.isspace()):
                                    result.append(inner)
                            elif not (isinstance(item, str) and item.isspace()):
                                result.append(item)
                        return result
                    else:
                        return (
                            [content]
                            if not (isinstance(content, str) and content.isspace())
                            else []
                        )
            else:
                # It's a simple string
                return child
        elif len(visited_children) == 3:
            # Direct list structure: "(", content, ")"
            left_paren, content, right_paren = visited_children
            if left_paren == "(" and right_paren == ")":
                if not content:  # Empty list
                    return []
                if isinstance(content, list):
                    result = []
                    for item in content:
                        if isinstance(item, list) and len(item) == 1:
                            if not (isinstance(item[0], str) and item[0].isspace()):
                                result.append(item[0])
                        elif not (isinstance(item, str) and item.isspace()):
                            result.append(item)
                    return result
                else:
                    return (
                        [content]
                        if not (isinstance(content, str) and content.isspace())
                        else []
                    )

        # Fallback
        return visited_children

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

    def visit_decimal(self, node, visited_children):
        # decimal = "0" / (~"[1-9]" digit*)
        return node.text

    def visit_verbatim(self, node, visited_children):
        # verbatim = decimal ":" octet*
        # The issue is that octet* greedily consumes everything, but we need exactly length chars
        full_text = node.text
        colon_pos = full_text.find(":")
        if colon_pos == -1:
            raise ValueError(
                f"Invalid verbatim string at position {node.start}: no colon found"
            )

        length_str = full_text[:colon_pos]
        length = int(length_str)

        data_start = colon_pos + 1

        # Take exactly length characters from the data part
        if len(full_text) < data_start + length:
            raise ValueError(
                f"Verbatim string at position {node.start} expects {length} bytes, but got {len(full_text) - data_start}."
            )

        data = full_text[data_start : data_start + length]
        return data

    def visit_quoted_string(self, node, visited_children):
        # The content is everything between the quotes
        # Find the actual string content by extracting from the node text
        full_text = node.text

        # Handle length prefix
        expected_length = None
        if full_text[0].isdigit():
            # Has length prefix: N"content"
            quote_start = full_text.find('"')
            length_str = full_text[:quote_start]
            expected_length = int(length_str)
            content = full_text[quote_start + 1 : -1]
        else:
            # No length prefix: "content"
            content = full_text[1:-1]

        # Handle C-style escape sequences according to RFC 9804
        result = []
        i = 0
        while i < len(content):
            if content[i] == "\\" and i + 1 < len(content):
                next_char = content[i + 1]
                if next_char == "a":
                    result.append("\a")  # bell
                elif next_char == "b":
                    result.append("\b")  # backspace
                elif next_char == "t":
                    result.append("\t")  # tab
                elif next_char == "v":
                    result.append("\v")  # vertical tab
                elif next_char == "n":
                    result.append("\n")  # newline
                elif next_char == "f":
                    result.append("\f")  # form feed
                elif next_char == "r":
                    result.append("\r")  # carriage return
                elif next_char == '"':
                    result.append('"')  # quote
                elif next_char == "'":
                    result.append("'")  # single quote
                elif next_char == "?":
                    result.append("?")  # question mark
                elif next_char == "\\":
                    result.append("\\")  # backslash
                elif next_char == "x" and i + 3 < len(content):
                    # Hex escape \xhh
                    try:
                        hex_val = int(content[i + 2 : i + 4], 16)
                        # Handle byte values that may not be valid UTF-8
                        result.append(chr(hex_val))
                        i += 2  # Skip the hex digits (will be incremented by 2 at end)
                    except (ValueError, OverflowError):
                        # Invalid hex escape, keep as literal
                        result.append("\\")
                        i -= 1  # Back up to process the backslash normally
                elif next_char.isdigit() and i + 3 < len(content):
                    # Octal escape \ooo (exactly 3 digits)
                    octal_str = content[i + 1 : i + 4]
                    if len(octal_str) == 3 and all(c in "01234567" for c in octal_str):
                        try:
                            octal_val = int(octal_str, 8)
                            # C semantics: octal values wrap around at 256
                            byte_val = octal_val % 256
                            result.append(chr(byte_val))
                            i += 2  # Skip the octal digits (will be incremented by 2 at end)
                        except (ValueError, OverflowError):
                            result.append("\\")
                            result.append(next_char)
                            i += 1
                    else:
                        result.append("\\")
                        result.append(next_char)
                        i += 1
                elif next_char == "\r":
                    # Handle \<carriage-return> - ignore the CR
                    if i + 2 < len(content) and content[i + 2] == "\n":
                        # \<CR><LF> - ignore both
                        i += 2
                    else:
                        # Just \<CR> - ignore it
                        i += 1
                elif next_char == "\n":
                    # Handle \<line-feed> - ignore the LF
                    if i + 2 < len(content) and content[i + 2] == "\r":
                        # \<LF><CR> - ignore both
                        i += 2
                    else:
                        # Just \<LF> - ignore it
                        i += 1
                else:
                    # Unknown escape, keep the backslash
                    result.append("\\")
                    i -= 1  # Back up so we process the next char normally
                i += 2
            else:
                result.append(content[i])
                i += 1

        final_result = "".join(result)

        # Check length constraint if specified
        if expected_length is not None:
            actual_length = len(final_result.encode("utf-8"))
            if actual_length != expected_length:
                raise ValueError(
                    f"Quoted string length mismatch: expected {expected_length} bytes, got {actual_length} bytes"
                )

        return final_result

    def visit_hexadecimal(self, node, visited_children):
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

    def visit_base_64(self, node, visited_children):
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

    def visit_boolean(self, node, visited_children):
        text = node.text.strip()
        if text == "#t":
            return True
        elif text == "#f":
            return False
        else:
            raise ValueError(f"Invalid boolean value: {text}")

    def generic_visit(self, node, visited_children):
        # Debug: uncomment to see what's being processed
        # print(f"generic_visit: rule={node.expr_name}, text='{node.text[:20]}...', children={visited_children}")
        return visited_children or node.text


def loads(s: str):
    """Parse a string into a list of S-expressions."""
    s = s.strip()

    def parse_sexp(text, index=0):
        """Parse a single S-expression starting at index, return (result, new_index)"""
        # Skip whitespace
        while index < len(text) and text[index].isspace():
            index += 1

        if index >= len(text):
            raise ValueError(f"Unexpected end of input at position {index}")

        char = text[index]

        if char == "(":
            # Parse list
            index += 1  # skip '('
            items = []
            while True:
                # Skip whitespace
                while index < len(text) and text[index].isspace():
                    index += 1
                if index >= len(text):
                    raise ValueError(f"Unterminated list at position {index}")
                if text[index] == ")":
                    index += 1  # skip ')'
                    break
                item, index = parse_sexp(text, index)
                items.append(item)
            return items, index

        elif char.isdigit():
            # Could be verbatim string or quoted string with length prefix
            # Look ahead to determine which
            colon_pos = text.find(":", index)
            quote_pos = text.find('"', index)

            if colon_pos != -1 and (quote_pos == -1 or colon_pos < quote_pos):
                # Verbatim string: length:data - delegate to grammar for proper handling
                # Find the end of what could be a verbatim string
                try:
                    length = int(text[index:colon_pos])
                    expected_end = colon_pos + 1 + length
                    if expected_end <= len(text):
                        verbatim_part = text[index:expected_end]
                        tree = RFC9804_GRAMMAR["verbatim"].parse(verbatim_part)
                        visitor = SExpressionVisitor(verbatim_part)
                        result = visitor.visit(tree)
                        return result, expected_end
                    else:
                        raise ValueError(
                            f"Verbatim string at position {index} expects {length} bytes, but only {len(text) - colon_pos - 1} available"
                        )
                except Exception:
                    # If verbatim parsing fails, treat as a number token
                    end = index
                    while end < len(text) and text[end].isdigit():
                        end += 1
                    token = text[index:end]
                    return token, end
            elif quote_pos != -1:
                # Quoted string with length prefix: length"content"
                # Delegate to grammar for proper handling
                quote_start = quote_pos
                end_quote = quote_start + 1
                while end_quote < len(text):
                    if text[end_quote] == '"' and (
                        end_quote == quote_start + 1 or text[end_quote - 1] != "\\"
                    ):
                        break
                    end_quote += 1
                if end_quote >= len(text):
                    raise ValueError(
                        f"Unterminated quoted string at position {quote_start}"
                    )

                quoted_part = text[index : end_quote + 1]  # Include length prefix
                try:
                    tree = RFC9804_GRAMMAR["quoted_string"].parse(quoted_part)
                    visitor = SExpressionVisitor(quoted_part)
                    result = visitor.visit(tree)
                    return result, end_quote + 1
                except Exception as e:
                    raise ValueError(
                        f"Failed to parse quoted string at position {index}: {str(e)}"
                    )
            else:
                # Just a number token
                end = index
                while end < len(text) and text[end].isdigit():
                    end += 1
                token = text[index:end]
                return token, end

        elif char == '"':
            # Parse quoted string - delegate to grammar for proper escape handling
            try:
                # Find the end of the quoted string (this is a simplification)
                end_quote = index + 1
                while end_quote < len(text):
                    if text[end_quote] == '"' and text[end_quote - 1] != "\\":
                        break
                    end_quote += 1
                if end_quote >= len(text):
                    raise ValueError(f"Unterminated quoted string at position {index}")

                quoted_part = text[index : end_quote + 1]
                tree = RFC9804_GRAMMAR["quoted_string"].parse(quoted_part)
                visitor = SExpressionVisitor(quoted_part)
                result = visitor.visit(tree)
                return result, end_quote + 1
            except Exception as e:
                raise ValueError(
                    f"Failed to parse quoted string at position {index}: {str(e)}"
                )

        elif char == "#":
            # Parse boolean, hex, or other # prefixed forms
            if index + 1 < len(text) and text[index + 1] in "tf":
                # Boolean
                if text[index : index + 2] == "#t":
                    return True, index + 2
                elif text[index : index + 2] == "#f":
                    return False, index + 2

            # For hex and other formats, find the end of this token first
            end = index + 1
            while end < len(text) and not text[end].isspace() and text[end] not in "()":
                end += 1
            token_part = text[index:end]

            # Try different grammar rules for # tokens
            for rule_name in ["hexadecimal", "base_64"]:
                try:
                    tree = RFC9804_GRAMMAR[rule_name].parse(token_part)
                    visitor = SExpressionVisitor(token_part)
                    result = visitor.visit(tree)
                    return result, end
                except Exception:
                    continue

            # If none of the # rules worked, treat it as a regular token
            return token_part, end

        else:
            # Parse token
            end = index
            while end < len(text) and not text[end].isspace() and text[end] not in "()":
                end += 1
            if end == index:
                raise ValueError(f"Unexpected character '{char}' at position {index}")
            token = text[index:end]
            return token, end

    try:
        results = []
        index = 0
        while index < len(s):
            result, index = parse_sexp(s, index)
            results.append(result)
            # Skip trailing whitespace
            while index < len(s) and s[index].isspace():
                index += 1

        # Return single result if only one, otherwise return list
        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            raise ValueError("No S-expressions found")
        else:
            return results

    except ValueError as e:
        raise ValueError(
            f"Failed to parse S-expression at position 0: {s[:30]}..."
        ) from e


def load(f):
    """Parse a file-like object into an S-expression."""
    return loads(f.read())


def _dumps_canonical(node):
    if isinstance(node, str):
        return f"{len(node.encode('utf-8'))}:{node}"
    elif isinstance(node, bool):
        return "#t" if node else "#f"
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
            # Proper quoting with C-style escapes
            result = ['"']
            for char in node:
                if char == '"':
                    result.append('\\"')
                elif char == "\\":
                    result.append("\\\\")
                elif char == "\a":
                    result.append("\\a")
                elif char == "\b":
                    result.append("\\b")
                elif char == "\t":
                    result.append("\\t")
                elif char == "\v":
                    result.append("\\v")
                elif char == "\n":
                    result.append("\\n")
                elif char == "\f":
                    result.append("\\f")
                elif char == "\r":
                    result.append("\\r")
                elif char == "'":
                    result.append("\\'")
                elif char == "?":
                    result.append("\\?")
                elif ord(char) < 32 or ord(char) > 126:
                    # Non-printable characters as hex escapes
                    result.append(f"\\x{ord(char):02x}")
                else:
                    result.append(char)
            result.append('"')

            # For empty strings, consider using length prefix format
            if not node:
                return '""'

            return "".join(result)
    elif isinstance(node, bool):
        return "#t" if node else "#f"
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


def dumps_roundtrip(original_s, node):
    """
    Serialize an S-expression node to a string, trying to preserve the original format
    when possible for round-tripping.
    """
    if isinstance(node, str):
        # If the original was a quoted string, try to preserve that format
        if original_s.strip().startswith('"') and original_s.strip().endswith('"'):
            return _dumps_advanced(node)
        else:
            return _dumps_canonical(node)
    elif isinstance(node, list):
        return f"({''.join(_dumps_canonical(n) for n in node)})"
    else:
        raise TypeError(
            f"Object of type {type(node).__name__} is not serializable to S-expression"
        )


def dump(node, f, *, advanced: bool = False):
    """Serialize an S-expression node to a file-like object."""
    f.write(dumps(node, advanced=advanced))
