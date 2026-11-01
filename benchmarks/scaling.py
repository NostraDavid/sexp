"""Bounded, serial measurements of locally checked-out S-expression parsing."""

import base64
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
SIZES = [1024 * 4**n for n in range(9)]
SCENARIOS = (
    "verbatim_bytes",
    "verbatim_utf8_str",
    "token_bytes",
    "quoted_bytes",
    "escaped_bytes",
    "hex_bytes",
    "base64_bytes",
    "basic_transport_bytes",
    "wide_list_bytes",
    "deep_list_bytes",
    "mixed_list_bytes",
    "whitespace_bytes",
)


def make_input(scenario, target_bytes):
    """Return deterministic valid input and its expected structural measurements."""
    if scenario not in SCENARIOS or target_bytes < 1:
        raise ValueError("unknown scenario or nonpositive target size")
    n = max(1, target_bytes)
    if scenario == "verbatim_bytes":
        payload = max(0, n - len(str(n)) - 1)
        data = str(payload).encode() + b":" + b"a" * payload
    elif scenario == "verbatim_utf8_str":
        payload = max(0, (n - len(str(n)) - 1) // 2) * 2
        data = str(payload) + ":" + "é" * (payload // 2)
    elif scenario == "token_bytes":
        payload = n
        data = b"a" * payload
    elif scenario == "quoted_bytes":
        payload = max(0, n - 2)
        data = b'"' + b"a" * payload + b'"'
    elif scenario == "escaped_bytes":
        payload = max(0, (n - 2) // 4)
        data = b'"' + b"\\x61" * payload + b'"'
    elif scenario == "hex_bytes":
        payload = max(0, (n - 2) // 2)
        data = b"#" + b"61" * payload + b"#"
    elif scenario == "base64_bytes":
        payload = max(0, (n - 2) // 4) * 3
        data = b"|" + b"YWFh" * (payload // 3) + b"|"
    elif scenario == "basic_transport_bytes":
        payload = max(0, ((n - 2) * 3 // 4) - len(str(n)) - 1)
        canonical = str(payload).encode() + b":" + b"a" * payload
        data = b"{" + base64.b64encode(canonical) + b"}"
    elif scenario == "wide_list_bytes":
        count = max(1, (n - 1) // 2)
        return b"(" + b"a " * (count - 1) + b"a)", {"atom_count": count, "depth": 1}
    elif scenario == "deep_list_bytes":
        depth = max(1, (n - 1) // 2)
        return b"(" * depth + b"a" + b")" * depth, {"atom_count": 1, "depth": depth}
    elif scenario == "mixed_list_bytes":
        unit = b'([hint]a 1:a "a" "\\x61" #61# |YQ==| (a))'
        count = max(1, (n - 2) // (len(unit) + 1))
        return b"(" + (unit + b" ") * (count - 1) + unit + b")", {
            "atom_count": count * 7,
            "group_count": count,
            "depth": 3,
        }
    else:
        return b"\f" * max(0, n - 2) + b"0:", {"payload_bytes": 0, "atom_count": 1}
    return data, {"payload_bytes": payload, "atom_count": 1}


def _validate(scenario, parser, result, info):
    from sexp.parser import DisplayString

    if parser.index != parser.text_length:
        raise ValueError("parser did not consume input")
    if scenario == "wide_list_bytes":
        if len(result) != info["atom_count"] or result[0] != b"a" or result[-1] != b"a":
            raise ValueError("invalid wide list")
    elif scenario == "deep_list_bytes":
        for _ in range(info["depth"]):
            if not isinstance(result, list) or len(result) != 1:
                raise ValueError("invalid nested list")
            result = result[0]
        if result != b"a":
            raise ValueError("invalid leaf")
    elif scenario == "mixed_list_bytes":
        if len(result) != info["group_count"]:
            raise ValueError("invalid mixed list length")
        for group in (result[0], result[-1]):
            if (
                len(group) != 7
                or group[0] != DisplayString(b"a", b"hint")
                or any(x != b"a" for x in group[1:6])
                or group[6] != [b"a"]
            ):
                raise ValueError("invalid mixed list content")
    elif (
        not isinstance(result, bytes)
        or len(result) != info["payload_bytes"]
        or (
            result
            and (
                result[:1] != (b"\xc3" if scenario == "verbatim_utf8_str" else b"a")
                or result[-1:] != (b"\xa9" if scenario == "verbatim_utf8_str" else b"a")
            )
        )
    ):
        raise ValueError("invalid atom")


def measure_case(scenario, target_bytes, repeats=5):
    """Measure a case in the calling process; run_sweep isolates it in a child."""
    from sexp.parser import SExpressionParser

    data, info = make_input(scenario, target_bytes)
    info.update(
        scenario=scenario,
        target_bytes=target_bytes,
        input_bytes=len(data.encode("utf-8") if isinstance(data, str) else data),
    )
    wall, cpu = [], []
    try:
        for iteration in range(repeats + 1):
            gc.collect()
            start_wall, start_cpu = time.perf_counter(), time.process_time()
            parser = SExpressionParser(data)
            result = parser.parse()
            elapsed_cpu, elapsed_wall = (
                time.process_time() - start_cpu,
                time.perf_counter() - start_wall,
            )
            if iteration:
                wall.append(elapsed_wall)
                cpu.append(elapsed_cpu)
            _validate(scenario, parser, result, info)
            del result, parser
        info.update(
            status="ok",
            wall_seconds=wall,
            cpu_seconds=cpu,
            wall_median=statistics.median(wall),
            wall_min=min(wall),
            wall_max=max(wall),
            cpu_median=statistics.median(cpu),
            cpu_min=min(cpu),
            cpu_max=max(cpu),
        )
    except MemoryError:
        info.update(status="memory_censored", wall_seconds=wall, cpu_seconds=cpu)
    except Exception as exc:
        info.update(
            status="error",
            error=f"{type(exc).__name__}: {exc}",
            wall_seconds=wall,
            cpu_seconds=cpu,
        )
    info["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return info


def _child(scenario, size, repeats, memory_bytes):
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    try:
        result = measure_case(scenario, size, repeats)
    except MemoryError:
        result = {
            "scenario": scenario,
            "target_bytes": size,
            "status": "memory_censored",
            "wall_seconds": [],
            "cpu_seconds": [],
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        }
    print(json.dumps(result))


def _run_case(scenario, size, repeats, timeout, memory_bytes):
    command = [
        sys.executable,
        "-c",
        "import sys; sys.path.insert(0, 'src'); from benchmarks.scaling import _child; _child(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))",
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
            check=False,
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


def run_sweep(
    scenarios=None,
    sizes=None,
    repeats=5,
    timeout=45,
    memory_bytes=768 * 1024**2,
    stop_seconds=1.5,
):
    """Run each scenario and encoded target size serially in fresh processes."""
    scenarios = SCENARIOS if scenarios is None else tuple(scenarios)
    sizes = SIZES if sizes is None else tuple(sizes)
    if (
        any(s not in SCENARIOS for s in scenarios)
        or any(n < 1 for n in sizes)
        or repeats < 1
        or timeout <= 0
        or memory_bytes <= 0
        or stop_seconds <= 0
    ):
        raise ValueError("invalid sweep parameters")
    try:
        cpu_model = next(
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text().splitlines()
            if line.startswith("model name")
        )
    except (OSError, StopIteration):
        cpu_model = platform.processor() or None
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        head = None
    report = {
        "metadata": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "executable": sys.executable,
            "python": sys.version,
            "platform": platform.platform(),
            "cpu_model": cpu_model,
            "cpu_count": os.cpu_count(),
            "load_average": list(os.getloadavg()),
            "repo_head": head,
            "parser_sha256": hashlib.sha256(
                (ROOT / "src/sexp/parser.py").read_bytes(),
            ).hexdigest(),
            "benchmark_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "policy": {
            "sizes_are": "encoded input byte targets; actual input_bytes recorded separately",
            "repeats": repeats,
            "warmups": 1,
            "timeout_seconds": timeout,
            "child_rlimit_as_bytes": memory_bytes,
            "stop_median_wall_seconds": stop_seconds,
            "method": "fresh serial subprocess per case; constructor and parse timed; input generation, imports, subprocess startup, validation, destruction and explicit GC excluded; GC normally enabled",
            "peak_rss": "child process high-water RSS in KiB through measurement, including interpreter, input construction, warmup and parsed output",
        },
        "results": [],
    }
    for scenario in scenarios:
        for size in sizes:
            result = _run_case(scenario, size, repeats, timeout, memory_bytes)
            result.update(timeout_seconds=timeout, memory_limit_bytes=memory_bytes)
            report["results"].append(result)
            if result["status"] != "ok" or result["wall_median"] > stop_seconds:
                break
    return report
