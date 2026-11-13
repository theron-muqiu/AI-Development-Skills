"""Guard the review bundle's resources and independent report contracts."""

import unittest

from ai_devlop.cli import load_payload, REQUIRED_ASSETS


class ReviewSkillTests(unittest.TestCase):
    def test_both_review_templates_are_required_and_packaged(self):
        payload = load_payload()
        for name, filename in (("ai-devlop-check", "一致性检查.md"),
                               ("ai-devlop-verify", "实现验证.md")):
            with self.subTest(skill=name):
                self.assertEqual(REQUIRED_ASSETS[name], (filename,))
                definition = payload[name]["SKILL.md"].decode("utf-8")
                template = payload[name]["assets/" + filename].decode("utf-8")
                self.assertIn("ai-dev-docs/requirements/", definition)
                self.assertIn(name + "/" + filename, definition)
                self.assertIn("Rule ID", definition + template)
                self.assertIn("未验证", definition + template)
                self.assertIn("不适用", definition + template)
                self.assertIn("场景", template)
                self.assertIn("证据", template)

    def test_all_skill_resources_are_self_contained_and_use_code_not_title_marks(self):
        for name, files in load_payload().items():
            for relative, data in files.items():
                if not relative.endswith(".md"):
                    continue
                with self.subTest(skill=name, file=relative):
                    text = data.decode("utf-8")
                    self.assertNotRegex(text, r"[《》]")
                    self.assertNotRegex(text.lower(), r"spec.?kit|\.specify/")


if __name__ == "__main__":
    unittest.main()
