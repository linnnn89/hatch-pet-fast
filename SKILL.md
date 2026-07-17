---
name: hatch-pet-fast
description: Quickly create a new, validated Codex v2 animated pet from a concrete image reference or clear character concept while minimizing image-generation retries, context use, and intermediate files. Use when the user explicitly wants a fast or token-efficient normal new-pet workflow. Route brand-only discovery, existing-atlas repair or upgrade, unusual renderer contracts, and unresolved pipeline failures to the full $hatch-pet skill.
---

# Fast Hatch Pet

Create a normal new Codex v2 pet through early visual gates, deterministic reuse, and compact worker handoffs. Preserve every release gate; save time by rejecting weak inputs early and avoiding unnecessary regeneration.

## Scope

Use this fast path only when all are true:

- The request is for one new pet.
- A concrete reference image or sufficiently clear concept exists.
- The standard Codex v2 atlas contract is appropriate.
- No existing atlas must be repaired, migrated, or partially preserved.

Use the full `$hatch-pet` skill instead for brand-only discovery, an existing 8x9 or 8x11 atlas, nonstandard renderer behavior, manual cell repair, or a failure not covered by `references/failure-matrix.md`.

## Required tools and source of truth

1. Read and follow the `$imagegen` skill before visual generation.
2. Reuse the production scripts from `$CODEX_HOME/skills/hatch-pet/scripts`; do not copy or rewrite them. Use this skill's `scripts/check_frame_component_ownership.py` for the additional cross-slot component gate.
3. Load the workspace dependency paths and use the returned Python executable exactly.
4. Read `references/commands.md` only for the current deterministic stage.
5. Read `references/failure-matrix.md` when a gate fails and before starting look-direction generation.

## Non-negotiable output contract

- Produce an `8 x 11` atlas at `1536 x 2288` pixels.
- Use `192 x 208` cells.
- Include all nine standard rows and all sixteen clockwise look directions.
- Package with `spriteVersionNumber: 2`.
- Generate visual art only with `$imagegen`; use scripts only for extraction, mirroring when safe, assembly, cleanup, measurement, and validation.
- Generate a complete row again when its visual content fails. Never patch a final cell from an unrelated generation.
- Require deterministic atlas validation, cardinal-direction blind QA, labeled direction semantics, continuity review, and independent final visual QA.
- Never overwrite an existing package. Stop, version the name, or ask the user.

## Lean run state

Maintain one compact run note containing:

- pet name and canonical identity lock;
- exclusions and symmetry decision;
- current stage and passed gates;
- accepted warnings with visible evidence;
- strategy changes after recurrent failures;
- final package and QA paths.

Keep prompts, manifests, and intermediate images inside the run directory. Do not paste long prompts, base64 data, or full manifests into the parent conversation.

## Stage 0 — Lock identity and scan risks

Write an identity lock of at most 100 words covering silhouette, palette, face, hair/ears, clothing or body material, and one or two essential distinguishing features.

Remove from the canonical base unless the user explicitly needs them:

- secondary characters or dolls;
- watermark, signature, text, borders, and decorative background;
- dispensable objects near the face or limbs;
- detached sparkles, speed lines, dust, shadows, glows, and motion marks.

Record these risks before generation:

- bilateral asymmetry, handed props, colored limbs, one-sided ornaments;
- long braids, tails, loops, ear ornaments, or other detached-looking parts;
- intentional negative spaces that may look like alpha holes;
- very wide poses that may exceed automatic component slots;
- source colors close to the chosen chroma key.

Decide whether `running-left` may be mirrored. Mark it safe only if body design, markings, props, lighting, and visible accessories remain semantically correct after a horizontal flip. Otherwise plan a native left-facing row.

## Stage 1 — Build the canonical base

Prepare the run with `prepare_pet_run.py`, then assign exactly one base-image job.

The base must show one complete pet on a flat chroma background with no cropped extremities, secondary figure, guide marks, text, watermark, or detached effects. Approve identity and silhouette before requesting any animation row.

Copy only the selected result into the run directory and remove the task-generated duplicate after confirming the copy. Return from the visual job using only:

```text
selected_source=<absolute path>
qa_note=<one concrete sentence>
```

## Stage 2 — Gate standard motion early

Generate `idle` and `running-right` first. Do not spend calls on the other seven rows until both pass extraction and visual review.

For `running-right`, require a true screen-right side profile:

- nose, chin, torso, and gait point toward the right edge;
- the far eye is hidden or clearly occluded when the design allows it;
- the pose does not read as front-facing or merely three-quarter front;
- limbs alternate and the body stays grounded.

If the same direction failure occurs twice, stop rewriting synonyms. Change the construction: use a strict 2D profile, simplify the prop or silhouette, hide the far eye, or redesign the pose family.

After `running-right` passes, apply the recorded mirror decision:

- mirror deterministically only when the symmetry checklist still passes on the generated row;
- otherwise generate `running-left` natively and verify asymmetric markings and prop handedness.

Generate the remaining six standard rows in parallel only after the gate passes. Extract and inspect every returned row immediately. Classify a failure before acting:

- **Visual/content failure:** regenerate the complete row.
- **Stable source but failed component grouping:** retry deterministic extraction with `stable-slots` and explicitly allow it during inspection.
- **Chroma fringe only:** defer to the single final despill pass; do not regenerate.
- **Intentional holes or gaps:** inspect at high contrast and record evidence; do not repair merely because a metric flags them.

