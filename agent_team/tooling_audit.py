"""Report locally discoverable developer tools without installing or contacting anything.

Usage: python -m agent_team.tooling_audit [--json]
This command is intentionally offline and does not inspect environment variable values.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timezone

COMMANDS = (
    "git", "pytest", "ruff", "semgrep", "ast-grep", "pip-audit", "bandit",
    "gitleaks", "detect-secrets", "promptfoo", "deepeval", "mcp-scan",
    "mcp-inspector", "ghidra", "radare2", "frida", "mitmproxy",
)
MODULES = ("pytest", "requests", "hypothesis", "ruff", "bandit", "pip_audit", "deepeval", "langgraph")


def collect_inventory() -> dict:
    commands = {name: shutil.which(name) is not None for name in COMMANDS}
    modules = {name: importlib.util.find_spec(name) is not None for name in MODULES}
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "execution_mode": "local_discovery_only",
        "network_calls": 0,
        "installations_performed": 0,
        "secret_values_read": False,  # nosec B105 - boolean metadata flag, not a credential
        "commands": commands,
        "python_modules": modules,
        "limitations": [
            "Command discovery does not establish that a tool is correctly configured or safe.",
            "A missing command/module may still be available in another environment.",
            "No vulnerability database or remote repository was queried.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args(argv)
    result = collect_inventory()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Local tooling inventory | Python {result['python_version']} | offline")
        print("Commands:")
        for name, present in result["commands"].items():
            print(f"  {'FOUND' if present else 'missing':7} {name}")
        print("Python modules:")
        for name, present in result["python_modules"].items():
            print(f"  {'FOUND' if present else 'missing':7} {name}")
        print("No installs, network calls, or secret-value reads were performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
