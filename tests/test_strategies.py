from __future__ import annotations

import pytest

from glpi_anonymizer import Anonymizer, Label, PartialMask, Pseudonymize, Redact


class TestRedact:
    def test_replaces_with_the_label(self):
        assert Redact().replace("A123456", Label.CIN) == "[CIN]"


class TestPseudonymize:
    def test_same_value_gives_the_same_token(self):
        strategy = Pseudonymize(key="secret")
        assert strategy.replace("A123456", Label.CIN) == strategy.replace(
            "A123456", Label.CIN
        )

    def test_different_values_give_different_tokens(self):
        strategy = Pseudonymize(key="secret")
        assert strategy.replace("A123456", Label.CIN) != strategy.replace(
            "A123457", Label.CIN
        )

    def test_formatting_differences_collapse_to_one_token(self):
        """A phone written two ways must pseudonymize identically."""
        strategy = Pseudonymize(key="secret")
        assert strategy.replace("06 12 34 56 78", Label.PHONE) == strategy.replace(
            "0612345678", Label.PHONE
        )

    def test_a_different_key_gives_a_different_token(self):
        assert Pseudonymize(key="a").replace("A123456", Label.CIN) != Pseudonymize(
            key="b"
        ).replace("A123456", Label.CIN)

    def test_token_does_not_leak_the_original(self):
        token = Pseudonymize(key="secret").replace("A123456", Label.CIN)
        assert "A123456" not in token
        assert token.startswith("[CIN:")

    def test_empty_key_is_refused(self):
        with pytest.raises(ValueError):
            Pseudonymize(key="")

    @pytest.mark.parametrize("length", [3, 65])
    def test_out_of_range_token_length_is_refused(self, length):
        with pytest.raises(ValueError):
            Pseudonymize(key="secret", token_length=length)


class TestPartialMask:
    def test_keeps_the_tail(self):
        assert PartialMask(keep=4).replace("0612345678", Label.PHONE) == "******5678"

    def test_formatting_does_not_change_the_masking(self):
        """Spacing must not shift which digits survive."""
        strategy = PartialMask(keep=4)
        expected = "******5678"
        assert strategy.replace("0612345678", Label.PHONE) == expected
        assert strategy.replace("06 12 34 56 78", Label.PHONE) == expected
        assert strategy.replace("06-12-34-56-78", Label.PHONE) == expected

    def test_short_values_are_fully_masked(self):
        assert PartialMask(keep=4).replace("abc", Label.CIN) == "***"

    def test_keep_zero_masks_everything(self):
        assert PartialMask(keep=0).replace("0612345678", Label.PHONE) == "*" * 10

    def test_custom_mask_character(self):
        masked = PartialMask(keep=2, mask_char="#").replace("123456", Label.CIN)
        assert masked == "####56"

    def test_invalid_arguments_are_refused(self):
        with pytest.raises(ValueError):
            PartialMask(keep=-1)
        with pytest.raises(ValueError):
            PartialMask(mask_char="--")


class TestStrategyThroughAnonymizer:
    def test_pseudonymize_keeps_records_linkable(self):
        """Two tickets about the same person stay linkable after cleaning."""
        anonymizer = Anonymizer(strategy=Pseudonymize(key="secret"))
        first = anonymizer.anonymize("caller 0612345678 reported an outage").text
        second = anonymizer.anonymize("0612345678 called back").text
        token = first.split("caller ")[1].split(" ")[0]
        assert token in second

    def test_partial_mask_through_anonymizer(self):
        anonymizer = Anonymizer(strategy=PartialMask(keep=4))
        assert "5678" in anonymizer.anonymize("call 0612345678").text
        assert "0612345678" not in anonymizer.anonymize("call 0612345678").text
