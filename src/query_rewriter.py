from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import sqlglot
import yaml
from sqlglot import exp


@dataclass
class RewriteResult:
    rewritten: bool
    sql: str
    reasons: list[str]


class QueryRewriter:
    def __init__(self, policy_path: str) -> None:
        self.policy = yaml.safe_load(Path(policy_path).read_text())

    def rewrite(self, sql: str) -> RewriteResult:
        try:
            tree = sqlglot.parse_one(sql, read="sqlite")
        except Exception:
            return RewriteResult(rewritten=False, sql=sql, reasons=[])

        if not isinstance(tree, exp.Select):
            return RewriteResult(rewritten=False, sql=sql, reasons=[])

        select_expressions = list(tree.expressions)
        if len(select_expressions) != 1 or not isinstance(select_expressions[0], exp.Star):
            return RewriteResult(rewritten=False, sql=sql, reasons=[])

        tables = [table.name for table in tree.find_all(exp.Table)]
        if len(tables) != 1:
            return RewriteResult(rewritten=False, sql=sql, reasons=[])

        table_name = tables[0]
        allowed_columns = self.policy.get("allowed_columns", {}).get(table_name, [])
        if not allowed_columns:
            return RewriteResult(rewritten=False, sql=sql, reasons=[])

        tree.set(
            "expressions",
            [exp.column(column_name, table=table_name) for column_name in allowed_columns],
        )
        return RewriteResult(
            rewritten=True,
            sql=tree.sql(dialect="sqlite"),
            reasons=[f"expanded wildcard select for table: {table_name}"],
        )
