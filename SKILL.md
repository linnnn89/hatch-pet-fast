---
name: hatch-pet-fast
description: Create a new validated Codex v2 animated pet from a concrete image reference or clear character concept with an enforced generation budget, early semantic gates, deterministic repair routing, compact QA output, and minimal intermediates. Use for normal new-pet requests where speed or token efficiency matters. Route existing-atlas repair or migration, unusual renderer contracts, brand-only discovery, and unresolved pipeline failures to the full $hatch-pet skill.
---

# Fast Hatch Pet

Produce one standard Codex v2 pet with hard early gates. Save time by preventing bad art from reaching downstream stages, not by skipping release validation.

## Scope

Use this path only when all are true:

- one new pet is requested;
- a concrete reference or clear concept exists;
- the standard v2 atlas contract applies;
- no existing atlas must be repaired, migrated, or preserved.

Use full `$hatch-pet` for an existing atlas, nonstandard renderer behavior, manual cell repair, brand-only discovery, or a failure not covered by `references/failure-matrix.md`.

## Required sources

1. Read `$imagegen` before visual generation.
2. Reuse `$CODEX_HOME/skills/hatch-pet/scripts`; do not copy or rewrite production scripts.
3. Use this skill's `scripts/check_frame_component_ownership.py` for cross-slot ownership and `scripts/fast_run_guard.py` for attempt and dependency gates.
4. Load workspace dependencies and use the exact returned Python path.
5. Read only the current section of `references/commands.md`.
6. Read `references/failure-matrix.md` before look generation and whenever a gate fails.

## Release contract

- Atlas: `8 x 11`, `1536 x 2288`, `192 x 208` cells.
- Content: nine standard rows plus sixteen clockwise look directions.
- Package: `spriteVersionNumber: 2`.
- Art: generate only with `$imagegen`; use scripts for extraction, safe mirroring, registration, whole-row transforms, assembly, cleanup, measurement, and validation.
- Repair: regenerate a complete row only for visual/content failure. Never patch a final cell from another generation.
- QA: require deterministic atlas validation, blind cardinal QA, labeled direction semantics, continuity review, component ownership where risky, and one final visual review.
- Safety: never overwrite an existing pet package.

## Attempt budget and machine guard

The normal image-generation baseline is:

- base: 1;
- nine standard rows: 9, minus any proven-safe deterministic mirror;
- cardinal strip: 1;
- look rows: 2.

Default to a soft ceiling of 15 image-generation calls. Immediately before every call, record it with `fast_run_guard.py attempt`. The guard must refuse call 16. Continue beyond 15 only after reporting the failure classes and obtaining user approval.

Initialize `qa/fast-run-ledger.json` at the start. Record every passed gate and failure class. Before `row9`, `row10`, raw assembly, despill, and packaging, run the corresponding guard requirement. Do not rely on prose memory or a stale `imagegen-jobs.json`.

Never spend an image-generation call on:

- an exact chroma-background mismatch when identity and silhouette pass;
- extraction or grouping failure with stable source art;
- uniform scale, centering, baseline, or canvas registration drift;
- chroma fringe before final cleanup;
- a metric warning without a visible defect.

Use deterministic exact-background recomposition, extraction, registration, or one uniform whole-row transform instead. Never transform individual final cells independently.

## Compact run state

Maintain one short run note with identity, exclusions, symmetry, stage, attempt count by job, passed gates, one-line failure classes, accepted warnings, strategy changes, and final paths.

Keep prompts, manifests, and detailed JSON inside the run directory. In the parent conversation:

- return only `selected_source=<path>` and one concrete QA sentence from visual jobs;
- print only top-level `ok`, `errors`, `warnings`, size, mode, version, residue, and hash summaries;
- never print full manifests, per-cell validation arrays, prompt bodies, or base64 data.

## Stage 0 - Lock identity and risk

Write an identity lock of at most 100 words covering silhouette, palette, face, hair or ears, clothing or material, and one or two distinguishing features.

Remove secondary figures, text, watermarks, scenery, shadows, detached effects, and dispensable face/limb-adjacent objects unless explicitly required.

Record asymmetry, handed props, one-sided colors or ornaments, long or detached-looking appendages, intentional negative spaces, wide poses, and colors near the chroma key. Decide whether `running-left` is safe to mirror. Treat it as unsafe unless the actual generated right row preserves all semantics after a hypothetical flip.

## Stage 1 - Approve one canonical base

Prepare a new run with `prepare_pet_run.py`, initialize the guard ledger, then issue one base job.

Approve identity and silhouette before animation. If the only defect is non-exact chroma, deterministically key and recompose onto the exact run chroma; do not generate another base. Generate a second base only for a visible identity, anatomy, silhouette, clipping, or excluded-content failure.

Pass the `base` gate only after visual and pixel checks succeed.

## Stage 2 - Gate and parallelize standard motion

Generate `idle` and `running-right` first. Pass both gates before releasing any other standard row.

Require `running-right` to be a true screen-right profile: nose, chin, torso, and gait point right; the far eye is hidden or clearly occluded where the design allows; limbs alternate; the body stays grounded. After two failures with the same root cause, change the construction instead of rewriting synonyms.

After the early gate:

- mirror `running-left` only after proving symmetry on the generated right row;
- otherwise generate it natively;
- release the remaining visual jobs in waves of at most three concurrent calls when the host permits;
- extract and inspect each returned row immediately before starting a replacement call.

