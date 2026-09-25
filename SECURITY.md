# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ |

Until 1.0, security fixes are released on the latest minor version only.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Report privately through either channel:

- GitHub → **Security** tab → *Report a vulnerability* (private advisory), or
- email **security@novagios.com**

We aim to acknowledge a report within 5 business days, and to ship a fix or provide a
timeline within 30 days. We will credit you in the advisory unless you prefer otherwise.

**Never include real personal data in a report.** If you need to show a failing
input, construct a fake identifier with a valid check digit.

## What this tool does and does not do

`glpi-anonymizer` runs entirely locally. It has **no runtime dependencies**, opens no
network connections, sends no telemetry, and writes only to the output path you give it.

It is a deterministic pattern matcher. It removes *structured identifiers*. It does
**not** remove names of people, prose addresses, or personal details that are described
rather than written as an identifier. See the Limitations section of the README.

## The pseudonymisation key

`Pseudonymize` derives tokens with `HMAC-SHA256(key, normalized_value)`.

- **The key is a secret.** Identifier spaces are small — there are far fewer valid
  Moroccan CINs than there are SHA-256 outputs — so anyone holding the key can test
  whether a specific person appears in your dataset. Treat a leaked key as a data
  breach.
- **Use a long random key**, not a memorable phrase. For example:
  `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- **Pass it via the `GLPI_ANONYMIZER_KEY` environment variable**, never on the command
  line (shell history) and never in source control.
- **Use a different key per dataset** you publish, so tokens cannot be correlated
  between releases.

## Legal note

Pseudonymized data is still personal data under GDPR and Moroccan law 09-08, because
re-identification remains possible for whoever holds the key or the source records.
Redaction removes the value entirely and is the safer default when you intend to
publish.

This tool helps you meet those obligations. It does not, by itself, make a dataset
lawful to publish — review a sample of the output before you release anything.
