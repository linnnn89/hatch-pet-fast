#!/usr/bin/env python3
"""Detect detached or cross-slot sprite components in extracted pet frames."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

IMAGE_SUFFIXES = {".png", ".webp"}


def natural_key(path: Path) -> list[object]:
    return [int(token) if token.isdigit() else token.lower() for token in re.split(r"(\d+)", path.name)]


def connected_components(alpha: Image.Image, threshold: int) -> list[dict[str, object]]:
    width, height = alpha.size
    mask = bytearray(1 if value > threshold else 0 for value in alpha.tobytes())
    components: list[dict[str, object]] = []

    for seed in range(width * height):
        if not mask[seed]:
            continue
        mask[seed] = 0
        stack = [seed]
        count = 0
        min_x = width
        min_y = height
        max_x = -1
        max_y = -1

        while stack:
            index = stack.pop()
            y, x = divmod(index, width)
            count += 1
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

            for neighbor_y in range(max(0, y - 1), min(height, y + 2)):
                row_offset = neighbor_y * width
                for neighbor_x in range(max(0, x - 1), min(width, x + 2)):
                    neighbor = row_offset + neighbor_x
                    if mask[neighbor]:
                        mask[neighbor] = 0
                        stack.append(neighbor)

        components.append(
            {
                "pixels": count,
                "bbox": [min_x, min_y, max_x + 1, max_y + 1],
            }
        )

    return sorted(components, key=lambda item: int(item["pixels"]), reverse=True)


def make_black_sheet(
    frames: list[tuple[Path, Image.Image]],
    results: list[dict[str, object]],
    output: Path,
) -> None:
    width, height = frames[0][1].size
    header = 18
    sheet = Image.new("RGB", (width * len(frames), height + header), (0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, ((_, frame), result) in enumerate(zip(frames, results)):
        black = Image.new("RGBA", frame.size, (0, 0, 0, 255))
        black.alpha_composite(frame)
        sheet.paste(black.convert("RGB"), (index * width, header))
        status = "PASS" if result["ok"] else "FAIL"
        color = (120, 255, 140) if result["ok"] else (255, 100, 100)
        draw.text((index * width + 4, 3), f"{index:02d} {status}", fill=color, font=font)

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail extracted pet frames that contain significant detached alpha components."
    )
    parser.add_argument("--frames-dir", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--black-sheet")
    parser.add_argument("--alpha-threshold", type=int, default=12)
    parser.add_argument("--secondary-pixel-threshold", type=int, default=25)
    parser.add_argument("--expected-width", type=int, default=192)
    parser.add_argument("--expected-height", type=int, default=208)
    parser.add_argument(
        "--allow-secondary",
        action="store_true",
        help="Report significant secondary components as warnings instead of errors.",
    )
    args = parser.parse_args()

    frames_dir = Path(args.frames_dir).expanduser().resolve()
    files = sorted(
        (path for path in frames_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )
    if not files:
        raise SystemExit(f"no PNG or WebP frames found under {frames_dir}")

    opened_frames: list[tuple[Path, Image.Image]] = []
    results: list[dict[str, object]] = []
    errors: list[str] = []
    warnings: list[str] = []

    for index, path in enumerate(files):
        with Image.open(path) as opened:
            frame = opened.convert("RGBA")
        opened_frames.append((path, frame))
        components = connected_components(frame.getchannel("A"), args.alpha_threshold)
        significant = [
            component
            for component in components
            if int(component["pixels"]) >= args.secondary_pixel_threshold
        ]
        secondary = significant[1:]
        frame_errors: list[str] = []
        frame_warnings: list[str] = []

        if frame.size != (args.expected_width, args.expected_height):
            frame_errors.append(
                f"frame {index} is {frame.width}x{frame.height}; expected "
                f"{args.expected_width}x{args.expected_height}"
            )
        if not significant:
            frame_errors.append(f"frame {index} has no visible component above the threshold")
        elif secondary:
            message = (
                f"frame {index} has {len(secondary)} significant secondary component(s): "
                + ", ".join(
                    f"{component['pixels']}px at {component['bbox']}" for component in secondary
                )
            )
            if args.allow_secondary:
                frame_warnings.append(message)
            else:
                frame_errors.append(message)

        errors.extend(frame_errors)
        warnings.extend(frame_warnings)
        results.append(
            {
                "index": index,
                "file": str(path),
                "size": list(frame.size),
                "ok": not frame_errors,
                "significant_components": significant,
                "secondary_components": secondary,
                "errors": frame_errors,
                "warnings": frame_warnings,
            }
        )

    report = {
        "ok": not errors,
        "frames_dir": str(frames_dir),
        "frame_count": len(files),
        "alpha_threshold": args.alpha_threshold,
        "secondary_pixel_threshold": args.secondary_pixel_threshold,
        "allow_secondary": args.allow_secondary,
        "errors": errors,
        "warnings": warnings,
        "frames": results,
    }

    json_out = Path(args.json_out).expanduser().resolve()
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.black_sheet:
        make_black_sheet(opened_frames, results, Path(args.black_sheet).expanduser().resolve())

    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
