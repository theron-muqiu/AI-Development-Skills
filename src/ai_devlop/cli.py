"""Install the complete skill bundle as one guarded filesystem transaction."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from importlib import resources
import re
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone

from . import __version__

SKILLS = ("ai-devlop-spec", "ai-devlop-plan", "ai-devlop-task", "ai-devlop-implement")
LEGACY_SKILLS = SKILLS[:2]
PRE_IMPLEMENT_SKILLS = SKILLS[:3]
REQUIRED_ASSETS = {
    SKILLS[0]: ("需求分析.md",),
    SKILLS[1]: ("详细设计.md", "接口设计.md", "数据结构设计.md"),
    SKILLS[2]: ("任务清单.md",),
    SKILLS[3]: ("实现记录.md",),
}


class InstallError(Exception):
    """An installation could not safely proceed."""


@dataclass(frozen=True)
class Target:
    """Resolved agent directory; management data stays outside skills discovery."""

    agent: str
    root: Path
    project: bool = False

    @property
    def skills(self) -> Path:
        """Return the agent's native skills directory."""
        return self.root / "skills"

    @property
    def manager(self) -> Path:
        """Return the installer-owned state and backup directory."""
        return self.root / "ai-devlop"

    @property
    def record(self) -> Path:
        """Return the install manifest for this destination."""
        return self.manager / "install.json"


def check_path(path: Path, *, directory: bool) -> None:
    """Reject links, Windows junctions and wrong types before filesystem changes."""
    for candidate in reversed((path, *path.parents)):
        if not os.path.lexists(candidate):
            continue
        info = candidate.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise InstallError(f"不支持链接或 junction 路径：{candidate}")
        expects_dir = directory if candidate == path else True
        if expects_dir and not stat.S_ISDIR(info.st_mode):
            raise InstallError(f"目标不是普通目录：{candidate}")
        if not expects_dir and not stat.S_ISREG(info.st_mode):
            raise InstallError(f"目标不是普通文件：{candidate}")


def resolve_target(agent: str, project: str | None) -> Target:
    """Use native user directories or an explicit existing project directory."""
    if project is not None:
        project_root = Path(project).expanduser().absolute()
        check_path(project_root, directory=True)
        if not project_root.is_dir():
            raise InstallError(f"项目目录不存在：{project_root}")
        # Hermes discovers only the nearest Git root, and never auto-trusts it.
        if agent == "hermes" and (project_root == Path.home().absolute()
                                  or not (project_root / ".git").exists()):
            raise InstallError("Hermes 项目级安装必须指定非主目录的 Git 根目录；不自动创建 Git 仓库。")
        root = project_root / (".agents" if agent == "codex" else ".hermes")
    elif agent == "codex":
        root = Path.home() / ".agents"
    else:
        configured = os.environ.get("HERMES_HOME", "").strip()
        if configured:
            root = Path(os.path.expandvars(configured)).expanduser().absolute()
        elif sys.platform == "win32":
            local = os.environ.get("LOCALAPPDATA", "").strip()
            root = (Path(local) if local else Path.home() / "AppData" / "Local") / "hermes"
        else:
            root = Path.home() / ".hermes"
    root = Path(os.path.abspath(root))
    if root == Path(root.anchor) or root == Path.home().absolute():
        raise InstallError("Agent 目录不能直接设置为磁盘根目录或用户主目录。")
    check_path(root, directory=True)
    return Target(agent, root, project is not None)


def load_payload() -> dict[str, dict[str, bytes]]:
    """Load packaged resources, or the single canonical source in a checkout."""
    source = resources.files("ai_devlop").joinpath("resources", "skills")
    if not source.is_dir():
        source = Path(__file__).absolute().parents[2] / "skills"
        if not source.is_dir():
            raise InstallError("安装包缺少技能资源，请重新构建或安装完整包。")
    payload: dict[str, dict[str, bytes]] = {}
    for name in SKILLS:
        skill = source.joinpath(name)
        if isinstance(skill, Path):
            check_path(skill, directory=True)
        if not skill.is_dir():
            raise InstallError(f"安装包缺少技能：{name}")
        files: dict[str, bytes] = {}
        pending = [(skill, "")]
        while pending:
            node, prefix = pending.pop()
            for entry in node.iterdir():
                if entry.name in (".", "..") or any(c in entry.name for c in "/\\:"):
                    raise InstallError("安装包包含非法资源路径。")
                relative = prefix + entry.name
                if isinstance(entry, Path):
                    check_path(entry, directory=entry.is_dir())
                if entry.is_dir():
                    pending.append((entry, relative + "/"))
                elif entry.is_file():
                    files[relative] = entry.read_bytes()
                else:
                    raise InstallError(f"安装包包含非普通文件：{relative}")
        for required in ("SKILL.md", *("assets/" + a for a in REQUIRED_ASSETS[name])):
            if required not in files:
                raise InstallError(f"安装包缺少必要资源：{name}/{required}")
        definition = files["SKILL.md"].decode("utf-8-sig")
        if not re.search(r"(?m)^name:\s*" + re.escape(name) + r"\s*$", definition):
            raise InstallError(f"技能名称与目录不一致：{name}")
        payload[name] = files
    return payload


