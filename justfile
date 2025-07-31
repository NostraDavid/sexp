#!/usr/bin/env -S just --justfile

# `just --list` to list all recipes.
# `just --choose` to choose a recipe interactively.
# Several of these programs use the configuration from pyproject.toml to
# influence their behavior.
# example: https://github.com/casey/just/blob/master/justfile

alias t := test

log := "warn"

export JUST_LOG := log

[group: 'testing']
test:
  uv run pytest --cov=sexp tests/

[group: 'linting']
lint:
  uv run ruff check --fix --unsafe-fixes .

[group: 'formatting']
format:
  uv run ruff format src tests

[group: 'benchmarking']
benchmark:
  uv run asv run --show-stderr --show-stderr --config asv.conf.json

[group: 'packaging']
build:
  PYO3_PYTHON="$PWD/.venv/bin/python" maturin develop --release
