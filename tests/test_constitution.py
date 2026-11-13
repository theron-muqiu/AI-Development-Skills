"""Regression checks for the constitution resource and downstream contract."""

import unittest

from ai_devlop.cli import load_payload, SKILLS


class ConstitutionTests(unittest.TestCase):
    def test_templates_cover_required_domains(self):
        payload = load_payload()["ai-devlop-constitution"]
        domains = {
            "engineering.md": ("Coding Standards", "Code Quality", "Testing", "Dependency Management",
                               "Error Handling", "Logging", "Build", "CI/CD", "Documentation"),
            "architecture.md": ("Architecture Style", "Layer Boundary", "Module Boundary", "Dependency Rules",
                                "Data Ownership", "API Contract", "Transaction Boundary", "Integration",
                                "Extensibility", "Architecture Testing"),
            "security.md": ("Authentication", "Authorization", "Data Isolation", "Sensitive Data",
                            "Input Validation", "Secure Communication", "Audit Logging",
                            "Dependency Security", "Error Handling", "Security Testing"),
        }
        for filename, headings in domains.items():
            text = payload["assets/" + filename].decode("utf-8")
            for heading in headings:
                with self.subTest(filename=filename, heading=heading):
                    self.assertIn(heading, text)
        self.assertIn("assets/constitution.md", payload)

    def test_all_downstream_skills_read_project_rules(self):
        payload = load_payload()
        for name in SKILLS:
            if name == "ai-devlop-constitution":
                continue
            text = payload[name]["SKILL.md"].decode("utf-8")
            for filename in (".ai-dev/memory/constitution.md", "engineering.md", "architecture.md", "security.md"):
                with self.subTest(skill=name, filename=filename):
                    self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
