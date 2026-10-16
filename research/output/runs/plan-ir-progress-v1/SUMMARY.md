# Plan IR progress evidence: a declared goal/abort pair decides the bounded row

Suite: plan-ir-progress (28 readings x 3 routes), 84 measured rows at bounds 1, 2, 3, 4.
Source commit: `e36b1277d1f89d24aca50c71b84823f639646337`.

The liveness obligation the plan IR recorded before this bundle is `AG(step >= bound -> terminated)`, and the abstraction assigns `terminated` itself, so a bounded row satisfied it by construction. The readings here declare a plan's two good endings instead - the node that reaches the goal and a node that stops without it - and measure `step >= bound -> (goal_reached or safe_abort)` with the support invariants `safe-abort-clean` and `goal-reached-clean`.

The population is structured, not selected: the positive reading, the five controls and the no-endpoint reading each appear once at every bound from 1 to 4, and each reading states its expectation before it is measured.

Expectations met: 84 of 84 measured rows (0 reading(s) missed).
The three routes agree by verdict class on 28 of 28 readings (0 class disagreements).

Positive control: 20 of 28 readings carry an unsafe reference verdict, one per reading of every control family, so the agreement cannot come from a population nothing can refute. The controls are: an endpoint declared on a node a path may never take, a three-node plan whose first node may be taken forever, an abort node recorded as executed without authorisation, a goal action recorded as not executed, and the obligation weakened to a bare `goal_reached` claim.

The no-endpoint reading keeps the shape every earlier bundle recorded: [5] invariants and [8] state variables (unchanged).

What each route needed, per row: `nuxmv` - none on this bounded route: the step counter keeps its declared range; the symbolic route's transition-guard auxiliary is recorded in parameter-general-v1; `reference` - the bound is declared; the interpreter walks the reachable states; `z3` - the bound is declared; the obligation is asserted at the final step.

What this does not show: Four bounds of one plan shape family with declared endpoints, and one control per way the obligation can fail, are not a claim that a plan in general reaches its goal: the readings cover the three plan shapes, one operation catalogue and one mutant per lever, the endpoint declaration is the caller's, and whether a goal predicate can be read from a plan field rather than from a recorded effect summary is still open.

Rerun: `python scripts/generate_plan_ir_progress_evidence.py`
Detail: `evidence.json` in this directory.
