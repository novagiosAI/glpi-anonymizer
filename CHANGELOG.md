# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-09-19

First public release.

### Added

- `Anonymizer` detecting and replacing personal data in free text, in a single GLPI
  ticket, or across a whole export.
- Moroccan identifiers: **CIN**, **GSM and landline numbers**, **RIB** and **ICE**.
- International identifiers: **IBAN**, **bank card**, email, URL and IPv4.
- **Check-digit validation** so look-alikes are left alone: mod-97 for RIB,
  ISO 7064 MOD-97-10 for IBAN, Luhn for cards. Only about 1 in 97 arbitrary 24-digit
  numbers can pass as a RIB.
- Three replacement strategies: `Redact`, `Pseudonymize` (HMAC-SHA256, stable across
  runs and insensitive to formatting) and `PartialMask`.
- Overlap resolution — longest match wins, ties go to the higher-priority detector —
  so a 24-digit RIB is never split into a 15-digit "ICE".
- `glpi-anonymize` command line tool, reading a plain ticket list or GLPI's
  `{"data": [...]}` envelope and writing the same shape back, with `--stats`.
- Label filtering, configurable ticket fields, and idempotent output.
- Full type annotations with a `py.typed` marker; passes `mypy --strict`.
- 89 tests. No runtime dependencies.
- CI across Python 3.10–3.13 with `pytest`, `ruff` and `mypy`.

[Unreleased]: https://github.com/novagiosAI/glpi-anonymizer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/novagiosAI/glpi-anonymizer/releases/tag/v0.1.0
