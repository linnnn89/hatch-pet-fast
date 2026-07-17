#!/usr/bin/env python3
"""Aggregate detailed QA JSON files into one compact release-gate summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FAIL_STATUSES = {"fail", "failed", "blocked", "error", "invalid"}
WARN_STATUSES = {"warn", "warning", "review", "needs-review", "needs_retry"}


def parse_input(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("input must use LABEL=PATH")
    label, raw_path = value.split("=", 1)
    label = label.strip()
    if not label or not raw_path.strip():
        raise argparse.ArgumentTypeError("input must use non-empty LABEL=PATH")
    return label, Path(raw_path).expanduser().resolve()


def item_count(value: object) -> int:
    if value is None or value is False or value == "":
        return 0
    if isinstance(value, (list, dict, tuple, set)):
        return len(value)
    return 1


def inspect(label: str, path: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {
            "label": label,
            "path": str(path),
            "ok": False,
            "error_count": 1,
            "warning_count": 0,
            "errors": ["input file not found"],
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "label": label,
            "path": str(path),
            "ok": False,
            "error_count": 1,
            "warning_count": 0,
            "errors": [f"invalid JSON: {exc}"],
        }
    if not isinstance(data, dict):
        errors.append("top-level JSON value must be an object")
    else:
        if data.get("ok") is False:
            errors.append("ok=false")
        status = str(data.get("status", "")).strip().lower()
        if status in FAIL_STATUSES:
            errors.append(f"status={status}")
        elif status in WARN_STATUSES:
            warnings.append(f"status={status}")
        if item_count(data.get("errors")):
            errors.append(f"reported_errors={item_count(data.get('errors'))}")
        if item_count(data.get("hard_failures")):
            errors.append(f"hard_failures={item_count(data.get('hard_failures'))}")
        if item_count(data.get("duplicate_groups")):
            errors.append(f"duplicate_groups={item_count(data.get('duplicate_groups'))}")
        if item_count(data.get("warnings")):
            warnings.append(f"reported_warnings={item_count(data.get('warnings'))}")
        if item_count(data.get("soft_warnings")):
            warnings.append(f"soft_warnings={item_count(data.get('soft_warnings'))}")
    return {
        "label": label,
        "path": str(path),
        "ok": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        action="append",
        type=parse_input,
        required=True,
        metavar="LABEL=PATH",
    )
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()

    labels = [label for label, _ in args.input]
    if len(labels) != len(set(labels)):
        raise SystemExit("input labels must be unique")
    checks = [inspect(label, path) for label, path in args.input]
    failed = [str(check["label"]) for check in checks if not check["ok"]]
    error_count = sum(int(check["error_count"]) for check in checks)
    warning_count = sum(int(check["warning_count"]) for check in checks)
    report = {
        "ok": not failed,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "error_count": error_count,
        "warning_count": warning_count,
        "failed_checks": failed,
        "checks": checks,
    }
    output = Path(args.json_out).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    status = "PASS" if report["ok"] else "FAIL"
    failed_text = ",".join(failed) if failed else "none"
    print(
        f"{status} checks={report['passed_count']}/{report['check_count']} "
        f"errors={error_count} warnings={warning_count} failed={failed_text}"
    )
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
