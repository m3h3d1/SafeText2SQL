from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class InputFilterResult:
    decision: str
    risk_score: int
    reasons: list[str]


class InputFilter:
    def __init__(self) -> None:
        self.repeated_punctuation = [r"\?\?", r"::", r";;"]
        self.suspicious_terms = [
            r"(?i)\bor\s+1=1\b",
            r"(?i)\bunion\b",
            r"(?i)\bdrop\b",
            r"(?i)\bdelete\b",
            r"(?i)\bignore the rules\b",
            r"(?i)\bbypass\b",
            r"--",
        ]

    def assess(self, question: str) -> InputFilterResult:
        score = 0
        reasons: list[str] = []

        for pattern in self.repeated_punctuation:
            if re.search(pattern, question):
                score += 1
                reasons.append(f"trigger-like punctuation: {pattern}")

        for pattern in self.suspicious_terms:
            if re.search(pattern, question):
                score += 2
                reasons.append(f"suspicious term: {pattern}")

        if score >= 3:
            decision = "block"
        elif score > 0:
            decision = "warn"
        else:
            decision = "allow"

        return InputFilterResult(decision=decision, risk_score=score, reasons=reasons)
