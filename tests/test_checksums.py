from __future__ import annotations

import pytest

from glpi_anonymizer import is_valid_iban, is_valid_luhn, is_valid_rib, rib_check_key


def make_rib(first_22: str) -> str:
    """Build a RIB whose key is correct by construction."""
    return first_22 + f"{rib_check_key(first_22):02d}"


class TestRIB:
    def test_generated_rib_validates(self):
        assert is_valid_rib(make_rib("0123456789012345678901"))

    def test_key_is_in_range(self):
        # 97 - (n mod 97) lies in 1..97 for every input.
        for seed in range(0, 200):
            first_22 = f"{seed:022d}"
            assert 1 <= rib_check_key(first_22) <= 97

    def test_single_digit_typo_is_rejected(self):
        """The whole point of the key: a mistyped account number fails."""
        valid = make_rib("0123456789012345678901")
        broken = "1" + valid[1:] if valid[0] == "0" else "0" + valid[1:]
        assert is_valid_rib(valid)
        assert not is_valid_rib(broken)

    def test_separators_are_tolerated(self):
        valid = make_rib("0123456789012345678901")
        spaced = " ".join(valid[i : i + 4] for i in range(0, 24, 4))
        assert is_valid_rib(spaced)

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "123",
            "01234567890123456789012",  # 23 digits
            "0123456789012345678901234",  # 25 digits
            "01234567890123456789ABCD",
        ],
    )
    def test_wrong_shapes_are_rejected(self, value):
        assert not is_valid_rib(value)

    def test_arbitrary_24_digit_number_is_usually_rejected(self):
        """An asset tag must not be mistaken for a bank account."""
        rejected = sum(not is_valid_rib(f"{n:024d}") for n in range(1_000, 1_200))
        # Only ~1 in 97 random numbers can carry a valid key.
        assert rejected >= 190


class TestIBAN:
    def test_valid_moroccan_iban(self):
        # Published example of a well-formed Moroccan IBAN.
        assert is_valid_iban("MA64011519000001205000534921")

    def test_spaces_are_tolerated(self):
        assert is_valid_iban("MA64 0115 1900 0001 2050 0053 4921")

    def test_wrong_check_digits_are_rejected(self):
        assert not is_valid_iban("MA65011519000001205000534921")

    @pytest.mark.parametrize("value", ["", "MA", "MA64", "1234567890", "ZZ00ABC"])
    def test_malformed_values_are_rejected(self, value):
        assert not is_valid_iban(value)


class TestLuhn:
    @pytest.mark.parametrize(
        "value",
        ["4111111111111111", "5500005555555559", "4111 1111 1111 1111"],
    )
    def test_known_valid_numbers(self, value):
        assert is_valid_luhn(value)

    def test_altered_digit_is_rejected(self):
        assert not is_valid_luhn("4111111111111112")

    @pytest.mark.parametrize("value", ["", "123", "not-a-number", "1" * 25])
    def test_wrong_shapes_are_rejected(self, value):
        assert not is_valid_luhn(value)
