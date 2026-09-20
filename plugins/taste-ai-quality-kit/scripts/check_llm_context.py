#!/usr/bin/env python3
"""Validate only the shape of a user-owned LLM context directory."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


REQUIRED_FILES = ("models.md", "prompting.md", "decisions.md")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-dir", default=os.getenv("TASTE_LLM_CONTEXT_DIR", ""))
    args = parser.parse_args()

    if not args.context_dir:
        print(json.dumps({"status": "CONTEXT_NOT_READY", "reason": "TASTE_LLM_CONTEXT_DIR is unset"}))
        return 10

    root = Path(args.context_dir).expanduser()
    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    incomplete = [
        name
        for name in REQUIRED_FILES
        if (root / name).is_file()
        and (
            len((root / name).read_text(encoding="utf-8").strip()) < 80
            or "status: TODO" in (root / name).read_text(encoding="utf-8")
        )
    ]
    if missing or incomplete:
        print(json.dumps({
            "status": "CONTEXT_NOT_READY",
            "context_dir": str(root),
            "missing": missing,
            "incomplete": incomplete,
        }))
        return 10

    print(json.dumps({"status": "CONTEXT_READY", "context_dir": str(root)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
