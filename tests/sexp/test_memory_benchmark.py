import hashlib
import json
import sys

import pytest

if sys.platform != "linux":
    pytest.skip(
        "Memory comparisons use Linux RLIMIT_AS and RSS",
        allow_module_level=True,
    )

from benchmarks import memory  # noqa: E402 -- skip unsupported platforms before import


def test_comparison_uses_selected_snapshots():
    report = memory.run_comparison(cases=[("mixed_list_bytes", 128)], repeats=1)
    json.dumps(report)
    assert len(report["metadata"]["baseline_revision"]) == 40
    candidate_source = (memory.ROOT / "src/sexp/parser.py").read_bytes()
    assert (
        report["metadata"]["parser_sha256"]["candidate"]
        == hashlib.sha256(candidate_source).hexdigest()
    )
    for row in report["results"]:
        assert row["status"] == "ok"
        assert (
            row["parser_sha256"] == report["metadata"]["parser_sha256"][row["version"]]
        )
        assert f"/{row['version']}/sexp/parser.py" in row["parser_path"]
        assert len(row["wall_seconds"]) == len(row["cpu_seconds"]) == 1
        assert row["peak_rss_kib"] > 0


def test_snapshot_hash_mismatch_is_worker_failure(tmp_path):
    package = tmp_path / "sexp"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "parser.py").write_bytes(
        (memory.ROOT / "src/sexp/parser.py").read_bytes(),
    )
    row = memory._run_case(
        tmp_path,
        "wrong",
        "token_bytes",
        128,
        1,
        10,
        768 * memory.MIB,
    )
    assert row["status"] == "worker_failed"
    assert "does not match" in row["error"]


def test_invalid_parameters():
    with pytest.raises(ValueError):
        memory.run_comparison(cases=[("not_a_case", 128)])


def test_fallback_when_preferred_scratch_is_unavailable(monkeypatch):
    original = memory.tempfile.TemporaryDirectory
    directories = []

    def record_directory(*args, **kwargs):
        directories.append(kwargs.get("dir"))
        return original(*args, **kwargs)

    monkeypatch.setattr(memory.os, "access", lambda *args: False)
    monkeypatch.setattr(memory.tempfile, "TemporaryDirectory", record_directory)
    assert memory.run_comparison(cases=[])["results"] == []
    assert directories == [None]
