# ADR-027: Complete AgentDojo coverage and the full benchmark run

- Type: adr
- Status: accepted
- Date: 2026-10-10
- Owners: Conflux maintainers

## Context

The local AgentDojo adapter mediates exactly two upstream operations, `search_emails` and
`delete_file`, both from the workspace suite (`src/conflux/adapters/benchmarks/agentdojo_annotations.py`).
Every other tool call in every other suite is refused as `unsupported_tool`
(`src/conflux/adapters/benchmarks/agentdojo_local.py:188`), so cells outside the two-tool pilot have
zero achievable utility. `docs/evidence/VERIFICATION.md` section 32 measures the consequence: the 14B
stratified workspace bundle holds 156 refusal records across 78 cells with utility 1/78, and the
banking bundle holds 192 refusals across 24 cells with utility 0/24. The suites expose 69 distinct
tools (workspace 24, banking 11, slack 11, travel 28). The retained stratified bundles therefore
measure adapter coverage, not model behaviour, and a complete run is impossible in the current state.

The owner decided on 2026-10-10: complete means the entire AgentDojo benchmark; the full attack list;
one repetition and one seed; the same H100 guard caps, staged over several days if needed; and an ADR
before implementation starts.

## Decision

1. Stage 0, honesty before coverage: fix the two defects an independent survey found, namely one
   loaded source of truth for the mediated set and an honest split between policy denials and
   out-of-scope refusals in `failure_counts.policy`; make the sweep tool flag a suite whose cells all
   block on `unsupported_tool`; rescope the claims rows that describe the retained stratified bundles.
2. Stages 1 to 4 extend mediation to every tool of every suite, in the order workspace (24),
   banking (11), slack (11), travel (28). Each tool needs a reviewed argument-role annotation, one
   resource, an explicit permission rather than the current tool-name ternary
   (`agentdojo_local.py:210`), and per-suite environment data with reviewed fixture provenance.
   Each stage regenerates the pinned schemas, updates the tests that pin the pilot scope, and lands
   only on a green tier.
3. Stage 5 runs the entire benchmark: every user task against every injection task of its suite,
   against every registered attack, under the three defence settings, one repetition and seed 0.
   Benign runs use the user tasks alone.
4. Every stage is reviewed by an agent that did not write it, and no stage claims more coverage than
   its own measurements show.

## Size arithmetic (first-hand measurements, 2026-10-10)

- Suite shapes: banking 16 user tasks and 9 injection tasks, slack 21 and 5, travel 20 and 7,
  workspace 40 and 14. That is 949 user-and-injection pairs.
- Tool surface: 74 registered tool entries and 69 distinct names (workspace 24, banking 11, slack 11,
  travel 28); five names appear in more than one suite. Whether mediation keys on the suite-qualified
  entry or the bare name is a stage 1 design decision.
- Registered attacks in the pinned package (0.1.35): 17, of which five are denial-of-service attacks
  (`captcha_dos`, `dos`, `felony_dos`, `offensive_email_dos`, `swearwords_dos`) and six are
  `important_instructions` variants.
- Attacked cells: 949 pairs x 17 attacks x 3 defences = 48,399. Benign cells: 97 user tasks x 3
  defences = 291. Total 48,690 model cells.
- Measured per-cell latency, from the staged cells of the three 14B bundles (n=132): median 9.6 s,
  mean 10.1 s, p75 11.9 s, maximum 39.2 s, plus about two minutes of model load per run.
- At the median to p75 rate the full matrix is 130 to 160 pod hours, or 520 to 640 US dollars at 3.99
  dollars per hour: roughly four to five weeks if the 20 dollar daily cap is spent each day.
- Collapsing the six `important_instructions` variants to one leaves 12 canonical attack families:
  34,455 cells, about 92 to 114 pod hours, 368 to 453 dollars, roughly three weeks.
- The frozen stratified selection stays as the cheap regression tier: 192 cells, about 31 to 38 minutes at the measured rate.

## Consequences

- Extending coverage changes the tool-schema and annotation pins, and those pins live inside the
  protocol `inputs` block, so every future protocol fingerprint changes. Retained bundles keep their
  historical fingerprints and stay internally consistent; they must not be compared to new protocols
  as if the fingerprints matched.
- The generated manuscript tables and the literal counts pinned in `tests/test_fourth_year_tables.py`
  depend on those numbers and must be regenerated in the same change set that changes coverage.
- `failure_counts.policy` currently means "at least one blocked record", so it mixes policy denials
  with out-of-scope refusals. After stage 0 the two are counted separately, and existing bundles are
  not rewritten: their counts keep their recorded meaning.
- Test and gate changes go through the mutation-audit habit already used in this repository: an
  independent reviewer tries to weaken the tests and reports whether the gate notices.
- Cost is real and bounded by the guard: the full matrix is weeks of four-hour windows. Each full
  sweep is therefore preceded by the 192-cell regression tier, and no full sweep runs unattended.
- The extension also settles the six-cell assumptions still present in RunPod and paper scripts
  (`EXPECTED_AGENTDOJO_CELLS=6`, `AGENTDOJO_PREFLIGHT_CELLS=4`).
- Rejected alternatives: keeping the two-tool subset and only rescoping the claims (does not meet the
  owner's goal of a complete run), and running the full matrix before extending coverage (produces
  vacuous cells and would misreport adapter refusals as model failures).
