set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

alias t := test

default:
    @just --list

sync:
    uv sync --locked

update:
    devenv update
    uv lock --upgrade
    uv sync --locked

test:
    uv run --locked pytest --cov=sexp tests/

lint:
    uv run --locked ruff check src tests

format:
    uv run --locked ruff format src tests

format-check:
    uv run --locked ruff format --check src tests

typecheck:
    uv run --locked ty check src

benchmark:
    uv run --locked asv run --show-stderr --config asv.conf.json

benchmark-scaling:
    uv run --locked python -c 'import json; from benchmarks.scaling import run_sweep; print(json.dumps(run_sweep(), indent=2))'

benchmark-memory:
    uv run --locked python -c 'import json; from benchmarks.memory import run_comparison; print(json.dumps(run_comparison(), indent=2))'

build:
    uv build

check: lint format-check typecheck test build