def snapshot(path: Path) -> dict[str, str] | None:
    """Hash every installed file, rejecting links and preserving extra-file detection."""
    check_path(path, directory=True)
    if not path.exists():
        return None
    hashes: dict[str, str] = {}
    for entry in path.rglob("*"):
        check_path(entry, directory=entry.is_dir())
        if entry.is_file():
            hashes[entry.relative_to(path).as_posix()] = hashlib.sha256(entry.read_bytes()).hexdigest()
    return hashes


def read_record(target: Target) -> dict | None:
    """Validate metadata without trusting it to select any filesystem path."""
    check_path(target.record, directory=False)
    if not target.record.exists():
        return None
    try:
        record = json.loads(target.record.read_text(encoding="utf-8"))
        if (record["schema"] != 1 or record["agent"] != target.agent
                or record["target"] != str(target.skills)
                or not isinstance(record["version"], str)
                or set(record["skills"]) not in (set(SKILLS), set(LEGACY_SKILLS),
                                                  set(PRE_IMPLEMENT_SKILLS))):
            raise ValueError("manifest identity")
        for hashes in record["skills"].values():
            if not isinstance(hashes, dict) or "SKILL.md" not in hashes:
                raise ValueError("manifest hashes")
            for name, digest in hashes.items():
                if (not isinstance(name, str) or not isinstance(digest, str)
                        or not re.fullmatch(r"[0-9a-f]{64}", digest)):
                    raise ValueError("manifest entry")
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise InstallError(f"安装记录损坏或不属于此目标：{target.record}") from exc
    return record


def apply_install(target: Target, payload: dict[str, dict[str, bytes]], *,
                  update: bool, force: bool, dry_run: bool) -> None:
    """Preflight the bundle, including legacy upgrades, then commit or roll back."""
    check_path(target.skills, directory=True)
    check_path(target.manager, directory=True)
    check_path(target.manager / "backups", directory=True)
    check_path(target.manager / ".lock", directory=False)
    record = read_record(target)
    expected = {name: {file: hashlib.sha256(data).hexdigest() for file, data in files.items()}
                for name, files in payload.items()}
    current = {name: snapshot(target.skills / name) for name in SKILLS}
    # Registered two- or three-skill bundles may add missing skills during update.
    required = tuple(record["skills"]) if record else SKILLS
    if update and any(current[name] is None for name in required):
        raise InstallError("技能尚未完整安装，请先使用 install 或 init。")
    # Without a baseline, differing directories are unowned; never silently adopt them.
    conflicts = []
    for name in SKILLS:
        if current[name] is None or current[name] == expected[name]:
            continue
        baseline = record["skills"].get(name) if record else None
        if not update or current[name] != baseline:
            conflicts.append(name)
    if conflicts and not force:
        raise InstallError("技能存在冲突或本地修改：" + ", ".join(conflicts)
                           + "。确认后使用 --force，旧目录将先备份。")
    manifest = {"schema": 1, "agent": target.agent, "target": str(target.skills),
                "version": __version__, "skills": expected}
    changes = [name for name in SKILLS if current[name] != expected[name]]
    print(f"[{target.agent}] 目标：{target.skills}")
    for name in SKILLS:
        print(f"  {name}：{'安装/替换' if name in changes else '内容一致，跳过'}")
    if dry_run:
        print("预览完成，未写入文件。")
        return
    if not changes and record == manifest:
        print("全部技能已是当前包版本，无需更改。")
        return

    target.manager.mkdir(parents=True, exist_ok=True)
    lock = target.manager / ".lock"
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise InstallError(f"另一个安装正在进行，或中断后遗留锁：{lock}；确认无安装进程后移除锁。") from exc
    workspace: Path | None = None
    backed_up: list[str] = []
    installed: list[str] = []
    backup: Path | None = None
    preserve_workspace = False
    try:
        os.close(lock_fd)
        # Recheck under the lock: another installer may have finished since preflight.
        if (read_record(target) != record
                or any(snapshot(target.skills / name) != current[name] for name in SKILLS)):
            raise InstallError("安装目标在检查后发生变化，请重新执行。")
        workspace = Path(tempfile.mkdtemp(prefix=".stage-", dir=target.manager))
        for name in changes:
            for relative, data in payload[name].items():
                staged_file = workspace / "new" / name / relative
                staged_file.parent.mkdir(parents=True, exist_ok=True)
                staged_file.write_bytes(data)
        staged_record = workspace / "install.json"
        staged_record.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if record is not None:
            shutil.copy2(target.record, workspace / "old-install.json")
        if any(current[name] is not None for name in changes):
            backups = target.manager / "backups"
            backups.mkdir(exist_ok=True)
            prefix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
            backup = Path(tempfile.mkdtemp(prefix=prefix, dir=backups))
            if record is not None:
                shutil.copy2(target.record, backup / "install.json")
        target.skills.mkdir(parents=True, exist_ok=True)
        try:
            for name in changes:
                destination = target.skills / name
                if current[name] is not None:
                    destination.rename(backup / name)
                    backed_up.append(name)
                (workspace / "new" / name).rename(destination)
                installed.append(name)
            # Commit the manifest last, only after all skill directories succeeded.
            os.replace(staged_record, target.record)
        except BaseException as exc:
            rollback_errors = []
            for name in reversed(installed):
                try:
                    destination = target.skills / name
                    check_path(destination, directory=True)
                    destination.rename(workspace / ("failed-" + name))
                except (OSError, InstallError) as rollback_exc:
                    rollback_errors.append(str(rollback_exc))
            for name in reversed(backed_up):
                try:
                    (backup / name).rename(target.skills / name)
                except OSError as rollback_exc:
                    rollback_errors.append(str(rollback_exc))
            try:
                if record is not None:
                    old_record = workspace / "old-install.json"
                    if not target.record.exists() or target.record.read_bytes() != old_record.read_bytes():
                        os.replace(old_record, target.record)
                elif target.record.exists():
                    check_path(target.record, directory=False)
                    target.record.unlink()
            except (OSError, InstallError) as rollback_exc:
                rollback_errors.append(str(rollback_exc))
            if rollback_errors:
                preserve_workspace = True
                raise InstallError(f"回滚未完成，旧文件保留在 {backup}；暂存目录 {workspace}。"
                                   + "; ".join(rollback_errors)) from exc
            raise
        if backup is not None:
            print(f"旧版本备份：{backup}")
        print(f"安装完成，版本 {__version__}。请在新的 {target.agent} 会话中加载技能。")
        if target.agent == "hermes" and target.project:
            print("Hermes 项目技能需用户信任：请在项目内自行运行 hermes skills trust。")
    finally:
        # Remove only our concrete staging directory; keep backups for recovery.
        if workspace is not None and workspace.exists():
            if workspace.parent != target.manager or not workspace.name.startswith(".stage-"):
                raise InstallError("暂存目录清理路径不合法。")
            # Failed rollback data must remain available rather than being discarded.
            if not preserve_workspace:
                check_path(workspace, directory=True)
                shutil.rmtree(workspace)
        lock.unlink(missing_ok=True)


