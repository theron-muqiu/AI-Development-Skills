"""Inspect and run the actual distribution, never falling back to source resources."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

from ai_devlop.cli import SKILLS, REQUIRED_ASSETS
from ai_devlop import __version__

PROJECT = Path(__file__).absolute().parents[1]
WHEEL = PROJECT / "dist" / f"ai_devlop_cli-{__version__}-py3-none-any.whl"
SDIST = PROJECT / "dist" / f"ai_devlop_cli-{__version__}.tar.gz"


@unittest.skipUnless(WHEEL.exists() and SDIST.exists(), "run uv build first for package tests")
class PackageTests(unittest.TestCase):
    """Check packaged canonical resources and clean uvx installation paths."""

    def test_archive_resources_match_source(self):
        """Wheel and sdist must contain every skill and four unchanged templates."""
        with zipfile.ZipFile(WHEEL) as wheel, tarfile.open(SDIST) as sdist:
            for name in SKILLS:
                for relative in ("SKILL.md", *("assets/" + a for a in REQUIRED_ASSETS[name])):
                    original = (PROJECT / "skills" / name / relative).read_bytes()
                    self.assertEqual(wheel.read(f"ai_devlop/resources/skills/{name}/{relative}"), original)
                    archived = sdist.extractfile(f"ai_devlop_cli-{__version__}/skills/{name}/{relative}")
                    self.assertIsNotNone(archived)
                    self.assertEqual(archived.read(), original)
            self.assertIn("ai-devlop = ai_devlop.cli:main", wheel.read(f"ai_devlop_cli-{__version__}.dist-info/entry_points.txt").decode())

    @unittest.skipUnless(shutil.which("uv"), "uv is required for the executable smoke test")
    def test_isolated_wheel_entrypoint_both_agents(self):
        """Run installed wheel commands outside the checkout using isolated homes."""
        with tempfile.TemporaryDirectory(prefix="ai-devlop-wheel-test-") as temporary:
            root = Path(temporary)
            native_home = root / "用户 目录"
            native_home.mkdir()
            hermes_home = root / "Hermes profile"
            env = {**os.environ, "USERPROFILE": str(native_home), "HOME": str(native_home),
                   "HERMES_HOME": str(hermes_home), "PYTHONPATH": "", "PYTHONIOENCODING": "utf-8"}
            prefix = [shutil.which("uv"), "tool", "run", "--offline", "--python", sys.executable,
                      "--from", str(WHEEL), "ai-devlop"]
            for agent, destination in (("codex", native_home / ".agents" / "skills"),
                                       ("hermes", hermes_home / "skills")):
                for args in (("install", "--dry-run"), ("install",), ("install",), ("status",), ("update",)):
                    result = subprocess.run(prefix + [args[0], "--agent", agent, *args[1:]],
                                            cwd=root, env=env, capture_output=True,
                                            encoding="utf-8", timeout=60)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    if "--dry-run" in args:
                        self.assertFalse(destination.exists())
                self.assertEqual(set(p.name for p in destination.iterdir()), set(SKILLS))
                for name in SKILLS:
                    for asset in REQUIRED_ASSETS[name]:
                        self.assertEqual((destination / name / "assets" / asset).read_bytes(),
                                         (PROJECT / "skills" / name / "assets" / asset).read_bytes())
            project = root / "Git 项目"
            (project / ".git").mkdir(parents=True)
            for agent, folder in (("codex", ".agents"), ("hermes", ".hermes")):
                for command in ("init", "status", "update"):
                    result = subprocess.run(prefix + [command, "--agent", agent, "--project", str(project)],
                                            cwd=root, env=env, capture_output=True,
                                            encoding="utf-8", timeout=60)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(set(p.name for p in (project / folder / "skills").iterdir()), set(SKILLS))
            self.assertFalse((hermes_home / "config.yaml").exists())


if __name__ == "__main__":
    unittest.main()
