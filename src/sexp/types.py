from __future__ import annotations

from typing import Iterable, Union


class SexpAtom:
    def __init__(self, value: Union[bytes, str]):
        self.value: Union[bytes, str] = value

    def is_bytes(self) -> bool:
        return isinstance(self.value, bytes)

    def as_bytes(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        if isinstance(self.value, bytes):
            return self.value
        return self.value.encode(encoding, errors)

    def as_str(self, encoding: str = "utf-8", errors: str = "strict") -> str:
        if isinstance(self.value, str):
            return self.value
        return self.value.decode(encoding, errors)


# forward reference string keeps it lowercase in code while still valid typing
SexpNode = Union["SexpList", SexpAtom]


class SexpList:
    def __init__(self, items: Iterable[SexpNode] = ()):
        self.items: list[SexpNode] = list(items)

    def append(self, node: SexpNode) -> None:
        self.items.append(node)

    def extend(self, nodes: Iterable[SexpNode]) -> None:
        self.items.extend(nodes)
