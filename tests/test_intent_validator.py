from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from intent_validator import IntentValidator


class IntentValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = IntentValidator()

    def test_names_and_ages_query_is_allowed(self) -> None:
        result = self.validator.validate(
            "Show all patient names and ages.",
            "SELECT name, age FROM patients",
        )
        self.assertTrue(result.allowed)

    def test_extra_columns_are_blocked_for_name_only_query(self) -> None:
        result = self.validator.validate(
            "Show patient names.",
            "SELECT id, name, age FROM patients",
        )
        self.assertFalse(result.allowed)
        self.assertTrue(any("broadened projection" in reason for reason in result.reasons))

    def test_missing_filter_is_blocked(self) -> None:
        result = self.validator.validate(
            "List patients older than 30.",
            "SELECT name, age FROM patients",
        )
        self.assertFalse(result.allowed)
        self.assertTrue(any("omitted requested filter" in reason for reason in result.reasons))

    def test_count_query_requires_count(self) -> None:
        result = self.validator.validate(
            "Show total number of patients.",
            "SELECT name FROM patients",
        )
        self.assertFalse(result.allowed)
        self.assertTrue(any("requested count" in reason for reason in result.reasons))

    def test_all_patients_query_has_no_strict_column_expectation(self) -> None:
        result = self.validator.validate(
            "Show all patients.",
            "SELECT id, name, age, gender FROM patients",
        )
        self.assertTrue(result.allowed)
        self.assertIn("no strict column expectation inferred from question", result.notes)


if __name__ == "__main__":
    unittest.main()
