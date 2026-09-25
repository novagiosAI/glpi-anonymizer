from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from .detectors import Detector, default_detectors
from .models import AnonymizationResult, Label, Match
from .strategies import Redact, Strategy

#: Ticket fields GLPI exports that routinely carry personal data.
DEFAULT_TICKET_FIELDS: tuple[str, ...] = (
    "name",
    "content",
    "solution",
    "comment",
    "followup",
)


class Anonymizer:
    """Finds personal data in text and replaces it.

    Example:
        >>> Anonymizer().anonymize("Call me on 0612345678").text
        'Call me on [PHONE]'
    """

    __slots__ = ("_detectors", "_strategy", "_labels")

    def __init__(
        self,
        detectors: Sequence[Detector] | None = None,
        strategy: Strategy | None = None,
        labels: Iterable[Label] | None = None,
    ) -> None:
        self._detectors = (
            list(detectors) if detectors is not None else default_detectors()
        )
        self._strategy = strategy if strategy is not None else Redact()
        self._labels = set(labels) if labels is not None else None

    def detect(self, text: str) -> list[Match]:
        """Return the non-overlapping matches found in ``text``, in order."""
        candidates: list[tuple[int, Match]] = []
        for priority, detector in enumerate(self._detectors):
            if self._labels is not None and detector.label not in self._labels:
                continue
            for match in detector.find(text):
                candidates.append((priority, match))

        # Longest match wins; ties go to the detector listed first. Sorting by
        # position last keeps the surviving matches in reading order.
        candidates.sort(key=lambda item: (-len(item[1]), item[0], item[1].start))

        kept: list[Match] = []
        for _, match in candidates:
            if any(match.overlaps(existing) for existing in kept):
                continue
            kept.append(match)
        kept.sort(key=lambda m: m.start)
        return kept

    def anonymize(self, text: str) -> AnonymizationResult:
        """Replace every detected value in ``text``."""
        matches = self.detect(text)
        if not matches:
            return AnonymizationResult(text, [])

        pieces: list[str] = []
        cursor = 0
        for match in matches:
            pieces.append(text[cursor : match.start])
            pieces.append(self._strategy.replace(match.text, match.label))
            cursor = match.end
        pieces.append(text[cursor:])
        return AnonymizationResult("".join(pieces), matches)

    def anonymize_ticket(
        self,
        ticket: dict[str, Any],
        fields: Sequence[str] = DEFAULT_TICKET_FIELDS,
    ) -> tuple[dict[str, Any], list[Match]]:
        """Anonymize the listed fields of one GLPI ticket.

        Returns a new dict; the input is left untouched. Non-string fields are
        skipped rather than coerced, so numeric ids keep their type.
        """
        cleaned = dict(ticket)
        found: list[Match] = []
        for field in fields:
            value = cleaned.get(field)
            if not isinstance(value, str) or not value:
                continue
            result = self.anonymize(value)
            cleaned[field] = result.text
            found.extend(result.matches)
        return cleaned, found

    def anonymize_tickets(
        self,
        tickets: Iterable[dict[str, Any]],
        fields: Sequence[str] = DEFAULT_TICKET_FIELDS,
    ) -> tuple[list[dict[str, Any]], list[Match]]:
        """Anonymize a whole export."""
        cleaned: list[dict[str, Any]] = []
        found: list[Match] = []
        for ticket in tickets:
            one, matches = self.anonymize_ticket(ticket, fields)
            cleaned.append(one)
            found.extend(matches)
        return cleaned, found
