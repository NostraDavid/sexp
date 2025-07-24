# S-Expression Parser (RFC 9804) - AI Coding Guide

## Project Overview

This is a Python implementation of RFC 9804 SPKI S-Expressions parser. The project focuses on parsing S-expressions with support for multiple data formats: verbatim strings (`3:abc`), quoted strings (`"abc"`), hex strings (`#616263#`), base64 strings (`|YWJj|`), tokens, booleans (`#t`/`#f`), and nested lists.

## Architecture & Core Components

### Parser Design (`src/sexp/parser.py`)

- **`SExpressionParser`**: Stateful parser with index-based character consumption
- **Type System**: `SExpression = str | list["SExpression"]` - recursive union type
- **Key Methods**: `_parse_sexpr()` (main dispatcher), `_parse_list()`, `_parse_atom()` with specialized parsers for each format
- **Error Handling**: Position-aware error messages with context

### Entry Point (`src/sexp/__init__.py`)

- **CLI Interface**: Simple argparse-based tool accessible via `uv run sexp <file>`
- **Batch Processing**: Parses multiple S-expressions from a single file using parser state continuation
- **Output Format**: Direct Python object representation (lists/strings)

## Development Workflow

### Environment Setup

```bash
# Primary development environment (uses Nix + uv)
nix develop .#uv2nix

# Alternative: Direct uv usage
uv run sexp data/input1.lisp
```

### Testing Strategy

- **Parametrized Tests**: Heavy use of `@pytest.mark.parametrize` in `tests/test_parser.py`
- **Mocking Pattern**: `pytest-mock` for file I/O and parser isolation in `tests/test_init.py`
- **Test Data**: `data/input*.lisp` files contain RFC-compliant examples
- **Coverage**: Run `uv run pytest` for comprehensive test suite

### Package Management

- **uv-based**: Dependencies managed via `pyproject.toml` with uv.lock
- **No External Runtime Deps**: Pure Python stdlib implementation
- **Dev Dependencies**: pytest, coverage, ruff, hypothesis for property testing

## Code Patterns & Conventions

### Parsing Architecture

- **Character Consumption**: Use `_consume()` and `_consume_while()` for safe index advancement
- **Lookahead**: `_peek()` and `_peek_ahead()` for non-destructive inspection
- **Whitespace/Comments**: `_skip_whitespace()` handles both whitespace and `;` comments
- **Format Detection**: Character-based dispatch in `_parse_atom()` (`"` → quoted, `#` → hex/boolean, `|` → base64, digit → verbatim/number)

### Error Handling Pattern

```python
raise ValueError(f"Error description at position {self.index}: context")
```

Always include parser position and relevant context for debugging.

### Testing Patterns

```python
@pytest.mark.parametrize("input_text, expected", [
    ("()", []),
    ("(foo)", ["foo"]),
])
def test_parse_list(input_text: str, expected: list):
    parser = SExpressionParser(input_text)
    assert parser.parse() == expected
```

## Integration Points

### RFC 9804 Compliance

- **Canonical Form**: Supports all RFC-specified formats
- **Transport Representations**: Focus on textual representation parsing
- **Documentation**: `docs/rfc9804.{txt,html,xml}` contains the full specification

### CLI Integration

- **Script Entry**: `[project.scripts] sexp = "sexp:main"` in pyproject.toml
- **File Processing**: Designed for batch processing of `.lisp` files
- **Error Reporting**: User-friendly error messages with file context

## Common Issues & Debugging

### Parser State Management

- **Index Tracking**: Always verify `self.index` progression in parser methods
- **EOF Handling**: Check `self.index < len(self.text)` before character access
- **Error Position**: Include `self.index` in error messages for precise debugging

### Data Format Edge Cases

- **Empty Hex Strings**: `##` is valid and returns empty string
- **Unicode Handling**: Fallback to raw bytes if UTF-8 decoding fails
- **Verbatim Length**: Strict validation of `length:content` format

When working on this codebase, focus on maintaining the stateful parser pattern and comprehensive error reporting. The project prioritizes RFC compliance and robust error handling over performance optimization.
