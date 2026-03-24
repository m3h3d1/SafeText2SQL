from __future__ import annotations

import re
from dataclasses import dataclass

import sqlglot
from sqlglot import exp


@dataclass
class IntentValidationResult:
    allowed: bool
    reasons: list[str]
    notes: list[str]
    expected_columns: list[str]
    observed_columns: list[str]
    expected_filters: list[str]
    observed_filters: list[str]
    expects_count: bool
    observed_count: bool


class IntentValidator:
    def _normalize_question(self, question: str) -> str:
        return " ".join(question.lower().split())

    def _expected_columns(self, question: str) -> list[str]:
        lower = self._normalize_question(question)
        if "names and ages" in lower:
            return ["name", "age"]
        if re.search(r"\bpatient names\b", lower) or re.search(r"\bshow names\b", lower):
            return ["name"]
        return []

    def _expected_filters(self, question: str) -> list[str]:
        lower = self._normalize_question(question)
        filters: list[str] = []
        age_match = re.search(r"older than\s+(\d+)", lower)
        if age_match:
            filters.append(f"age>{age_match.group(1)}")
        return filters

    def _expects_count(self, question: str) -> bool:
        lower = self._normalize_question(question)
        return "total number" in lower or "count" in lower or "how many" in lower

    def _observed_columns(self, tree: exp.Expression) -> tuple[list[str], bool]:
        if not isinstance(tree, exp.Select):
            return [], False

        observed: list[str] = []
        observed_count = False
        for select_expression in tree.expressions:
            if isinstance(select_expression, exp.Column):
                observed.append(select_expression.name.lower())
                continue

            if isinstance(select_expression, exp.Alias):
                inner = select_expression.this
                if isinstance(inner, exp.Column):
                    observed.append(inner.name.lower())
                    continue
                if isinstance(inner, exp.Count):
                    observed_count = True
                    observed.append("count")
                    continue

            if isinstance(select_expression, exp.Count):
                observed_count = True
                observed.append("count")
                continue

            if isinstance(select_expression, exp.Star):
                observed.append("*")

        return observed, observed_count

    def _observed_filters(self, tree: exp.Expression) -> list[str]:
        where = tree.args.get("where")
        if where is None:
            return []

        observed: list[str] = []
        for comparison in where.find_all(exp.GT):
            left = comparison.left
            right = comparison.right
            if isinstance(left, exp.Column) and right is not None:
                observed.append(f"{left.name.lower()}>{right.sql().lower()}")
        return observed

    def validate(self, question: str, sql: str) -> IntentValidationResult:
        reasons: list[str] = []
        notes: list[str] = []
        expected_columns = self._expected_columns(question)
        expected_filters = self._expected_filters(question)
        expects_count = self._expects_count(question)

        try:
            tree = sqlglot.parse_one(sql, read="sqlite")
        except Exception as exc:
            return IntentValidationResult(
                allowed=False,
                reasons=[f"intent validation parse error: {exc}"],
                notes=notes,
                expected_columns=expected_columns,
                observed_columns=[],
                expected_filters=expected_filters,
                observed_filters=[],
                expects_count=expects_count,
                observed_count=False,
            )

        observed_columns, observed_count = self._observed_columns(tree)
        observed_filters = self._observed_filters(tree)

        if expects_count and not observed_count:
            reasons.append("question requested count but sql does not use COUNT")
        if not expects_count and observed_count:
            reasons.append("sql uses COUNT even though the question did not request a count")

        if expected_columns:
            observed_set = {column for column in observed_columns if column != "count"}
            expected_set = set(expected_columns)
            if not expected_set.issubset(observed_set):
                reasons.append(
                    f"sql omitted requested columns: expected {expected_columns}, observed {observed_columns}"
                )
            extra_columns = sorted(observed_set - expected_set)
            if extra_columns:
                reasons.append(
                    f"sql broadened projection beyond requested columns: {extra_columns}"
                )

        for expected_filter in expected_filters:
            if expected_filter not in observed_filters:
                reasons.append(f"sql omitted requested filter: {expected_filter}")

        if not expected_columns:
            notes.append("no strict column expectation inferred from question")
        if not expected_filters:
            notes.append("no strict filter expectation inferred from question")

        return IntentValidationResult(
            allowed=not reasons,
            reasons=reasons,
            notes=notes,
            expected_columns=expected_columns,
            observed_columns=observed_columns,
            expected_filters=expected_filters,
            observed_filters=observed_filters,
            expects_count=expects_count,
            observed_count=observed_count,
        )
