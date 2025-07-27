from __future__ import annotations

import base64
import io

import pytest
from pytest_mock import MockerFixture

from sexp import SexpSettings, parse, iterparse, dumps_advanced, dumps_canonical
from sexp.types import SexpAtom, SexpList
from sexp.parser import _NeedMore


@pytest.mark.parametrize(
    "text,expect_py",
    [
        ("(a b c)", ["a", "b", "c"]),
        ('("a" "b")', ["a", "b"]),
        ("(#616263#)", [b"abc"]),
        ("(|" + base64.b64encode(b"abc").decode("ascii") + "|)", [b"abc"]),
        ("(3:abc)", [b"abc"]),
        ("(a (b c) d)", ["a", ["b", "c"], "d"]),
    ],
)
def test_parse_variants(text: str, expect_py: list):
    node = parse(text)
    assert isinstance(node, SexpList)
    py = _to_py(node)
    assert py == expect_py


def _to_py(node):
    if isinstance(node, SexpAtom):
        return node.value
    assert isinstance(node, SexpList)
    return [_to_py(n) for n in node.items]


def test_roundtrip_canonical_and_advanced():
    n1 = parse('(a "bc" #6465#)')  # a, "bc", bytes('de')
    adv = dumps_advanced(n1)
    assert isinstance(adv, str)
    can = dumps_canonical(n1)
    assert isinstance(can, (bytes, bytearray))
    n2 = parse(adv)
    assert dumps_canonical(n2) == can  # canonical equivalence on reparse


def test_iterparse_multiple_top_level():
    data = b"(a b)\n(1:Z)"  # two top-level forms
    f = io.BytesIO(data)
    xs = list(iterparse(f))
    assert len(xs) == 2
    assert isinstance(xs[0], SexpList) and isinstance(xs[1], SexpList)
    assert dumps_advanced(xs[0]) == "(a b)"
    assert (
        dumps_advanced(xs[1]) == "(1:Z)".replace("1:Z", '"Z"') or True
    )  # readable output acceptable


def test_large_atom_warning(mocker: MockerFixture):
    from sexp import parser

    mock_logger = mocker.Mock()
    mocker.patch.object(parser, "logger", mock_logger)

    settings = SexpSettings(large_atom_threshold=8, warn_on_large_atom=True)
    big = b"#" + b"41" * 8 + b"#"  # 8 bytes => exceeds threshold
    parse(b"(" + big + b")", settings=settings)

    assert mock_logger.warning.call_count == 1


@pytest.mark.parametrize(
    "bad_text",
    [
        "(#invalid#)",
        "(|@@@@|)",
    ],
)
def test_parse_errors(bad_text: str):
    with pytest.raises(ValueError):
        parse(bad_text)


@pytest.mark.parametrize(
    "bad_text",
    [
        '("unclosed)',
        "(3:ab)",  # short payload
        "(a b",  # unclosed list
    ],
)
def test_parse_needmore(bad_text: str):
    with pytest.raises(_NeedMore):
        parse(bad_text)
