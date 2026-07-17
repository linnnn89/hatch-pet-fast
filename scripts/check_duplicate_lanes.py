#!/usr/bin/env python3
"""Block pixel-identical animation lanes before atlas assembly."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image


def parse_lane(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("lane must use NAME=PATH")
    name, raw_path = value.split("=", 1)
    name = name.strip()
    if not name or not raw_path.strip():
        raise argparse.ArgumentTypeError("lane must use non-empty NAME=PATH")
    return name, Path(raw_path).expanduser().resolve()


def pixel_digest(path: Path) -> tuple[str, str, list[int], str]:
    if not path.is_file():
        raise ValueError(f"lane file not found: {path}")
    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as opened:
        rgba = opened.convert("RGBA")
        pixel_hash = hashlib.sha256(
            f"{rgba.width}x{rgba.height}:RGBA:".encode("ascii") + rgba.tobytes()
        ).hexdigest()
        return file_hash, pixel_hash, [rgba.width, rgba.height], opened.format or "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lane",
        action="append",
        type=parse_lane,
        required=True,
        metavar="NAME=PATH",
        help="Animation lane name and source strip. Repeat for every lane.",
    )
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()

    names = [name for name, _ in args.lane]
    if len(names) != len(set(names)):
        raise SystemExit("lane names must be unique")

    errors: list[str] = []
    lanes: list[dict[str, object]] = []
    by_pixels: dict[str, list[str]] = defaultdict(list)

    for name, path in args.lane:
        try:
            file_hash, pixel_hash, size, image_format = pixel_digest(path)
        except (OSError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
            continue
        by_pixels[pixel_hash].append(name)
        lanes.append(
            {
                "name": name,
                "path": str(path),
                "size": size,
                "format": image_format,
                "file_sha256": file_hash,
                "pixel_sha256": pixel_hash,
            }
        )

    duplicate_groups = [group for group in by_pixels.values() if len(group) > 1]
    for group in duplicate_groups:
        errors.append("pixel-identical lanes: " + " == ".join(group))

    report = {
        "ok": not errors,
        "checked_lane_count": len(lanes),
        "duplicate_groups": duplicate_groups,
        "errors": errors,
        "warnings": [],
        "lanes": lanes,
    }
    output = Path(args.json_out).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    status = "PASS" if report["ok"] else "FAIL"
    print(
        f"{status} lanes={len(lanes)} duplicates={len(duplicate_groups)} "
        f"errors={len(errors)}"
    )
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
