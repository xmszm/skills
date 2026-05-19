#!/usr/bin/env python3
"""Validate a project-local Yunxiao work item JSON config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = ".trellis/config/yunxiao-workitem.json"


def read_config(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise SystemExit(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return data


def is_unknown(value: Any) -> bool:
    return not value or str(value).strip().lower() == "unknown"


def collect_status_meanings(statuses: list[dict[str, Any]]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {
        "unfinished": [],
        "active": [],
        "terminal": [],
    }
    for item in statuses:
        meaning = str(item.get("meaning", "")).strip()
        status_id = str(item.get("id", "")).strip()
        if meaning in buckets and status_id.isdigit():
            buckets[meaning].append(status_id)
    return buckets


def lint_config(config: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    meaning_ids: dict[str, list[str]] = {
        "unfinished": [],
        "active": [],
        "terminal": [],
    }

    required_scalars = {
        "organization_id": config.get("organization_id"),
        "project_id": config.get("project_id"),
        "project_code": config.get("project_code"),
    }
    for name, value in required_scalars.items():
        if is_unknown(value):
            errors.append(f"missing required value: {name}")

    statuses = config.get("statuses", [])
    if not isinstance(statuses, list) or not statuses:
        errors.append("missing statuses")
    else:
        numeric_statuses = [
            item for item in statuses
            if isinstance(item, dict) and str(item.get("id", "")).isdigit()
        ]
        if not numeric_statuses:
            errors.append("missing numeric status IDs")
        meaning_ids = collect_status_meanings(numeric_statuses)
        if not meaning_ids["unfinished"]:
            warnings.append("no status marked unfinished")
        if not meaning_ids["active"]:
            warnings.append("no status marked active")
        if not meaning_ids["terminal"]:
            warnings.append("no status marked terminal")

    if is_unknown(config.get("unfinished_statuses")) and not meaning_ids["unfinished"]:
        warnings.append("unfinished_statuses is empty")
    if is_unknown(config.get("active_status")) and not meaning_ids["active"]:
        warnings.append("active_status is empty")
    if not config.get("production_targets"):
        warnings.append("production_targets is empty")
    if not config.get("validations"):
        warnings.append("validations is empty")

    owners = config.get("owners", {})
    if isinstance(owners, dict):
        for label in ("backend", "ui_product", "qa"):
            if is_unknown(owners.get(label)):
                warnings.append(f"owner is empty: {label}")

    status_policy = str(config.get("status_policy", ""))
    updates_enabled = "Do not update statuses automatically" not in status_policy
    if updates_enabled and is_unknown(config.get("active_status")) and not meaning_ids["active"]:
        errors.append("status updates appear enabled but active_status is empty")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "values": {
            "organizationId": config.get("organization_id", ""),
            "projectId": config.get("project_id", ""),
            "projectCode": config.get("project_code", ""),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint a Yunxiao project config")
    parser.add_argument("--config-path", default=DEFAULT_CONFIG_PATH, help="JSON config path")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    config_path = Path(args.config_path)
    result = lint_config(read_config(config_path))
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"config: {config_path}")
        print(f"ok: {str(result['ok']).lower()}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
        for warning in result["warnings"]:
            print(f"WARN: {warning}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
