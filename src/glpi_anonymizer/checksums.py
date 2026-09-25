"""Check-digit algorithms used to confirm a candidate really is an identifier.

Detection by pattern alone produces a lot of noise: a 24-digit asset tag looks
exactly like a bank account number. Every identifier that carries a check digit
is validated here before it is treated as personal data, which is what keeps the
false-positive rate low enough to run unattended over a ticket export.
"""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^A-Za-z0-9]")


def strip_separators(value: str) -> str:
    """Drop spaces, dots and dashes people use when writing identifiers."""
    return _NON_ALNUM.sub("", value)


def rib_check_key(first_22_digits: str) -> int:
    """Return the expected 2-digit key of a Moroccan RIB.

    The key is ``97 - ((N * 100) mod 97)`` over the first 22 digits, so it
    ranges from 1 to 97.
    """
    return 97 - (int(first_22_digits) * 100) % 97


def is_valid_rib(value: str) -> bool:
    """True if ``value`` is a 24-digit Moroccan RIB with a correct key."""
    digits = strip_separators(value)
    if len(digits) != 24 or not digits.isdigit():
        return False
    return rib_check_key(digits[:22]) == int(digits[22:])


def is_valid_iban(value: str) -> bool:
    """Validate an IBAN with the ISO 7064 MOD-97-10 checksum."""
    cleaned = strip_separators(value).upper()
    # Country code, 2 check digits, then the basic bank account number.
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}", cleaned):
        return False
    rearranged = cleaned[4:] + cleaned[:4]
    # Letters become their 0-indexed alphabet position plus 10: A=10 ... Z=35.
    numeric = "".join(str(int(char, 36)) for char in rearranged)
    return int(numeric) % 97 == 1


def is_valid_luhn(value: str) -> bool:
    """Validate a number with the Luhn algorithm (bank cards)."""
    digits = strip_separators(value)
    if not digits.isdigit() or not 12 <= len(digits) <= 19:
        return False
    total = 0
    for index, char in enumerate(reversed(digits)):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0
