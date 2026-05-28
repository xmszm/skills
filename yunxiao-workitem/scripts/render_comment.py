#!/usr/bin/env python3
"""Render standardized Yunxiao work item comments from structured data."""

from __future__ import annotations

import argparse
import html
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


def pick_nested(config: dict[str, Any], object_name: str, name: str) -> str:
    value = config.get(object_name, {})
    if isinstance(value, dict):
        nested = value.get(name, "")
        return "" if nested is None else str(nested)
    return ""


def nested_value(config: dict[str, Any], object_name: str, name: str) -> Any:
    value = config.get(object_name, {})
    if isinstance(value, dict):
        return value.get(name)
    return None


def bullet(items: list[str], fallback: str = "无") -> str:
    values = items or [fallback]
    return "\n".join(f"- {item}" for item in values)


def attr(name: str, value: str) -> str:
    return f' {name}="{html.escape(value, quote=True)}"' if value else ""


def render_structured_mention(value: Any) -> str:
    if not isinstance(value, dict):
        return ""

    mention_html = value.get("mention_html") or value.get("html")
    if mention_html:
        return str(mention_html)

    text = str(value.get("text") or value.get("name") or value.get("display_name") or "")
    mention_id = str(value.get("id") or value.get("mention_id") or "")
    cangjie_key = str(value.get("data-cangjie-key") or value.get("data_cangjie_key") or value.get("cangjie_key") or "")
    if not text or not (mention_id or cangjie_key):
        return ""

    visible_text = text if text.startswith("@") else f"@{text}"
    outer_class = str(value.get("outer_class") or "sc-jJcwTH fUUHak")
    inner_class = str(value.get("class") or value.get("inner_class") or "sc-cPyLVi jAgzPW")
    inner_attrs = (
        attr("data-cangjie-key", cangjie_key)
        + attr("id", mention_id)
        + ' data-type="mention"'
        + attr("class", inner_class)
    )
    return (
        f'<span{attr("class", outer_class)}>'
        f"<span{inner_attrs}>{html.escape(visible_text)}</span>"
        "</span>"
    )


def render_mention(config: dict[str, Any], owner_field: str, role: str, fallback: str) -> str:
    mention_html = pick(config, f"{owner_field}_mention_html")
    if mention_html:
        return mention_html

    nested_mentions = [nested_value(config, "owner_mentions", role), nested_value(config, "mentions", role)]
    for mention in nested_mentions:
        if isinstance(mention, str) and mention.startswith("<span"):
            return mention

    structured_mention = (
        config.get(f"{owner_field}_mention")
        or next((mention for mention in nested_mentions if isinstance(mention, dict)), None)
    )
    rendered = render_structured_mention(structured_mention)
    if rendered:
        return rendered

    nested_owner = next((mention for mention in nested_mentions if isinstance(mention, str)), "")
    owner = pick(config, owner_field) or pick_nested(config, "owners", role) or nested_owner or fallback
    if owner.startswith("@") or owner.startswith("<span"):
        return owner
    return f"@{owner}"


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
    owner = render_mention(config, "backend_owner", "backend", "<backend owner>")
    key = pick(config, "work_item_key", "<work item key>")
    return f"""{owner} {key} 需要后端补一下。

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
