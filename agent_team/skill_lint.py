"""Offline validator for portable Agent Skills folders.

Validates a conservative subset of the Agent Skills metadata contract. It does
not execute skill content or certify the safety/quality of instructions.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\n(?P<meta>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)


def validate_skill_file(path: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [{"severity": "error", "code": "read-error", "message": type(exc).__name__}]

    match = FRONTMATTER_RE.match(raw)
    if not match:
        return [{"severity": "error", "code": "frontmatter-missing", "message": "Expected YAML frontmatter delimited by --- lines."}]

    fields: dict[str, str] = {}
    for line in match.group("meta").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            findings.append({"severity": "error", "code": "metadata-line-invalid", "message": "Metadata lines must use key: value syntax."})
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key in fields:
            findings.append({"severity": "error", "code": "metadata-duplicate", "message": f"Duplicate metadata key: {key}"})
        fields[key] = value.strip("\"'")

    name = fields.get("name", "")
    description = fields.get("description", "")
    folder_name = path.parent.name
    if not name:
        findings.append({"severity": "error", "code": "name-missing", "message": "Required metadata field 'name' is missing."})
    elif len(name) > 64 or not NAME_RE.fullmatch(name):
        findings.append({"severity": "error", "code": "name-invalid", "message": "Name must be <=64 chars, lowercase alphanumeric words separated by single hyphens."})
    elif name != folder_name:
        findings.append({"severity": "error", "code": "name-folder-mismatch", "message": f"Metadata name '{name}' does not match folder '{folder_name}'."})

    if not description:
        findings.append({"severity": "error", "code": "description-missing", "message": "Required metadata field 'description' is missing."})
    elif len(description) > 1024:
        findings.append({"severity": "error", "code": "description-too-long", "message": "Description exceeds 1024 characters."})

    unknown = sorted(set(fields) - {"name", "description"})
    if unknown:
        findings.append({"severity": "warning", "code": "unknown-metadata", "message": "Unvalidated metadata keys: " + ", ".join(unknown)})
    if not match.group("body").strip():
        findings.append({"severity": "error", "code": "body-empty", "message": "Skill instructions are empty."})
    if not findings:
        findings.append({"severity": "pass", "code": "skill-metadata-valid", "message": "Required metadata and body are present."})
    return findings


def validate_skill_tree(root: Path) -> dict:
    skills_root = root / "skills" if (root / "skills").is_dir() else root
    files = sorted(skills_root.glob("*/SKILL.md"))
    results = []
    seen_names: set[str] = set()
    for path in files:
        findings = validate_skill_file(path)
        for item in findings:
            if item["code"] == "skill-metadata-valid":
                name = path.parent.name
                if name in seen_names:
                    findings = [{"severity": "error", "code": "duplicate-skill-folder", "message": f"Duplicate skill folder: {name}"}]
                seen_names.add(name)
        results.append({"path": path.relative_to(root).as_posix(), "findings": findings})
    errors = sum(f["severity"] == "error" for r in results for f in r["findings"])
    warnings = sum(f["severity"] == "warning" for r in results for f in r["findings"])
    return {
        "schema_version": 1,
        "mode": "offline_static_metadata_validation",
        "skills_root": skills_root.relative_to(root).as_posix() if skills_root != root else ".",
        "skills_checked": len(results),
        "errors": errors,
        "warnings": warnings,
        "results": results,
        "limitations": [
            "This validates a conservative metadata subset only; it does not fully implement the Agent Skills specification.",
            "It does not execute or assess the safety, correctness, permissions, or quality of skill instructions.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".", help="Project root or skills directory")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args(argv)
    root = Path(args.path).resolve()
    report = validate_skill_tree(root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Skill metadata lint | checked={report['skills_checked']} errors={report['errors']} warnings={report['warnings']}")
        for item in report["results"]:
            for finding in item["findings"]:
                print(f"{finding['severity'].upper():7} {item['path']}: {finding['code']} — {finding['message']}")
        print("Note: metadata validation is not a skill safety certification.")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
