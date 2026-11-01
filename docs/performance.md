# Parser performance

The tables below preserve the original pre-optimization baseline, committed in
`cdfd9f9`; they are not a new scaling sweep of the memory-optimized parser.
Use `just benchmark-memory` for a focused before/after comparison of that baseline
and the current parser, including both latency and whole-process peak RSS.
The changes and comparison methodology are described in
[memory optimization](memory-optimization.md).
That follow-up also records explicit normal/development-mode controls; the
original scaling report did not record the development-mode flag directly.
Do not interpret its roughly 330 MiB peak as a universal production requirement.

## Baseline results: 2026-11-01

**There is no single performant byte limit.** On this machine, a 64 MiB verbatim
byte string parsed in **68.7 ms**, but a roughly 1 MiB list of tiny tokens took
**472.0 ms**. For the tested complex shapes, 128 KiB is a conservative reference
point below 100 ms; roughly 2 MiB remained below one second. These are measured
medians for synthetic inputs, not guaranteed limits for arbitrary expressions.

Environment: **AMD Ryzen 9 9950X3D**, Linux x86-64, **CPython 3.14.9**, one parsing
thread. Initial system load averages were 2.31 / 2.20 / 2.12 on 32 logical CPUs.
The parser was not modified or optimized for these measurements.

The primary sweep contains 97 cases; a second sweep measured 21 geometric
midpoints around the 100 ms and 1 s brackets. Together: **118 distinct cases,
590 timed parses and 118 warmups**. All cases succeeded; no timeouts or memory
censoring occurred. Exact timings, byte counts, metadata and source hashes are in
[`performance-results.json`](performance-results.json). Recalculation verified
the sample counts, medians, extrema, unique case keys and identical source hashes
across the two sweeps.

Commit hooks subsequently normalized trailing commas and formatting in the
parser and benchmark. The original measurement hashes are retained; the JSON's
`source_equivalence` records the formatted source hashes and matching AST hashes.
The measured and formatted sources were compared with Python's AST, excluding
source positions, and were identical. Timings were not rerun for formatting alone.

### Measured latency boundaries

“Within budget” below means the **largest tested** input with median latency at
or below the budget. The next column brackets it with the first tested input
above the budget. Sizes are rounded to the target grid labels; exact encoded
byte lengths, which can differ slightly due to framing, are retained in the JSON.
These are not interpolated exact cutoffs.

| Input shape | Within 100 ms | First above 100 ms | Within 1 second | First above 1 second |
| --- | --- | --- | --- | --- |
| One verbatim atom, `bytes` | 64 MiB — 68.7 ms | Not reached through 64 MiB | 64 MiB — 68.7 ms | Not reached through 64 MiB |
| UTF-8 verbatim atom, `str` | 32 MiB — 56.7 ms | 64 MiB — 102.7 ms | 64 MiB — 102.7 ms | Not reached through 64 MiB |
| One large token | 1 MiB — 83.5 ms | 2 MiB — 167.8 ms | 8 MiB — 690.3 ms | 16 MiB — 1,391.2 ms |
| Quoted ASCII | 256 KiB — 52.4 ms | 512 KiB — 105.5 ms | 4 MiB — 841.0 ms | 8 MiB — 1,680.2 ms |
| Escaped quoted text (`\x61`) | 512 KiB — 81.4 ms | 1 MiB — 162.6 ms | 4 MiB — 651.3 ms | 8 MiB — 1,305.9 ms |
| Hexadecimal atom | 512 KiB — 53.1 ms | 1 MiB — 108.5 ms | 8 MiB — 868.4 ms | 16 MiB — 1,701.7 ms |
| Base64 atom | 512 KiB — 54.8 ms | 1 MiB — 108.3 ms | 8 MiB — 892.4 ms | 16 MiB — 1,804.4 ms |
| Basic transport wrapper | 512 KiB — 54.2 ms | 1 MiB — 108.4 ms | 8 MiB — 892.9 ms | 16 MiB — 1,817.8 ms |
| Wide list of tiny tokens | 128 KiB — 57.6 ms | 256 KiB — 112.9 ms | 2 MiB — 914.3 ms | 4 MiB — 1,824.0 ms |
| Deeply nested lists | 128 KiB — 49.9 ms | 256 KiB — 102.2 ms | 2 MiB — 853.3 ms | 4 MiB — 1,803.0 ms |
| Mixed advanced expressions | 256 KiB — 77.4 ms | 512 KiB — 155.5 ms | 2 MiB — 615.0 ms | 4 MiB — 1,274.5 ms |
| Leading form-feed whitespace | 256 KiB — 79.4 ms | 512 KiB — 156.9 ms | 2 MiB — 619.7 ms | 4 MiB — 1,251.0 ms |

