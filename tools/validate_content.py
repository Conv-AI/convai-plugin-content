#!/usr/bin/env python3
"""Validate convai-plugin-content feeds against schema + quality rules."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"

FEED_SCHEMA_MAP = {
    "announcements-common.json": "announcements-feed.schema.json",
    "announcements-unreal.json": "announcements-feed.schema.json",
    "changelogs-common.json": "changelogs-feed.schema.json",
    "changelogs-unreal.json": "changelogs-feed.schema.json",
}


def _parse_iso8601(value: str, field_path: str, errors: list[str]) -> None:
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        errors.append(f"{field_path}: invalid ISO-8601 datetime '{value}'")


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _run_schema_validation(filename: str, payload: Any, errors: list[str]) -> None:
    schema_path = SCHEMA_DIR / FEED_SCHEMA_MAP[filename]
    schema = _load_json(schema_path)
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(payload), key=lambda e: str(e.path)):
        json_path = ".".join(str(x) for x in err.path) or "$"
        errors.append(f"{filename}:{json_path}: {err.message}")


def _validate_announcements(filename: str, payload: dict[str, Any], errors: list[str]) -> None:
    _parse_iso8601(payload["lastUpdated"], f"{filename}.lastUpdated", errors)

    seen_ids: set[str] = set()
    for idx, item in enumerate(payload.get("announcements", [])):
        item_path = f"{filename}.announcements[{idx}]"
        item_id = item.get("id", "")
        if item_id in seen_ids:
            errors.append(f"{item_path}.id: duplicate id '{item_id}'")
        seen_ids.add(item_id)
        _parse_iso8601(item["date"], f"{item_path}.date", errors)


def _validate_changelogs(filename: str, payload: dict[str, Any], errors: list[str]) -> None:
    _parse_iso8601(payload["lastUpdated"], f"{filename}.lastUpdated", errors)

    seen_ids: set[str] = set()
    for idx, item in enumerate(payload.get("changelogs", [])):
        item_path = f"{filename}.changelogs[{idx}]"
        item_id = item.get("id", "")
        if item_id in seen_ids:
            errors.append(f"{item_path}.id: duplicate id '{item_id}'")
        seen_ids.add(item_id)
        _parse_iso8601(item["date"], f"{item_path}.date", errors)


def main() -> int:
    errors: list[str] = []

    for filename in FEED_SCHEMA_MAP:
        file_path = ROOT / filename
        if not file_path.exists():
            errors.append(f"{filename}: file does not exist")
            continue

        try:
            payload = _load_json(file_path)
        except json.JSONDecodeError as exc:
            errors.append(f"{filename}: invalid JSON - {exc}")
            continue

        error_count_before = len(errors)
        _run_schema_validation(filename, payload, errors)
        if len(errors) > error_count_before:
            continue

        if filename.startswith("announcements-"):
            _validate_announcements(filename, payload, errors)
        else:
            _validate_changelogs(filename, payload, errors)

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("All content files passed schema and quality validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
