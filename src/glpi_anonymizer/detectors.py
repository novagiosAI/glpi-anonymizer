"""Detectors locating personal data in free text.

Ordering matters: the anonymizer resolves overlaps by preferring the detector
listed first, then the longer match. A RIB is 24 digits and an ICE is 15, so
RIB must be attempted before ICE or a RIB's first 15 digits would be taken for
a company identifier.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from re import Pattern

from .checksums import is_valid_iban, is_valid_luhn, is_valid_rib
from .models import Label, Match

# A Moroccan CIN is a one- or two-letter regional code followed by 5-6 digits
# (e.g. A123456, BE12345). Case-sensitive on purpose: lowercase sequences in
# running text are far more often ordinary words than identifiers.
CIN_PATTERN = re.compile(r"\b[A-Z]{1,2}\d{5,6}\b")

# Nine national digits after the country code, starting with 5 (landline) or
# 6/7 (mobile). Accepts +212, 00212 or a leading 0, with spaces, dots or dashes.
PHONE_PATTERN = re.compile(
    r"(?<![\d+])(?:(?:\+|00)212[\s.\-]?|0)[5-7](?:[\s.\-]?\d){8}(?![\d])"
)

# 24 digits, optionally grouped. Validated against its check key afterwards.
RIB_PATTERN = re.compile(r"(?<![\d])(?:\d[\s.\-]?){23}\d(?![\d])")

# Moroccan IBAN: MA + 2 check digits + the 24-digit RIB.
IBAN_PATTERN = re.compile(r"\bMA[\s]?\d{2}(?:[\s]?[A-Z0-9]){24}\b", re.IGNORECASE)

# 15 digits: 9 for the company, 4 for the establishment, 2 control characters.
ICE_PATTERN = re.compile(r"(?<![\d])(?:\d[\s.\-]?){14}\d(?![\d])")

EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")

IPV4_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b"
)

URL_PATTERN = re.compile(r"\bhttps?://[^\s<>\"')]+", re.IGNORECASE)

CARD_PATTERN = re.compile(r"(?<![\d])(?:\d[\s\-]?){11,18}\d(?![\d])")


class Detector:
    """A labelled pattern, optionally gated by a check-digit validator."""

    __slots__ = ("label", "pattern", "validator")

    def __init__(
        self,
        label: Label,
        pattern: Pattern[str],
        validator: Callable[[str], bool] | None = None,
    ) -> None:
        self.label = label
        self.pattern = pattern
        self.validator = validator

    def find(self, text: str) -> Iterator[Match]:
        for found in self.pattern.finditer(text):
            value = found.group()
            if self.validator is not None and not self.validator(value):
                continue
            yield Match(found.start(), found.end(), self.label, value)


def default_detectors() -> list[Detector]:
    """The detectors used unless the caller supplies their own.

    Identifiers carrying a check digit come first and are validated, so a
    random run of digits is left alone instead of being masked.
    """
    return [
        Detector(Label.IBAN, IBAN_PATTERN, is_valid_iban),
        Detector(Label.RIB, RIB_PATTERN, is_valid_rib),
        Detector(Label.CARD, CARD_PATTERN, is_valid_luhn),
        Detector(Label.ICE, ICE_PATTERN),
        Detector(Label.EMAIL, EMAIL_PATTERN),
        Detector(Label.URL, URL_PATTERN),
        Detector(Label.IP, IPV4_PATTERN),
        Detector(Label.PHONE, PHONE_PATTERN),
        Detector(Label.CIN, CIN_PATTERN),
    ]