Classify before acting:

- visual/content failure: regenerate the complete row;
- stable art with grouping failure: use deterministic extraction or `stable-slots`;
- uniform scale/registration drift: apply one deterministic whole-row transform and re-inspect;
- chroma-only or metric-only issue: do not regenerate.

Run component ownership and inspect a black sheet after every `stable-slots` extraction and every row with a plausible detached hair lock, braid, tail, loop, ornament, or prop. Fail a component that appears in only one or two frames, jumps sides, resembles a neighbor, or floats outside the current pose. Do not run this expensive gate on clearly single-component low-risk rows merely by habit.

## Stage 3 - Review standard motion once

After all nine rows pass immediate checks, assemble one 8x9 atlas, one contact sheet, and the animation previews. Review identity, scale, baseline, attachments, direction, gait, and playback once.

Reserve parent visual inspection for the canonical base, standard contact sheet, necessary GIFs, direction sheet, and final contact sheet. Open individual source strips only to diagnose a failed gate.

Pass `standard-motion` only when no identity change, clipping, wrong direction, broken attachment, cross-frame component, inert animation, or conspicuous pop remains.

## Stage 4 - Prove look semantics before downstream work

Write a short look-mechanics note defining screen coordinates, anchored parts, gaze leaders, followers, occlusion, and prop behavior.

Generate and approve cardinals in this exact order:

1. `000` up
2. `090` screen-right
3. `180` down
4. `270` screen-left

Cardinals are hard gates. Do not continue if `090` or `270` is front-facing, ambiguous, or reversed.

Generate row 9, register it, and inspect a labeled normal-size strip before row 10. Hard requirements:

- `022.5` through `157.5` retain the screen-right facial half-plane;
- `112.5`, `135`, and `157.5` visibly progress toward down;
- no slot reverses quadrant, clips, changes identity, or snaps in scale.

Pass `look-row-9-semantics`, then run the guard for `row10`. If row 9 fails, row 10, raw atlas assembly, despill, and final blind QA are forbidden.

Generate row 10 from approved cardinals plus passed row 9. Hard requirements:

- `202.5` through `337.5` retain the screen-left facial half-plane;
- `292.5`, `315`, and `337.5` visibly progress toward up;
- the `157.5 -> 180 -> 202.5` and `337.5 -> 000` boundaries remain continuous.

If semantics pass but size differs, register or uniformly scale the whole row; do not generate again. Pass `look-row-10-semantics` only after the registered result passes.

Use at most five image references in priority order: layout, canonical base, standard contact sheet, cardinals, and passed row 9 for row 10. Omit the original reference after faithful canonicalization when necessary.

## Stage 5 - Preflight raw art, then clean once

Require both look-row semantic gates before assembling one raw 8x11 candidate.

Before despill, generate from the raw candidate:

1. contact review;
2. labeled direction review;
3. blind direction pairs and exactly three isolated verdicts;
4. continuity report.

The green background is acceptable for this preflight. Require both cardinal axis pairs, all labeled quadrants, and visible continuity to pass. Treat intermediate blind disagreement as review-only when labeled normal-size evidence confirms the intended quadrant without reversal.

Only after `raw-contact`, `raw-labeled-direction`, `raw-blind-direction`, and `raw-continuity` pass may the guard allow `despill`.

Then:

1. despill the accepted raw atlas exactly once;
2. validate the cleaned atlas with v2, chroma, RGBA, dimensions, residue, and cell checks;
3. create the cleaned final contact sheet and run one independent visual review;
4. package only the cleaned WebP and valid `pet.json`;
5. validate the packaged copy and compare its hash with the accepted cleaned atlas.

After despill reports `ok: true` and validation passes, cleanup is closed. Do not tune thresholds, run a second despill, or regenerate art for perceived fringe without a reproducible validation failure.

## Failure and cleanup policy

Count failures by root cause. After two occurrences, change construction, cardinal family, complexity, symmetry, or deterministic method. See `references/failure-matrix.md`.

After success, keep the package, accepted final WebP, compact validation and despill reports, final contact and direction sheets, blind majority/validation, semantics, continuity, previews, final review, request, and run summary.

Remove only task-created intermediates inside the confirmed run directory: prompts, duplicated guides, extracted frames, generated strips, obsolete raw/cleaned atlas versions, full per-cell debug JSON, and manifests. Keep at most one representative rejected artifact per root cause when it materially documents a repair. Never delete the source reference, installed package, or user files.

## Completion checklist

- [ ] Guard ledger exists and image-generation attempts are within the approved budget.
- [ ] Identity, exclusions, symmetry, and risks are recorded.
- [ ] Base passed; chroma-only issues used deterministic repair.
- [ ] `idle` and `running-right` passed before remaining standard jobs.
- [ ] Nine standard rows passed immediate and playback QA.
- [ ] Risky rows passed component ownership on black.
- [ ] Cardinals passed.
- [ ] Row 9 semantics passed before row 10 began.
- [ ] Row 10 semantics passed before raw atlas assembly.
- [ ] Raw contact, labeled, blind, and continuity gates passed before despill.
- [ ] Despill ran exactly once.
- [ ] Final atlas is RGBA `1536 x 2288`, v2, and deterministically valid.
- [ ] Independent final visual QA passed.
- [ ] New package and matching hash passed without overwrite.
- [ ] Task-only intermediates were cleaned.
