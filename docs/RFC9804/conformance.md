# RFC 9804 conformance

Reference: [RFC 9804, June 2025](https://datatracker.ietf.org/doc/html/rfc9804).
The bundled `rfc9804.txt` is retained as the reference text. This implementation
targets the mandatory **canonical** and **basic transport** forms, and also
supports the optional **advanced transport** form (§§6 and 8).

## Requirements and evidence

Tests below are in `tests/sexp/` and run as part of `just check`.

| RFC section | Implemented behavior | Executable evidence |
| --- | --- | --- |
| §§1–2 | Byte-valued atoms and finite, ordered, nested lists, including empty values | `test_rfc9804.py::test_rfc_examples`; `test_expression.py::test_complete_expression` |
| §§3, 7.1 | ASCII syntax, exactly six whitespace characters, arbitrary octets only in verbatim payloads or decoded encodings | `test_rfc9804.py::test_sections_3_and_7_character_classes_for_every_octet` checks all 256 octets; malformed-expression tests reject Unicode whitespace and raw non-ASCII tokens/quotes |
| §4.1 | Decimal byte counts, no leading zeroes, no interpretation of payload punctuation, exact payload length | `test_rfc_examples`; `test_cursor_counts_utf8_bytes`, `test_binary_delimiters_are_not_syntax`, `test_malformed_expression` in `test_expression.py` |
| §4.2 | All C escapes, exactly three octal/two hex digits, single-octet values, four line-continuation forms; optional decoded byte count | `test_rfc_examples`; `test_escape_sequences`, `test_primitive_length_mismatch`, `test_malformed_expression` in `test_expression.py` |
| §4.3 | Nonempty, case-sensitive ASCII tokens, not starting with digits; all eight punctuation characters | `test_rfc_examples`; exhaustive character-class checks; `test_gen.py::test_token_strategy` |
| §4.4 | Even number of hex digits, ignored RFC whitespace, rejected non-hex characters; optional decoded length | `test_rfc_examples`; `test_equivalent_octet_encodings` and malformed-expression tests in `test_expression.py` |
| §4.5 | Standard base64 alphabet and padding, optional missing padding accepted on input, ignored RFC whitespace; optional decoded length | `test_rfc_examples`, `test_rfc4648_section_10_base64_vectors`; encoding-equivalence and malformed-expression tests |
| §§4.6–4.7 | Explicit byte-valued hints retained, including empty/default hints; no nested hints or hints on lists; UTF-8 recommended for text | `test_section_4_6_explicit_default_hint_is_preserved`, literal UTF-8 example test; hinted, binary, Unicode and malformed cases in `test_expression.py` |
| §5 | Ordered lists, greedy token boundaries, whitespace where tokens could otherwise merge | List examples in `test_expression.py`; `test_gen.py::test_advanced_parser_interoperability` independently checks generated list elements and separators |
| §§6.2, 7.2 | Canonical strings use only verbatim form; no structural whitespace; hints retained | `test_sections_6_and_7_mandatory_canonical_and_basic`; `test_reject_noncanonical_expression` in `test_expression.py` |
| §§6.1, 6.3, 7.3 | Basic transport accepts canonical input and `{base64(canonical)}`; decoded content must be exactly one canonical expression | `test_sections_6_and_7_mandatory_canonical_and_basic` exercises every permitted whitespace character and missing-padding variant; malformed basic payload tests in `test_expression.py` |
| §§6.4, 7.1 | All five advanced string representations, lists and display-hints | `test_rfc_examples`; independent atom and whole-expression oracles in `test_gen.py` |
| §7.1 | ABNF helpers consume one base64 group (four data characters, or two/three in an ending) or one two-digit hex group, not arbitrary repetitions | `test_section_7_helpers_consume_one_abnf_group`; grammar strategy interoperability checks in `test_gen.py` |

## Interpretation and scope

- The parser returns `bytes`, Python lists and `DisplayString(data, display_hint)`.
  It does not normalize case, interpret numeric atoms, insert implicit default
  hints or discard explicit default hints. Applications may implement the
  application-specific default-hint comparison permitted by §§4.6–4.7.
- `str` input is encoded as UTF-8 before parsing. Lengths and positions count
  bytes. Raw non-ASCII text belongs in verbatim payloads, or is represented by
  byte escapes, hex or base64, rather than extending the quoted/token grammar.
- `parse()` consumes exactly one complete expression and permits surrounding
  RFC whitespace. `parse_canonical()` also rejects structural whitespace.
  The brace payload is validated with `parse_canonical()`, not the permissive
  advanced reader. Binary payload whitespace is data, not structural whitespace.
- The printed UTF-8 example in §4.6 contains `C3 B7`, which encodes **÷**, although
  its prose says **ö** (`C3 B6`). The parser preserves the literal bytes. Tests
  cover both the printed example and the corrected spelling; the reference text
  is not silently changed.
- The Hypothesis generator produces valid **decoder test inputs**, not a
  production serialization API. RFC 9804 §§4.5 and 6.1 explicitly allow whitespace
  in base64 inputs. Such whitespace is deliberately generated, including line
  feeds. Whole-string base64 generation uses padded `base64.b64encode` output
  with zero pad bits; grammar-fragment strategies also exercise the permitted
  missing-padding inputs. These input choices do not prescribe serializer line
  wrapping or waive the encoder requirements of
  [RFC 4648 §§3.1–3.5](https://www.rfc-editor.org/rfc/rfc4648#section-3).
- The independent advanced oracle checks the generator's separated-list subset
  of the advanced grammar. It is test code, not a second public RFC validator.
- §8 lists optional application restrictions; none are imposed as a protocol
  profile. Generator size bounds keep tests finite, not parser atom-size limits.
  §9's in-memory layouts are suggestions, not mandatory wire encodings. Signing,
  signature verification, a general Lisp reader and serialization are outside
  this parser/test-generator API.

This matrix records reviewed behavior and executable regression evidence, not a
formal proof or third-party conformance certification. Coverage measures exercised
code, not correctness against a specification. No external implementation
interoperability certification is claimed.
