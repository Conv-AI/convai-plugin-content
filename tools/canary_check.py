#!/usr/bin/env python3
"""Canary checks for raw GitHub vs jsDelivr content freshness."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


FILES = [
    "announcements-common.json",
    "announcements-unreal.json",
    "changelogs-common.json",
    "changelogs-unreal.json",
]

RAW_BASE = "https://raw.githubusercontent.com/Conv-AI/convai-plugin-content/main"
CDN_BASE = "https://cdn.jsdelivr.net/gh/Conv-AI/convai-plugin-content@main"


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "convai-content-canary/1.0",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read()


def _extract_last_updated(payload: dict[str, Any]) -> str:
    return str(payload.get("lastUpdated", ""))


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-json", default="canary_result.json")
    parser.add_argument("--warning-md", default="canary_warnings.md")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    for file_name in FILES:
        raw_url = f"{RAW_BASE}/{file_name}"
        cdn_url = f"{CDN_BASE}/{file_name}"

        try:
            raw_bytes = _fetch(raw_url)
            raw_payload = json.loads(raw_bytes.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(f"{file_name}: raw endpoint failed ({exc})")
            continue

        raw_last_updated = _extract_last_updated(raw_payload)
        raw_hash = _sha256(raw_bytes)

        try:
            cdn_bytes = _fetch(cdn_url)
            cdn_payload = json.loads(cdn_bytes.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            warnings.append(f"{file_name}: jsDelivr endpoint unavailable ({exc})")
            continue

        cdn_last_updated = _extract_last_updated(cdn_payload)
        cdn_hash = _sha256(cdn_bytes)

        if raw_hash != cdn_hash or raw_last_updated != cdn_last_updated:
            warnings.append(
                f"{file_name}: jsDelivr diverged from raw "
                f"(raw.lastUpdated={raw_last_updated}, cdn.lastUpdated={cdn_last_updated})"
            )

    for warning in warnings:
        print(f"::warning::{warning}")
    for error in errors:
        print(f"::error::{error}")

    warning_md = Path(args.warning_md)
    if warnings:
        body = ["# Content Canary Warnings", "", "The following items need attention:", ""]
        body.extend([f"- {item}" for item in warnings])
        warning_md.write_text("\n".join(body), encoding="utf-8")
    elif warning_md.exists():
        warning_md.unlink()

    result = {
        "warnings_count": len(warnings),
        "errors_count": len(errors),
        "warnings": warnings,
        "errors": errors,
    }
    Path(args.result_json).write_text(json.dumps(result, indent=2), encoding="utf-8")

    if errors:
        print("Canary check failed due to raw endpoint errors.")
        return 1

    print(f"Canary check completed. warnings={len(warnings)} errors={len(errors)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
