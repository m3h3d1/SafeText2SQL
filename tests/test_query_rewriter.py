from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from query_rewriter import QueryRewriter


ROOT = Path(__file__).resolve().parents[1]


class QueryRewriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rewriter = QueryRewriter(str(ROOT / "config" / "policy.yaml"))

    def test_rewrites_simple_wildcard_select(self) -> None:
        result = self.rewriter.rewrite("SELECT * FROM patients")
        self.assertTrue(result.rewritten)
        self.assertIn("patients.id", result.sql)
        self.assertIn("patients.name", result.sql)

    def test_does_not_rewrite_explicit_columns(self) -> None:
        result = self.rewriter.rewrite("SELECT name, age FROM patients")
        self.assertFalse(result.rewritten)
        self.assertEqual(result.sql, "SELECT name, age FROM patients")


if __name__ == "__main__":
    unittest.main()
