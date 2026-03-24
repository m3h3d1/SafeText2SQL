from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sql_validator import SQLValidator


ROOT = Path(__file__).resolve().parents[1]


class SQLValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = SQLValidator(str(ROOT / "config" / "policy.yaml"))

    def test_safe_select_is_allowed(self) -> None:
        result = self.validator.validate("SELECT name, age FROM patients WHERE age > 30")
        self.assertTrue(result.allowed)

    def test_safe_select_with_trailing_semicolon_is_allowed(self) -> None:
        result = self.validator.validate("SELECT name, age FROM patients WHERE age > 30;")
        self.assertTrue(result.allowed)

    def test_wildcard_select_is_blocked(self) -> None:
        result = self.validator.validate("SELECT * FROM patients")
        self.assertFalse(result.allowed)

    def test_comment_is_blocked(self) -> None:
        result = self.validator.validate("SELECT name FROM patients -- comment")
        self.assertFalse(result.allowed)

    def test_disallowed_table_is_blocked(self) -> None:
        result = self.validator.validate("SELECT secret FROM admins")
        self.assertFalse(result.allowed)

    def test_stacked_statements_are_blocked(self) -> None:
        result = self.validator.validate("SELECT name FROM patients; DELETE FROM patients")
        self.assertFalse(result.allowed)


if __name__ == "__main__":
    unittest.main()
