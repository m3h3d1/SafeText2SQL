from __future__ import annotations


class Text2SQLGenerator:
    """Small rule-based baseline used to wire the pipeline before adding an LLM."""

    def generate(self, question: str) -> str:
        lower = question.lower()

        if "older than 30" in lower:
            return "SELECT name, age FROM patients WHERE age > 30"
        if "all patient names and ages" in lower or "all patient names" in lower:
            return "SELECT name, age FROM patients"
        if "show all" in lower:
            return "SELECT id, name, age, gender FROM patients"

        return "SELECT id, name, age, gender FROM patients LIMIT 10"
