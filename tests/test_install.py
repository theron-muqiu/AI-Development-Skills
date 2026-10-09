"""Verify installer behavior without touching real agent skill directories."""

import contextlib
import copy
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ai_devlop import cli
from ai_devlop import __version__


class InstallerTests(unittest.TestCase):
    """Use one isolated destination per test, including forced failure scenarios."""

    def setUp(self):
        """Load canonical resources and create an isolated Chinese/space path."""
        self.temp = tempfile.TemporaryDirectory(prefix="ai-devlop-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "测试 项目"
        self.root.mkdir()
        self.target = cli.Target("codex", self.root / ".agents", True)
        self.payload = cli.load_payload()

    def install(self, payload=None, *, update=False, force=False, dry_run=False):
        """Run a complete bundle transaction while suppressing progress output."""
        with contextlib.redirect_stdout(io.StringIO()):
            cli.apply_install(self.target, self.payload if payload is None else payload,
                              update=update, force=force, dry_run=dry_run)

    def changed_payload(self):
        """Simulate a newer package without editing repository templates."""
        newer = copy.deepcopy(self.payload)
        for name in cli.SKILLS:
            newer[name]["SKILL.md"] += b"\nNew package content.\n"
        return newer

    def test_first_install_both_skills_and_manifest(self):
        """Both complete directories and their hash baseline must be present."""
        self.install()
        for name, files in self.payload.items():
            for relative, expected in files.items():
                self.assertEqual((self.target.skills / name / relative).read_bytes(), expected)
        record = cli.read_record(self.target)
        self.assertEqual(set(record["skills"]), set(cli.SKILLS))
        self.assertEqual(record["version"], __version__)
        self.assertFalse((self.target.manager / ".lock").exists())
        self.assertFalse(list(self.target.manager.glob(".stage-*")))

    def test_repeated_install_skips_writes(self):
        """Identical repeat installation must not rewrite skills or metadata."""
        self.install()
        before = self.target.record.stat().st_mtime_ns
        with patch.object(cli.os, "replace", side_effect=AssertionError("unexpected write")):
            self.install()
        self.assertEqual(before, self.target.record.stat().st_mtime_ns)
        self.assertFalse((self.target.manager / "backups").exists())

    def test_legacy_bundle_update_adds_task_skill(self):
        """Upgrade a registered two-skill install without losing its baseline."""
        legacy = {name: self.payload[name] for name in cli.LEGACY_SKILLS}
        with patch.object(cli, "SKILLS", cli.LEGACY_SKILLS):
            self.install(legacy)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.show_status(self.target, self.payload), 1)
        self.install(self.changed_payload(), update=True)
        self.assertEqual(set(cli.read_record(self.target)["skills"]), set(cli.SKILLS))
        for name, files in self.changed_payload().items():
            for relative, expected in files.items():
                self.assertEqual((self.target.skills / name / relative).read_bytes(), expected)

    def test_legacy_upgrade_preserves_modified_skills(self):
        """Adding task support must retain local-edit protection for old skills."""
        legacy = {name: self.payload[name] for name in cli.LEGACY_SKILLS}
        with patch.object(cli, "SKILLS", cli.LEGACY_SKILLS):
            self.install(legacy)
        changed = self.target.skills / cli.SKILLS[0] / "SKILL.md"
        changed.write_bytes(b"local edit")
        with self.assertRaises(cli.InstallError):
            self.install(self.changed_payload(), update=True)
        self.assertEqual(changed.read_bytes(), b"local edit")
        self.assertFalse((self.target.skills / cli.SKILLS[2]).exists())

    def test_three_skill_update_adds_implement_skill(self):
        """Upgrade a registered task-era bundle while preserving all resources."""
        old = {name: self.payload[name] for name in cli.PRE_IMPLEMENT_SKILLS}
        with patch.object(cli, "SKILLS", cli.PRE_IMPLEMENT_SKILLS):
            self.install(old)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.show_status(self.target, self.payload), 1)
        self.install(update=True)
        for name, files in self.payload.items():
            for relative, expected in files.items():
                self.assertEqual((self.target.skills / name / relative).read_bytes(), expected)
        self.assertEqual(set(cli.read_record(self.target)["skills"]), set(cli.SKILLS))

    def test_four_skill_update_adds_clarify_skill(self):
        """A registered v0.2.0 bundle upgrades with a complete clarify payload."""
        old = {name: self.payload[name] for name in cli.PRE_CLARIFY_SKILLS}
        with patch.object(cli, "SKILLS", cli.PRE_CLARIFY_SKILLS):
            self.install(old)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.show_status(self.target, self.payload), 1)
        self.install(update=True)
        for name, files in self.payload.items():
            for relative, expected in files.items():
                self.assertEqual((self.target.skills / name / relative).read_bytes(), expected)
        self.assertEqual(set(cli.read_record(self.target)["skills"]), set(cli.SKILLS))

    def test_four_skill_upgrade_protects_local_changes(self):
        """Adding clarify must not overwrite edits to registered skills."""
        old = {name: self.payload[name] for name in cli.PRE_CLARIFY_SKILLS}
        with patch.object(cli, "SKILLS", cli.PRE_CLARIFY_SKILLS):
            self.install(old)
        changed = self.target.skills / cli.SKILLS[3] / "SKILL.md"
        changed.write_bytes(b"local implementation rules")
        with self.assertRaises(cli.InstallError):
            self.install(self.changed_payload(), update=True)
        self.assertEqual(changed.read_bytes(), b"local implementation rules")
        self.assertFalse((self.target.skills / cli.SKILLS[4]).exists())

    def test_three_skill_update_rolls_back_new_skill_failure(self):
        """A failed fourth-skill commit restores the entire old bundle and record."""
        old = {name: self.payload[name] for name in cli.PRE_IMPLEMENT_SKILLS}
        with patch.object(cli, "SKILLS", cli.PRE_IMPLEMENT_SKILLS):
            self.install(old)
        record = self.target.record.read_bytes()
        before = {name: cli.snapshot(self.target.skills / name) for name in cli.SKILLS}
        rename = Path.rename

        def fail_implement(source, destination):
            """Fail only when publishing the staged implementation skill."""
            path = Path(source)
            if path.parent.name == "new" and path.name == cli.SKILLS[3]:
                raise OSError("simulated implementation skill failure")
            return rename(source, destination)

        with patch.object(Path, "rename", fail_implement):
            with self.assertRaises(OSError):
                self.install(self.changed_payload(), update=True)
        self.assertEqual(self.target.record.read_bytes(), record)
        self.assertEqual({name: cli.snapshot(self.target.skills / name) for name in cli.SKILLS}, before)

    def test_legacy_upgrade_rejects_unregistered_task_conflict(self):
        """A task directory absent from the legacy manifest cannot be adopted."""
        legacy = {name: self.payload[name] for name in cli.LEGACY_SKILLS}
        with patch.object(cli, "SKILLS", cli.LEGACY_SKILLS):
            self.install(legacy)
        task = self.target.skills / cli.SKILLS[2]
        task.mkdir()
        (task / "SKILL.md").write_bytes(b"custom task")
        with self.assertRaises(cli.InstallError):
            self.install(update=True)
        self.assertEqual((task / "SKILL.md").read_bytes(), b"custom task")

    def test_dry_run_creates_nothing(self):
        """Preview must not even create the destination directory or lock."""
        self.install(dry_run=True)
        self.assertFalse(self.target.root.exists())

    def test_conflict_in_second_skill_prevents_first_install(self):
        """Preflight must reject the bundle before writing the first skill."""
        conflicting = self.target.skills / cli.SKILLS[1]
        conflicting.mkdir(parents=True)
        (conflicting / "SKILL.md").write_text("user content", encoding="utf-8")
        with self.assertRaises(cli.InstallError):
            self.install()
        self.assertFalse((self.target.skills / cli.SKILLS[0]).exists())
        self.assertFalse(self.target.manager.exists())
        self.assertEqual((conflicting / "SKILL.md").read_text(), "user content")

    def test_force_backs_up_complete_old_directory(self):
        """Forced replacement retains user additions, but removes them from new install."""
        self.install()
        custom = self.target.skills / cli.SKILLS[0] / "custom.txt"
        custom.write_text("keep this", encoding="utf-8")
        self.install(force=True)
        backups = list((self.target.manager / "backups").iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / cli.SKILLS[0] / "custom.txt").read_text(), "keep this")
        self.assertFalse(custom.exists())

    def test_update_unmodified_old_bundle(self):
        """Baseline-matching old skills can be updated without forcing."""
        self.install()
        newer = self.changed_payload()
        self.install(newer, update=True)
        for name in cli.SKILLS:
            self.assertEqual((self.target.skills / name / "SKILL.md").read_bytes(), newer[name]["SKILL.md"])
        self.assertEqual(len(list((self.target.manager / "backups").iterdir())), 1)

    def test_update_local_change_is_protected(self):
        """Update must not overwrite an edited skill even when another is unchanged."""
        self.install()
        changed = self.target.skills / cli.SKILLS[1] / "SKILL.md"
        changed.write_bytes(b"user edit")
        original = (self.target.skills / cli.SKILLS[0] / "SKILL.md").read_bytes()
        with self.assertRaises(cli.InstallError):
            self.install(self.changed_payload(), update=True)
        self.assertEqual(changed.read_bytes(), b"user edit")
        self.assertEqual((self.target.skills / cli.SKILLS[0] / "SKILL.md").read_bytes(), original)

    def test_update_requires_complete_install(self):
        """Update must not masquerade as first installation or repair a missing skill."""
        with self.assertRaises(cli.InstallError):
            self.install(update=True)
        self.assertFalse(self.target.root.exists())

    def test_old_files_removed_on_update(self):
        """Whole-directory replacement must remove obsolete tracked files."""
        old = copy.deepcopy(self.payload)
        old[cli.SKILLS[0]]["assets/old.md"] = b"obsolete"
        self.install(old)
        self.install(update=True)
        self.assertFalse((self.target.skills / cli.SKILLS[0] / "assets/old.md").exists())

    def test_rollback_second_skill_failure(self):
        """Failure after replacing the first skill must restore both and old metadata."""
        self.install()
        original = {name: cli.snapshot(self.target.skills / name) for name in cli.SKILLS}
        record = self.target.record.read_bytes()
        real_rename = Path.rename

        def fail_second(path, destination):
            """Inject a failure only while committing the second staged skill."""
            if path.parent.name == "new" and path.name == cli.SKILLS[1]:
                raise OSError("simulated second skill failure")
            return real_rename(path, destination)

        with patch.object(Path, "rename", fail_second), self.assertRaises(OSError):
            self.install(self.changed_payload(), update=True)
        self.assertEqual({name: cli.snapshot(self.target.skills / name) for name in cli.SKILLS}, original)
        self.assertEqual(self.target.record.read_bytes(), record)
        self.assertFalse(list(self.target.manager.glob(".stage-*")))

    def test_first_install_failure_leaves_neither_skill(self):
        """A failed fresh install must not leave a partially installed bundle."""
        real_rename = Path.rename

        def fail_second(path, destination):
            """Inject the fresh transaction's second directory failure."""
            if path.parent.name == "new" and path.name == cli.SKILLS[1]:
                raise OSError("fresh install failure")
            return real_rename(path, destination)

        with patch.object(Path, "rename", fail_second), self.assertRaises(OSError):
            self.install()
        self.assertTrue(all(not (self.target.skills / n).exists() for n in cli.SKILLS))
        self.assertFalse(self.target.record.exists())

    def test_manifest_commit_failure_rolls_back(self):
        """Metadata commit failure must restore every replaced skill."""
        self.install()
        before = self.target.record.read_bytes()
        with patch.object(cli.os, "replace", side_effect=OSError("manifest failure")), self.assertRaises(OSError):
            self.install(self.changed_payload(), update=True)
        self.assertEqual(self.target.record.read_bytes(), before)
        for name in cli.SKILLS:
            self.assertEqual((self.target.skills / name / "SKILL.md").read_bytes(), self.payload[name]["SKILL.md"])

    def test_keyboard_interrupt_rolls_back(self):
        """User interruption during commit gets the same bundle rollback."""
        self.install()
        real_rename = Path.rename

        def interrupt(path, destination):
            """Interrupt only after the first directory has been replaced."""
            if path.parent.name == "new" and path.name == cli.SKILLS[1]:
                raise KeyboardInterrupt()
            return real_rename(path, destination)

        with patch.object(Path, "rename", interrupt), self.assertRaises(KeyboardInterrupt):
            self.install(self.changed_payload(), update=True)
        for name in cli.SKILLS:
            self.assertEqual((self.target.skills / name / "SKILL.md").read_bytes(), self.payload[name]["SKILL.md"])

    def test_failed_rollback_keeps_recovery_files(self):
        """Never discard staged or backed-up data if recovery itself fails."""
        self.install()
        real_rename = Path.rename

        def fail_commit_and_restore(path, destination):
            """Fail commit and one restore without affecting unrelated moves."""
            if (path.parent.name == "new" and path.name == cli.SKILLS[1]
                    or path.parent.parent.name == "backups" and path.name == cli.SKILLS[0]):
                raise OSError("recovery failure")
            return real_rename(path, destination)

        with patch.object(Path, "rename", fail_commit_and_restore), self.assertRaises(cli.InstallError):
            self.install(self.changed_payload(), update=True)
        self.assertEqual(len(list(self.target.manager.glob(".stage-*"))), 1)
        backups = list((self.target.manager / "backups").iterdir())
        self.assertTrue((backups[0] / cli.SKILLS[0] / "SKILL.md").exists())

    def test_corrupted_manifest_blocks_even_force(self):
        """Do not overwrite malformed or foreign metadata under force."""
        self.target.manager.mkdir(parents=True)
        self.target.record.write_text("[]", encoding="utf-8")
        with self.assertRaises(cli.InstallError):
            self.install(force=True)
        self.assertFalse(self.target.skills.exists())

    def test_concurrent_lock_blocks_install(self):
        """An existing lock is not automatically removed or overridden."""
        self.target.manager.mkdir(parents=True)
        lock = self.target.manager / ".lock"
        lock.write_text("busy", encoding="utf-8")
        with self.assertRaises(cli.InstallError):
            self.install()
        self.assertEqual(lock.read_text(), "busy")
        self.assertFalse(self.target.skills.exists())

    def test_target_changed_after_preflight(self):
        """A second read under the lock must catch preflight races."""
        real_snapshot = cli.snapshot
        calls = 0

        def raced_snapshot(path):
            """Simulate a newly arrived destination when the lock is held."""
            nonlocal calls
            calls += 1
            return {"SKILL.md": "changed"} if calls == 3 else real_snapshot(path)

        with patch.object(cli, "snapshot", raced_snapshot), self.assertRaises(cli.InstallError):
            self.install()
        self.assertFalse(self.target.skills.exists())

    def test_codex_native_user_target(self):
        """Codex uses the current official ~/.agents/skills location."""
        with patch.object(Path, "home", return_value=self.root), patch.dict(os.environ, {"CODEX_HOME": str(self.root / "custom")}, clear=True):
            target = cli.resolve_target("codex", None)
        self.assertEqual(target.skills, self.root / ".agents" / "skills")

    def test_hermes_home_override(self):
        """An explicit Hermes home or profile must win over platform defaults."""
        home = self.root / "hermes profile"
        with patch.dict(os.environ, {"HERMES_HOME": str(home)}):
            target = cli.resolve_target("hermes", None)
        self.assertEqual(target.skills, home / "skills")

    def test_hermes_windows_default(self):
        """Windows Hermes uses LOCALAPPDATA/hermes, not ~/.hermes."""
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.root)}, clear=True), patch.object(cli.sys, "platform", "win32"), patch.object(Path, "home", return_value=self.root):
            target = cli.resolve_target("hermes", None)
        self.assertEqual(target.skills, self.root / "hermes" / "skills")

    def test_hermes_unix_default(self):
        """Unix Hermes uses the native .hermes user directory."""
        with patch.dict(os.environ, {}, clear=True), patch.object(cli.sys, "platform", "linux"), patch.object(Path, "home", return_value=self.root):
            target = cli.resolve_target("hermes", None)
        self.assertEqual(target.skills, self.root / ".hermes" / "skills")

    def test_project_targets_and_hermes_git_requirement(self):
        """Use distinct project paths without silently creating a Git repository."""
        self.assertEqual(cli.resolve_target("codex", str(self.root)).skills, self.target.skills)
        with self.assertRaises(cli.InstallError):
            cli.resolve_target("hermes", str(self.root))
        (self.root / ".git").write_text("gitdir: elsewhere", encoding="utf-8")
        self.assertEqual(cli.resolve_target("hermes", str(self.root)).skills, self.root / ".hermes" / "skills")

    def test_dangerous_hermes_root_rejected(self):
        """Misconfigured agent home must not select an entire disk or user home."""
        with patch.dict(os.environ, {"HERMES_HOME": self.root.anchor}):
            with self.assertRaises(cli.InstallError):
                cli.resolve_target("hermes", None)

    def test_symlink_is_rejected(self):
        """Linked skill directories must not redirect a replacement outside scope."""
        self.target.skills.mkdir(parents=True)
        outside = self.root / "outside"
        outside.mkdir()
        link = self.target.skills / cli.SKILLS[0]
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("symlink privileges unavailable")
        with self.assertRaises(cli.InstallError):
            self.install(force=True)
        self.assertTrue(outside.exists())

    @unittest.skipUnless(sys.platform == "win32", "Windows junction check")
    def test_windows_junction_is_rejected(self):
        """Reject Windows junctions even when ordinary symlinks are unavailable."""
        self.target.skills.mkdir(parents=True)
        outside = self.root / "outside"
        outside.mkdir()
        link = self.target.skills / cli.SKILLS[0]
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
        if result.returncode:
            self.skipTest("junction creation unavailable")
        try:
            with self.assertRaises(cli.InstallError):
                self.install(force=True)
            self.assertTrue(outside.exists())
        finally:
            link.rmdir()

    def test_agent_isolation_and_unrelated_skills(self):
        """Never touch another agent or unrelated directories in the destination."""
        other = self.root / ".hermes" / "skills" / "unrelated"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("unchanged", encoding="utf-8")
        same_agent_other = self.target.skills / "unrelated"
        same_agent_other.mkdir(parents=True)
        (same_agent_other / "SKILL.md").write_text("unchanged", encoding="utf-8")
        self.install()
        self.assertEqual((other / "SKILL.md").read_text(), "unchanged")
        self.assertEqual((same_agent_other / "SKILL.md").read_text(), "unchanged")

    def test_status_and_no_write(self):
        """Status must distinguish missing, healthy, old and locally modified skills."""
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.show_status(self.target, self.payload), 1)
        self.assertFalse(self.target.root.exists())
        self.install()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.show_status(self.target, self.payload), 0)
            self.assertEqual(cli.show_status(self.target, self.changed_payload()), 0)
        (self.target.skills / cli.SKILLS[0] / "SKILL.md").write_bytes(b"changed")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.show_status(self.target, self.payload), 1)

    def test_parser_rejects_single_skill_and_unknown_agent(self):
        """Agent is mandatory; neither third-party agents nor --skill are accepted."""
        for args in (["install"], ["install", "--agent", "claude"],
                     ["install", "--agent", "codex", "--skill", "spec"],
                     ["init", "--agent", "codex"],
                     ["init", "--agent", "codex", "--here", "--project", str(self.root)]):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                cli.main(args)
            self.assertEqual(exc.exception.code, 2)

    def test_cli_project_install(self):
        """Exercise the public argument parser and operation dispatch end to end."""
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["init", "--agent", "codex", "--project", str(self.root)]), 0)
            self.assertEqual(cli.main(["status", "--agent", "codex", "--project", str(self.root)]), 0)
        self.assertEqual(set(p.name for p in self.target.skills.iterdir()), set(cli.SKILLS))


if __name__ == "__main__":
    unittest.main()
