# Deterministic Command Map

Load only the section needed for the current stage. The full argument contract remains authoritative in `$CODEX_HOME/skills/hatch-pet/SKILL.md` and each script's `--help` output.

## Contents

- [Environment](#environment)
- [Prepare](#prepare)
- [Guard ledger](#guard-ledger)
- [Extract and inspect one standard row](#extract-and-inspect-one-standard-row)
- [Check component ownership](#check-component-ownership)
- [Create, audit, and conditionally repair shared scale](#create-audit-and-conditionally-repair-shared-scale)
- [Derive a proven-safe running-left row](#derive-a-proven-safe-running-left-row)
- [Block duplicate lanes](#block-duplicate-lanes)
- [Standard atlas and review artifacts](#standard-atlas-and-review-artifacts)
- [Cardinal anchors](#cardinal-anchors)
- [Register row 9, then assemble row 10](#register-row-9-then-assemble-row-10)
- [Raw direction preflight](#raw-direction-preflight)
- [Single final despill and validation](#single-final-despill-and-validation)
- [Compact result output](#compact-result-output)
- [Package](#package)

## Environment

Use absolute paths. Obtain Python from the workspace dependency loader.

```powershell
$Python = '<exact returned Python path>'
$SkillDir = Join-Path $env:CODEX_HOME 'skills\hatch-pet'
$RunDir = '<absolute run directory>'
```

Before writing outputs, confirm `$RunDir` is the intended new run directory and no final package will be overwritten.

## Prepare

```powershell
& $Python "$SkillDir\scripts\prepare_pet_run.py" --help
```

Run it with the concrete reference, pet name/notes, and new output directory. It creates the request, prompts, layout guides, manifests, decoded, QA, and final structure.

## Guard ledger

Use the fast skill guard. Initialize once; never overwrite an existing ledger.

```powershell
$FastSkillDir = Join-Path $env:CODEX_HOME 'skills\hatch-pet-fast'
$Ledger = Join-Path $RunDir 'qa\fast-run-ledger.json'

& $Python "$FastSkillDir\scripts\fast_run_guard.py" init `
  --ledger $Ledger --pet-id '<pet-id>' --budget 15
```

Immediately before each image-generation call:

```powershell
& $Python "$FastSkillDir\scripts\fast_run_guard.py" attempt `
  --ledger $Ledger --job '<base-or-row-name>'
```

Record a passed gate or classified failure:

```powershell
& $Python "$FastSkillDir\scripts\fast_run_guard.py" pass `
  --ledger $Ledger --gate '<gate>' --artifact '<relative-path>'

& $Python "$FastSkillDir\scripts\fast_run_guard.py" fail `
  --ledger $Ledger --job '<job>' --class '<failure-class>' `
  --note '<160-character concrete note>'
```

Require dependencies before expensive stages:

```powershell
& $Python "$FastSkillDir\scripts\fast_run_guard.py" require --ledger $Ledger --stage row10
& $Python "$FastSkillDir\scripts\fast_run_guard.py" require --ledger $Ledger --stage assemble-standard
& $Python "$FastSkillDir\scripts\fast_run_guard.py" require --ledger $Ledger --stage assemble-raw
& $Python "$FastSkillDir\scripts\fast_run_guard.py" require --ledger $Ledger --stage despill
& $Python "$FastSkillDir\scripts\fast_run_guard.py" require --ledger $Ledger --stage package
```

Allowed gate names are free-form. The guarded dependencies additionally use `scale-profile`, `running-right-scale`, `standard-scale-audit`, `standard-lane-uniqueness`, and `all-lane-uniqueness`.

## Extract and inspect one standard row

```powershell
& $Python "$SkillDir\scripts\extract_strip_frames.py" `
  --strip "$RunDir\decoded\<row>.png" `
  --output-dir "$RunDir\decoded\frames\<row>" `
  --json-out "$RunDir\qa\<row>-extraction.json"

& $Python "$SkillDir\scripts\inspect_frames.py" `
  --frames-dir "$RunDir\decoded\frames\<row>" `
  --json-out "$RunDir\qa\<row>-inspection.json"
```

For a stable strip whose automatic component grouping alone failed:

```powershell
& $Python "$SkillDir\scripts\extract_strip_frames.py" `
  --strip "$RunDir\decoded\<row>.png" `
  --output-dir "$RunDir\decoded\frames\<row>" `
  --json-out "$RunDir\qa\<row>-extraction.json" `
  --method stable-slots

& $Python "$SkillDir\scripts\inspect_frames.py" `
  --frames-dir "$RunDir\decoded\frames\<row>" `
  --json-out "$RunDir\qa\<row>-inspection.json" `
  --allow-stable-slots
```

## Check component ownership

Run this after every `stable-slots` extraction and every row with long braids, hair, tails, loops, ornaments, or other detached-looking parts. Point `--frames-dir` at the directory that directly contains the extracted frame PNGs.

```powershell
$FastSkillDir = Join-Path $env:CODEX_HOME 'skills\hatch-pet-fast'

& $Python "$FastSkillDir\scripts\check_frame_component_ownership.py" `
  --frames-dir "$RunDir\qa\rows\<row>\frames\<row>" `
  --json-out "$RunDir\qa\rows\<row>\component-ownership.json" `
  --black-sheet "$RunDir\qa\rows\<row>\components-black.png"
```

The default hard gate fails any frame with a secondary alpha component of at least 25 pixels. Use `--allow-secondary` only for a design with intentional separate opaque parts, then visually assign every warning to the current pose on the black sheet. Stable playback without this check is insufficient.

## Create, audit, and conditionally repair shared scale

Create one profile from accepted extracted `idle` frames:

```powershell
& $Python "$FastSkillDir\scripts\lane_scale_profile.py" create `
  --frames-dir "$RunDir\decoded\frames\idle" `
  --output "$RunDir\qa\canonical-scale-profile.json"
```

Audit every grounded standard row and keep the detailed JSON on disk:

```powershell
& $Python "$FastSkillDir\scripts\lane_scale_profile.py" audit `
  --profile "$RunDir\qa\canonical-scale-profile.json" `
  --frames-dir "$RunDir\decoded\frames\<row>" --row '<row>' `
  --json-out "$RunDir\qa\<row>-scale.json"
```

The default `--metric auto` compares both alpha-bbox height and the square root of visible-alpha area. The area proxy catches rows that an extractor normalized back to full cell height despite a visible zoom. For a visibly confirmed silhouette-changing pose whose body scale does not pop during normal-size playback, repeat the audit with `--pose-variant`. This converts metric drift into a review warning. Do not use it to waive an actually shrunken jumping lane or a cross-action zoom.

If and only if a visually correct row fails the size gate, repair the complete row into a new directory:

```powershell
& $Python "$FastSkillDir\scripts\lane_scale_profile.py" repair `
  --profile "$RunDir\qa\canonical-scale-profile.json" `
  --frames-dir "$RunDir\decoded\frames\<row>" --row '<row>' `
  --output-dir "$RunDir\decoded\frames\<row>-scale-repaired" `
  --json-out "$RunDir\qa\<row>-scale-repair.json" `
  --anchor-mode median --resample nearest
```

For `jumping`, use `--anchor-mode lowest` so the lowest pose keeps the canonical feet baseline while every frame's vertical offset remains part of the arc. Never point `--output-dir` at the source directory. After repair, rerun row inspection, risky-component QA, playback review, and scale audit.

Aggregate the accepted per-row audit and repair reports. Include only rows whose body scale is meaningfully comparable; include pose-variant reports when their warning was visually confirmed.

```powershell
& $Python "$FastSkillDir\scripts\fast_qa_summary.py" `
  --input "idle=$RunDir\qa\idle-scale.json" `
  --input "running-right=$RunDir\qa\running-right-scale.json" `
  --input "running-left=$RunDir\qa\running-left-scale.json" `
  --input "waiting=$RunDir\qa\waiting-scale.json" `
  --input "running=$RunDir\qa\running-scale.json" `
  --input "review=$RunDir\qa\review-scale.json" `
  --json-out "$RunDir\qa\standard-scale-summary.json"
```

## Derive a proven-safe running-left row

```powershell
& $Python "$SkillDir\scripts\derive_running_left_from_running_right.py" --help
```

Use only after visually approving `running-right` and rechecking symmetry on the actual generated row. Otherwise generate left natively.

## Block duplicate lanes

Run the checker on explicit accepted strips. It compares decoded RGBA pixels, not only file bytes, so different PNG encodings cannot hide a duplicated animation.

```powershell
& $Python "$FastSkillDir\scripts\check_duplicate_lanes.py" `
  --lane "idle=$RunDir\decoded\idle.png" `
  --lane "running-right=$RunDir\decoded\running-right.png" `
  --lane "running-left=$RunDir\decoded\running-left.png" `
  --lane "waving=$RunDir\decoded\waving.png" `
  --lane "jumping=$RunDir\decoded\jumping.png" `
  --lane "failed=$RunDir\decoded\failed.png" `
  --lane "waiting=$RunDir\decoded\waiting.png" `
  --lane "running=$RunDir\decoded\running.png" `
  --lane "review=$RunDir\decoded\review.png" `
  --json-out "$RunDir\qa\standard-lane-uniqueness.json"
```

Run it again with the two accepted look strips before 8x11 assembly. Do not delete a duplicate automatically. Classify which job returned the wrong artifact, invalidate only that lane, and regenerate or recopy it from its bound generation result.

## Standard atlas and review artifacts

```powershell
& $Python "$SkillDir\scripts\compose_atlas.py" --help
& $Python "$SkillDir\scripts\make_contact_sheet.py" --help
& $Python "$SkillDir\scripts\render_animation_previews.py" --help
```

Build these once after all nine standard rows pass immediate checks.

## Cardinal anchors

```powershell
& $Python "$SkillDir\scripts\extract_cardinal_anchors.py" `
  --strip "$RunDir\decoded\look-cardinals.png" `
  --output-dir "$RunDir\decoded\look-anchors" `
  --json-out "$RunDir\qa\cardinal-anchors.json"

& $Python "$SkillDir\scripts\compose_cardinal_anchor_strip.py" `
  --anchors-dir "$RunDir\decoded\look-anchors" `
  --output "$RunDir\decoded\look-anchors-approved.png"
```

Approve `000`, `090`, `180`, and `270` semantically before row 9.

## Register row 9, then assemble row 10

Use `assemble_extended_atlas.py --help` for the current script signature.

First register row 9 and write:

- `qa/look-row-9-registered.png`
- `qa/look-row-9-registration.json`

Inspect its eight cells and labeled semantics before generating row 10. Pass `look-row-9-semantics`, then require `row10` with the guard. Register and inspect row 10, pass `look-row-10-semantics`, then require `assemble-raw` before assembling the raw atlas.

For a semantically correct row with uniform scale or registration drift, measure the accepted-row median bounds and apply one aspect-preserving transform to the complete row. Re-extract and inspect all cells. Do not generate again and do not transform cells independently.

## Raw direction preflight

Create these from the accepted raw 8x11 atlas before despill:

```powershell
& $Python "$SkillDir\scripts\make_contact_sheet.py" --help
& $Python "$SkillDir\scripts\make_direction_qa_sheet.py" --help
& $Python "$SkillDir\scripts\make_direction_blind_qa_sheet.py" --help
& $Python "$SkillDir\scripts\measure_direction_continuity.py" --help
& $Python "$SkillDir\scripts\combine_direction_blind_verdicts.py" --help
& $Python "$SkillDir\scripts\validate_direction_blind_verdicts.py" --help
```

The chroma background is acceptable for this semantic preflight. Record and pass `raw-contact`, `raw-labeled-direction`, `raw-blind-direction`, and `raw-continuity`. Require `despill` with the guard. Never despill a candidate that has not passed these four gates.

## Single final despill and validation

```powershell
& $Python "$SkillDir\scripts\despill_chroma_edges.py" --help
& $Python "$SkillDir\scripts\validate_atlas.py" --help
```

Despill the complete extended atlas exactly once. Validate the cleaned output with `--require-v2`, the run's chroma key, and the expected `1536 x 2288` dimensions. Stop with a pipeline failure if either deterministic result fails.

Create the final cleaned contact sheet and perform one independent visual review. The raw semantic verdicts remain authoritative because despill changes only edge/background color, not pose direction. If cleanup visibly changes anatomy, treat that as a reproducible cleanup failure rather than rerunning art generation.

## Compact result output

Write detailed JSON to disk, then aggregate only the required release reports:

```powershell
& $Python "$FastSkillDir\scripts\fast_qa_summary.py" `
  --input "validation=$RunDir\qa\validation.json" `
  --input "despill=$RunDir\qa\despill-report.json" `
  --input "duplicates=$RunDir\qa\all-lane-uniqueness.json" `
  --input "scale=$RunDir\qa\standard-scale-summary.json" `
  --input "final-visual=$RunDir\qa\final-visual-qa.json" `
  --json-out "$RunDir\qa\fast-qa-summary.json"
```

The script prints one line. Never print `checks`, `cells`, manifests, prompt bodies, or full component arrays unless the compact summary names that report as failed.

## Package

Create a new pet package containing the cleaned extended WebP and `pet.json` with:

```json
{
  "spriteVersionNumber": 2
}
```

Validate the packaged spritesheet again. Never copy into an existing package path without explicit user approval.

After matching the packaged hash, remove task-created obsolete versions and detailed debug intermediates only from the confirmed run directory. Keep one representative rejected artifact per root cause only when needed for the run summary.
