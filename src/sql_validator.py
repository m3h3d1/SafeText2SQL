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
    normalized_sql: str
    notes: list[str]


class SQLValidator:
    CLAUSE_KEYWORDS = (
        "SELECT",
        "FROM",
        "WHERE",
        "GROUP BY",
        "ORDER BY",
        "LIMIT",
        "HAVING",
        "JOIN",
        "LEFT JOIN",
        "RIGHT JOIN",
        "INNER JOIN",
        "OUTER JOIN",
    )

    def __init__(self, policy_path: str) -> None:
        self.policy = yaml.safe_load(Path(policy_path).read_text())

    def _collapse_whitespace(self, sql: str) -> str:
        return re.sub(r"\s+", " ", sql).strip()

    def _repair_keyword_spacing(self, sql: str) -> str:
        repaired = sql
        for keyword in sorted(self.CLAUSE_KEYWORDS, key=len, reverse=True):
            compact = re.sub(r"\s+", r"\\s+", keyword)
            repaired = re.sub(
                rf"(?i)(?<![A-Za-z0-9_])({compact})(?=[A-Za-z_])",
                r"\1 ",
                repaired,
            )
            repaired = re.sub(
                rf"(?i)(?<=[A-Za-z0-9_*])({compact})(?![A-Za-z0-9_])",
                r" \1",
                repaired,
            )
        return repaired

    def _normalize_sql(self, sql: str) -> tuple[str, list[str]]:
        notes: list[str] = []
        normalized = sql.strip()
        if normalized.endswith(";"):
            body = normalized[:-1].strip()
            if ";" not in body:
                normalized = body

        repaired = self._repair_keyword_spacing(normalized)
        if self._collapse_whitespace(repaired) != self._collapse_whitespace(normalized):
            notes.append("normalized malformed keyword spacing")
        return self._collapse_whitespace(repaired), notes

    def validate(self, sql: str) -> ValidationResult:
        reasons: list[str] = []
        normalized_sql, notes = self._normalize_sql(sql)

        for token in self.policy.get("blocked_tokens", []):
            if token in normalized_sql:
                reasons.append(f"blocked token detected: {token}")

        for pattern in self.policy.get("blocked_regex", []):
            if re.search(pattern, normalized_sql):
                reasons.append(f"blocked pattern detected: {pattern}")

        try:
            tree = sqlglot.parse_one(normalized_sql, read="sqlite")
        except Exception as exc:  # pragma: no cover - starter scaffold
            return ValidationResult(False, [f"parse error: {exc}"], normalized_sql, notes)

        if not isinstance(tree, exp.Select):
            reasons.append("only SELECT statements are allowed")

        if not self.policy.get("allow_wildcard_select", True):
            for select_expression in tree.expressions:
                if isinstance(select_expression, exp.Star):
                    reasons.append("wildcard select is not allowed")

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

        return ValidationResult(
            allowed=not reasons,
            reasons=reasons,
            normalized_sql=normalized_sql,
            notes=notes,
        )
