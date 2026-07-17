#!/usr/bin/env python3
"""Compact attempt ledger and dependency guard for hatch-pet-fast runs."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1
DEFAULT_BUDGET = 15
PREREQUISITES = {
    "bulk-standard": ["idle", "running-right", "scale-profile", "running-right-scale"],
    "assemble-standard": [
        "standard-scale-audit",
        "standard-lane-uniqueness",
    ],
    "row9": ["base", "standard-motion", "cardinals"],
    "row10": ["look-row-9-semantics"],
    "assemble-raw": [
        "look-row-9-semantics",
        "look-row-10-semantics",
        "all-lane-uniqueness",
    ],
    "despill": [
        "raw-contact",
        "raw-labeled-direction",
        "raw-blind-direction",
        "raw-continuity",
    ],
    "package": ["despill", "atlas-validation", "final-visual"],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"ledger not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise SystemExit("unsupported ledger schema")
    return data


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def compact(data: dict, message: str = "") -> str:
    attempts = data.get("imagegen_attempts", [])
    gates = data.get("passed_gates", {})
    failures = data.get("failures", [])
    prefix = f"{message} " if message else ""
    return (
        f"{prefix}attempts={len(attempts)}/{data['imagegen_budget']} "
        f"gates={len(gates)} failures={len(failures)}"
    )


def require_stage(data: dict, stage: str) -> list[str]:
    if stage not in PREREQUISITES:
        raise SystemExit(f"unknown guarded stage: {stage}")
    passed = data.get("passed_gates", {})
    return [gate for gate in PREREQUISITES[stage] if gate not in passed]


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    if path.exists():
        raise SystemExit(f"refusing to overwrite ledger: {path}")
    data = {
        "schema_version": SCHEMA_VERSION,
        "pet_id": args.pet_id,
        "created_at": now(),
        "imagegen_budget": args.budget,
        "imagegen_attempts": [],
        "passed_gates": {},
        "failures": [],
    }
    save(path, data)
    print(compact(data, "initialized"))
    return 0


def cmd_attempt(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    data = load(path)
    attempts = data["imagegen_attempts"]
    if len(attempts) >= data["imagegen_budget"]:
        print(compact(data, f"blocked job={args.job}"), file=sys.stderr)
        return 2
    attempts.append({"job": args.job, "at": now()})
    save(path, data)
    print(compact(data, f"recorded job={args.job}"))
    return 0


def cmd_pass(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    data = load(path)
    entry = {"at": now()}
    if args.artifact:
        entry["artifact"] = args.artifact
    data["passed_gates"][args.gate] = entry
    save(path, data)
    print(compact(data, f"passed gate={args.gate}"))
    return 0


def cmd_fail(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    data = load(path)
    note = (args.note or "").strip()
    if len(note) > 160:
        raise SystemExit("failure note must be 160 characters or fewer")
    data["failures"].append(
        {"job": args.job, "class": args.failure_class, "note": note, "at": now()}
    )
    save(path, data)
    print(compact(data, f"failed job={args.job} class={args.failure_class}"))
    return 0


def cmd_require(args: argparse.Namespace) -> int:
    data = load(Path(args.ledger))
    missing = require_stage(data, args.stage)
    if missing:
        print(
            compact(data, f"blocked stage={args.stage} missing={','.join(missing)}"),
            file=sys.stderr,
        )
        return 2
    print(compact(data, f"allowed stage={args.stage}"))
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    data = load(Path(args.ledger))
    print(compact(data, f"pet={data['pet_id']}"))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--ledger", required=True)
    init.add_argument("--pet-id", required=True)
    init.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    init.set_defaults(func=cmd_init)

    attempt = sub.add_parser("attempt")
    attempt.add_argument("--ledger", required=True)
    attempt.add_argument("--job", required=True)
    attempt.set_defaults(func=cmd_attempt)

    passed = sub.add_parser("pass")
    passed.add_argument("--ledger", required=True)
    passed.add_argument("--gate", required=True)
    passed.add_argument("--artifact")
    passed.set_defaults(func=cmd_pass)

    failed = sub.add_parser("fail")
    failed.add_argument("--ledger", required=True)
    failed.add_argument("--job", required=True)
    failed.add_argument("--class", dest="failure_class", required=True)
    failed.add_argument("--note")
    failed.set_defaults(func=cmd_fail)

    required = sub.add_parser("require")
    required.add_argument("--ledger", required=True)
    required.add_argument("--stage", choices=sorted(PREREQUISITES), required=True)
    required.set_defaults(func=cmd_require)

    summary = sub.add_parser("summary")
    summary.add_argument("--ledger", required=True)
    summary.set_defaults(func=cmd_summary)
    return root


def main() -> int:
    args = parser().parse_args()
    if getattr(args, "budget", DEFAULT_BUDGET) < 1:
        raise SystemExit("budget must be positive")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
