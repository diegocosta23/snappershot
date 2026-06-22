from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Company:
    """
    Representerar ett företag.
    """

    name: str
    ticker: str