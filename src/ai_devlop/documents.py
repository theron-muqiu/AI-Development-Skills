"""Validate and render one structured requirement directory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from importlib import resources
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


DOCUMENTS = {
    "raw": ("原始需求/原始需求.json", "ai-devlop-spec", "原始需求"),
    "spec": ("ai-devlop-spec/需求分析.json", "ai-devlop-spec", "需求分析"),
    "plan": ("ai-devlop-plan/详细设计.json", "ai-devlop-plan", "详细设计"),
    "api": ("ai-devlop-plan/接口设计.json", "ai-devlop-plan", "接口设计"),
    "data": ("ai-devlop-plan/数据结构设计.json", "ai-devlop-plan", "数据结构设计"),
    "task": ("ai-devlop-task/任务清单.json", "ai-devlop-task", "任务清单"),
    "implement": ("ai-devlop-implement/实现记录.json", "ai-devlop-implement", "实现记录"),
}


@dataclass(frozen=True)
class Diagnostic:
    """A location-aware validation finding."""

    file: str
    pointer: str
    code: str
    message: str


def _pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON members before schema validation."""
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise ValueError(f"重复属性：{key}")
        result[key] = value
    return result


def _pointer(parts: Any) -> str:
    """Encode a JSON Pointer for diagnostics."""
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts)


def _resource(relative: str):
    """Find packaged resources, or the canonical checkout source."""
    packaged = resources.files("ai_devlop").joinpath("resources", "documents", relative)
    if packaged.is_file():
        return packaged
    return Path(__file__).absolute().parents[2] / "resources" / "documents" / relative


def _schema(kind: str) -> dict[str, Any]:
    """Load the canonical schema bundled with its producing skill."""
    _, skill, name = DOCUMENTS[kind]
    packaged = resources.files("ai_devlop").joinpath(
        "resources", "skills", skill, "assets", name + ".schema.json"
    )
    source = packaged if packaged.is_file() else Path(__file__).absolute().parents[2] / "skills" / skill / "assets" / (name + ".schema.json")
    return json.loads(source.read_text(encoding="utf-8"))


def _within(path: Path, root: Path) -> bool:
    """Keep requirement references and attachments inside their requirement."""
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def load_documents(root: Path, extra: list[Path]) -> tuple[dict[Path, dict], list[Diagnostic]]:
    """Find present stages and recursively load explicit local references."""
    root = root.resolve()
    diagnostics: list[Diagnostic] = []
    pending: list[Path] = [root / relative for relative, _, _ in DOCUMENTS.values() if (root / relative).is_file()]
    pending.extend((path if path.is_absolute() else root / path) for path in extra)
    loaded: dict[Path, dict] = {}
    while pending:
        path = pending.pop().resolve()
        label = str(path)
        if not _within(path, root):
            diagnostics.append(Diagnostic(label, "", "outside_requirement", "文件位于需求目录之外"))
            continue
        if path in loaded:
            continue
        if not path.is_file():
            diagnostics.append(Diagnostic(label, "", "missing_document", "引用的文档不存在"))
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_pairs)
        except (OSError, UnicodeError, ValueError) as exc:
            diagnostics.append(Diagnostic(label, "", "invalid_json", str(exc)))
            continue
        if not isinstance(data, dict):
            diagnostics.append(Diagnostic(label, "", "invalid_document", "顶层必须是 JSON 对象"))
            continue
        loaded[path] = data
        for ref, pointer in _references(data):
            target = (path.parent / ref["path"]).resolve()
            if not _within(target, root):
                diagnostics.append(Diagnostic(label, pointer, "outside_requirement", "引用越出当前需求目录"))
            elif target not in loaded:
                pending.append(target)
    if not loaded and not diagnostics:
        diagnostics.append(Diagnostic(str(root), "", "empty_requirement", "未发现 JSON 文档"))
    return loaded, diagnostics


def _references(data: Any):
    """Yield internal file/entity references with source pointers."""
    def walk(node: Any, parts: list[str | int]):
        if isinstance(node, dict):
            if {"path", "id"}.issubset(node) and set(node).issubset({"path", "id", "locator", "url"}) and all(isinstance(node[k], str) for k in ("path", "id")):
                yield node, _pointer(parts)
            else:
                for key, value in node.items():
                    yield from walk(value, [*parts, key])
        elif isinstance(node, list):
            for index, value in enumerate(node):
                yield from walk(value, [*parts, index])
    yield from walk(data, [])


