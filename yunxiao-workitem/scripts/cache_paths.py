#!/usr/bin/env python3
"""Resolve local cache roots for Yunxiao work-item artifacts."""

from __future__ import annotations

import os
import platform
from pathlib import Path


SYSTEM_CACHE_SENTINELS = {
    "",
    "system-cache",
    "system-cache://yunxiao-workitem/images",
}


def get_system_cache_root() -> Path:
    override = os.environ.get("YUNXIAO_WORKITEM_CACHE_DIR")
    if override:
        return Path(override).expanduser()

    system = platform.system().lower()
    if system == "windows":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "Codex" / "yunxiao-workitem" / "images"
        return Path.home() / "AppData" / "Local" / "Codex" / "yunxiao-workitem" / "images"

    if system == "darwin":
        return Path.home() / "Library" / "Caches" / "Codex" / "yunxiao-workitem" / "images"

    base = os.environ.get("XDG_CACHE_HOME")
    if base:
        return Path(base) / "codex" / "yunxiao-workitem" / "images"
    return Path.home() / ".cache" / "codex" / "yunxiao-workitem" / "images"


def resolve_cache_root(value: str | None) -> Path:
    raw_value = (value or "").strip()
    if raw_value in SYSTEM_CACHE_SENTINELS:
        return get_system_cache_root()
    return Path(os.path.expandvars(raw_value)).expanduser()

