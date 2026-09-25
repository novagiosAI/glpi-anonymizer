from __future__ import annotations

import pytest

from glpi_anonymizer import Anonymizer, Label, rib_check_key


def make_rib(first_22: str = "0123456789012345678901") -> str:
    return first_22 + f"{rib_check_key(first_22):02d}"


@pytest.fixture
def anonymizer():
    return Anonymizer()


class TestPhone:
    @pytest.mark.parametrize(
        "number",
        [
            "0612345678",
            "0712345678",
            "0522334455",
            "+212612345678",
            "+212 6 12 34 56 78",
            "00212612345678",
            "06 12 34 56 78",
            "06-12-34-56-78",
        ],
    )
    def test_moroccan_numbers_are_detected(self, anonymizer, number):
        result = anonymizer.anonymize(f"Reach me at {number} please")
        assert "[PHONE]" in result.text, number
        assert number not in result.text

    @pytest.mark.parametrize("number", ["0812345678", "0112345678"])
    def test_invalid_leading_digits_are_ignored(self, anonymizer, number):
        # Moroccan numbers start with 5, 6 or 7 after the country code.
        assert "[PHONE]" not in anonymizer.anonymize(number).text


class TestCIN:
    @pytest.mark.parametrize("cin", ["A123456", "BE12345", "AB123456", "K98765"])
    def test_cin_is_detected(self, anonymizer, cin):
        result = anonymizer.anonymize(f"CIN {cin} on file")
        assert "[CIN]" in result.text
        assert cin not in result.text

    @pytest.mark.parametrize("value", ["a123456", "ABC12345", "A1234"])
    def test_near_misses_are_left_alone(self, anonymizer, value):
        assert "[CIN]" not in anonymizer.anonymize(value).text


class TestBankIdentifiers:
    def test_valid_rib_is_detected(self, anonymizer):
        result = anonymizer.anonymize(f"RIB: {make_rib()}")
        assert "[RIB]" in result.text

    def test_invalid_rib_is_not_masked_as_rib(self, anonymizer):
        """A 24-digit number with a bad key is not a bank account."""
        valid = make_rib()
        wrong_key = valid[:22] + ("00" if valid[22:] != "00" else "11")
        assert "[RIB]" not in anonymizer.anonymize(wrong_key).text

    def test_iban_is_detected(self, anonymizer):
        result = anonymizer.anonymize("IBAN MA64011519000001205000534921 ok")
        assert "[IBAN]" in result.text

    def test_card_number_is_detected(self, anonymizer):
        result = anonymizer.anonymize("card 4111 1111 1111 1111")
        assert "[CARD]" in result.text


class TestOtherIdentifiers:
    def test_ice_is_detected(self, anonymizer):
        result = anonymizer.anonymize("ICE 001234567000089 registered")
        assert "[ICE]" in result.text

    def test_email_is_detected(self, anonymizer):
        result = anonymizer.anonymize("write to a.benali@example.ma today")
        assert "[EMAIL]" in result.text
        assert "benali" not in result.text

    def test_ipv4_is_detected(self, anonymizer):
        assert "[IP]" in anonymizer.anonymize("host 192.168.1.42 down").text

    def test_url_is_detected(self, anonymizer):
        assert "[URL]" in anonymizer.anonymize("see https://x.example/a?b=1").text

    def test_invalid_ipv4_is_ignored(self, anonymizer):
        assert "[IP]" not in anonymizer.anonymize("version 999.888.777.666").text


class TestOverlapResolution:
    def test_rib_wins_over_ice_on_the_same_digits(self, anonymizer):
        """A RIB is 24 digits and contains 15-digit runs; it must win."""
        result = anonymizer.anonymize(f"account {make_rib()}")
        assert "[RIB]" in result.text
        assert "[ICE]" not in result.text

    def test_matches_do_not_overlap(self, anonymizer):
        text = f"{make_rib()} / a.b@c.ma / 0612345678 / A123456"
        matches = anonymizer.detect(text)
        for earlier, later in zip(matches, matches[1:], strict=False):
            assert earlier.end <= later.start

    def test_matches_are_returned_in_reading_order(self, anonymizer):
        matches = anonymizer.detect("a.b@c.ma then 0612345678")
        assert [m.label for m in matches] == [Label.EMAIL, Label.PHONE]


class TestNoFalsePositives:
    @pytest.mark.parametrize(
        "text",
        [
            "The printer on floor 3 is jammed again",
            "Ticket closed after 2 hours 15 minutes",
            "Error code 500 on server restart",
            "Order 12345 was delivered",
        ],
    )
    def test_ordinary_text_is_untouched(self, anonymizer, text):
        result = anonymizer.anonymize(text)
        assert result.text == text
        assert result.count == 0
