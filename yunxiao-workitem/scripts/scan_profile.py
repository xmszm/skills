#!/usr/bin/env python3
"""Scan a repository and draft a Yunxiao project config JSON."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
}
IGNORE_PATH_PARTS = {
    (".trellis", "tasks"),
    (".trellis", "workspace"),
    (".trellis", ".runtime"),
    (".trellis", ".backup-2026-05-07T09-42-05"),
    (".trellis", ".backup-2026-05-07T10-23-44"),
    (".codex", "agents"),
    (".gemini", "agents"),
    (".gemini", "skills"),
}
DOC_NAMES = {"AGENTS.md", "README.md", "README.zh-CN.md", "readme.md"}
VALIDATION_SCRIPT_PRIORITY = (
    "build:weapp",
    "build:h5",
    "build",
    "typecheck",
    "type-check",
    "lint",
    "test",
)
DEFAULT_CONFIG_PATH = Path(".trellis/config/yunxiao-workitem.json")


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = item.strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def rel(path: Path, root: Path) -> str:
    value = path.relative_to(root).as_posix()
    return "root" if value == "." else value


def iter_files(root: Path, max_depth: int) -> list[Path]:
    result: list[Path] = []
    root_depth = len(root.parts)
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        relative_parts = current_path.relative_to(root).parts
        if any(relative_parts[: len(parts)] == parts for parts in IGNORE_PATH_PARTS):
            dirs[:] = []
            continue
        current_depth = len(current_path.parts) - root_depth
        dirs[:] = [
            name
            for name in dirs
            if name not in IGNORE_DIRS and current_depth < max_depth
        ]
        if current_depth > max_depth:
            continue
        for name in files:
            result.append(current_path / name)
    return result


def scan_docs(root: Path, max_depth: int) -> tuple[str, list[Path]]:
    docs = [path for path in iter_files(root, max_depth) if is_doc_candidate(path, root)]
    text = "\n".join(read_text(path) for path in docs)
    return text, docs


def is_doc_candidate(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    if path.name in DOC_NAMES and len(parts) <= 3:
        return True
    if parts == (".trellis", "workflow.md"):
        return True
    if "yunxiao" in path.name.lower() and path.suffix.lower() in {".md", ".txt"}:
        return True
    return False


def first_match(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" `:：,，。")
    return ""


def infer_project_code(text: str) -> str:
    explicit = first_match(
        [
            r"(?:project\s*code|项目\s*(?:code|编码|代号))\s*[:：]\s*`?([A-Z][A-Z0-9_-]{1,15})`?",
            r"(?:云效|Yunxiao).*?([A-Z][A-Z0-9]{1,12})-\d+",
        ],
        text,
    )
    if explicit:
        return explicit
    counts: dict[str, int] = {}
    for key in re.findall(r"\b([A-Z][A-Z0-9]{1,12})-\d+\b", text):
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def infer_statuses(text: str) -> tuple[list[dict[str, str]], str, str]:
    statuses: list[dict[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if len(cells) < 2 or not any(cell.isdigit() for cell in cells):
            continue
        if len(cells) >= 4 and cells[2].isdigit():
            item_type, status, status_id, meaning = cells[:4]
        elif len(cells) >= 2 and cells[1].isdigit():
            item_type, status, status_id = "Bug", cells[0], cells[1]
            meaning = "unknown"
        else:
            continue
        if status.lower() in {"status", "id"} or item_type.lower() == "type":
            continue
        if meaning == "unknown":
            if re.search(r"处理中|进行中|active|progress", status, re.I):
                meaning = "active"
            elif re.search(r"关闭|完成|修复|取消|terminal|closed|done|fixed", status, re.I):
                meaning = "terminal"
            else:
                meaning = "unfinished"
        statuses.append(
            {"type": item_type, "status": status, "id": status_id, "meaning": meaning}
        )

    unfinished_match = re.search(
        r"Treat unfinished[^`]*statuses as `([^`]+)`", text, flags=re.I
    )
    unfinished = unfinished_match.group(1).strip() if unfinished_match else ""
    active = ""
    for item in statuses:
        if item["meaning"] == "active":
            active = item["id"]
            break
    return statuses, unfinished, active


def infer_ids(text: str) -> dict[str, str]:
    return {
        "organization_id": first_match(
            [
                r"`?organizationId`?\s*[:：]\s*`?([A-Za-z0-9_-]{8,})`?",
                r"`?organization_id`?\s*[:：]\s*`?([A-Za-z0-9_-]{8,})`?",
            ],
            text,
        ),
        "project_id": first_match(
            [
                r"`?(?:spaceId|projectId)`?\s*(?:/[^:：]+)?[:：]\s*`?([A-Za-z0-9_-]{8,})`?",
                r"`?project_id`?\s*[:：]\s*`?([A-Za-z0-9_-]{8,})`?",
            ],
            text,
        ),
    }


def infer_names(text: str) -> dict[str, str]:
    return {
        "organization": first_match(
            [r"(?:Organization|组织)\s*[:：]\s*`?([^`\n]+)`?"],
            text,
        ),
        "project": first_match(
            [r"(?:Project|项目)\s*[:：]\s*`?([^`\n]+)`?"],
            text,
        ),
    }


def infer_rules(text: str) -> list[str]:
    rules: list[str] = []
    for line in text.splitlines():
        stripped = line.strip(" -*\t")
        lowered = stripped.lower()
        if not stripped:
            continue
        if lowered.startswith("do not use sub") or lowered.startswith("treat `api/`"):
            rules.append(stripped)
        elif any(
            token in lowered
            for token in (
                "read-only",
                "dirty worktree",
                "preserve unrelated",
            )
        ):
            rules.append(stripped)
        elif "只读" in stripped or "不要使用子" in stripped or "保留无关" in stripped:
            rules.append(stripped)
    return unique(rules)


def infer_heading_list(text: str, headings: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    heading_pattern = "|".join(re.escape(heading) for heading in headings)
    pattern = rf"(?im)^\s*(?:#+\s*)?(?:{heading_pattern})\s*:?\s*$"
    for match in re.finditer(pattern, text):
        tail = text[match.end() :].splitlines()
        for line in tail:
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r"^#{1,6}\s+\S|^[A-Za-z][A-Za-z\s-]{2,}:$", stripped):
                break
            item_match = re.match(r"^[-*]\s+`?([^`\n]+?)`?\s*$", stripped)
            if item_match:
                values.append(item_match.group(1).strip())
            elif values:
                break
    return unique(values)


def load_package(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_existing_config(root: Path) -> dict[str, Any]:
    path = root / DEFAULT_CONFIG_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def detect_runner(package_dir: Path, root: Path) -> str:
    for directory in (package_dir, root):
        if (directory / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (directory / "package-lock.json").exists():
            return "npm"
        if (directory / "yarn.lock").exists():
            return "yarn"
    return "npm"


def scan_packages(root: Path, max_depth: int) -> tuple[list[str], list[str], list[list[str]]]:
    package_paths = [
        path
        for path in iter_files(root, max_depth)
        if path.name == "package.json" and "node_modules" not in path.parts
    ]
    production_targets: list[str] = []
    reference_targets: list[str] = []
    validations: list[list[str]] = []

    for package_path in sorted(package_paths):
        package_dir = package_path.parent
        label = rel(package_dir, root)
        data = load_package(package_path)
        scripts = data.get("scripts") if isinstance(data.get("scripts"), dict) else {}

        if label != "root":
            if re.search(r"(^|[-_/])(ui|mock|demo|prototype)([-_/]|$)", label, re.I):
                reference_targets.append(label)
            else:
                production_targets.append(label)

        for script_name in VALIDATION_SCRIPT_PRIORITY:
            if script_name in scripts:
                runner = detect_runner(package_dir, root)
                validations.append([label, f"{runner} run {script_name}"])
                break

    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in IGNORE_DIRS:
            continue
        name = child.name
        if re.search(r"(^|[-_/])(ui|mock|demo|prototype)([-_/]|$)", name, re.I):
            reference_targets.append(name)
        elif (child / "src").exists() or (child / "package.json").exists():
            production_targets.append(name)

    return unique(production_targets), unique(reference_targets), validations


def scan_profile(root: Path, max_depth: int) -> dict[str, Any]:
    existing = load_existing_config(root)
    text, docs = scan_docs(root, max_depth)
    package_targets, reference_targets, validations = scan_packages(root, max_depth)
    documented_production = infer_heading_list(
        text, ("Production targets", "Production target", "生产目标", "生产目录")
    )
    documented_reference = infer_heading_list(
        text, ("Reference-only targets", "Reference targets", "参考目录", "参考目标")
    )
    ids = infer_ids(text)
    names = infer_names(text)
    statuses, unfinished_statuses, active_status = infer_statuses(text)

    profile: dict[str, Any] = {
        "organization": existing.get("organization", names.get("organization", "")),
        "organization_id": existing.get("organization_id", ids.get("organization_id", "")),
        "project": existing.get("project", names.get("project", "")),
        "project_id": existing.get("project_id", ids.get("project_id", "")),
        "project_code": existing.get("project_code", infer_project_code(text)),
        "default_query": existing.get("default_query", "assigned to `self` and not completed"),
        "owners": existing.get("owners", {}),
        "work_item_types": existing.get("work_item_types", ["Bug", "Task", "Req"]),
        "statuses": existing.get("statuses", statuses),
        "unfinished_statuses": existing.get("unfinished_statuses", unfinished_statuses),
        "active_status": existing.get("active_status", active_status),
        "repository_rules": existing.get("repository_rules") or infer_rules(text),
        "production_targets": existing.get("production_targets") or unique(package_targets + documented_production),
        "reference_targets": existing.get("reference_targets") or unique(reference_targets + documented_reference),
        "status_policy": existing.get("status_policy", ""),
        "implementation_rules": existing.get("implementation_rules", []),
        "validations": existing.get("validations", validations),
        "runtime_notes": existing.get("runtime_notes", []),
        "final_fields": existing.get("final_fields", [
            "Yunxiao status/comment update when applicable.",
        ]),
        "_scan": {
            "root": str(root),
            "docs": [path.relative_to(root).as_posix() for path in docs],
            "notes": [
                "Status IDs usually require Yunxiao workflow metadata or user confirmation.",
                "Review generated values before passing them to init_profile.py.",
            ],
        },
    }
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft a Yunxiao config JSON from a repo")
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--output", help="Write JSON to this path")
    parser.add_argument("--pretty", action="store_true", default=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    profile = scan_profile(root, args.max_depth)
    content = json.dumps(profile, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        Path(args.output).write_text(content + "\n", encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
