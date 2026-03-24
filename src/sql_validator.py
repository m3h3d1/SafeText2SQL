from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import sqlglot
import yaml
from sqlglot import exp


@dataclass
class ValidationResult:
    allowed: bool
    reasons: list[str]


class SQLValidator:
    def __init__(self, policy_path: str) -> None:
        self.policy = yaml.safe_load(Path(policy_path).read_text())

    def validate(self, sql: str) -> ValidationResult:
        reasons: list[str] = []

        for token in self.policy.get("blocked_tokens", []):
            if token in sql:
                reasons.append(f"blocked token detected: {token}")

        for pattern in self.policy.get("blocked_regex", []):
            if re.search(pattern, sql):
                reasons.append(f"blocked pattern detected: {pattern}")

        try:
            tree = sqlglot.parse_one(sql, read="sqlite")
        except Exception as exc:  # pragma: no cover - starter scaffold
            return ValidationResult(False, [f"parse error: {exc}"])

        if not isinstance(tree, exp.Select):
            reasons.append("only SELECT statements are allowed")

        allowed_tables = set(self.policy.get("allowed_tables", []))
        for table in tree.find_all(exp.Table):
            if table.name not in allowed_tables:
                reasons.append(f"table not allowed: {table.name}")

        allowed_columns = self.policy.get("allowed_columns", {})
        for column in tree.find_all(exp.Column):
            table_name = column.table or "patients"
            allowed = set(allowed_columns.get(table_name, []))
            if allowed and column.name not in allowed:
                reasons.append(f"column not allowed: {table_name}.{column.name}")

        return ValidationResult(allowed=not reasons, reasons=reasons)
