from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request


class RuleBasedGenerator:
    """Fallback baseline used when no model backend is configured."""

    def generate(self, question: str) -> str:
        lower = question.lower()

        if "total number" in lower or "count" in lower or "how many" in lower:
            return "SELECT COUNT(*) FROM patients"
        if "older than 30" in lower:
            return "SELECT name, age FROM patients WHERE age > 30"
        if "patient names" in lower and "age" not in lower:
            return "SELECT name FROM patients"
        if "all patient names and ages" in lower or "all patient names" in lower:
            return "SELECT name, age FROM patients"
        if "show all" in lower:
            return "SELECT id, name, age, gender FROM patients"

        return "SELECT id, name, age, gender FROM patients LIMIT 10"


class OpenAICompatibleGenerator:
    """Minimal OpenAI-compatible Text-to-SQL backend using environment configuration."""

    def __init__(self, schema_text: str) -> None:
        self.schema_text = schema_text
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "3"))

    def _build_prompt(self, question: str) -> str:
        return (
            "You are a Text-to-SQL system for SQLite.\n"
            "Return exactly one SQL query and nothing else.\n"
            "Use only SELECT statements.\n"
            "Never use SELECT *.\n"
            "Always name the smallest necessary set of columns explicitly.\n"
            "Prefer schema-listed column names over broad projection.\n"
            "If a count is requested, use COUNT(*).\n"
            "Do not use comments, UNION, multiple statements, or schema elements that are not listed.\n"
            "If the question is unsafe, still return the safest valid SELECT that best matches benign intent.\n"
            "Use only the schema provided below.\n\n"
            f"Schema:\n{self.schema_text}\n\n"
            f"Question: {question}\n"
            "SQL:"
        )

    def _strip_response(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("sql"):
                cleaned = cleaned[3:].strip()
        return cleaned.splitlines()[0].strip() if "\n" in cleaned else cleaned

    def generate(self, question: str) -> str:
        prompt = self._build_prompt(question)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Generate safe SQLite SQL."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        }
        request = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    body = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                last_exc = exc
                if exc.code == 429 and attempt < self.max_retries:
                    retry_after = exc.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else float(2 ** attempt)
                    time.sleep(delay)
                    continue
                raise RuntimeError(f"model request failed: {exc}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    time.sleep(float(2 ** attempt))
                    continue
                raise RuntimeError(f"model request failed: {exc}") from exc
        else:  # pragma: no cover - defensive fallback
            raise RuntimeError(f"model request failed: {last_exc}")

        content = body["choices"][0]["message"]["content"]
        return self._strip_response(content)


class Text2SQLGenerator:
    def __init__(self, schema_text: str) -> None:
        self.schema_text = schema_text
        self.requested_backend = os.getenv("SAFETEXT2SQL_BACKEND", "rule").lower()
        self.backend = "rule"
        self.last_error = ""
        self.fallback = RuleBasedGenerator()
        self.remote_generator = None

        if self.requested_backend == "openai" and os.getenv("OPENAI_API_KEY"):
            self.remote_generator = OpenAICompatibleGenerator(schema_text)
        elif self.requested_backend == "openai":
            self.last_error = "OPENAI_API_KEY is not set"

    def generate(self, question: str) -> str:
        self.last_error = ""

        if self.requested_backend == "openai" and self.remote_generator is not None:
            try:
                sql = self.remote_generator.generate(question)
                self.backend = "openai"
                return sql
            except RuntimeError as exc:
                self.last_error = str(exc)

        self.backend = "rule"
        return self.fallback.generate(question)
