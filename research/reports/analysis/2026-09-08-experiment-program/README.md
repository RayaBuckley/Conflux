# Conflux experiment programme — 2026-09-08

This package is a coder-facing experiment plan for the current Conflux repository. It is intended to be unpacked at the repository root. It does not replace canonical repository documentation; it is dated analysis and implementation guidance.

## Primary objective

Convert the current breadth of Conflux into a small set of defensible research results. The priority is stronger evidence, not additional surface area.

The recommended order is:

1. Reproducibility and baseline freeze.
2. SLED-V reduction and unbounded-verification experiments.
3. Comparative defence verification and implementation-conformance experiments.
4. Real-model AgentDojo experiments.
5. Planning utility and authority-footprint experiments.
6. Persistent-memory and argument-effect semantics experiments.
7. Delegation activation only after the above evidence is stable.
8. Production-policy/Cedar differential work as a lower-priority track.

## Repository state assumed by this plan

As inspected on 2026-09-08, the public `main` branch reports:

- one fail-closed ITES mediation kernel;
- Principal Context evaluated at action time;
- separate authorisation, visibility, consent, and read decisions;
- bounded native SLED verification with shortest counterexamples;
- a serialisable verification IR;
- optional Z3 bounded checking and a nuXmv adapter;
- property-scoped cone-of-influence reduction;
- bounded observational-confidentiality self-composition;
- finite comparative models for ITES, Dual-LLM, CaMeL, Progent, and PACT;
- authenticated dynamic planning;
- a pinned AgentDojo boundary and local model runners;
- retained Qwen2.5 1.5B/3B/7B smoke results;
- operational delegation still disabled;
- persistent-memory authority and richer argument-effect semantics still future work.

The repository itself states that current formal evidence is bounded and that comparative defence models are not implementation-conformance evidence. Preserve those claim boundaries.

## Source basis

This package synthesises:

- the current public Conflux `main` branch, especially `AGENTS.md`, `docs/reference/SECURITY_MODEL.md`, `docs/evidence/STATUS.md`, `research/experiments/`, and `src/conflux/planning/`;
- the Part B project report and preprint, which motivate planning, delegation, real-model testing, and stronger implementation verification;
- the project's earlier SLED-V research brainstorming, which proposes state reduction, IC3/PDR, confidentiality, controller synthesis, conformance, and persistent multi-session verification.

## Files in this package

- `00_EXECUTIVE_ROADMAP.md` — experiment priorities and thesis-level questions.
- `01_SLEDV_EXPERIMENTS.md` — state-reduction and unbounded-verification experiments.
- `02_COMPARATIVE_AND_CONFORMANCE.md` — defence comparison and implementation-conformance work.
- `03_AGENTDOJO_MODEL_EXPERIMENTS.md` — real-model benchmark design.
- `04_PLANNING_EXPERIMENTS.md` — planning utility/security experiment design.
- `05_SEMANTIC_EXTENSION_EXPERIMENTS.md` — persistent memory, argument effects, and delegation.
- `06_REPRODUCIBILITY_PROTOCOL.md` — mandatory evidence and statistics rules.
- `07_AI_CODER_EXECUTION_PLAN.md` — implementation sequence, commits, tests, and stop conditions.
- `experiment_program.json` — machine-readable task and acceptance-criteria summary.

## Non-negotiable research rules

Do not alter security semantics to improve a benchmark result. Do not silently post-process benchmark outputs so that a failed model run becomes a success. Do not call a finite or bounded result an unbounded proof. Do not claim an abstraction is faithful to CaMeL, Progent, PACT, or another system without explicit source-to-model validation. Do not combine implementation changes and generated experimental evidence in the same commit when they are independently meaningful. Preserve raw outputs and failure classifications.

Every experiment should produce evidence that a reviewer can inspect without trusting the AI coder's prose summary.
