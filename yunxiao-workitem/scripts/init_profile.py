#!/usr/bin/env python3
"""Generate a project-local Yunxiao work item JSON config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = ".trellis/config/yunxiao-workitem.json"
DEFAULT_RUNTIME_LIMITS = {
    "query_page_size": 5,
    "max_enrich_per_round": 3,
    "max_implement_per_round": 1,
    "max_trellis_tasks_per_round": 5,
    "stop_after_code_change": True,
    "full_requires_explicit_confirmation": True,
}
DEFAULT_TRELLIS_INTAKE = {
    "enabled": True,
    "image_root": "system-cache",
    "create_parent_task_for_full": True,
    "leave_yunxiao_unchanged": True,
    "full_drain_until_no_creatable": True,
    "full_execute_after_intake": True,
    "writeback_after_task_done": True,
}


def comma_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_pair(value: str) -> list[str]:
    if "|" not in value:
        raise argparse.ArgumentTypeError("expected '<label>|<value>'")
    label, content = value.split("|", 1)
    return [label.strip(), content.strip()]


def parse_status(value: str) -> dict[str, str]:
    parts = [part.strip() for part in value.split("|")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            "expected '<type>|<status>|<id>|<unfinished|active|terminal>'"
        )
    return {"type": parts[0], "status": parts[1], "id": parts[2], "meaning": parts[3]}


def load_config(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def merge_cli(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    direct_values = {
        "organization": args.organization,
        "organization_id": args.organization_id,
        "project": args.project,
        "project_id": args.project_id,
        "project_code": args.project_code,
        "default_query": args.default_query,
        "backend_owner": args.backend_owner,
        "ui_owner": args.ui_owner,
        "qa_owner": args.qa_owner,
        "unfinished_statuses": args.unfinished_statuses,
        "active_status": args.active_status,
        "status_policy": args.status_policy,
    }
    for key, value in direct_values.items():
        if value:
            config[key] = value

    if args.work_item_types:
        config["work_item_types"] = comma_list(args.work_item_types)
    if args.status:
        config["statuses"] = args.status
    if args.repository_rule:
        config["repository_rules"] = args.repository_rule
    if args.production_target:
        config["production_targets"] = args.production_target
    if args.reference_target:
        config["reference_targets"] = args.reference_target
    if args.implementation_rule:
        config["implementation_rules"] = args.implementation_rule
    if args.validation:
        config["validations"] = args.validation
    if args.final_field:
        config["final_fields"] = args.final_field
    return config


def prompt_missing(config: dict[str, Any], fields: list[str]) -> None:
    for field in fields:
        if config.get(field):
            continue
        value = input(f"{field}: ").strip()
        if value:
            config[field] = value


def normalize(config: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {
        "version": 1,
        "organization": config.get("organization", ""),
        "organization_id": config.get("organization_id", ""),
        "project": config.get("project", ""),
        "project_id": config.get("project_id", ""),
        "project_code": config.get("project_code", ""),
        "default_query": config.get("default_query", "assigned to `self` and not completed"),
        "owners": {
            "backend": config.get("backend_owner", config.get("owners", {}).get("backend", "")),
            "ui_product": config.get("ui_owner", config.get("owners", {}).get("ui_product", "")),
            "qa": config.get("qa_owner", config.get("owners", {}).get("qa", "")),
        },
        "work_item_types": config.get("work_item_types", []),
        "statuses": config.get("statuses", []),
        "unfinished_statuses": config.get("unfinished_statuses", ""),
        "active_status": config.get("active_status", ""),
        "repository_rules": config.get("repository_rules", []),
        "production_targets": config.get("production_targets", []),
        "reference_targets": config.get("reference_targets", []),
        "status_policy": config.get(
            "status_policy",
            "Do not update statuses automatically unless the user or project config explicitly allows it.",
        ),
        "implementation_rules": config.get("implementation_rules", []),
        "validations": config.get("validations", []),
        "runtime_limits": {
            **DEFAULT_RUNTIME_LIMITS,
            **config.get("runtime_limits", {}),
        },
        "trellis_intake": {
            **DEFAULT_TRELLIS_INTAKE,
            **config.get("trellis_intake", {}),
        },
        "runtime_notes": config.get("runtime_notes", []),
        "final_fields": config.get("final_fields", []),
    }
    if "_scan" in config:
        normalized["_scan"] = config["_scan"]
    return normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate .trellis/config/yunxiao-workitem.json"
    )
    parser.add_argument("--config", help="JSON config file with profile fields")
    parser.add_argument("--output", default=DEFAULT_CONFIG_PATH, help="Output JSON path")
    parser.add_argument("--organization")
    parser.add_argument("--organization-id")
    parser.add_argument("--project")
    parser.add_argument("--project-id")
    parser.add_argument("--project-code")
    parser.add_argument("--default-query")
    parser.add_argument("--backend-owner")
    parser.add_argument("--ui-owner")
    parser.add_argument("--qa-owner")
    parser.add_argument("--work-item-types", help="Comma-separated type names")
    parser.add_argument("--unfinished-statuses")
    parser.add_argument("--active-status")
    parser.add_argument("--status", action="append", type=parse_status, default=[])
    parser.add_argument("--repository-rule", action="append", default=[])
    parser.add_argument("--production-target", action="append", default=[])
    parser.add_argument("--reference-target", action="append", default=[])
    parser.add_argument("--status-policy")
    parser.add_argument("--implementation-rule", action="append", default=[])
    parser.add_argument("--validation", action="append", type=parse_pair, default=[])
    parser.add_argument("--final-field", action="append", default=[])
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--print", action="store_true", dest="print_only")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = merge_cli(load_config(args.config), args)

    if args.interactive:
        prompt_missing(
            config,
            [
                "organization",
                "organization_id",
                "project",
                "project_id",
                "project_code",
            ],
        )

    content = json.dumps(normalize(config), ensure_ascii=False, indent=2) + "\n"
    if args.print_only:
        print(content, end="")
        return 0

    output_path = Path(args.output)
    if output_path.exists() and not args.overwrite:
        parser.error(f"{output_path} exists; pass --overwrite to replace it")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
