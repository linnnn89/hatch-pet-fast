# Deterministic Command Map

Load only the section needed for the current stage. The full argument contract remains authoritative in `$CODEX_HOME/skills/hatch-pet/SKILL.md` and each script's `--help` output.

## Contents

- [Environment](#environment)
- [Prepare](#prepare)
- [Extract and inspect one standard row](#extract-and-inspect-one-standard-row)
- [Check component ownership](#check-component-ownership)
- [Derive a proven-safe running-left row](#derive-a-proven-safe-running-left-row)
- [Standard atlas and review artifacts](#standard-atlas-and-review-artifacts)
- [Cardinal anchors](#cardinal-anchors)
- [Register row 9, then assemble row 10](#register-row-9-then-assemble-row-10)
- [Single final despill and validation](#single-final-despill-and-validation)
- [Final QA artifacts](#final-qa-artifacts)
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

## Derive a proven-safe running-left row

```powershell
& $Python "$SkillDir\scripts\derive_running_left_from_running_right.py" --help
```

Use only after visually approving `running-right` and rechecking symmetry on the actual generated row. Otherwise generate left natively.

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

Inspect its eight cells and semantics before generating row 10. Then assemble the final atlas using the registered row 9, its manifest, row 10, and a neutral cell from the approved standard atlas.

## Single final despill and validation

```powershell
& $Python "$SkillDir\scripts\despill_chroma_edges.py" --help
& $Python "$SkillDir\scripts\validate_atlas.py" --help
```

Despill the complete extended atlas exactly once. Validate the cleaned output with `--require-v2`, the run's chroma key, and the expected `1536 x 2288` dimensions. Stop with a pipeline failure if either deterministic result fails.

## Final QA artifacts

```powershell
& $Python "$SkillDir\scripts\make_contact_sheet.py" --help
& $Python "$SkillDir\scripts\make_direction_qa_sheet.py" --help
& $Python "$SkillDir\scripts\make_direction_blind_qa_sheet.py" --help
& $Python "$SkillDir\scripts\measure_direction_continuity.py" --help
& $Python "$SkillDir\scripts\combine_direction_blind_verdicts.py" --help
& $Python "$SkillDir\scripts\validate_direction_blind_verdicts.py" --help
```

Create three isolated verdict files, combine by strict majority, and require the cardinal pairs to pass. Record labeled semantic resolution for intermediate warnings.

## Package

Create a new pet package containing the cleaned extended WebP and `pet.json` with:

```json
{
  "spriteVersionNumber": 2
}
```

Validate the packaged spritesheet again. Never copy into an existing package path without explicit user approval.