def validate(root: Path, extra: list[Path] | None = None) -> tuple[dict[Path, dict], list[Diagnostic]]:
    """Validate schemas, provenance, references, dependencies, and task status."""
    root = root.resolve()
    loaded, diagnostics = load_documents(root, extra or [])
    ids_by_file: dict[Path, dict[str, str]] = {}
    valid_by_file: dict[Path, bool] = {}
    requirement_ids = set()
    by_kind: dict[str, tuple[Path, dict]] = {}
    for path, data in loaded.items():
        label = str(path)
        kind = data.get("documentType")
        if not isinstance(kind, str) or kind not in DOCUMENTS:
            diagnostics.append(Diagnostic(label, "/documentType", "unknown_document_type", "未知文档类型"))
            continue
        if kind in by_kind:
            diagnostics.append(Diagnostic(label, "/documentType", "duplicate_document_type", "同一需求存在重复文档类型"))
        by_kind[kind] = path, data
        if isinstance(data.get("requirementId"), str):
            requirement_ids.add(data["requirementId"])
        schema_errors = list(Draft202012Validator(_schema(kind), format_checker=FormatChecker()).iter_errors(data))
        valid_by_file[path] = not schema_errors
        for error in schema_errors:
            diagnostics.append(Diagnostic(label, _pointer(error.absolute_path), "schema", error.message))
        seen: dict[str, str] = {}

        def walk(node: Any, parts: list[str | int]) -> None:
            if isinstance(node, dict):
                if {"path", "id"}.issubset(node) and set(node).issubset({"path", "id", "locator", "url"}):
                    return
                entity_id = node.get("id")
                if isinstance(entity_id, str):
                    pointer = _pointer(parts)
                    if entity_id in seen:
                        diagnostics.append(Diagnostic(label, pointer + "/id", "duplicate_id", f"编号 {entity_id} 与 {seen[entity_id]} 重复"))
                    else:
                        seen[entity_id] = pointer
                for key, value in node.items():
                    walk(value, [*parts, key])
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, [*parts, index])
        walk(data, [])
        ids_by_file[path] = seen
    if len(requirement_ids) > 1:
        for path in loaded:
            diagnostics.append(Diagnostic(str(path), "/requirementId", "requirement_mismatch", "需求编号与关联文档不一致"))

    for path, data in loaded.items():
        if not valid_by_file.get(path, False):
            continue
        for ref, pointer in _references(data):
            target = (path.parent / ref["path"]).resolve()
            if not _within(target, root):
                continue
            if target not in loaded:
                diagnostics.append(Diagnostic(str(path), pointer, "missing_reference_document", f"引用文件不存在：{ref['path']}"))
            elif ref["id"] not in ids_by_file.get(target, {}):
                diagnostics.append(Diagnostic(str(path), pointer, "missing_reference_id", f"引用编号不存在：{ref['id']}"))
        if data.get("documentType") == "spec":
            for key in ("terms", "goals", "rules", "scenarios", "stateTransitions"):
                for index, node in enumerate(data.get(key, [])):
                    if isinstance(node, dict) and not node.get("sourceRefs"):
                        diagnostics.append(Diagnostic(str(path), f"/{key}/{index}/sourceRefs", "missing_source", "需求结论必须有出处"))
        if data.get("documentType") == "raw":
            times = [entry.get("timestamp", "") for entry in data.get("entries", []) if isinstance(entry, dict)]
            try:
                parsed = [datetime.fromisoformat(value.replace("Z", "+00:00")) for value in times]
                if any(value.tzinfo is None for value in parsed):
                    raise ValueError("timestamp 需包含时区")
                ordered = parsed == sorted(parsed)
            except ValueError:
                ordered = None
                diagnostics.append(Diagnostic(str(path), "/entries", "invalid_timestamp", "输入时间需为带时区的 ISO 8601 时间"))
            if ordered is False:
                diagnostics.append(Diagnostic(str(path), "/entries", "input_order", "原始输入必须按时间正序排列"))
            for i, entry in enumerate(data.get("entries", [])):
                for j, attachment in enumerate(entry.get("attachments", [])):
                    target = (path.parent / attachment.get("path", "")).resolve()
                    if not _within(target, root) or not target.is_file():
                        diagnostics.append(Diagnostic(str(path), f"/entries/{i}/attachments/{j}/path", "missing_attachment", "附件路径无效"))
        if data.get("documentType") == "implement":
            for key in ("taskResults", "verifications"):
                items = data.get(key, [])
                try:
                    moments = [datetime.fromisoformat(item["recordedAt"].replace("Z", "+00:00")) for item in items]
                    if any(moment.tzinfo is None for moment in moments) or moments != sorted(moments):
                        raise ValueError("记录时间无效或未按时间排序")
                except ValueError:
                    diagnostics.append(Diagnostic(str(path), f"/{key}", "record_order", "历史记录需有带时区的时间并按时间正序排列"))

    if "task" in by_kind:
        task_path, task_doc = by_kind["task"]
        if not valid_by_file.get(task_path, False):
            diagnostics.sort(key=lambda d: (d.file, d.pointer, d.code))
            return loaded, diagnostics
        tasks = {task.get("id"): task for task in task_doc.get("tasks", []) if isinstance(task, dict)}
        if "implement" not in by_kind:
            for task_id, task in tasks.items():
                if task.get("status") == "completed":
                    diagnostics.append(Diagnostic(str(task_path), "/tasks", "missing_completion_evidence", f"任务 {task_id} 缺少实现记录"))
        for i, task in enumerate(task_doc.get("tasks", [])):
            for dependency in task.get("dependsOn", []):
                if dependency not in tasks:
                    diagnostics.append(Diagnostic(str(task_path), f"/tasks/{i}/dependsOn", "missing_dependency", f"前置任务不存在：{dependency}"))
                elif dependency == task.get("id"):
                    diagnostics.append(Diagnostic(str(task_path), f"/tasks/{i}/dependsOn", "dependency_cycle", "任务不能依赖自己"))
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                diagnostics.append(Diagnostic(str(task_path), "/tasks", "dependency_cycle", f"任务依赖存在环：{task_id}"))
                return
            if task_id in visited or task_id not in tasks:
                return
            visiting.add(task_id)
            for previous in tasks[task_id].get("dependsOn", []):
                visit(previous)
            visiting.remove(task_id)
            visited.add(task_id)
        for task_id in tasks:
            visit(task_id)
        if "implement" in by_kind:
            implementation_path, implementation = by_kind["implement"]
            if not valid_by_file.get(implementation_path, False):
                diagnostics.sort(key=lambda d: (d.file, d.pointer, d.code))
                return loaded, diagnostics
            results: dict[str, list[dict]] = {}
            for result in implementation.get("taskResults", []):
                if isinstance(result, dict):
                    results.setdefault(result.get("taskRef", {}).get("id"), []).append(result)
            verifications = {item.get("id"): item for item in implementation.get("verifications", []) if isinstance(item, dict)}
            for task_id, task in tasks.items():
                history = results.get(task_id, [])
                if history and history[-1].get("status") != task.get("status"):
                    diagnostics.append(Diagnostic(str(implementation_path), "/taskResults", "status_mismatch", f"任务 {task_id} 当前状态与最新记录不一致"))
                if task.get("status") == "completed":
                    if not history:
                        diagnostics.append(Diagnostic(str(task_path), "/tasks", "missing_completion_evidence", f"任务 {task_id} 缺少实现记录"))
                    else:
                        evidence = history[-1].get("evidenceRefs", [])
                        if not evidence or not any(verifications.get(ref.get("id"), {}).get("result") == "passed" for ref in evidence):
                            diagnostics.append(Diagnostic(str(implementation_path), "/taskResults", "missing_completion_evidence", f"任务 {task_id} 缺少通过的验证依据"))
            if implementation.get("conclusion") == "complete" and any(t.get("status") != "completed" for t in tasks.values()):
                diagnostics.append(Diagnostic(str(implementation_path), "/conclusion", "incomplete_conclusion", "存在未完成任务，整体结论不能为全部完成"))
    diagnostics.sort(key=lambda d: (d.file, d.pointer, d.code))
    return loaded, diagnostics


def run_docs(args) -> int:
    """Handle the public docs validate/render commands."""
    root = args.requirement_dir.resolve()
    documents, diagnostics = validate(root, args.document)
    if args.format == "json":
        print(json.dumps({"valid": not diagnostics, "documents": len(documents),
                          "diagnostics": [d.__dict__ for d in diagnostics]}, ensure_ascii=False, indent=2))
    else:
        for finding in diagnostics:
            print(f"{finding.file}{finding.pointer}: [{finding.code}] {finding.message}", file=sys.stderr)
        if not diagnostics:
            print(f"校验通过：{len(documents)} 份文档")
    if diagnostics:
        return 1
    if args.docs_command == "render":
        try:
            from .reader import render
            target = render(root, documents)
        except (OSError, ValueError) as exc:
            print(f"渲染失败，原 index.html 未替换：{exc}", file=sys.stderr)
            return 1
        if args.format != "json":
            print(f"已生成：{target}")
    return 0
