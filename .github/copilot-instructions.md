# S-expression parser development

Use `devenv shell` or `direnv allow` to enter the development environment.
Run `just --list` for commands and `just check` for lint, format and type checks,
tests with coverage, and package builds.

`src/sexp/parser.py` defines `SExpressionParser` (`SexpParser` is a compatibility
alias). It accepts UTF-8 text or bytes and parses canonical, basic transport and
advanced RFC 9804 expressions. Atoms are bytes, lists are Python lists, and
`DisplayString` preserves explicit display-hints. Lengths and cursor offsets
count bytes; `text` is an internal Latin-1 byte view. Test valid and invalid input,
full-input consumption, byte lengths and cursor advancement when changing rules.

`src/sexp/gen.py` defines `SExpressionGenerator`; its advanced strategies return
text, while `canonical` and `basic_transport` return binary encodings. Keep
generated lengths and token boundaries valid and cover parser interoperability.
Tests live in `tests/sexp/`. The RFC and ABNF grammar are in `docs/RFC9804/`.

The package has no console entry point. The generator uses the optional
`generator` extra; importing the parser must not require Hypothesis.
