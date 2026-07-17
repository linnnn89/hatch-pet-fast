from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_script(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *map(str, args)],
        text=True,
        capture_output=True,
        check=False,
    )


def make_frame(path: Path, *, height: int, bottom: int, width: int = 48, center: int = 96) -> None:
    image = Image.new("RGBA", (192, 208), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    left = center - width // 2
    draw.rectangle((left, bottom - height, left + width - 1, bottom - 1), fill=(120, 80, 220, 255))
    image.save(path)


class DuplicateLaneTests(unittest.TestCase):
    def test_detects_pixel_duplicates_with_different_file_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            image = Image.new("RGBA", (16, 16), (12, 34, 56, 255))
            first = root / "first.png"
            second = root / "second.png"
            image.save(first, compress_level=0)
            image.save(second, compress_level=9)
            report = root / "duplicates.json"
            result = run_script(
                "check_duplicate_lanes.py",
                "--lane",
                f"idle={first}",
                "--lane",
                f"waiting={second}",
                "--json-out",
                report,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertFalse(data["ok"])
            self.assertEqual(data["duplicate_groups"], [["idle", "waiting"]])
            self.assertNotEqual(data["lanes"][0]["file_sha256"], data["lanes"][1]["file_sha256"])
            self.assertEqual(data["lanes"][0]["pixel_sha256"], data["lanes"][1]["pixel_sha256"])

    def test_unique_lanes_pass(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = root / "first.png"
            second = root / "second.png"
            Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(first)
            Image.new("RGBA", (8, 8), (0, 0, 255, 255)).save(second)
            result = run_script(
                "check_duplicate_lanes.py",
                "--lane",
                f"idle={first}",
                "--lane",
                f"waiting={second}",
                "--json-out",
                root / "unique.json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout.startswith("PASS lanes=2"))


class ScaleProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.idle = self.root / "idle"
        self.jump = self.root / "jump"
        self.idle.mkdir()
        self.jump.mkdir()
        for index in range(4):
            make_frame(self.idle / f"{index:02d}.png", height=100, bottom=190)
        for index, bottom in enumerate((190, 170, 150, 170, 190)):
            make_frame(self.jump / f"{index:02d}.png", height=70, bottom=bottom, width=36)
        self.profile = self.root / "profile.json"
        created = run_script(
            "lane_scale_profile.py",
            "create",
            "--frames-dir",
            self.idle,
            "--output",
            self.profile,
        )
        self.assertEqual(created.returncode, 0, created.stderr)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_profile_and_audit(self) -> None:
        profile = json.loads(self.profile.read_text(encoding="utf-8"))
        self.assertEqual(profile["target_height"], 100.0)
        passed = run_script(
            "lane_scale_profile.py",
            "audit",
            "--profile",
            self.profile,
            "--frames-dir",
            self.idle,
            "--row",
            "idle",
            "--json-out",
            self.root / "idle-audit.json",
        )
        failed = run_script(
            "lane_scale_profile.py",
            "audit",
            "--profile",
            self.profile,
            "--frames-dir",
            self.jump,
            "--row",
            "jumping",
            "--json-out",
            self.root / "jump-audit.json",
        )
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertEqual(failed.returncode, 2, failed.stderr)

    def test_conditional_repair_preserves_jump_arc(self) -> None:
        output = self.root / "repaired"
        report = self.root / "repair.json"
        result = run_script(
            "lane_scale_profile.py",
            "repair",
            "--profile",
            self.profile,
            "--frames-dir",
            self.jump,
            "--row",
            "jumping",
            "--output-dir",
            output,
            "--json-out",
            report,
            "--anchor-mode",
            "lowest",
            "--resample",
            "nearest",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(data["action"], "repaired")
        self.assertAlmostEqual(data["after"]["measurement"]["median_height"], 100.0)
        self.assertGreater(
            data["after"]["measurement"]["vertical_travel"],
            data["before"]["measurement"]["vertical_travel"],
        )
        self.assertEqual(len(list(output.glob("*.png"))), 5)

        repeated = run_script(
            "lane_scale_profile.py",
            "repair",
            "--profile",
            self.profile,
            "--frames-dir",
            self.jump,
            "--row",
            "jumping",
            "--output-dir",
            output,
            "--json-out",
            self.root / "repeat.json",
            "--anchor-mode",
            "lowest",
        )
        self.assertNotEqual(repeated.returncode, 0)
        self.assertIn("refusing to overwrite", repeated.stderr)

    def test_pose_variant_converts_metric_to_review_warning(self) -> None:
        report = self.root / "pose-variant.json"
        result = run_script(
            "lane_scale_profile.py",
            "audit",
            "--profile",
            self.profile,
            "--frames-dir",
            self.jump,
            "--row",
            "jumping",
            "--json-out",
            report,
            "--pose-variant",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertTrue(data["ok"])
        self.assertTrue(data["pose_variant"])
        self.assertFalse(data["needs_scale_repair"])
        self.assertTrue(data["warnings"])

    def test_in_tolerance_repair_is_noop(self) -> None:
        output = self.root / "noop-output"
        report = self.root / "noop.json"
        result = run_script(
            "lane_scale_profile.py",
            "repair",
            "--profile",
            self.profile,
            "--frames-dir",
            self.idle,
            "--row",
            "idle",
            "--output-dir",
            output,
            "--json-out",
            report,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(output.exists())
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["action"], "not-needed")

    def test_area_metric_catches_height_normalized_zoom(self) -> None:
        zoomed = self.root / "zoomed"
        zoomed.mkdir()
        for index in range(4):
            make_frame(zoomed / f"{index:02d}.png", height=100, bottom=190, width=72)
        audit_path = self.root / "zoomed-audit.json"
        result = run_script(
            "lane_scale_profile.py",
            "audit",
            "--profile",
            self.profile,
            "--frames-dir",
            zoomed,
            "--row",
            "zoomed",
            "--json-out",
            audit_path,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(audit["height_ratio"], 1.0)
        self.assertEqual(audit["selected_metric"], "area")
        self.assertGreater(audit["area_scale_ratio"], 1.1)


class CompactSummaryTests(unittest.TestCase):
    def test_summary_is_one_line_and_blocks_failed_input(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            passed = root / "passed.json"
            failed = root / "failed.json"
            passed.write_text(json.dumps({"ok": True, "warnings": ["reviewed"]}), encoding="utf-8")
            failed.write_text(json.dumps({"ok": False, "errors": ["duplicate"]}), encoding="utf-8")

            pass_result = run_script(
                "fast_qa_summary.py",
                "--input",
                f"validation={passed}",
                "--json-out",
                root / "pass-summary.json",
            )
            self.assertEqual(pass_result.returncode, 0, pass_result.stderr)
            self.assertEqual(len(pass_result.stdout.strip().splitlines()), 1)
            self.assertIn("warnings=1", pass_result.stdout)

            fail_result = run_script(
                "fast_qa_summary.py",
                "--input",
                f"validation={passed}",
                "--input",
                f"duplicates={failed}",
                "--json-out",
                root / "fail-summary.json",
            )
            self.assertEqual(fail_result.returncode, 2, fail_result.stderr)
            self.assertEqual(len(fail_result.stdout.strip().splitlines()), 1)
            self.assertIn("failed=duplicates", fail_result.stdout)


class GuardIntegrationTests(unittest.TestCase):
    def test_new_scale_and_uniqueness_dependencies_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            ledger = Path(raw) / "ledger.json"
            initialized = run_script(
                "fast_run_guard.py", "init", "--ledger", ledger, "--pet-id", "test-pet"
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)

            for gate in ("idle", "running-right", "scale-profile", "running-right-scale"):
                passed = run_script(
                    "fast_run_guard.py", "pass", "--ledger", ledger, "--gate", gate
                )
                self.assertEqual(passed.returncode, 0, passed.stderr)
            bulk = run_script(
                "fast_run_guard.py", "require", "--ledger", ledger, "--stage", "bulk-standard"
            )
            self.assertEqual(bulk.returncode, 0, bulk.stderr)

            blocked_standard = run_script(
                "fast_run_guard.py",
                "require",
                "--ledger",
                ledger,
                "--stage",
                "assemble-standard",
            )
            self.assertEqual(blocked_standard.returncode, 2)
            for gate in ("standard-scale-audit", "standard-lane-uniqueness"):
                run_script("fast_run_guard.py", "pass", "--ledger", ledger, "--gate", gate)
            allowed_standard = run_script(
                "fast_run_guard.py",
                "require",
                "--ledger",
                ledger,
                "--stage",
                "assemble-standard",
            )
            self.assertEqual(allowed_standard.returncode, 0, allowed_standard.stderr)

            for gate in ("look-row-9-semantics", "look-row-10-semantics"):
                run_script("fast_run_guard.py", "pass", "--ledger", ledger, "--gate", gate)
            blocked_raw = run_script(
                "fast_run_guard.py", "require", "--ledger", ledger, "--stage", "assemble-raw"
            )
            self.assertEqual(blocked_raw.returncode, 2)
            run_script(
                "fast_run_guard.py",
                "pass",
                "--ledger",
                ledger,
                "--gate",
                "all-lane-uniqueness",
            )
            allowed_raw = run_script(
                "fast_run_guard.py", "require", "--ledger", ledger, "--stage", "assemble-raw"
            )
            self.assertEqual(allowed_raw.returncode, 0, allowed_raw.stderr)


class PolicyTests(unittest.TestCase):
    def test_skill_orders_scale_duplicate_and_cleanup_gates(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(text.index("canonical-scale-profile.json"), text.index("After the early gate:"))
        self.assertLess(text.index("standard-lane-uniqueness"), text.index("Assemble one 8x9 atlas"))
        self.assertLess(text.index("all-lane-uniqueness"), text.index("Before despill"))
        self.assertIn("despill the accepted raw atlas exactly once", text)
        self.assertLess(text.index("look-row-9-semantics"), text.index("run the guard for `row10`"))

    def test_guard_encodes_new_dependencies(self) -> None:
        text = (SCRIPTS / "fast_run_guard.py").read_text(encoding="utf-8")
        self.assertIn('"assemble-standard"', text)
        self.assertIn('"standard-lane-uniqueness"', text)
        self.assertIn('"all-lane-uniqueness"', text)
        self.assertIn('"scale-profile"', text)


if __name__ == "__main__":
    unittest.main()
