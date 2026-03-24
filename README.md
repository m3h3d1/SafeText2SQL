# SafeText2SQL

SafeText2SQL is a small prototype for defending Text-to-SQL pipelines against:

- prompt-induced SQL injection
- trigger-style backdoor behavior

## Project Structure
- `src/` application modules
- `data/` SQLite schema and sample data
- `prompts/` benign and adversarial prompt sets
- `config/` security policy
- `results/` evaluation outputs
- `docs/` notes and future documentation

## Modules
- `text2sql.py` baseline SQL generator
- `input_filter.py` prompt screening
- `sql_validator.py` SQL policy enforcement
- `safe_executor.py` restricted execution
- `model_probe.py` trigger-style model probing
- `evaluate.py` end-to-end evaluation runner

## Quick Start
1. Install dependencies from `requirements.txt`.
2. Initialize the SQLite database with `data/schema.sql`.
3. Run `src/evaluate.py` to exercise the baseline pipeline.

## Current Scope
- SQLite only
- Read-only `SELECT` queries
- Rule-based baseline defenses
- Small demo prompt sets
