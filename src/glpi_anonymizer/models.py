from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Label(str, Enum):
    """What kind of personal data a match represents.

    The value doubles as the placeholder name, so a redacted CIN reads
    ``[CIN]``. Inheriting from ``str`` keeps these usable as plain dict keys
    and JSON values.
    """

    CIN = "CIN"
    PHONE = "PHONE"
    RIB = "RIB"
    IBAN = "IBAN"
    ICE = "ICE"
    EMAIL = "EMAIL"
    IP = "IP"
    CARD = "CARD"
    URL = "URL"


@dataclass(frozen=True, slots=True)
class Match:
    """One piece of personal data located in a string."""

    start: int
    end: int
    label: Label
    text: str

    def __len__(self) -> int:
        return self.end - self.start

    def overlaps(self, other: Match) -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True, slots=True)
class AnonymizationResult:
    """The anonymized text plus what was replaced in it."""

    text: str
    matches: list[Match] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.matches)

    def counts_by_label(self) -> dict[Label, int]:
        counts: dict[Label, int] = {}
        for match in self.matches:
            counts[match.label] = counts.get(match.label, 0) + 1
        return counts
