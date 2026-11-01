import json
import sys

import pytest

if sys.platform != "linux":
    pytest.skip(
        "Scaling measurements use Linux resource limits and RSS units",
        allow_module_level=True,
    )

from benchmarks import scaling  # noqa: E402 -- skip unsupported platforms before import


@pytest.mark.parametrize("scenario", scaling.SCENARIOS)
def test_small_scenarios(scenario):
    result = scaling.measure_case(scenario, 128, repeats=1)
    assert result["status"] == "ok", result
    assert result["input_bytes"] > 0
    assert len(result["wall_seconds"]) == len(result["cpu_seconds"]) == 1
    assert result["wall_min"] <= result["wall_median"] <= result["wall_max"]
    assert result["peak_rss_kib"] > 0


def test_sweep_in_subprocess():
    report = scaling.run_sweep(["verbatim_utf8_str"], [128], repeats=1)
    assert report["results"][0]["status"] == "ok"
    assert report["results"][0]["input_bytes"] <= 128
    assert len(report["metadata"]["parser_sha256"]) == 64
    json.dumps(report)


def test_stop_and_censored_cases(monkeypatch):
    calls = []

    def fake(scenario, size, repeats, timeout, memory_bytes):
        calls.append((scenario, size))
        if scenario == "token_bytes":
            return {"status": "timeout_censored"}
        return {"status": "ok", "wall_median": 2}

    monkeypatch.setattr(scaling, "_run_case", fake)
    report = scaling.run_sweep(["token_bytes", "quoted_bytes"], [4, 8])
    assert calls == [("token_bytes", 4), ("quoted_bytes", 4)]
    assert report["results"][0]["status"] == "timeout_censored"


def test_memory_failure_during_input(monkeypatch, capsys):
    def fail(*args):
        raise MemoryError

    monkeypatch.setattr(scaling.resource, "setrlimit", lambda *args: None)
    monkeypatch.setattr(scaling, "measure_case", fail)
    scaling._child("token_bytes", 128, 1, 1024)
    assert json.loads(capsys.readouterr().out)["status"] == "memory_censored"


def test_timeout(monkeypatch):
    def fail(*args, **kwargs):
        raise scaling.subprocess.TimeoutExpired("worker", 1)

    monkeypatch.setattr(scaling.subprocess, "run", fail)
    assert (
        scaling._run_case("token_bytes", 128, 1, 1, 1024)["status"]
        == "timeout_censored"
    )