### Memory and variation

- A 64 MiB verbatim `bytes` input reached **276.5 MiB process peak RSS**; its
  five timing samples ranged from 67.3 to 71.5 ms.
- At approximately 2 MiB input, the deeply nested case reached **179.3 MiB**
  process peak RSS (about 1,048,575 list levels), versus **35.9 MiB** for the wide
  list (about 1,048,575 one-byte atoms). Their timing ranges were 850.5–857.0 ms
  and 903.4–919.9 ms respectively.
- The largest process peak observed was **330.5 MiB**, for the approximately
  4 MiB deeply nested case (about 2,097,151 list levels). It parsed successfully
  in a median 1.80 seconds, then the growth policy stopped that scenario.

The measurements do not establish a maximum supported input size. Larger inputs
were intentionally not attempted once a scenario exceeded the stop budget or
reached 64 MiB. Actual application performance also includes I/O, result use and
cleanup; production tail latency and concurrent workloads were not measured.

## Measurement method

Run on Linux from the checkout with its locked development environment:

```bash
just benchmark-scaling > performance-results.json
```

`benchmarks/scaling.py` measures the local parser rather than a historical wheel.
The output records the parser and benchmark SHA-256 hashes, Git HEAD, interpreter,
CPU model, initial system load and raw wall/CPU samples. The working tree can be
dirty; the parser hash identifies the measured source more precisely than HEAD.

- Twelve deterministic, valid RFC 9804 shapes: binary verbatim, UTF-8 verbatim
  supplied as `str`, one large token, quoted ASCII, escaped quoted text, hex,
  base64, basic transport, wide lists of tiny tokens, deeply nested lists,
  mixed advanced expressions and form-feed whitespace.
- Sizes are **encoded input bytes**, not decoded payload sizes. Actual byte
  counts are recorded because framing and grouping can round a target slightly.
The primary grid is 1 KiB, 4 KiB, 16 KiB, 64 KiB, 256 KiB, 1 MiB, 4 MiB,
  16 MiB and 64 MiB. One MiB is 1,048,576 bytes.
- Cases run **serially**, each in a fresh subprocess, with one warmup and five
  measured repetitions. The reported latency is the median, with all samples
  retained. Wall and process CPU clocks are both recorded.
- Timing includes `SExpressionParser(input).parse()`: constructor decoding or
  UTF-8 encoding, AST allocation and parsing. It excludes imports, subprocess
  startup, input generation, validation, explicit garbage collection and result
  destruction. Normal automatic GC stays enabled. This is warmed in-memory
  parsing, not file/network I/O or complete application latency.
- Validation outside the timer checks complete consumption and expected atom,
  list or nesting properties. Parser implementation and semantics are unchanged
  by this performance exercise.
- Each child has a 768 MiB **virtual address-space** cap and a 45-second
  **whole-case** timeout, including setup, warmup, all repetitions and cleanup.
  Those bounds are measurement safety controls, not limits built into the parser.
  A timeout or allocation failure does not establish a single-parse latency or
  parser-only memory threshold.
- A scenario stops after its first completed median above 1.5 seconds, or a
  failure. A completed slow measurement is observed, not censored. Larger
  unattempted sizes are unmeasured, not failures or successes.
- Peak RSS is the **whole child process high-water mark**, including interpreter,
  input-construction temporaries, warmup and parsed output. It is neither extra
  parser memory nor the virtual address-space cap. No allocation tracer runs
  during timing.

## Interpretation

For this run, **100 ms** is a practical interactive budget and **1 second** is a
practical batch budget, per expression. These are explicitly chosen reference
budgets, not a library SLA or universal definition of “performant”.

There is no universal byte limit: a single verbatim payload is copied using
native operations, whereas tokens/encodings are scanned character by character,
and lists allocate Python objects. Depth and atom count matter independently of
byte length. A tested latency boundary applies to that shape, interpreter and
machine; it is not a guarantee for arbitrary valid or adversarial inputs.

The machine is not reserved exclusively for benchmarking. Five-sample ranges
describe observed variation, not statistically established production tail latency.
No comparison with a previous release or performance-regression claim is made.
