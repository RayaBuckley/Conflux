# Conflux SaTML Experiment Package

Date prepared: 2026-09-10
Target: SaTML 2027 submission evidence
Repository: https://github.com/RayaBuckley/Conflux

## Purpose

This package is a self-contained execution brief for the AI coder. The objective is to produce fast, meaningful, publication-grade evidence without broadening Conflux's security semantics or adding speculative features.

The repository already has a strong offline security kernel, canonical Principal Context semantics, native finite-state SLED, a serialisable verification IR, Z3 BMC, COI reduction, planning infrastructure, AgentDojo integration, provenance/read/visibility separation, mutation fixtures, and retained evidence bundles. The experiments below should extend those existing paths rather than reimplement them.

## Non-negotiable rules

Follow the repository's `AGENTS.md` and `docs/AI_AGENT_GUIDE.md` before editing. Preserve these invariants:

1. Provenance is never silently discarded.
2. Principal Context is evaluated at action time.
3. Authorisation, visibility, read access, and consent remain separate decisions.
4. Consent cannot create authority.
5. Evaluation code may not encode benchmark-specific shortcuts.
6. Generated evidence must be separate from the implementation commit that generates it.
7. Every numerical claim must point to retained raw evidence and a reproducible command.
8. Never promote bounded evidence to an unbounded claim.
9. Do not treat candidate models of CaMeL, Progent, PACT, or Dual-LLM as implementation-faithful comparative results unless fidelity is independently established.
10. Model failures, parser failures, benchmark failures, unavailable backends, secure blocks, and task failures must be distinct outcome classes.

## Current evidence baseline that must remain reproducible

The following existing repository claims should be treated as regression anchors:

- Historical Part B reproduction: exactly 1,462,607 raw traces across the three archived environments.
- Canonical-state compression for that reproduction: 31 unique canonical states.
- Native SLED seeded monitor defects: 5/5 detected with one-step witnesses in retained reproduction evidence.
- Delegation/security mutation evidence: 7/7 retained mutants detected within the bounded fixture model.
- COI and Z3 agreement: original/reduced/reference/Z3 verdict agreement on retained fixtures and scaling through 16 irrelevant variables.
- AgentDojo: the end-to-end pipeline already executes; current small-model results are diagnostic, not efficacy evidence.
- Planning: four-mode pipeline executes; current 7B pilot is encouraging but small.
- Cedar: differential harness is ready but provider parity is not yet evidenced.

If any experiment implementation changes one of these outcomes, stop and diagnose before producing new paper evidence.

## Priority order

Run work in this order unless an existing repository path makes a later task essentially free:

P0. SLED -> SLED-V scaling
P0. Security mutation benchmark expansion
P0. Provenance precision vs utility
P0. Real-model AgentDojo evaluation
P1. Planning utility recovery
P1. Cedar differential run and confidentiality fixture expansion
P0. Aggregation, figures, evidence bundles, claim ledger update

The first three tracks should be entirely deterministic and are expected to produce useful results quickly. Do not wait for H100 access to begin them.

## Definition of done for every experiment

An experiment is not done until it has:

- a committed manifest describing parameters, source commit, implementation version, and assumptions;
- raw machine-readable output;
- explicit cell-level status (`complete`, `unavailable`, `model_failed`, `benchmark_failed`, etc.);
- deterministic aggregation code;
- generated summary JSON/CSV;
- at least one human-reviewable table or plot if the result is central to the paper;
- checksums for retained artifacts;
- a single rerun command;
- a claim-strength note explaining exactly what the evidence does and does not establish;
- tests for aggregation logic and any new security-relevant experiment semantics;
- `python scripts/validate.py` passing before the implementation commit and again before the evidence commit.

## Do not do

Do not spend submission time on production AWS completeness, persistent memory, runtime delegation activation, general generated-program verification, new agent frameworks, broad UI work, or implementing every neighbouring defence. Those are not needed to strengthen the SaTML evidence package.

## Files in this package

- `00_EXECUTION_ORDER.md`: precise work sequence and stopping rules.
- `01_SLEDV_SCALING.md`: flagship scaling experiment.
- `02_MUTATION_BENCHMARK.md`: expanded verification fault-injection benchmark.
- `03_PROVENANCE_PRECISION.md`: deterministic utility/precision experiment.
- `04_AGENTDOJO.md`: real-model benchmark protocol.
- `05_PLANNING.md`: planning utility-recovery protocol.
- `06_CEDAR_CONFIDENTIALITY.md`: cheap credibility extensions.
- `07_AGGREGATION_AND_FIGURES.md`: exact outputs needed for paper writing.
- `08_CLAIMS_AND_PAPER.md`: claim boundaries and paper mapping.
- `09_COMMIT_PLAN.md`: atomic commit sequence.
- `CODER_TASKS.json`: machine-readable task backlog.
- `EXPERIMENT_MATRIX.json`: target matrices and minimum viable runs.
- `ACCEPTANCE_CRITERIA.json`: hard completion gates.
- `RESULT_RECORD_SCHEMA.json`: common result-record shape to reuse or map onto current schemas.

