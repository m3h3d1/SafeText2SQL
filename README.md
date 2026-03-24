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
4. Run `src/cli.py "your question"` for a single interactive request.

## Model Backends
- Default: rule-based fallback for local development.
- Optional: OpenAI-compatible backend via environment variables.

Example:
- copy values from `config/model.env.example`
- set `SAFETEXT2SQL_BACKEND=openai`
- set `OPENAI_API_KEY`
- optionally set `OPENAI_BASE_URL` and `OPENAI_MODEL`
- see [ENV_SETUP.md](/home/user/Downloads/ms/toxic/SafeText2SQL/docs/ENV_SETUP.md) for shell setup

## Outputs
- `results/evaluation.json` detailed per-case results
- `results/summary.json` aggregate metrics
- `results/report.md` human-readable evaluation report

## Current Scope
- SQLite only
- Read-only `SELECT` queries
- Rule-based baseline defenses
- small benchmark with benign, injection, and trigger cases
