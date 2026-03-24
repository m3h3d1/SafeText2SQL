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


if __name__ == "__main__":
    unittest.main()
