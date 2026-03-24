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
        self.block_terms = [
            r"(?i)\bor\s+1=1\b",
            r"(?i)\bunion\b",
            r"(?i)\bdrop\b",
            r"(?i)\bdelete\b",
            r"(?i)\bignore the rules\b",
            r"(?i)\bbypass\b",
            r"--",
        ]
        self.warn_terms = [
            r"(?i)\bcomment\b",
            r"(?i)\bsemicolon\b",
            r"(?i)\btrigger\b",
        ]

    def assess(self, question: str) -> InputFilterResult:
        score = 0
        reasons: list[str] = []
        hard_block = False

        for pattern in self.repeated_punctuation:
            if re.search(pattern, question):
                score += 1
                reasons.append(f"trigger-like punctuation: {pattern}")

        for pattern in self.block_terms:
            if re.search(pattern, question):
                score += 3
                hard_block = True
                reasons.append(f"blocked term: {pattern}")

        for pattern in self.warn_terms:
            if re.search(pattern, question):
                score += 1
                reasons.append(f"warning term: {pattern}")

        if hard_block or score >= 3:
            decision = "block"
        elif score > 0:
            decision = "warn"
        else:
            decision = "allow"

        return InputFilterResult(decision=decision, risk_score=score, reasons=reasons)
