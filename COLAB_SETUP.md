# Google Colab setup (mobile-friendly, v0.7)

1. Upload and extract `agent_team_starter_v0.7.zip` in Colab. Confirm the extracted folder is `agent_team_starter_v0.7`.
2. In that folder, install dependencies: `!pip -q install -r requirements.txt`
3. Prefer Colab's **Secrets** panel for `GEMINI_API_KEY` and/or `OPENROUTER_API_KEY`. Grant notebook access only to secrets you need. Optional secrets: `GEMINI_MODEL`, `OPENROUTER_FREE_MODELS`.
4. Load secrets without printing values:
```python
import os
try:
    from google.colab import userdata
    for name in ("GEMINI_API_KEY", "OPENROUTER_API_KEY", "GEMINI_MODEL", "OPENROUTER_FREE_MODELS"):
        try: value = userdata.get(name)
        except Exception: value = None
        if value: os.environ[name] = value
except Exception: pass
print("Configured provider names:", [n for n in ("GEMINI_API_KEY", "OPENROUTER_API_KEY") if os.getenv(n)])
```
5. Run offline checks: `!python run_tests.py`
6. Inspect configuration without a network request: `!python -m agent_team.cli --check-config`
7. Only after verifying current provider quota/billing settings, run a small task: `!python -m agent_team.cli "Create a checklist for validating a small business idea"`

No configured key means no provider requests. `--check-config` checks presence only; it does not verify credentials, availability, quota, or billing. OpenRouter IDs are accepted only when they are `openrouter/free` or end in `:free`; free routing does not guarantee availability or zero ancillary costs. Never put keys in notebooks, source files, screenshots, or GitHub.
