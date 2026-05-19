#!/usr/bin/env python3
"""Render standardized Yunxiao work item comments from structured data."""

from __future__ import annotations

import argparse
import json
from typing import Any


def load_config(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def pick(config: dict[str, Any], name: str, fallback: str = "") -> str:
    value = config.get(name, fallback)
    return fallback if value is None else str(value)


def pick_list(config: dict[str, Any], name: str) -> list[str]:
    value = config.get(name, [])
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []


def bullet(items: list[str], fallback: str = "无") -> str:
    values = items or [fallback]
    return "\n".join(f"- {item}" for item in values)


def render_done(config: dict[str, Any]) -> str:
    notes = pick_list(config, "notes")
    notes_block = f"\n备注：\n{bullet(notes)}\n" if notes else ""
    return f"""AI: 已处理

项目：{pick(config, 'project', '需人工确认')}
路径：{pick(config, 'trigger_path', '需人工确认')}

改动：
{bullet(pick_list(config, 'changes'))}

核验：{pick(config, 'verification_result', pick(config, 'verification_level', '需人工确认'))}
{notes_block}""".rstrip()


def render_blocked(config: dict[str, Any]) -> str:
    return f"""暂未处理。

处理项目：
- {pick(config, 'project', '需人工确认')}

触发路径：
- {pick(config, 'trigger_path', '需人工确认')}

阻塞原因：
- {pick(config, 'result', '缺少必要信息或能力')}

需要补充：
{bullet(pick_list(config, 'needs'))}"""


def render_backend_gap(config: dict[str, Any]) -> str:
    owner = pick(config, "backend_owner", "<backend owner>")
    key = pick(config, "work_item_key", "<work item key>")
    return f"""@{owner} {key} 需要后端补一下。

目标路径：
{pick(config, 'target_path', '需人工确认')}

缺少功能：
{pick(config, 'missing_capability', '需人工确认')}

建议调整：
{pick(config, 'suggested_change', '需人工确认')}"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Yunxiao comment")
    parser.add_argument("kind", choices=["done", "blocked", "backend-gap"])
    parser.add_argument("--config", help="JSON file with comment fields")
    parser.add_argument("--set", action="append", default=[], help="Set scalar field: key=value")
    parser.add_argument("--list", action="append", default=[], help="Append list item: key=value")
    args = parser.parse_args()

    config = load_config(args.config)
    for item in args.set:
        if "=" not in item:
            parser.error("--set expects key=value")
        key, value = item.split("=", 1)
        config[key] = value
    for item in args.list:
        if "=" not in item:
            parser.error("--list expects key=value")
        key, value = item.split("=", 1)
        config.setdefault(key, [])
        if not isinstance(config[key], list):
            config[key] = [config[key]]
        config[key].append(value)

    if args.kind == "done":
        print(render_done(config))
    elif args.kind == "blocked":
        print(render_blocked(config))
    else:
        print(render_backend_gap(config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
