# Parser memory optimization

## Measured results: 2026-11-01

The code reduces peak memory while preserving the public API. It is a
**memory/CPU trade-off**, not an across-the-board speed optimization.

The fresh, controlled comparisons below use the same baseline commit, candidate
source, CPython 3.14.9 interpreter and Ryzen 9 9950X3D machine. Only the Python
development-mode setting differs between the two groups. Values are whole-process
peak RSS and median constructor-plus-parse time, with five timed repeats after
one warmup in each fresh child.

| Runtime mode | Encoded input | Baseline RSS | Optimized RSS | RSS reduction | Baseline time | Optimized time |
| --- | --- | --- | --- | --- | --- | --- |
| Development mode | 4 MiB deeply nested lists | 330.8 MiB | 268.0 MiB | 19.0% | 1,774.9 ms | 1,968.1 ms |
| Normal mode | 4 MiB deeply nested lists | 232.9 MiB | 200.7 MiB | 13.8% | 1,721.9 ms | 1,844.3 ms |
| Normal mode | 4 MiB wide list of tiny tokens | 48.9 MiB | 49.6 MiB | -1.6% | 1,673.0 ms | 1,667.7 ms |
| Normal mode | 16 MiB hexadecimal atom | 203.8 MiB | 83.7 MiB | 58.9% | 1,690.1 ms | 1,750.8 ms |
| Normal mode | 16 MiB base64 atom | 204.4 MiB | 95.0 MiB | 53.5% | 1,736.4 ms | 1,810.3 ms |

This reduces the original extreme nested-input concern, but does not make an
object-heavy result cheap. Deep-list parsing was approximately **7% slower in
normal mode** and **11% slower in development mode** in these runs. Hex/base64
parsing was about **4% slower in normal mode** for the large cases, in return for
substantially lower temporary-buffer memory. The wide-list result did not show
a memory improvement; its roughly 0.8 MiB RSS increase is retained in the report,
not hidden by reporting only the winning cases.

An initial 13-case comparison also covered mixed expressions, a large token,
verbatim bytes/UTF-8 text, quoted/escaped text and whitespace. Untargeted paths
showed little memory change, and their timings varied, so small percentage
differences are not treated as proof of a speed change. The original 64 MiB
verbatim fast path was not rewritten.

[`memory-results.json`](memory-results.json) preserves all three reports:
`initial_project_environment` (26 versioned cases), `explicit_development_mode`
(2) and `normal_mode` (8): **36 successful cases and 180 timed parses** in the
retained reports. Samples, actual byte lengths, selected source hashes and
effective runtime-mode observations for the controlled runs are included.
The initial report did not directly record that flag; its metadata is retained
as collected rather than retroactively rewritten.

### Development-mode context

The project shell has `PYTHONDEVMODE=1`. Python's
[development mode](https://docs.python.org/3.14/library/devmode.html) installs
additional runtime checks and debug hooks on memory allocators. The separately
controlled development-mode run reproduces the roughly 330 MiB baseline; the
normal-mode run shows why that absolute figure is not a universal production
memory requirement.

The project setting was **not changed**. Normal-mode benchmarks only unset the
variable for their own processes. Setting it to the nonempty string `0` does
not disable this Python flag; use:

```bash
env -u PYTHONDEVMODE just benchmark-memory > memory-normal.json
PYTHONDEVMODE=1 just benchmark-memory > memory-development.json
```

Savings in the table compare old and new code **within the same mode**. The
difference between modes is not counted as a code optimization. The two
explicit-mode reports record `sys.flags.dev_mode`, the relevant environment
values and the child invocation flags. None of the reported timing/RSS runs
used `tracemalloc`.

## Scope

The committed baseline is `cdfd9f9`. Parsed values still use the same public
types: `bytes`, ordinary mutable Python lists and `DisplayString`. The parser
still validates the same canonical, basic and advanced RFC 9804 syntax. No
maximum atom size or nesting restriction has been introduced.

Two allocations changed:

1. Open lists use a `None` frame until their first value arrives, instead of
   immediately allocating an empty Python list for every opening parenthesis.
   Singletons and pairs are built with compact list literals. Lists of three or
   four children are compacted on close so this does not retain the extra
   capacity caused by growing a compact pair. Larger lists retain normal
   amortized `append` behavior.
2. Hex/base64 readers collect ASCII characters in a `bytearray`, not a Python
   list containing one pointer per input character. The helper still returns
   the same validated string to the existing decoders.

On the measured CPython 3.14 build, an append-built singleton list occupies
88 bytes, while a literal singleton occupies 64 bytes. The approximately 4 MiB
deep-list fixture contains 2,097,151 distinct list objects, so even compact
64-byte lists alone require about 128 MiB before input, interpreter and other
allocation costs. Eliminating that result cost would require a different API,
such as streaming events or a compact tree, which this change deliberately avoids.

## Reproduction and measurement boundaries

On Linux:

```bash
just benchmark-memory > memory-results.json
```

`benchmarks/memory.py` reads the baseline parser directly from Git and captures
the current parser before beginning. It places both immutable sources in
temporary package snapshots, then checks the actual imported path and SHA-256
inside each child. No checkout, branch or working file is replaced.

For each selected fixture, the baseline and candidate run serially in separate
fresh processes on the same interpreter. The existing scaling harness performs
one warmup and five measured parses and validates results outside the timer.
Wall times include constructor and parsing, but exclude setup, explicit garbage
collection, validation and result destruction; automatic GC remains enabled.

RSS is the **whole-process high-water mark**, including input construction,
interpreter, warmup and output. It is not additional parser memory or a retained
heap measurement. The 768 MiB virtual-address-space cap and 60-second whole-case
timeout are safety controls, not parser limits. No allocation tracer is active
during the timings. Timing medians and process peak RSS describe these selected
fixtures on this machine, not production tail latency or a universal byte limit.

The original scaling report and raw data are preserved unchanged. This focused
comparison does not recompute every scaling boundary from that report.

## Regression checks

- Existing RFC examples, malformed-input tests and independent generator oracles
  check semantic compatibility on supported Python versions.
- Additional tests exercise distinct mutable empty/singleton sibling lists,
  small lists of zero through eight children, deep lists with trailing siblings,
  cursor behavior, canonical strings and display-hints.
- CPython allocation checks compare small-list capacity against ordinary append
  construction and verify compact singleton allocation using runtime sizes rather
  than a hard-coded object ABI.
- Isolated `tracemalloc` checks put a generous bound on encoded-string temporary
  allocations. All three checks failed on the original pointer-per-character
  buffers and pass with the compact buffer. These are separate from the RSS and
  timing comparisons.
