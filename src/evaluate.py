from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from input_filter import InputFilter
from model_probe import ModelProbe
from safe_executor import SafeExecutor
from sql_validator import SQLValidator
from text2sql import Text2SQLGenerator


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "safe_text2sql.db"
SCHEMA_PATH = ROOT / "data" / "schema.sql"
POLICY_PATH = ROOT / "config" / "policy.yaml"
RESULTS_PATH = ROOT / "results" / "evaluation.json"


def initialize_db() -> None:
    script = SCHEMA_PATH.read_text()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(script)
    conn.close()


def load_prompts(name: str) -> list[dict]:
    return json.loads((ROOT / "prompts" / name).read_text())


def run() -> list[dict]:
    initialize_db()

    input_filter = InputFilter()
    generator = Text2SQLGenerator()
    validator = SQLValidator(str(POLICY_PATH))
    executor = SafeExecutor(str(DB_PATH))
    probe = ModelProbe()

    results: list[dict] = []
    prompt_files = ["benign.json", "injection.json", "triggers.json"]

    for prompt_file in prompt_files:
        for item in load_prompts(prompt_file):
            question = item["question"]
            filter_result = input_filter.assess(question)

            generated_sql = generator.generate(question)
            validation_result = validator.validate(generated_sql)

            execution = None
            if filter_result.decision != "block" and validation_result.allowed:
                execution = executor.execute(generated_sql)

            probe_result = None
            if prompt_file == "triggers.json":
                clean_question = question.replace("??", "").replace("::", "").strip()
                clean_sql = generator.generate(clean_question)
                probe_result = probe.compare(clean_sql, generated_sql).__dict__

            results.append(
                {
                    "id": item["id"],
                    "category": prompt_file,
                    "question": question,
                    "filter": filter_result.__dict__,
                    "sql": generated_sql,
                    "validation": validation_result.__dict__,
                    "execution": None if execution is None else execution.__dict__,
                    "probe": probe_result,
                    "expected_behavior": item["expected_behavior"],
                }
            )

    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    for item in run():
        print(f"{item['id']} [{item['category']}] -> {item['filter']['decision']}")
