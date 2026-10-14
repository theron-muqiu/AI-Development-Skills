"""Build a single self-contained, read-only HTML snapshot."""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape
import hashlib
import json
import os
from pathlib import Path
import tempfile

from .documents import _resource


def render(root: Path, documents: dict[Path, dict]) -> Path:
    """Atomically replace index.html only after all resources are ready."""
    root = root.resolve()
    entries = []
    order = {kind: index for index, kind in enumerate(("raw", "spec", "plan", "api", "data", "task", "implement"))}
    for path, data in sorted(documents.items(), key=lambda item: (order.get(item[1].get("documentType"), 99), item[0].as_posix())):
        raw = path.read_bytes()
        entries.append({"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "data": data})
    payload = json.dumps({"generatedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                          "documents": entries}, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    css = _resource("reader.css").read_text(encoding="utf-8")
    js = _resource("reader.js").read_text(encoding="utf-8")
    vendor = _resource("vendor.js").read_text(encoding="utf-8")
    title = next((data.get("requirementId", "需求") for data in documents.values()), "需求")
    html = ("<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{escape(str(title))} · 需求文档</title><style>{css}</style></head><body>"
            "<aside><h1>需求文档</h1><div id=\"meta\"></div><input id=\"search\" type=\"search\" placeholder=\"搜索文档\" aria-label=\"搜索文档\">"
            "<nav id=\"nav\"></nav><label class=\"filter\">任务状态 <select id=\"status-filter\"><option value=\"all\">全部</option>"
            "<option value=\"pending\">待开始</option><option value=\"in_progress\">进行中</option>"
            "<option value=\"blocked\">受阻</option><option value=\"completed\">完成</option></select></label></aside>"
            "<main id=\"content\"></main><script id=\"doc-data\" type=\"application/json\">"
            f"{payload}</script><script>{vendor}</script><script>{js}</script></body></html>")
    root.mkdir(parents=True, exist_ok=True)
    target = root / "index.html"
    descriptor, temporary = tempfile.mkstemp(prefix=".index-", suffix=".html", dir=root)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(html)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target
