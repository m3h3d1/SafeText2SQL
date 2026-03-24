# Environment Setup

## Rule-Based Local Mode
No API key is required. The project uses the fallback generator by default.

Run:

```bash
.venv/bin/python src/evaluate.py
```

## OpenAI-Compatible Mode
Set these variables in your shell:

```bash
export SAFETEXT2SQL_BACKEND="openai"
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_MODEL="gpt-4o-mini"
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

Then run:

```bash
.venv/bin/python src/evaluate.py
```

## Notes
- If the model request fails, the generator falls back to rule-based mode.
- Do not commit real API keys into the repository.
