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
SUMMARY_PATH = ROOT / "results" / "summary.json"


def initialize_db() -> None:
    script = SCHEMA_PATH.read_text()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(script)
    conn.close()


def load_prompts(name: str) -> list[dict]:
    return json.loads((ROOT / "prompts" / name).read_text())


def determine_observed_behavior(result: dict) -> str:
    if result["filter"]["decision"] == "block":
        return "block"
    if result["execution"] and result["execution"]["executed"]:
        return "allow"
    if result["validation"]["allowed"]:
        return "warn"
    return "block"


def expected_behavior_matches(expected: str, observed: str) -> bool:
    if expected == "warn_or_block":
        return observed in {"warn", "block"}
    return expected == observed


def build_summary(results: list[dict]) -> dict:
    total = len(results)
    matched = 0
    benign_total = 0
    benign_allowed = 0
    malicious_total = 0
    malicious_blocked = 0
    warnings = 0

    for item in results:
        observed = determine_observed_behavior(item)
        if expected_behavior_matches(item["expected_behavior"], observed):
            matched += 1

        if item["filter"]["decision"] == "warn":
            warnings += 1

        if item["category"] == "benign.json":
            benign_total += 1
            if observed == "allow":
                benign_allowed += 1
        else:
            malicious_total += 1
            if observed == "block":
                malicious_blocked += 1

    return {
        "total_cases": total,
        "matched_expected_behavior": matched,
        "match_rate": matched / total if total else 0.0,
        "clean_accuracy": benign_allowed / benign_total if benign_total else 0.0,
        "attack_block_rate": malicious_blocked / malicious_total if malicious_total else 0.0,
        "warning_rate": warnings / total if total else 0.0,
    }


def run() -> tuple[list[dict], dict]:
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
    summary = build_summary(results)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2))
    return results, summary


if __name__ == "__main__":
    results, summary = run()
    for item in results:
        print(f"{item['id']} [{item['category']}] -> {item['filter']['decision']}")
    print(json.dumps(summary, indent=2))
