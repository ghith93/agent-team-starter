import tempfile
import unittest
from pathlib import Path
from agent_team.skill_lint import validate_skill_file, validate_skill_tree


class SkillLintTests(unittest.TestCase):
    def test_valid_skill_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "sample-skill"
            p.mkdir()
            f = p / "SKILL.md"
            f.write_text("---\nname: sample-skill\ndescription: A sample skill.\n---\n\nDo the task safely.\n", encoding="utf-8")
            findings = validate_skill_file(f)
            self.assertEqual(findings[0]["code"], "skill-metadata-valid")

    def test_name_must_match_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "folder-name"
            p.mkdir()
            f = p / "SKILL.md"
            f.write_text("---\nname: another-name\ndescription: A sample skill.\n---\n\nBody.\n", encoding="utf-8")
            codes = {x["code"] for x in validate_skill_file(f)}
            self.assertIn("name-folder-mismatch", codes)

    def test_rejects_missing_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "sample-skill"
            p.mkdir()
            f = p / "SKILL.md"
            f.write_text("# No metadata\n", encoding="utf-8")
            self.assertEqual(validate_skill_file(f)[0]["code"], "frontmatter-missing")

    def test_validates_project_skills_offline(self):
        root = Path(__file__).resolve().parents[1]
        report = validate_skill_tree(root)
        self.assertGreaterEqual(report["skills_checked"], 6)
        self.assertEqual(report["errors"], 0)


if __name__ == "__main__":
    unittest.main()
