from __future__ import annotations

from typing import Iterable
from schemas import Assertion


def all_passed(assertions: Iterable[Assertion]) -> bool:
    return all(a.passed for a in assertions)
