from __future__ import annotations
from typing import Optional

from pydantic import BaseModel, Field


class SexpSettings(BaseModel):
    allow_comments: bool = Field(default=True)
    large_atom_threshold: int = Field(default=1 << 20)
    warn_on_large_atom: bool = Field(default=True)
    prefer_base64_min_len: int = Field(default=48)
    pretty_indent: Optional[int] = Field(default=2)
