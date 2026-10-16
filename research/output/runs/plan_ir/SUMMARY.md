# Plan IR evidence: a plan x effect x bound grid with a defect space inside it

Suite: plan-ir-grid (3 plan shapes x 3 effect summaries x 4 bounds), 36 readings.
Source commit: `e36b1277d1f89d24aca50c71b84823f639646337`.

The population is structured, not selected: every combination of the three plan shapes, the three effect summaries (cleared, first action unauthorised, first action outside its capability envelope) and the four bounds appears exactly once, and the bound is a parameter of the abstraction rather than a chosen reading.

Each reading states an expectation before it is measured. The abstraction flags a capability violation only for code execution, so a capability mutant of a write-only plan is expected to stay clear; the bundle records that instead of hiding it, and misses are listed by id.

Expectations met: 36 of 36 readings (0 missed).
The three backends agree by verdict class on 36 of 36 readings (0 class disagreements).

Positive control: 16 of 36 readings carry an unsafe reference verdict, so the agreement cannot come from a grid that nothing can refute. The 20 readings that stay clear are the 5 case pairs (`code:authorised`, `pair:authorised`, `pair:capability`, `single:authorised`, `single:capability`) at every bound, and the bundle records their ids.

What this shows: on every reading of the grid the Z3 and nuXmv encodings reproduce the reference interpreter's verdict class; the unauthorised readings are refuted at every bound from 1 to 4; and the code-capability reading is refuted while the same mutant on a write-only plan is not, which is the abstraction's documented boundary rather than a lost mutant.

What this does not show: Agreement between the two encodings on thirty-six readings of three plans up to bound four is not a claim that the plan IR is safe in general: the grid covers three plan shapes, one operation catalogue and one mutant per lever, so invariants that no mutant here exercises are unmeasured, and the space of plans and levers is open.

Rerun: `python scripts/generate_plan_ir_evidence.py`
Detail: `evidence.json` in this directory.
