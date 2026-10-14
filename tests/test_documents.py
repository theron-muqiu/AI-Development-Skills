"""Exercise the public document workflow with an entire requirement."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from ai_devlop.documents import validate
from ai_devlop.reader import render


FIXTURE = Path(__file__).parent / "fixtures" / "valid-requirement"


class DocumentTests(unittest.TestCase):
    """Check links, workflow invariants, and safe snapshot replacement."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="需求 测试 ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "中文 需求"
        shutil.copytree(FIXTURE, self.root)

    def edit(self, relative, change):
        path = self.root / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def codes(self):
        return {d.code for d in validate(self.root)[1]}

    def test_full_example_valid_and_renders_offline(self):
        docs, diagnostics = validate(self.root)
        self.assertEqual(diagnostics, [])
        self.assertEqual(len(docs), 7)
        target = render(self.root, docs)
        html = target.read_text(encoding="utf-8")
        self.assertIn("需求分析", html)
        self.assertIn("window.docVendor", html)
        self.assertNotIn("https://cdn", html)
        self.assertIn("S-001", html)

    def test_duplicate_id_and_missing_reference(self):
        self.edit("ai-devlop-spec/需求分析.json", lambda d: d["goals"][0].update(id="TERM-001"))
        self.assertIn("duplicate_id", self.codes())
        self.edit("ai-devlop-spec/需求分析.json", lambda d: d["goals"][0].update(id="G-001"))
        self.edit("ai-devlop-task/任务清单.json", lambda d: d["tasks"][0]["scenarioRefs"][0].update(id="S-404"))
        self.assertIn("missing_reference_id", self.codes())

    def test_cycle_and_status_evidence(self):
        self.edit("ai-devlop-task/任务清单.json", lambda d: d["tasks"][0].update(dependsOn=["T001"]))
        self.assertIn("dependency_cycle", self.codes())
        self.edit("ai-devlop-task/任务清单.json", lambda d: d["tasks"][0].update(dependsOn=[], status="blocked"))
        self.assertIn("status_mismatch", self.codes())
        self.assertIn("incomplete_conclusion", self.codes())

    def test_invalid_json_does_not_replace_html(self):
        docs, diagnostics = validate(self.root)
        self.assertFalse(diagnostics)
        target = render(self.root, docs)
        original = target.read_bytes()
        (self.root / "ai-devlop-spec" / "需求分析.json").write_text("{bad", encoding="utf-8")
        _, diagnostics = validate(self.root)
        self.assertIn("invalid_json", {d.code for d in diagnostics})
        self.assertEqual(original, target.read_bytes())

    def test_unknown_version_and_cross_requirement(self):
        self.edit("ai-devlop-spec/需求分析.json", lambda d: d.update(schemaVersion="2.0"))
        self.assertIn("schema", self.codes())
        self.edit("ai-devlop-spec/需求分析.json", lambda d: d.update(schemaVersion="1.0", requirementId="OTHER"))
        self.assertIn("requirement_mismatch", self.codes())

    def test_malformed_typed_fields_report_schema_error(self):
        self.edit("ai-devlop-task/任务清单.json", lambda d: d["tasks"][0].update(dependsOn=None))
        self.assertIn("schema", self.codes())

    def test_input_time_requires_timezone(self):
        self.edit("原始需求/原始需求.json", lambda d: d["entries"][0].update(timestamp="2026-10-13T09:00:00"))
        self.assertIn("invalid_timestamp", self.codes())

    def test_embedded_content_cannot_break_data_script(self):
        self.edit("原始需求/原始需求.json", lambda d: d["entries"][0].update(text='</script><script>alert(1)</script>'))
        docs, diagnostics = validate(self.root)
        self.assertFalse(diagnostics)
        html = render(self.root, docs).read_text(encoding="utf-8")
        self.assertNotIn('</script><script>alert(1)</script>', html)
        self.assertIn('\\u003c/script\\u003e', html)

    def test_partial_stage_is_valid(self):
        for relative in ("ai-devlop-plan", "ai-devlop-task", "ai-devlop-implement"):
            shutil.rmtree(self.root / relative)
        _, diagnostics = validate(self.root)
        self.assertEqual(diagnostics, [])

    def test_completed_task_requires_implementation_record(self):
        shutil.rmtree(self.root / "ai-devlop-implement")
        self.assertIn("missing_completion_evidence", self.codes())


if __name__ == "__main__":
    unittest.main()
