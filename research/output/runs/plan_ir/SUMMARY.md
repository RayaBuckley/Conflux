# Plan IR evidence: a plan x effect x bound grid, not a single reading

Suite: plan-ir-grid (2 plan shapes x 2 effect summaries x 4 bounds), 16 readings.
Source commit: `9fbe2b5215511714b8ec6847d283b10ac1eb7c4e`.

The population is structured, not selected: every combination of the two plan shapes, the two effect summaries and the four bounds appears exactly once, and the bound is a parameter of the abstraction rather than a chosen reading.

The three backends agree by verdict class on 16 of 16 readings (0 class disagreements).

Positive control: 8 readings carry an unsafe reference verdict, so the agreement cannot come from a grid that nothing can refute. The readings that are not refuted are recorded by id (`plan:evidence-plan-single:b1`, `plan:evidence-plan-single:b2`, `plan:evidence-plan-single:b3`, `plan:evidence-plan-single:b4`, `plan:evidence-plan-pair:b1`, `plan:evidence-plan-pair:b2`, `plan:evidence-plan-pair:b3`, `plan:evidence-plan-pair:b4`).

What this shows: on every reading of the grid the Z3 and nuXmv encodings reproduce the reference interpreter's verdict class, and the unauthorised readings are refuted at every bound from 1 to 4.

What this does not show: Agreement between the two encodings on sixteen readings of two plans up to bound four is not a claim that the plan IR is safe in general: the grid covers one plan shape, one operation catalogue and one effect-summary pattern, and the space of plans is open.

Rerun: `python scripts/generate_plan_ir_evidence.py`
Detail: `evidence.json` in this directory.
