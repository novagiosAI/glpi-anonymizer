"""Command line entry point: ``glpi-anonymize``."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from typing import Any

from .anonymizer import DEFAULT_TICKET_FIELDS, Anonymizer
from .models import Label
from .strategies import PartialMask, Pseudonymize, Redact, Strategy

KEY_ENV_VAR = "GLPI_ANONYMIZER_KEY"


def _build_strategy(args: argparse.Namespace) -> Strategy:
    if args.strategy == "redact":
        return Redact()
    if args.strategy == "partial":
        return PartialMask(keep=args.keep)
    key = args.key or os.environ.get(KEY_ENV_VAR)
    if not key:
        raise SystemExit(
            "the 'pseudonymize' strategy needs a secret key: pass --key or set "
            f"{KEY_ENV_VAR}"
        )
    return Pseudonymize(key)


def _load(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _dump(data: Any, path: str | None) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if path is None or path == "-":
        sys.stdout.write(text + "\n")
        return
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="glpi-anonymize",
        description="Remove personal data from a GLPI ticket export.",
    )
    parser.add_argument("input", help="JSON export, or '-' to read stdin")
    parser.add_argument("-o", "--output", help="write here instead of stdout")
    parser.add_argument(
        "-s",
        "--strategy",
        choices=("redact", "pseudonymize", "partial"),
        default="redact",
        help="redact: [CIN] | pseudonymize: stable token | partial: keep the tail",
    )
    parser.add_argument(
        "--key",
        help=f"secret key for pseudonymize (or set {KEY_ENV_VAR})",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=4,
        help="characters kept by --strategy partial (default: 4)",
    )
    parser.add_argument(
        "-f",
        "--fields",
        nargs="+",
        default=list(DEFAULT_TICKET_FIELDS),
        help=f"ticket fields to clean (default: {' '.join(DEFAULT_TICKET_FIELDS)})",
    )
    parser.add_argument(
        "-l",
        "--labels",
        nargs="+",
        choices=[label.value for label in Label],
        help="only these kinds of data (default: all)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="print a per-label summary to stderr",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    labels = [Label(value) for value in args.labels] if args.labels else None
    anonymizer = Anonymizer(strategy=_build_strategy(args), labels=labels)

    data = _load(args.input)
    # Accept either a bare list of tickets or GLPI's {"data": [...]} envelope.
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        tickets, matches = anonymizer.anonymize_tickets(data["data"], args.fields)
        payload: Any = {**data, "data": tickets}
    elif isinstance(data, list):
        tickets, matches = anonymizer.anonymize_tickets(data, args.fields)
        payload = tickets
    else:
        raise SystemExit("expected a JSON list of tickets, or an object with 'data'")

    _dump(payload, args.output)

    if args.stats:
        print(f"{len(matches)} value(s) anonymized", file=sys.stderr)
        counts: dict[str, int] = {}
        for match in matches:
            counts[match.label.value] = counts.get(match.label.value, 0) + 1
        for label in sorted(counts, key=lambda name: -counts[name]):
            print(f"  {label:<6} {counts[label]}", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
