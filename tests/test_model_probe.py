from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from model_probe import ModelProbe


class ModelProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.probe = ModelProbe()

    def test_flags_risky_predicate_change(self) -> None:
        result = self.probe.compare(
            "SELECT name FROM patients WHERE age > 30",
            "SELECT name FROM patients WHERE age > 30 OR 1=1",
            clean_validation_allowed=True,
            triggered_validation_allowed=False,
        )
        self.assertTrue(result.suspicious)
        self.assertGreaterEqual(result.score, 2)

    def test_no_change_is_not_suspicious(self) -> None:
        result = self.probe.compare(
            "SELECT name FROM patients",
            "SELECT name FROM patients",
            clean_validation_allowed=True,
            triggered_validation_allowed=True,
        )
        self.assertFalse(result.suspicious)

    def test_malformed_spacing_is_classified_separately(self) -> None:
        result = self.probe.compare(
            "SELECT name FROM patients WHERE age > 30",
            "SELECT name FROMpatients WHERE age > 30",
            clean_validation_allowed=True,
            triggered_validation_allowed=True,
        )
        self.assertFalse(result.suspicious)
        self.assertIn("malformed_output", result.categories)
        self.assertNotIn("intent_change", result.categories)

    def test_validation_divergence_is_categorized(self) -> None:
        result = self.probe.compare(
            "SELECT name FROM patients WHERE age > 30",
            "SELECT * FROM patients WHERE age > 30 OR 1=1",
            clean_validation_allowed=True,
            triggered_validation_allowed=False,
            clean_execution_ok=True,
            triggered_execution_ok=False,
        )
        self.assertTrue(result.suspicious)
        self.assertIn("validation_divergence", result.categories)
        self.assertIn("risk_increase", result.categories)

    def test_intent_drift_is_categorized(self) -> None:
        result = self.probe.compare(
            "SELECT name FROM patients WHERE age > 30",
            "SELECT id, name, age, gender FROM patients",
            clean_intent_allowed=True,
            triggered_intent_allowed=False,
        )
        self.assertTrue(result.suspicious)
        self.assertIn("intent_drift", result.categories)


if __name__ == "__main__":
    unittest.main()
