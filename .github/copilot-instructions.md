# S-expression parser development

Use `devenv shell` or `direnv allow` to enter the development environment.
Run `just --list` for commands and `just check` for lint, format and type checks,
tests with coverage, and package builds.

`src/sexp/parser.py` defines `SexpParser`, a parser for individual RFC 9804
primitives. It tracks `text` and `index` on each instance. The full expression
parser is incomplete. Follow existing primitive methods when adding grammar
rules and cover valid input, invalid input and cursor advancement in tests.

`src/sexp/gen.py` defines the Hypothesis generators used by parser tests.
Tests live in `tests/sexp/`. The RFC and ABNF grammar are in `docs/RFC9804/`.

The package exports `SexpParser` from `src/sexp/__init__.py`. It has no console
entry point. Keep commands and public interface examples consistent with the
current package rather than the earlier CLI or uv2nix templates.
