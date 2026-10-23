"""Validate a release ZIP for unsafe paths and accidental runtime/secret files."""
from __future__ import annotations
import json
import stat
import sys
import zipfile
from pathlib import PurePosixPath

FORBIDDEN_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}
FORBIDDEN_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv"}
DEFAULT_MAX_ENTRIES = 10_000
DEFAULT_MAX_MEMBER_BYTES = 100 * 1024 * 1024
DEFAULT_MAX_TOTAL_BYTES = 500 * 1024 * 1024
DEFAULT_MAX_COMPRESSION_RATIO = 1_000


def audit_archive(
    archive_path,
    max_entries=DEFAULT_MAX_ENTRIES,
    max_member_bytes=DEFAULT_MAX_MEMBER_BYTES,
    max_total_bytes=DEFAULT_MAX_TOTAL_BYTES,
    max_compression_ratio=DEFAULT_MAX_COMPRESSION_RATIO,
):
    findings = []
    entries = []
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            infos = zf.infolist()
            if len(infos) > max_entries:
                findings.append({"rule": "ENTRY_COUNT_LIMIT", "entry": str(len(infos))})
            seen = set()
            total_uncompressed = 0
            size_limit_exceeded = len(infos) > max_entries
            for info in infos:
                total_uncompressed += info.file_size
                if info.file_size > max_member_bytes:
                    findings.append({"rule": "MEMBER_SIZE_LIMIT", "entry": info.filename})
                    size_limit_exceeded = True
                if total_uncompressed > max_total_bytes:
                    if not any(item["rule"] == "TOTAL_SIZE_LIMIT" for item in findings):
                        findings.append({"rule": "TOTAL_SIZE_LIMIT", "entry": str(total_uncompressed)})
                    size_limit_exceeded = True
                if info.file_size > 0 and info.compress_size == 0:
                    findings.append({"rule": "COMPRESSION_RATIO_LIMIT", "entry": info.filename})
                    size_limit_exceeded = True
                elif info.compress_size > 0 and info.file_size / info.compress_size > max_compression_ratio:
                    findings.append({"rule": "COMPRESSION_RATIO_LIMIT", "entry": info.filename})
                    size_limit_exceeded = True
                raw = info.filename
                normalized = raw.replace("\\", "/")
                path = PurePosixPath(normalized)
                parts = path.parts
                if normalized.startswith("/") or (parts and ":" in parts[0]):
                    findings.append({"rule": "ABSOLUTE_PATH", "entry": raw})
                if ".." in parts:
                    findings.append({"rule": "PATH_TRAVERSAL", "entry": raw})
                key = normalized.rstrip("/")
                if key in seen:
                    findings.append({"rule": "DUPLICATE_ENTRY", "entry": raw})
                seen.add(key)
                if any(part in FORBIDDEN_DIRS for part in parts):
                    findings.append({"rule": "RUNTIME_OR_VCS_ARTIFACT", "entry": raw})
                basename = parts[-1] if parts else ""
                if basename in FORBIDDEN_NAMES or basename.endswith(tuple(FORBIDDEN_SUFFIXES)):
                    findings.append({"rule": "SENSITIVE_OR_BYTECODE_FILE", "entry": raw})
                mode = (info.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    findings.append({"rule": "SYMLINK_ENTRY", "entry": raw})
                entries.append(raw)
            # Do not decompress entries when metadata exceeds configured safety limits.
            if not size_limit_exceeded:
                bad = zf.testzip()
                if bad:
                    findings.append({"rule": "CRC_FAILURE", "entry": bad})
    except (OSError, zipfile.BadZipFile) as exc:
        findings.append({"rule": "INVALID_ARCHIVE", "entry": type(exc).__name__})
    return {
        "audit": "release_archive_hygiene",
        "archive": str(archive_path),
        "entries_checked": len(entries),
        "findings": findings,
        "status": "pass" if not findings else "fail",
        "limitations": [
            "Checks archive paths, selected accidental runtime files, symlinks, duplicate names, and ZIP CRC only.",
            "Does not prove source-code safety, dependency safety, or absence of all possible secrets.",
            "ZIP size and compression-ratio limits are metadata-based safeguards, not a substitute for sandboxing untrusted archives.",
        ],
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python evaluations/archive_audit.py PATH_TO_ZIP", file=sys.stderr)
        return 2
    report = audit_archive(sys.argv[1])
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())
