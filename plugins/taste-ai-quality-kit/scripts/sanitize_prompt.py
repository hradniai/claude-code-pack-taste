#!/usr/bin/env python3
"""Static hygiene checks. It never calls a model and never reads environment values."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CHECKS = {
    "secret_like_literal": re.compile(r"(?:sk-[A-Za-z0-9_-]{12,}|AIza[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})"),
    "environment_assignment": re.compile(r"(?m)^\s*(?:export\s+)?[A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)\s*="),
}
ESCAPE_HATCH = re.compile(r"\b(?:not[ _-]?found|uncertain|unverified|unknown|null)\b", re.IGNORECASE)
OUTPUT_CONTRACT = re.compile(r"\b(?:return|output|respond with|json|yaml|markdown)\b", re.IGNORECASE)


OPEN_TAG = re.compile(r"<([A-Za-z][A-Za-z0-9_-]*)(?:\s[^<>]*)?>")


def is_inside_xml_element(text: str, start: int, end: int) -> bool:
    """True when some <tag> opened before `start` is still open there and closed after `end`.

    Angle-bracket tokens that are not tags (`<jan@example.cz>`, `<https://...>`, `<br/>`) never match OPEN_TAG,
    so they cannot open an element and cannot crash the check.
    """
    before, after = text[:start], text[end:]
    last_open: dict[str, int] = {}
    for match in OPEN_TAG.finditer(before):
        last_open[match.group(1).lower()] = match.start()
    for tag, position in last_open.items():
        closer = re.compile(rf"</{re.escape(tag)}\s*>", re.IGNORECASE)
        if not closer.search(before, position) and closer.search(after):
            return True
    return False


def finding(level: str, rule: str, message: str, line: int | None = None) -> dict[str, object]:
    result: dict[str, object] = {"level": level, "rule": rule, "message": message}
    if line is not None:
        result["line"] = line
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()
    path = Path(args.prompt)

    if not path.is_file():
        print(json.dumps({"status": "FAIL", "findings": [finding("FAIL", "missing_file", "Prompt file does not exist")]}))
        return 20

    text = path.read_text(encoding="utf-8")
    findings: list[dict[str, object]] = []
    if not text.strip():
        findings.append(finding("FAIL", "empty_prompt", "Prompt is empty"))
    for rule, pattern in CHECKS.items():
        for match in pattern.finditer(text):
            findings.append(finding("FAIL", rule, "Prompt appears to contain a credential literal or assignment", text.count("\n", 0, match.start()) + 1))
    if not OUTPUT_CONTRACT.search(text):
        findings.append(finding("WARN", "missing_output_contract", "No explicit output contract detected"))
    if not ESCAPE_HATCH.search(text):
        findings.append(finding("WARN", "missing_escape_hatch", "No explicit missing-or-unverifiable-input escape hatch detected"))
    for match in re.finditer(r"\{\{[^}]*\}\}", text):
        if not is_inside_xml_element(text, match.start(), match.end()):
            findings.append(finding("WARN", "dynamic_input_boundary", "Template interpolation detected without an enclosing XML element that marks it as untrusted input", text.count("\n", 0, match.start()) + 1))
            break

    status = "FAIL" if any(item["level"] == "FAIL" for item in findings) else "WARN" if findings else "PASS"
    print(json.dumps({"status": status, "prompt": str(path), "findings": findings}, ensure_ascii=False))
    return 20 if status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
