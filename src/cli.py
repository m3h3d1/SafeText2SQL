from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from evaluate import load_schema_text
from input_filter import InputFilter
from intent_validator import IntentValidator
from query_rewriter import QueryRewriter
from safe_executor import SafeExecutor
from sql_validator import SQLValidator
from text2sql import Text2SQLGenerator


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "safe_text2sql.db"
SCHEMA_PATH = ROOT / "data" / "schema.sql"
POLICY_PATH = ROOT / "config" / "policy.yaml"


def initialize_db() -> None:
    script = SCHEMA_PATH.read_text()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(script)
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one SafeText2SQL question through the pipeline.")
    parser.add_argument("question", help="Natural-language question")
    args = parser.parse_args()

    initialize_db()

    input_filter = InputFilter()
    generator = Text2SQLGenerator(load_schema_text())
    rewriter = QueryRewriter(str(POLICY_PATH))
    validator = SQLValidator(str(POLICY_PATH))
    intent_validator = IntentValidator()
    executor = SafeExecutor(str(DB_PATH))

    filter_result = input_filter.assess(args.question)
    generated_sql = generator.generate(args.question)
    rewrite = rewriter.rewrite(generated_sql)
    final_sql = rewrite.sql if rewrite.rewritten else generated_sql
    validation = validator.validate(final_sql)
    intent = intent_validator.validate(args.question, validation.normalized_sql)
    executable_sql = validation.normalized_sql
    execution = None
    if filter_result.decision != "block" and validation.allowed and intent.allowed:
        execution = executor.execute(executable_sql)

    print(f"backend: {generator.backend}")
    print(f"requested_backend: {generator.requested_backend}")
    print(f"backend_error: {generator.last_error or 'None'}")
    print(f"filter_decision: {filter_result.decision}")
    print(f"filter_reasons: {filter_result.reasons}")
    print(f"generated_sql: {generated_sql}")
    print(f"rewrite_applied: {rewrite.rewritten}")
    print(f"rewrite_reasons: {rewrite.reasons}")
    print(f"final_sql: {final_sql}")
    print(f"executable_sql: {executable_sql}")
    print(f"validation_allowed: {validation.allowed}")
    print(f"validation_reasons: {validation.reasons}")
    print(f"validation_notes: {validation.notes}")
    print(f"intent_allowed: {intent.allowed}")
    print(f"intent_reasons: {intent.reasons}")
    print(f"intent_notes: {intent.notes}")
    if execution is None:
        print("execution: skipped")
    else:
        print(f"execution: {execution.executed}")
        print(f"rows: {execution.rows}")
        print(f"error: {execution.error}")


if __name__ == "__main__":
    main()
