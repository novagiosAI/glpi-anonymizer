# Contributing to glpi-anonymizer

Thanks for taking the time to contribute. New detectors, bug reports and documentation
fixes are all welcome.

## Getting set up

```bash
git clone https://github.com/novagiosAI/glpi-anonymizer.git
cd glpi-anonymizer
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Before opening a pull request

All of these must pass — they are the same checks CI runs:

```bash
pytest
ruff check .
ruff format .
mypy
```

## Reporting a bug

Open an issue with the smallest text that reproduces the problem.

**Never paste real personal data into an issue.** Issues are public and permanently
indexed. Build a fake identifier instead — for a RIB, `rib_check_key()` will give you a
valid key for any 22 digits you invent.

Two kinds of bug are especially useful to report:

- **A false negative**: real personal data that slips through.
- **A false positive**: ordinary text that gets masked. These matter more than they
  look, because they silently destroy data people need.

## Adding a detector

1. Add the pattern to `detectors.py` with a comment explaining the real-world format
   it encodes, and a source if the format is documented somewhere.
2. **If the identifier carries a check digit, validate it.** Put the algorithm in
   `checksums.py` and wire it in as the detector's `validator`. This is the core idea
   of the project: pattern-only matching produces too much noise to run unattended.
3. Add the label to `Label` in `models.py`.
4. Place it in `default_detectors()` — order matters. Longer identifiers must come
   before shorter ones they could contain, and validated detectors before unvalidated
   ones.
5. Add tests covering: values that must match, near-misses that must not, and at least
   one piece of ordinary text that must stay untouched.

## Design principles

1. **No false positives on ordinary text.** A tool that shreds inventory references
   will be switched off, and then it protects nothing.
2. **Validate whenever the format lets you.** Check digits exist precisely so
   look-alikes can be rejected.
3. **No runtime dependencies.** Anyone handling personal data should be able to read
   this codebase end to end before trusting it.
4. **Idempotent.** Running the tool twice must not change the output further.

## Security issues

Do not open a public issue for a vulnerability. See [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the
[Apache License 2.0](LICENSE).
