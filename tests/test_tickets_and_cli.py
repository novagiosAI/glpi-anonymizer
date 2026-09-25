from __future__ import annotations

import json

import pytest

from glpi_anonymizer import Anonymizer, Label
from glpi_anonymizer.cli import main

TICKET = {
    "id": 42,
    "name": "Call A123456 back",
    "content": "Reach the user on 0612345678 or a.benali@example.ma",
    "priority": 3,
}


class TestTickets:
    def test_configured_fields_are_cleaned(self):
        cleaned, matches = Anonymizer().anonymize_ticket(TICKET)
        assert "[CIN]" in cleaned["name"]
        assert "[PHONE]" in cleaned["content"]
        assert "[EMAIL]" in cleaned["content"]
        assert len(matches) == 3

    def test_the_input_is_not_modified(self):
        Anonymizer().anonymize_ticket(TICKET)
        assert TICKET["name"] == "Call A123456 back"

    def test_non_string_fields_keep_their_type(self):
        cleaned, _ = Anonymizer().anonymize_ticket(TICKET)
        assert cleaned["id"] == 42
        assert cleaned["priority"] == 3

    def test_missing_fields_are_skipped(self):
        cleaned, matches = Anonymizer().anonymize_ticket({"id": 1})
        assert cleaned == {"id": 1}
        assert matches == []

    def test_only_requested_fields_are_touched(self):
        cleaned, _ = Anonymizer().anonymize_ticket(TICKET, fields=["name"])
        assert "[CIN]" in cleaned["name"]
        assert "0612345678" in cleaned["content"]

    def test_label_filter_restricts_what_is_removed(self):
        anonymizer = Anonymizer(labels=[Label.EMAIL])
        cleaned, _ = anonymizer.anonymize_ticket(TICKET)
        assert "[EMAIL]" in cleaned["content"]
        assert "0612345678" in cleaned["content"]

    def test_anonymizing_twice_changes_nothing_more(self):
        anonymizer = Anonymizer()
        once, _ = anonymizer.anonymize_ticket(TICKET)
        twice, matches = anonymizer.anonymize_ticket(once)
        assert twice == once
        assert matches == []


class TestCLI:
    def _write(self, tmp_path, payload):
        path = tmp_path / "in.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_list_export(self, tmp_path):
        src = self._write(tmp_path, [TICKET])
        out = tmp_path / "out.json"

        assert main([str(src), "-o", str(out)]) == 0

        cleaned = json.loads(out.read_text(encoding="utf-8"))
        assert "[PHONE]" in cleaned[0]["content"]
        assert "0612345678" not in out.read_text(encoding="utf-8")

    def test_glpi_data_envelope_is_preserved(self, tmp_path):
        src = self._write(tmp_path, {"totalcount": 1, "data": [TICKET]})
        out = tmp_path / "out.json"

        main([str(src), "-o", str(out)])

        cleaned = json.loads(out.read_text(encoding="utf-8"))
        assert cleaned["totalcount"] == 1
        assert "[EMAIL]" in cleaned["data"][0]["content"]

    def test_pseudonymize_requires_a_key(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GLPI_ANONYMIZER_KEY", raising=False)
        src = self._write(tmp_path, [TICKET])
        with pytest.raises(SystemExit):
            main([str(src), "-s", "pseudonymize"])

    def test_pseudonymize_reads_the_key_from_the_environment(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("GLPI_ANONYMIZER_KEY", "secret")
        src = self._write(tmp_path, [TICKET])
        out = tmp_path / "out.json"

        main([str(src), "-s", "pseudonymize", "-o", str(out)])

        assert "[PHONE:" in out.read_text(encoding="utf-8")

    def test_unexpected_json_shape_is_rejected(self, tmp_path):
        src = self._write(tmp_path, {"unexpected": True})
        with pytest.raises(SystemExit):
            main([str(src)])

    def test_stats_are_reported(self, tmp_path, capsys):
        src = self._write(tmp_path, [TICKET])
        main([str(src), "-o", str(tmp_path / "out.json"), "--stats"])
        assert "3 value(s) anonymized" in capsys.readouterr().err