Treat `stable-slots` as a geometry fallback only. It can stabilize scale and placement while silently assigning a long braid, tail, hair lock, ornament, or other disconnected piece from an adjacent pose to the current frame. It does not prove component ownership.

After every `stable-slots` row, and after any row containing long or detached-looking appendages, run `scripts/check_frame_component_ownership.py` on the extracted frames. Keep its black-background sheet in QA. By default, fail any frame with a second alpha component of at least 25 pixels. If the design intentionally contains separate opaque parts, use `--allow-secondary` only after visually assigning every reported component to the current pose and recording that evidence.

Classify a component that appears in only one or two frames, jumps sides, resembles the neighboring pose, or floats outside the current silhouette as a visual/content failure. Regenerate the complete row. Never erase the fragment from a final cell, and never accept the row only because `inspect_frames.py --allow-stable-slots` passes.

## Stage 3 — Review standard motion once

Assemble the 8x9 intermediate atlas only after all nine rows pass their immediate checks. Build one contact sheet and the animation GIFs, then review identity, scale, baseline, attachments, direction, gait, and playback continuity.

Do not repeatedly open every source PNG in the parent context. Use row workers for local checks and reserve parent visual inspection for the canonical base, contact sheet, GIFs, direction sheet, and final extended contact sheet.

Block the look stage for a visible identity change, clipped body, wrong direction, broken attachment, cross-frame component, detached hair or appendage, reversed gait, inert animation, or conspicuous pop. Inspect high-risk rows on black; checkerboard transparency can hide a small neighboring-frame fragment. Ignore raw chroma fringe at this stage.

## Stage 4 — Build look directions in dependency order

Write a short pet-specific look-mechanics note: what remains anchored, what leads the gaze, what follows, which parts occlude, and how props behave. Define viewer/screen coordinates explicitly.

Generate and approve one four-cardinal strip in this order:

1. `000` up
2. `090` screen-right
3. `180` down
4. `270` screen-left

Cardinals are hard gates. For faces, use visible head, nose, pupil, eyelid, and occlusion evidence; do not accept every pose remaining front-facing. Repair a bad cardinal anchor before generating look rows.

Generate row 9 as one coherent eight-pose family, register and inspect it immediately, and continue only when no hard semantic or continuity failure remains. Then generate row 10 from the approved cardinals plus completed row 9 and inspect it immediately. Never generate both rows speculatively.

Keep image-generation references at five or fewer. Use this priority order:

1. matching layout guide;
2. canonical base;
3. standard-motion contact sheet;
4. approved cardinal strip;
5. completed row 9, for row 10 only.

If a canonical base has already captured the original reference faithfully, omit the redundant large original reference and record that decision. Never omit a required identity or direction source merely to satisfy the limit.

## Stage 5 — Assemble, validate, and package

1. Assemble the complete 8x11 atlas.
2. Run chroma despill exactly once on the complete atlas.
3. Validate the cleaned atlas with the v2 requirement.
4. Create the extended contact sheet, labeled direction sheet, blind direction pairs, and continuity report.
5. Obtain exactly three isolated blind verdicts and combine them by strict majority.
6. Require both cardinal axis pairs to pass. Treat intermediate blind disagreement as a warning only when labeled normal-size loop review confirms the intended quadrant and shows no reversal.
7. Run one independent final visual QA pass.
8. Package only after every hard gate passes.

When the despill report has `ok: true` and v2 atlas validation passes, treat chroma cleanup as closed. Do not regenerate art, tune thresholds repeatedly, or invent a second cleanup step because of perceived fringe.

After packaging, keep the final WebP, validation JSON, despill report, extended contact sheet, direction sheet, blind QA artifacts, semantics, continuity, previews, review, request, and run summary. Remove task-only prompts, layout guides, generated strips, extracted frames, PNG intermediates, 8x9 atlas, and manifest unless the user asks to preserve debug material.

## Efficiency rules

- Use at most three concurrent visual jobs; preserve dependency order.
- Give each visual worker one bounded job and the minimum required references.
- Return only the selected path and a concrete QA sentence.
- Inspect deterministic outputs immediately; late discovery multiplies regeneration cost.
- Do not retry image generation for an extraction-only, chroma-only, or metric-only issue.
- After two recurrences of one root failure, change strategy and record it.
- Treat cardinal ambiguity as a hard failure; treat an intermediate metric warning as evidence to inspect, not an automatic retry.
- Prefer a deterministic mirror or `stable-slots` only after its safety condition is proven.
- Never treat stable playback as proof of component ownership; require the component report and black-background sheet for every `stable-slots` or long-appendage row.
- Assemble expensive global artifacts once per accepted state, not after every row.

## Completion checklist

- [ ] Canonical identity lock and exclusions are recorded.
- [ ] Mirror safety is explicitly decided.
- [ ] `idle` and `running-right` passed before bulk generation.
- [ ] Nine standard rows passed immediate and playback QA.
- [ ] Every `stable-slots` or long-appendage row passed component-ownership QA on black.
- [ ] Look mechanics and four cardinals are approved.
- [ ] Row 9 passed before row 10 began.
- [ ] Final atlas is `1536 x 2288`, v2, and deterministically valid.
- [ ] Despill ran exactly once and reports success.
- [ ] Three blind verdicts were combined; cardinal pairs pass.
- [ ] Labeled semantics and continuity contain no hard failure.
- [ ] Independent final visual QA passed.
- [ ] A new package was created without overwriting an existing one.
- [ ] Task-only intermediates were cleaned after success.
