# Failure Matrix

Read this file when a gate fails and immediately before look-direction generation. Diagnose the failure class before spending another image-generation call.

| Symptom | Class | First action | Do not do | Escalation |
|---|---|---|---|---|
| Canonical identity passes but the flat background is not the exact chroma value | Deterministic chroma setup | Key and recompose the accepted character onto the exact run chroma; verify pixels | Spend another base-generation call for color alone | Regenerate only for visible identity, anatomy, silhouette, clipping, or excluded-content failure |
| Right-facing run still reads front-facing or three-quarter front | Visual semantics | Request a strict 2D side profile; show one near eye, hide the far eye, and make nose/chin/gait point screen-right | Keep swapping words such as “stronger right” in the same construction | After two occurrences, simplify the silhouette or pose family |
| Mirrored left row swaps a colored limb, marking, accessory, lighting, or prop hand | Mirror safety | Reject mirroring and generate the full left-facing row natively | Repair individual mirrored cells | Preserve the native row as one coherent generation |
| Long braids, tails, or loops cause unstable automatic component grouping while the strip itself is stable | Deterministic extraction | Use `stable-slots`, inspect with `--allow-stable-slots`, then run component-ownership QA and inspect the black sheet | Accept stable playback as proof that every component belongs to the frame | Regenerate if a component cannot be assigned to the current pose |
| Hair, braid, tail, or ornament appears only in one or two frames or looks copied from the neighboring pose | Cross-slot component ownership | Fail the row, preserve the evidence, and regenerate the complete row with isolated connected poses | Delete the fragment from one final cell or waive it because atlas validation passes | Prefer `auto/components`; if `stable-slots` remains necessary, require the strict 25-pixel gate before acceptance |
| Edge or alpha-hole warning occurs around ears, braids, legs, tail loops, or ornaments | Metric/visual review | Inspect at high contrast and normal size; record whether the gap is intentional negative space | Fill every hole automatically | Repair only visible seams, clipping, or detached anatomy |
| A row contains fewer or more than the required pose groups | Visual structure | Regenerate the complete row with the layout guide | Patch missing cells from another generation | Simplify pose width or spacing after recurrence |
| `090` and `270` cardinals are reversed or ambiguous | Direction semantics | Repair the bad cardinal anchor and recompose the approved cardinal strip | Continue to row 9 or trust labels | Change head/profile construction after the second failure |
| Look row changes the whole sprite by rotation, skew, or rocking | Look mechanics | Redesign gaze using eyes, head, face, upper body, or natural attached parts while preserving the grounded anchor | Accept whole-sprite rotation for an ordinary pet | Route unusual rigid-object mechanics to full `$hatch-pet` if unclear |
| Row 9 contains a wrong quadrant, reversal, clipped pose, or identity jump | Visual semantics/continuity | Strengthen the complete row instructions and resynthesize row 9 | Start row 10 or patch one final cell | Revisit cardinal pose families after recurrence |
| Row 9 reaches down but `112.5` to `157.5` crosses to the screen-left facial half-plane | Direction half-plane | Fail `look-row-9-semantics`, preserve one labeled artifact, and regenerate row 9 with a screen-right nose/near-eye lock | Generate row 10, assemble an atlas, despill, or wait for final blind QA | Rebuild the right/down-right cardinal family after recurrence |
| Row 10 breaks continuity with row 9 | Visual continuity | Regenerate row 10 using approved cardinals and completed row 9 as evidence | Independently restyle cells | Revisit look mechanics if boundary failures cycle |
| A semantically correct row is uniformly too small, too large, high, low, or off-center | Deterministic registration | Measure accepted bounds and apply one aspect-preserving transform to the complete row; re-extract and inspect | Regenerate art or transform final cells separately | Regenerate only if the transform exposes clipping or identity inconsistency |
| Image generation rejects more than five references | Tool limit | Keep layout, canonical base, contact sheet, cardinals, and row 9 when required; omit only a redundant original reference after canonicalization | Drop direction or identity evidence silently | Record every omitted reference and why it is redundant |
| Blind workers disagree on an intermediate direction | Review warning | Inspect the labeled normal-size ordered loop and continuity evidence | Regenerate automatically from blind uncertainty alone | Regenerate if labeled review confirms wrong quadrant, missing axis, or reversal |
| Blind majority fails a cardinal pair | Hard direction failure | Repair the corresponding cardinal basis and resynthesize the containing look row | Override a cardinal failure | Do not package until the cardinal pair passes |
| Continuity metric flags a large silhouette change between narrow profile and broad front view | Metric warning | Review the actual ordered loop at normal size | Treat the number alone as proof of failure | Repair only a visible snap, pop, identity shift, or semantic discontinuity |
| Chroma fringe appears before final cleanup | Pipeline timing | Continue to the final single despill pass | Regenerate rows or repeatedly tune source art | Stop only if final despill or v2 validation fails |
| Despill is about to run before raw contact, labeled direction, blind direction, and continuity gates pass | Pipeline order | Block despill with `fast_run_guard.py require --stage despill` | Create a disposable cleaned v1 candidate | Repair the failing raw semantic gate first |
| Perceived fringe remains after despill `ok: true` and v2 validation passes | Closed deterministic gate | Accept the authoritative deterministic result | Run despill again, invent another repair, or regenerate art | Escalate only with a reproducible validation failure |
| Parent context is filling with row images and prompt text | Token/process waste | Keep local worker inspection; return only selected path and one QA sentence | Attach previews, base64, or full prompt bodies | Parent opens only gate artifacts and final QA sheets |
| A validator emits a large per-cell JSON report | Token/process waste | Write full JSON to disk and print only top-level status, dimensions, mode, version, residue, errors, and warnings | Stream `cells`, manifests, or component arrays into the parent context | Open one failing cell entry only when its top-level error requires diagnosis |
| Attempt 16 is requested under the default fast budget | Budget guard | Stop and summarize attempts by job and failure class | Silently raise the budget or continue retrying synonyms | Continue only after a strategy change and explicit user approval |
| Success leaves multiple raw/cleaned atlas versions and full debug trees | Artifact waste | Keep accepted release/QA evidence and remove task-created obsolete versions inside the confirmed run directory | Delete sources, installed packages, user files, or evidence outside the run directory | Preserve one representative rejected artifact per root cause when useful |
| Target package already exists | File safety | Stop, choose a new versioned name, or ask the user | Overwrite, delete, or use force | Use full `$hatch-pet` if preservation/migration is required |

## Strategy-change rule

Count failures by root cause, not by filename or prompt wording. When the same root cause occurs twice, change one of:

- pose construction;
- cardinal pose family;
- prop complexity;
- symmetry decision;
- deterministic extraction method;
- pet feature design.

If the repair merely moves the failure to a neighboring cell or another gate, treat it as the same cycle and change strategy immediately.
