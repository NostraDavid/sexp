# Symbolic expressions

Parse RFC 9804 (SPKI) S-expressions with `SExpressionParser`, and generate valid
inputs with the Hypothesis-based `SExpressionGenerator`.

```python
from sexp import DisplayString, SExpressionParser

expression = SExpressionParser('(message 6:héllo [text/plain]"world")').parse()
assert expression == [
    b"message",
    "héllo".encode("utf-8"),
    DisplayString(data=b"world", display_hint=b"text/plain"),
]
assert expression[1].decode("utf-8") == "héllo"
```

## Supported representations

- **Canonical:** byte-counted verbatim strings, lists and display-hints,
  e.g. `(6:issuer3:bob)`.
- **Basic transport:** canonical expressions, optionally base64-encoded inside
  `{...}`. The decoded expression must itself be canonical.
- **Advanced transport:** tokens, quoted strings with C escapes and line
  continuations, hex and base64 strings, nested lists and display-hints.

Canonical and basic transport are the mandatory RFC 9804 baseline; advanced
transport is also supported. The [conformance matrix](docs/RFC9804/conformance.md)
maps the specification to executable tests and documents interpretation choices.

Atoms are always `bytes`; lists are Python lists. Explicit display-hints are
preserved as `DisplayString(data, display_hint)`, including empty hints. Strings
without hints remain plain bytes. No numeric or boolean coercion is performed.
This is the RFC 9804 syntax, not a Lisp reader: Lisp comments, quote shorthand
and dotted-pair semantics are not supported.

### UTF-8 and binary data

Input may be `str` (encoded as UTF-8) or `bytes` (arbitrary binary data). Lengths
and cursor offsets count **bytes**, not Unicode characters. All length prefixes
are checked, and leading zeroes are rejected. Quoted strings and tokens follow
the RFC's ASCII grammar: use verbatim strings, byte escapes, hex or base64 for
non-ASCII text.

```python
assert SExpressionParser("6:héllo").parse() == "héllo".encode("utf-8")
assert SExpressionParser(r'"h\xC3\xA9llo"').parse() == "héllo".encode("utf-8")
assert SExpressionParser(b"3:\x00\xff)").parse() == b"\x00\xff)"
```

`parse()` / `parse_sexp()` require exactly one complete expression; malformed,
truncated or trailing input raises `ValueError`. `parse_canonical()` also rejects
advanced syntax and structural whitespace. `parse_value()` reads one advanced
value at the current cursor, leaving subsequent input unread. Lists use an
explicit stack rather than Python recursion; input and results are held in memory.

### Migration

`SexpParser` remains an alias for `SExpressionParser`. Existing primitive methods
remain available. The legacy `parse_base_64()` method still returns UTF-8 `str`
when decodable, otherwise `bytes`; full-expression methods always use byte atoms.
Decimal parsing now rejects leading zeroes, and cursor offsets are byte-based.
The ABNF group helpers now read one group: `parse_base_64_chars()` and
`parse_base_64_end()` read at most four base64 characters, and
`parse_hexadecimals()` reads exactly two hex digits. Repeat calls for more groups.

## Generating test inputs

Install the optional generator dependencies with `pip install 'sexp[generator]'`.
The development environment already includes them.

```python
from hypothesis import given
from sexp import SExpressionParser
from sexp.gen import SExpressionGenerator

generator = SExpressionGenerator()


@given(generator.sexp)
def test_parse_generated_expression(source):
    SExpressionParser(source).parse()
```

The existing grammar strategies, including `sexp`, produce strings;
`canonical` and `basic_transport` produce bytes and cover arbitrary binary atoms.
Generated length prefixes match decoded byte lengths, token boundaries are
separated, and recursive list generation is bounded.
These are test-input strategies, not serializers: whitespace-bearing base64 and
optionally padded grammar fragments intentionally exercise legal decoder inputs.

## Development

Install devenv and direnv, then run:

```bash
direnv allow
just sync
just check
```

The shell supplies Python 3.14 and uv. `just check` runs lint, format and type
checks, the parser and generator tests with coverage, and package builds.
`just update` refreshes Python and Nix locks. `just --list` lists all tasks.

The package exposes a Python API, without a console entry point.

## Performance

On Linux, run `just benchmark-scaling` for serial, bounded measurements of different
expression shapes from 1 KiB to 64 MiB. The JSON output contains raw timings and
environment/source metadata. Each case runs in a fresh subprocess; slow or
resource-limited cases stop further growth of that scenario.

See [measured performance](docs/performance.md) for the results and methodology.
Encoded input bytes alone do not determine cost: a large verbatim atom is very
different from the same number of bytes in tiny atoms or deeply nested lists.

## Reference

The specification and grammar are stored in `docs/RFC9804/`. Example input is in
`data/`. The project uses the MIT license in `LICENSE`.
