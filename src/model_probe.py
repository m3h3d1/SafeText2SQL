from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProbeResult:
    suspicious: bool
    clean_sql: str
    triggered_sql: str
    reason: str


class ModelProbe:
    def compare(self, clean_sql: str, triggered_sql: str) -> ProbeResult:
        suspicious = clean_sql != triggered_sql
        reason = "output changed under trigger-like input" if suspicious else "no change"
        return ProbeResult(
            suspicious=suspicious,
            clean_sql=clean_sql,
            triggered_sql=triggered_sql,
            reason=reason,
        )
