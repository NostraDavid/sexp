"""Compare immutable parser snapshots using the scaling benchmark methodology."""

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

from benchmarks import scaling

ROOT = scaling.ROOT
MIB = 1024**2
DEFAULT_CASES = (
    ("deep_list_bytes", 4 * MIB),
    ("deep_list_bytes", MIB),
    ("wide_list_bytes", 4 * MIB),
    ("mixed_list_bytes", 4 * MIB),
    ("token_bytes", 4 * MIB),
    ("hex_bytes", 16 * MIB),
    ("base64_bytes", 16 * MIB),
    ("basic_transport_bytes", 16 * MIB),
    ("verbatim_bytes", 64 * MIB),
    ("verbatim_utf8_str", 64 * MIB),
    ("quoted_bytes", 4 * MIB),
    ("escaped_bytes", 4 * MIB),
    ("whitespace_bytes", 4 * MIB),
)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _child(snapshot, expected_hash, scenario, size, repeats, memory_bytes):
    import resource

    import sexp.parser as parser

    expected_path = Path(snapshot).resolve() / "sexp" / "parser.py"
    actual_path = Path(parser.__file__).resolve()
    actual_hash = _sha(actual_path.read_bytes())
    if actual_path != expected_path or actual_hash != expected_hash:
        raise RuntimeError("imported parser does not match requested snapshot")
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    try:
        result = scaling.measure_case(scenario, size, repeats)
    except MemoryError:
        result = {
            "scenario": scenario,
            "target_bytes": size,
            "status": "memory_censored",
            "wall_seconds": [],
            "cpu_seconds": [],
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        }
    result.update(parser_path=str(actual_path), parser_sha256=actual_hash)
    print(json.dumps(result))


def _run_case(snapshot, digest, scenario, size, repeats, timeout, memory_bytes):
    command = [
        sys.executable,
        "-B",
        "-c",
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "from benchmarks.memory import _child; "
        "_child(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), "
        "int(sys.argv[5]), int(sys.argv[6]))",
        str(snapshot),
        digest,
        scenario,
        str(size),
        str(repeats),
        str(memory_bytes),
    ]
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {
            "scenario": scenario,
            "target_bytes": size,
            "status": "timeout_censored",
        }
    if proc.returncode:
        return {
            "scenario": scenario,
            "target_bytes": size,
            "status": "worker_failed",
            "returncode": proc.returncode,
            "error": proc.stderr[-4000:],
        }
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "scenario": scenario,
            "target_bytes": size,
            "status": "worker_failed",
            "error": proc.stderr[-4000:] or "invalid worker output",
        }


def run_comparison(
    revision="cdfd9f9",
    cases=None,
    repeats=5,
    timeout=60,
    memory_bytes=768 * MIB,
):
    """Compare committed and current parser bytes in serial, isolated children.

    Cases are (scenario, encoded target byte count) pairs. No report is written.
    Linux is required because peak RSS units and RLIMIT_AS semantics are platform-specific.
    """
    if not sys.platform.startswith("linux"):
        raise RuntimeError("memory comparison requires Linux")
    cases = tuple(DEFAULT_CASES if cases is None else cases)
    if (
        any(s not in scaling.SCENARIOS or n < 1 for s, n in cases)
        or repeats < 1
        or timeout <= 0
        or memory_bytes <= 0
    ):
        raise ValueError("invalid comparison parameters")
    revision = subprocess.run(
        ["git", "rev-parse", "--verify", revision + "^{commit}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    baseline = subprocess.run(
        ["git", "show", revision + ":src/sexp/parser.py"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    candidate = (ROOT / "src/sexp/parser.py").read_bytes()
    sources = {"baseline": baseline, "candidate": candidate}
    hashes = {name: _sha(source) for name, source in sources.items()}
    try:
        cpu = next(
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text().splitlines()
            if line.startswith("model name")
        )
    except (OSError, StopIteration):
        cpu = platform.processor() or None
    report = {
        "metadata": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "python": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            "cpu_model": cpu,
            "cpu_count": os.cpu_count(),
            "load_average": list(os.getloadavg()),
            "baseline_revision": revision,
            "parser_sha256": hashes,
            "benchmark_sha256": {
                "scaling": _sha(Path(scaling.__file__).read_bytes()),
                "memory": _sha(Path(__file__).read_bytes()),
            },
        },
        "policy": {
            "repeats": repeats,
            "warmups": 1,
            "timeout_seconds": timeout,
            "child_rlimit_as_bytes": memory_bytes,
            "method": "fresh serial child per version and case; scaling.measure_case",
            "peak_rss": "whole child high-water RSS in KiB, including input and warmup",
        },
        "results": [],
    }
    preferred = Path("/tmp/opencode")
    scratch = (
        preferred
        if preferred.is_dir() and os.access(preferred, os.W_OK | os.X_OK)
        else None
    )
    with tempfile.TemporaryDirectory(prefix="sexp-memory-", dir=scratch) as tmp:
        snapshots = {}
        for name, source in sources.items():
            snapshot = Path(tmp) / name
            package = snapshot / "sexp"
            package.mkdir(parents=True)
            (package / "__init__.py").write_bytes(b"")
            (package / "parser.py").write_bytes(source)
            snapshots[name] = snapshot
        for scenario, size in cases:
            for name in ("baseline", "candidate"):
                row = _run_case(
                    snapshots[name],
                    hashes[name],
                    scenario,
                    size,
                    repeats,
                    timeout,
                    memory_bytes,
                )
                row["version"] = name
                report["results"].append(row)
    return report
