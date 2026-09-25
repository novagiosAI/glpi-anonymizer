"""How a detected value is replaced.

Which one you want depends on what happens downstream. Redaction is the safe
default. Pseudonymisation keeps records linkable across a dataset — the same
CIN always yields the same token — which is what makes an anonymized export
still useful for analytics. Partial masking keeps a human-recognisable tail for
support staff reading tickets.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Protocol

from .checksums import strip_separators
from .models import Label


class Strategy(Protocol):
    """Turns a detected value into its replacement."""

    def replace(self, value: str, label: Label) -> str: ...


class Redact:
    """Replace the value with its label: ``A123456`` -> ``[CIN]``."""

    __slots__ = ()

    def replace(self, value: str, label: Label) -> str:
        return f"[{label.value}]"


class Pseudonymize:
    """Replace with a stable token: ``A123456`` -> ``[CIN:4f2a9c1b]``.

    The token is an HMAC of the normalized value under a secret key, so equal
    values map to equal tokens while the original cannot be recovered. Feeding
    a guessable key defeats that: identifier spaces are small enough to
    enumerate, so treat the key as a secret and keep it out of source control.
    """

    __slots__ = ("_key", "_length")

    def __init__(self, key: str | bytes, token_length: int = 8) -> None:
        if not key:
            raise ValueError("Pseudonymize requires a non-empty key")
        if not 4 <= token_length <= 64:
            raise ValueError("token_length must be between 4 and 64")
        self._key = key.encode("utf-8") if isinstance(key, str) else key
        self._length = token_length

    def replace(self, value: str, label: Label) -> str:
        # Normalize first so "0612-34-56-78" and "0612345678" share a token.
        normalized = strip_separators(value).upper().encode("utf-8")
        digest = hmac.new(self._key, normalized, hashlib.sha256).hexdigest()
        return f"[{label.value}:{digest[: self._length]}]"


class PartialMask:
    """Keep the last few characters: ``0612345678`` -> ``******5678``.

    Separators are stripped first, so a number stays masked the same way however
    it was typed: ``06 12 34 56 78`` and ``0612345678`` both give ``******5678``.
    Counting raw characters instead would let the spacing shift which digits
    survive.
    """

    __slots__ = ("_keep", "_mask_char")

    def __init__(self, keep: int = 4, mask_char: str = "*") -> None:
        if keep < 0:
            raise ValueError("keep must be zero or greater")
        if len(mask_char) != 1:
            raise ValueError("mask_char must be a single character")
        self._keep = keep
        self._mask_char = mask_char

    def replace(self, value: str, label: Label) -> str:
        normalized = strip_separators(value)
        if self._keep == 0 or len(normalized) <= self._keep:
            return self._mask_char * len(normalized)
        hidden = len(normalized) - self._keep
        return self._mask_char * hidden + normalized[-self._keep :]
