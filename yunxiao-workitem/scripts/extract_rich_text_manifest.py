#!/usr/bin/env python3
"""Extract clean text and image placeholders from Yunxiao rich text."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


FILE_ID_RE = re.compile(r"fileIdentifier=([A-Za-z0-9]+)")
WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")


def load_input(path: str | None) -> Any:
    text = sys.stdin.read() if not path or path == "-" else Path(path).read_text(encoding="utf-8")
    text = text.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def maybe_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    value = value.strip()
    if not value:
        return ""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def pick_rich_text(value: Any, field: str | None) -> Any:
    value = maybe_json(value)
    if isinstance(value, dict) and field and field in value:
        return maybe_json(value[field])
    if isinstance(value, dict) and "content" in value:
        return maybe_json(value["content"])
    if isinstance(value, dict) and "description" in value:
        return maybe_json(value["description"])
    return value


def file_identifier_from_src(src: str) -> str:
    match = FILE_ID_RE.search(src or "")
    if match:
        return match.group(1)
    parsed = urlparse(src or "")
    values = parse_qs(parsed.query).get("fileIdentifier")
    return values[0] if values else ""


def guess_suffix(name: str, src: str) -> str:
    for candidate in (name, urlparse(src or "").path):
        suffix = Path(candidate).suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}:
            return suffix
    return ".png"


def normalize_text(parts: list[str]) -> str:
    lines: list[str] = []
    current: list[str] = []
    for part in parts:
        if part == "\n":
            line = WHITESPACE_RE.sub(" ", "".join(current)).replace("\xa0", " ").strip()
            if line:
                lines.append(line)
            current = []
            continue
        current.append(html.unescape(str(part)).replace("\xa0", " "))
    line = WHITESPACE_RE.sub(" ", "".join(current)).strip()
    if line:
        lines.append(line)
    return "\n".join(lines)


class ManifestBuilder:
    def __init__(self, source_label: str, item_key: str, cache_root: str) -> None:
        self.source_label = source_label
        self.item_key = item_key or "unknown-item"
        self.cache_root = cache_root
        self.parts: list[str] = []
        self.images: dict[str, dict[str, Any]] = {}
        self._index = 0

    def text(self, value: str) -> None:
        if value:
            self.parts.append(value)

    def newline(self) -> None:
        self.parts.append("\n")

    def image(self, attrs: dict[str, Any]) -> None:
        src = str(attrs.get("src") or "")
        file_id = str(attrs.get("fileIdentifier") or attrs.get("fileId") or "")
        if not file_id:
            file_id = file_identifier_from_src(src)
        if not file_id:
            return
        self._index += 1
        ref = f"{self.source_label}-{self._index}"
        suffix = guess_suffix(str(attrs.get("name") or ""), src)
        path = str(Path(self.cache_root) / self.item_key / f"{file_id}{suffix}")
        placeholder = f"{{{{image:{ref} path:{path}}}}}"
        self.parts.extend(["\n", placeholder, "\n"])
        self.images[ref] = {
            "fileIdentifier": file_id,
            "path": path,
            "valid": False,
            "source": "rich_text",
            "name": str(attrs.get("name") or ""),
        }

    def manifest(self) -> dict[str, Any]:
        annotated = normalize_text(self.parts)
        raw_parts = [part for part in self.parts if not str(part).startswith("{{image:")]
        return {
            "rawText": normalize_text(raw_parts),
            "annotatedText": annotated,
            "images": self.images,
        }


def walk_jsonml(node: Any, builder: ManifestBuilder) -> None:
    if node is None:
        return
    if isinstance(node, str):
        builder.text(node)
        return
    if not isinstance(node, list) or not node:
        return

    tag = str(node[0]).lower()
    attrs: dict[str, Any] = node[1] if len(node) > 1 and isinstance(node[1], dict) else {}
    children = node[2:] if attrs else node[1:]

    if tag == "img":
        builder.image(attrs)
        return
    if tag in {"p", "div", "li", "tr"}:
        builder.newline()
    if tag == "br":
        builder.newline()

    for child in children:
        walk_jsonml(child, builder)

    if tag in {"p", "div", "li", "tr"}:
        builder.newline()


class RichTextHTMLParser(HTMLParser):
    def __init__(self, builder: ManifestBuilder) -> None:
        super().__init__(convert_charrefs=True)
        self.builder = builder

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        tag = tag.lower()
        if tag == "img":
            self.builder.image(attr_map)
        elif tag in {"p", "div", "li", "tr", "br"}:
            self.builder.newline()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"p", "div", "li", "tr"}:
            self.builder.newline()

    def handle_data(self, data: str) -> None:
        self.builder.text(data)


def extract(value: Any, source_label: str, item_key: str, cache_root: str) -> dict[str, Any]:
    value = maybe_json(value)
    builder = ManifestBuilder(source_label=source_label, item_key=item_key, cache_root=cache_root)
    if isinstance(value, dict):
        if isinstance(value.get("jsonMLValue"), list):
            walk_jsonml(value["jsonMLValue"], builder)
            return builder.manifest()
        if value.get("htmlValue"):
            parser = RichTextHTMLParser(builder)
            parser.feed(str(value["htmlValue"]))
            return builder.manifest()
    if isinstance(value, list):
        walk_jsonml(value, builder)
        return builder.manifest()
    parser = RichTextHTMLParser(builder)
    parser.feed(str(value or ""))
    return builder.manifest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Yunxiao rich-text manifest")
    parser.add_argument("--input", "-i", help="Input file. Defaults to stdin")
    parser.add_argument("--field", help="Field to read when input is a work item JSON object")
    parser.add_argument("--source-label", default="description", help="Placeholder prefix, e.g. description or comment-123")
    parser.add_argument("--item-key", default="unknown-item", help="Work item key for cache path")
    parser.add_argument("--cache-root", default="/tmp/yunxiao-workitems", help="Image cache root")
    args = parser.parse_args()

    data = pick_rich_text(load_input(args.input), args.field)
    manifest = extract(data, args.source_label, args.item_key, args.cache_root)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
