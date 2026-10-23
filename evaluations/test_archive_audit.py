import tempfile
import unittest
import zipfile
import stat
from pathlib import Path
from archive_audit import audit_archive


class ArchiveAuditTests(unittest.TestCase):
    def make_zip(self, entries):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "fixture.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for name, content in entries:
                zf.writestr(name, content)
        return path

    def test_clean_archive_passes(self):
        report = audit_archive(self.make_zip([("pkg/README.md", "ok"), ("pkg/main.py", "print('ok')")]))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["entries_checked"], 2)

    def test_traversal_and_absolute_paths_fail(self):
        report = audit_archive(self.make_zip([("../outside.txt", "x"), ("/root.txt", "x"), ("pkg\\..\\escape.txt", "x")]))
        rules = {item["rule"] for item in report["findings"]}
        self.assertIn("PATH_TRAVERSAL", rules)
        self.assertIn("ABSOLUTE_PATH", rules)
        self.assertTrue(any(item["rule"] == "PATH_TRAVERSAL" and "escape.txt" in item["entry"] for item in report["findings"]))

    def test_runtime_and_env_files_fail(self):
        report = audit_archive(self.make_zip([("pkg/.env", "placeholder"), ("pkg/__pycache__/x.pyc", "x")]))
        rules = {item["rule"] for item in report["findings"]}
        self.assertIn("SENSITIVE_OR_BYTECODE_FILE", rules)
        self.assertIn("RUNTIME_OR_VCS_ARTIFACT", rules)

    def test_duplicate_entry_fails(self):
        path = self.make_zip([("pkg/a.txt", "1"), ("pkg/a.txt", "2")])
        report = audit_archive(path)
        self.assertIn("DUPLICATE_ENTRY", {item["rule"] for item in report["findings"]})

    def test_symlink_entry_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "symlink.zip"
            info = zipfile.ZipInfo("pkg/link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr(info, "target.txt")
            report = audit_archive(path)
            self.assertIn("SYMLINK_ENTRY", {item["rule"] for item in report["findings"]})

    def test_member_size_limit_fails_closed_before_crc_read(self):
        report = audit_archive(self.make_zip([("pkg/large.txt", "x" * 100)]), max_member_bytes=50)
        self.assertEqual(report["status"], "fail")
        self.assertIn("MEMBER_SIZE_LIMIT", {item["rule"] for item in report["findings"]})

    def test_total_size_limit_fails_closed(self):
        report = audit_archive(self.make_zip([("a.txt", "x" * 30), ("b.txt", "y" * 30)]), max_total_bytes=50)
        self.assertEqual(report["status"], "fail")
        self.assertIn("TOTAL_SIZE_LIMIT", {item["rule"] for item in report["findings"]})

    def test_compression_ratio_limit_fails_closed(self):
        report = audit_archive(self.make_zip([("pkg/repetitive.txt", "A" * 10000)]), max_compression_ratio=2)
        self.assertEqual(report["status"], "fail")
        self.assertIn("COMPRESSION_RATIO_LIMIT", {item["rule"] for item in report["findings"]})

    def test_entry_count_limit_fails_closed(self):
        report = audit_archive(self.make_zip([("a.txt", "a"), ("b.txt", "b")]), max_entries=1)
        self.assertEqual(report["status"], "fail")
        self.assertIn("ENTRY_COUNT_LIMIT", {item["rule"] for item in report["findings"]})

    def test_invalid_archive_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.zip"
            path.write_text("not a zip", encoding="utf-8")
            report = audit_archive(path)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["findings"][0]["rule"], "INVALID_ARCHIVE")

if __name__ == "__main__":
    unittest.main()
