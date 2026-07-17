#!/usr/bin/env python3
"""Create, audit, and conditionally repair a shared pet lane scale profile."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from statistics import median

from PIL import Image


IMAGE_SUFFIXES = {".png", ".webp"}
PROFILE_VERSION = 2


def natural_key(path: Path) -> list[object]:
    return [int(token) if token.isdigit() else token.lower() for token in re.split(r"(\d+)", path.name)]


def frame_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        raise ValueError(f"frames directory not found: {directory}")
    files = sorted(
        (path for path in directory.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )
    if not files:
        raise ValueError(f"no PNG or WebP frames found under {directory}")
    return files


def alpha_bbox(image: Image.Image, threshold: int) -> tuple[int, int, int, int] | None:
    alpha = image.getchannel("A")
    if threshold:
        alpha = alpha.point(lambda value: 255 if value > threshold else 0)
    return alpha.getbbox()


def measure(directory: Path, threshold: int, expected_size: tuple[int, int] | None = None) -> dict:
    frames: list[dict[str, object]] = []
    errors: list[str] = []
    sizes: set[tuple[int, int]] = set()
    for path in frame_files(directory):
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
        sizes.add(image.size)
        if expected_size and image.size != expected_size:
            errors.append(
                f"{path.name}: {image.width}x{image.height}; expected "
                f"{expected_size[0]}x{expected_size[1]}"
            )
        bbox = alpha_bbox(image, threshold)
        if bbox is None:
            errors.append(f"{path.name}: no visible pixels above alpha threshold {threshold}")
            continue
        left, top, right, bottom = bbox
        frames.append(
            {
                "file": str(path),
                "bbox": [left, top, right, bottom],
                "width": right - left,
                "height": bottom - top,
                "center_x": (left + right) / 2.0,
                "bottom": bottom,
                "visible_area": sum(1 for value in image.getchannel("A").tobytes() if value > threshold),
            }
        )
    if len(sizes) > 1:
        errors.append("frames do not share one cell size")
    if errors:
        return {"ok": False, "errors": errors, "warnings": [], "frames": frames}
    heights = [int(frame["height"]) for frame in frames]
    widths = [int(frame["width"]) for frame in frames]
    centers = [float(frame["center_x"]) for frame in frames]
    bottoms = [int(frame["bottom"]) for frame in frames]
    visible_areas = [int(frame["visible_area"]) for frame in frames]
    only_size = next(iter(sizes))
    return {
        "ok": True,
        "errors": [],
        "warnings": [],
        "frame_count": len(frames),
        "cell_size": list(only_size),
        "median_height": float(median(heights)),
        "median_width": float(median(widths)),
        "median_center_x": float(median(centers)),
        "median_bottom": float(median(bottoms)),
        "median_visible_area": float(median(visible_areas)),
        "max_bottom": int(max(bottoms)),
        "vertical_travel": int(max(bottoms) - min(bottoms)),
        "frames": frames,
    }


def read_profile(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"scale profile not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("profile_version") != PROFILE_VERSION:
        raise SystemExit("unsupported scale profile version")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def evaluate(
    stats: dict,
    profile: dict,
    row: str,
    pose_variant: bool = False,
    metric: str = "auto",
) -> dict:
    if not stats.get("ok"):
        return {
            "ok": False,
            "row": row,
            "errors": list(stats.get("errors", [])),
            "warnings": [],
            "measurement": stats,
        }
    target_height = float(profile["target_height"])
    height_ratio = float(stats["median_height"]) / target_height
    area_scale_ratio = (
        float(stats["median_visible_area"]) / float(profile["target_visible_area"])
    ) ** 0.5
    ratios = {"height": height_ratio, "area": area_scale_ratio}
    selected_metric = (
        max(ratios, key=lambda name: abs(ratios[name] - 1.0)) if metric == "auto" else metric
    )
    ratio = ratios[selected_metric]
    scale_drift = abs(ratio - 1.0)
    baseline_drift = abs(float(stats["median_bottom"]) - float(profile["baseline_y"]))
    errors: list[str] = []
    warnings: list[str] = []
    if scale_drift > float(profile["max_scale_drift"]):
        message = (
            f"{row}: {selected_metric} scale ratio {ratio:.4f} exceeds allowed drift "
            f"{profile['max_scale_drift']:.4f}"
        )
        if pose_variant:
            warnings.append(message + "; accepted as pose-variant review")
        else:
            errors.append(message)
    if baseline_drift > float(profile["max_baseline_drift_px"]):
        warnings.append(
            f"{row}: median baseline differs by {baseline_drift:.1f}px; inspect motion semantics"
        )
    return {
        "ok": not errors,
        "row": row,
        "height_ratio": height_ratio,
        "area_scale_ratio": area_scale_ratio,
        "selected_metric": selected_metric,
        "selected_scale_ratio": ratio,
        "scale_drift": scale_drift,
        "baseline_drift_px": baseline_drift,
        "pose_variant": pose_variant,
        "needs_scale_repair": bool(errors) and not pose_variant,
        "errors": errors,
        "warnings": warnings,
        "measurement": stats,
    }


def cmd_create(args: argparse.Namespace) -> int:
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite scale profile: {output}")
    source = Path(args.frames_dir).expanduser().resolve()
    stats = measure(source, args.alpha_threshold)
    if not stats.get("ok"):
        print(f"FAIL profile errors={len(stats['errors'])}")
        return 2
    profile = {
        "profile_version": PROFILE_VERSION,
        "source_frames": str(source),
        "source_frame_count": stats["frame_count"],
        "cell_size": stats["cell_size"],
        "alpha_threshold": args.alpha_threshold,
        "target_height": stats["median_height"],
        "target_width_reference": stats["median_width"],
        "target_visible_area": stats["median_visible_area"],
        "center_x": stats["median_center_x"],
        "baseline_y": stats["median_bottom"],
        "max_scale_drift": args.max_scale_drift,
        "max_baseline_drift_px": args.max_baseline_drift_px,
    }
    write_json(output, profile)
    print(
        f"PASS profile frames={stats['frame_count']} target_height={stats['median_height']:.1f} "
        f"baseline={stats['median_bottom']:.1f}"
    )
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    profile = read_profile(Path(args.profile).expanduser().resolve())
    source = Path(args.frames_dir).expanduser().resolve()
    stats = measure(source, int(profile["alpha_threshold"]), tuple(profile["cell_size"]))
    report = evaluate(stats, profile, args.row, args.pose_variant, args.metric)
    report["profile"] = str(Path(args.profile).expanduser().resolve())
    report["frames_dir"] = str(source)
    write_json(Path(args.json_out).expanduser().resolve(), report)
    status = "PASS" if report["ok"] else "FAIL"
    print(
        f"{status} row={args.row} scale_drift={report.get('scale_drift', 0):.4f} "
        f"errors={len(report['errors'])} warnings={len(report['warnings'])}"
    )
    return 0 if report["ok"] else 2


def resize_sprite(sprite: Image.Image, size: tuple[int, int], resample: str, clamp: int) -> Image.Image:
    method = Image.Resampling.NEAREST if resample == "nearest" else Image.Resampling.LANCZOS
    resized = sprite.resize(size, method)
    if resample == "lanczos" and clamp > 0:
        pixels = bytearray(resized.tobytes())
        for index in range(3, len(pixels), 4):
            if pixels[index] < clamp:
                pixels[index - 3 : index + 1] = b"\x00\x00\x00\x00"
        resized = Image.frombytes("RGBA", resized.size, bytes(pixels))
    return resized


def cmd_repair(args: argparse.Namespace) -> int:
    profile_path = Path(args.profile).expanduser().resolve()
    profile = read_profile(profile_path)
    source = Path(args.frames_dir).expanduser().resolve()
    output = Path(args.output_dir).expanduser().resolve()
    report_path = Path(args.json_out).expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {output}")

    expected_size = tuple(profile["cell_size"])
    stats = measure(source, int(profile["alpha_threshold"]), expected_size)
    audit = evaluate(stats, profile, args.row, metric=args.metric)
    if not audit.get("needs_scale_repair"):
        report = {
            **audit,
            "action": "not-needed",
            "profile": str(profile_path),
            "frames_dir": str(source),
            "output_dir": None,
        }
        write_json(report_path, report)
        print(
            f"PASS row={args.row} action=not-needed scale_drift={audit.get('scale_drift', 0):.4f}"
        )
        return 0 if audit["ok"] else 2

    if not stats.get("ok"):
        write_json(report_path, {**audit, "action": "blocked"})
        print(f"FAIL row={args.row} action=blocked errors={len(audit['errors'])}")
        return 2

    scale = 1.0 / float(audit["selected_scale_ratio"])
    source_anchor = (
        float(stats["max_bottom"])
        if args.anchor_mode == "lowest"
        else float(stats["median_bottom"])
    )
    row_center = float(stats["median_center_x"])
    target_center = float(profile["center_x"])
    target_baseline = float(profile["baseline_y"])
    planned: list[tuple[Path, Image.Image]] = []
    errors: list[str] = []

    for frame_info in stats["frames"]:
        path = Path(str(frame_info["file"]))
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
        left, top, right, bottom = [int(value) for value in frame_info["bbox"]]
        sprite = image.crop((left, top, right, bottom))
        width = max(1, round(sprite.width * scale))
        height = max(1, round(sprite.height * scale))
        sprite = resize_sprite(sprite, (width, height), args.resample, args.alpha_clamp)

        center_offset = (float(frame_info["center_x"]) - row_center) * scale
        bottom_offset = (float(frame_info["bottom"]) - source_anchor) * scale
        new_center = target_center + center_offset
        new_bottom = target_baseline + bottom_offset
        x = round(new_center - width / 2.0)
        y = round(new_bottom - height)
        if x < 0 or y < 0 or x + width > expected_size[0] or y + height > expected_size[1]:
            errors.append(
                f"{path.name}: repaired bounds {(x, y, x + width, y + height)} exceed cell {expected_size}"
            )
            continue
        canvas = Image.new("RGBA", expected_size, (0, 0, 0, 0))
        canvas.alpha_composite(sprite, (x, y))
        planned.append((path, canvas))

    if errors:
        report = {
            "ok": False,
            "row": args.row,
            "action": "blocked",
            "scale_factor": scale,
            "errors": errors,
            "warnings": audit["warnings"],
        }
        write_json(report_path, report)
        print(f"FAIL row={args.row} action=blocked errors={len(errors)}")
        return 2

    output.mkdir(parents=True, exist_ok=True)
    for source_path, image in planned:
        image.save(output / f"{source_path.stem}.png")
    after = measure(output, int(profile["alpha_threshold"]), expected_size)
    after_audit = evaluate(after, profile, args.row, metric=str(audit["selected_metric"]))
    report = {
        "ok": after_audit["ok"],
        "row": args.row,
        "action": "repaired",
        "anchor_mode": args.anchor_mode,
        "resample": args.resample,
        "scale_factor": scale,
        "profile": str(profile_path),
        "frames_dir": str(source),
        "output_dir": str(output),
        "before": audit,
        "after": after_audit,
        "errors": after_audit["errors"],
        "warnings": after_audit["warnings"],
    }
    write_json(report_path, report)
    status = "PASS" if report["ok"] else "FAIL"
    print(
        f"{status} row={args.row} action=repaired scale={scale:.4f} "
        f"errors={len(report['errors'])} warnings={len(report['warnings'])}"
    )
    return 0 if report["ok"] else 2


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--frames-dir", required=True)
    create.add_argument("--output", required=True)
    create.add_argument("--alpha-threshold", type=int, default=12)
    create.add_argument("--max-scale-drift", type=float, default=0.10)
    create.add_argument("--max-baseline-drift-px", type=float, default=8.0)
    create.set_defaults(func=cmd_create)

    audit = sub.add_parser("audit")
    audit.add_argument("--profile", required=True)
    audit.add_argument("--frames-dir", required=True)
    audit.add_argument("--row", required=True)
    audit.add_argument("--json-out", required=True)
    audit.add_argument("--metric", choices=("auto", "height", "area"), default="auto")
    audit.add_argument(
        "--pose-variant",
        action="store_true",
        help="Convert size drift to a review warning for a visibly confirmed silhouette-changing pose.",
    )
    audit.set_defaults(func=cmd_audit)

    repair = sub.add_parser("repair")
    repair.add_argument("--profile", required=True)
    repair.add_argument("--frames-dir", required=True)
    repair.add_argument("--row", required=True)
    repair.add_argument("--output-dir", required=True)
    repair.add_argument("--json-out", required=True)
    repair.add_argument("--metric", choices=("auto", "height", "area"), default="auto")
    repair.add_argument("--anchor-mode", choices=("median", "lowest"), default="median")
    repair.add_argument("--resample", choices=("nearest", "lanczos"), default="nearest")
    repair.add_argument("--alpha-clamp", type=int, default=24)
    repair.set_defaults(func=cmd_repair)
    return root


def main() -> int:
    args = build_parser().parse_args()
    if getattr(args, "alpha_threshold", 0) not in range(256):
        raise SystemExit("alpha threshold must be between 0 and 255")
    if getattr(args, "alpha_clamp", 0) not in range(256):
        raise SystemExit("alpha clamp must be between 0 and 255")
    if getattr(args, "max_scale_drift", 0.1) <= 0:
        raise SystemExit("max scale drift must be positive")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
