# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[Unreleased]

### Added

- Complete RFC 9804 canonical, basic transport and advanced transport parsing,
  including nested lists, all octet-string representations and display-hints.
- UTF-8 text and arbitrary binary input, byte-accurate lengths and cursor offsets,
  strict full-input validation, and iterative parsing for deeply nested lists.
- Binary canonical and basic transport Hypothesis strategies, plus parser/generator
  interoperability and malformed-input tests.
- A `generator` installation extra for Hypothesis-based generators.
- An RFC 9804 conformance matrix, section-labelled examples, exhaustive octet
  character-class checks and independent advanced-generator semantic checks.

### Changed

- Rename the parser to `SExpressionParser`; retain `SexpParser` as an alias.
- Return byte atoms, Python lists and `DisplayString` values from expression parsing.
- Validate optional string lengths and reject decimal prefixes with leading zeroes.
- Generate valid string lengths, single-octet escapes and bounded recursive lists
  with unambiguous token separators.
- Match individual ABNF groups in `parse_base_64_chars()`, `parse_base_64_end()`
  and `parse_hexadecimals()` instead of consuming multiple groups per call.
