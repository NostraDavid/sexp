# Symbolic expressions

This project develops parsing primitives and Hypothesis generators for
RFC 9804 S-expressions. `SexpParser` currently handles character classes, decimal
numbers, base64 strings and hexadecimal strings. The full expression parser is
still in progress.

```python
from sexp import SexpParser

assert SexpParser("|YWJj|").parse_base_64() == "abc"
```

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

The package exposes the Python API above. The previous `sexp` console entry
point referred to a missing function and has been removed.

## Reference

The specification and grammar are stored in `docs/RFC9804/`. Example input is in
`data/`. The project uses the MIT license in `LICENSE`.
