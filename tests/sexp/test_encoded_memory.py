"""Guard against one Python pointer per encoded input byte."""

import json
import platform
import subprocess
import sys

import pytest


@pytest.mark.skipif(
    platform.python_implementation() != "CPython",
    reason="CPython allocation regression",
)
@pytest.mark.parametrize("representation", ["hex", "base64", "transport"])
def test_encoded_temporary_buffers_are_compact(representation):
    # Isolate allocation tracing from pytest, coverage and other test fixtures.
    probe = r"""
import base64
import json
import sys
import tracemalloc
from sexp import SExpressionParser

data = bytes(range(256)) * 256
kind = sys.argv[1]
if kind == "hex":
    source = b"#" + data.hex().encode() + b"#"
elif kind == "base64":
    source = b"|" + base64.b64encode(data) + b"|"
else:
    canonical = str(len(data)).encode() + b":" + data
    source = b"{" + base64.b64encode(canonical) + b"}"
parser = SExpressionParser(source)
tracemalloc.start()
result = parser.parse()
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
assert result == data and parser.at_end()
print(json.dumps({"input_bytes": len(source), "peak_python_bytes": peak}))
"""
    result = subprocess.run(
        [sys.executable, "-c", probe, representation],
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    measured = json.loads(result.stdout)
    # Generous room for compact input/output buffers, but not an ~8x pointer array.
    assert measured["peak_python_bytes"] <= 4 * measured["input_bytes"] + 65536, (
        measured
    )