def show_status(target: Target, payload: dict[str, dict[str, bytes]]) -> int:
    """Report integrity separately from whether files match the current CLI payload."""
    record = read_record(target)
    print(f"[{target.agent}] 目标：{target.skills}")
    print(f"CLI 版本：{__version__}；安装记录版本：{record['version'] if record else '无'}")
    healthy = True
    for name in SKILLS:
        current = snapshot(target.skills / name)
        expected = {file: hashlib.sha256(data).hexdigest() for file, data in payload[name].items()}
        if current is None:
            state = "未安装"
            healthy = False
        elif record and current != record["skills"].get(name):
            state = "有本地修改或缺失文件"
            healthy = False
        elif current == expected:
            state = "与当前安装包一致" + ("（未登记）" if record is None else "")
        elif record:
            state = "已安装，内容与当前包不同；可使用 update"
        else:
            state = "未登记且与当前包不同；需检查后使用 --force"
            healthy = False
        print(f"  {name}：{state}")
    return 0 if healthy else 1


def main(argv: list[str] | None = None) -> int:
    """Expose only the two supported agents and whole-bundle operations."""
    parser = argparse.ArgumentParser(prog="ai-devlop", description="为 Codex 或 Hermes 完整安装需求分析和设计技能。")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command")
    for command, help_text in (("install", "用户级安装全部技能"), ("init", "项目级安装全部技能"),
                               ("status", "查看安装状态"), ("update", "用当前包更新全部技能")):
        sub = commands.add_parser(command, help=help_text)
        sub.add_argument("--agent", required=True, choices=("codex", "hermes"))
        if command != "install":
            scope = sub.add_mutually_exclusive_group(required=command == "init")
            scope.add_argument("--here", action="store_true", help="使用当前项目目录")
            scope.add_argument("--project", metavar="PATH", help="使用已有项目目录")
        if command != "status":
            sub.add_argument("--dry-run", action="store_true", help="仅预览，不写入")
            sub.add_argument("--force", action="store_true", help="备份后替换冲突技能")
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    try:
        project = str(Path.cwd()) if getattr(args, "here", False) else getattr(args, "project", None)
        target = resolve_target(args.agent, project)
        payload = load_payload()
        if args.command == "status":
            return show_status(target, payload)
        apply_install(target, payload, update=args.command == "update", force=args.force, dry_run=args.dry_run)
        return 0
    except (InstallError, OSError, UnicodeError) as exc:
        print(f"安装器错误：{exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("安装已中断。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
