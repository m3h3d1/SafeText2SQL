from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    executed: bool
    rows: list[tuple]
    error: str | None


class SafeExecutor:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def execute(self, sql: str, max_rows: int = 100) -> ExecutionResult:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchmany(max_rows)
            conn.close()
            return ExecutionResult(executed=True, rows=rows, error=None)
        except Exception as exc:  # pragma: no cover - starter scaffold
            return ExecutionResult(executed=False, rows=[], error=str(exc))
