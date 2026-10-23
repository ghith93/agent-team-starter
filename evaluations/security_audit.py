"""Offline static hygiene audit; not a substitute for dedicated scanners or review."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_SUFFIXES = {".py", ".json", ".md", ".ipynb", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".txt", ".example"}
SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache", ".ipynb_checkpoints"}

# Narrow token-shape heuristics; matching values are never printed.
SECRET_PATTERNS = [
    ("SECRET_GITHUB_TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("SECRET_GOOGLE_API_KEY", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    ("SECRET_OPENAI_STYLE_KEY", re.compile(r"\bsk-[A-Za-z0-9]{24,}\b")),
    ("SECRET_SLACK_TOKEN", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("SECRET_AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
]
_PRIVATE = "PRIVATE" + r"\s+KEY"
SECRET_PATTERNS.append(("SECRET_PRIVATE_KEY_BLOCK", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?" + _PRIVATE + r"-----")))
STATIC_PATTERNS = [
    ("DANGEROUS_EVAL", re.compile(r"\beval\s*\("), "review dynamic evaluation"),
    ("DANGEROUS_EXEC", re.compile(r"\bexec\s*\("), "review dynamic execution"),
    ("PICKLE_LOADS", re.compile(r"\bpickle\.(?:loads?|Unpickler)\b"), "review unsafe deserialization"),
    ("TLS_VERIFY_DISABLED", re.compile(r"\bverify\s*=\s*False\b"), "TLS verification appears disabled"),
    ("SUBPROCESS_SHELL_TRUE", re.compile(r"\bshell\s*=\s*True\b"), "review shell invocation"),
]


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if rel.as_posix().startswith("evaluations/results/"):
            continue
        yield path


def audit(root: Path = ROOT):
    findings = []
    files_scanned = 0
    for path in iter_files(root):
        files_scanned += 1
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append({"rule": "READ_ERROR", "severity": "error", "file": path.relative_to(root).as_posix(), "line": 0, "message": type(exc).__name__})
            continue
        rel = path.relative_to(root).as_posix()
        for line_no, line in enumerate(content.splitlines(), 1):
            for rule, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append({"rule": rule, "severity": "high", "file": rel, "line": line_no, "message": "possible credential/private key; value redacted"})
            if path.suffix.lower() == ".py":
                for rule, pattern, message in STATIC_PATTERNS:
                    if pattern.search(line):
                        findings.append({"rule": rule, "severity": "review", "file": rel, "line": line_no, "message": message})
    dependency_notes = []
    req = root / "requirements.txt"
    if req.exists():
        for line_no, line in enumerate(req.read_text(encoding="utf-8").splitlines(), 1):
            item = line.strip()
            if not item or item.startswith("#") or item.startswith(("-", "http://", "https://")):
                continue
            if ">=" in item and "<" not in item:
                dependency_notes.append({"file": "requirements.txt", "line": line_no, "message": "lower bound without upper bound; review dependency range"})
            if " @ " in item or item.startswith(("git+", "hg+", "svn+")):
                dependency_notes.append({"file": "requirements.txt", "line": line_no, "message": "direct URL/VCS dependency; verify provenance and pinning"})
    high = sum(1 for x in findings if x["severity"] == "high")
    errors = sum(1 for x in findings if x["severity"] == "error")
    review = sum(1 for x in findings if x["severity"] == "review")
    return {
        "audit": "offline_static_hygiene",
        "files_scanned": files_scanned,
        "findings": findings,
        "dependency_notes": dependency_notes,
        "summary": {"high_confidence_secret_candidates": high, "read_errors": errors, "manual_review_items": review, "dependency_notes": len(dependency_notes)},
        "status": "pass" if high == 0 and errors == 0 else "fail",
        "limitations": [
            "Offline heuristic scan only; may miss secrets and may produce false positives.",
            "Not a substitute for Gitleaks, Semgrep, OSV-Scanner, pip-audit, threat modeling, or human review.",
            "Does not query vulnerability databases or establish dependency vulnerability status.",
            "Review-level code patterns are leads for manual review, not proof of vulnerabilities."
        ]
    }


def main():
    report = audit()
    out = ROOT / "evaluations" / "results" / "offline_security_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())
