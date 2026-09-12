# Prompt to give the AI coder

You are working on the Conflux repository to produce SaTML-quality experimental evidence quickly and faithfully.

Read the repository root `AGENTS.md`, `docs/AI_AGENT_GUIDE.md`, `docs/evidence/CLAIMS.md`, `docs/evidence/STATUS.md`, `docs/reference/SLED.md`, `docs/reference/SECURITY_MODEL.md`, and `research/experiments/README.md` before changing code. Then read every file in this experiment package.

Your first objective is not to add new Conflux features. It is to extend existing experiment/evidence paths and produce reproducible results in this priority order:

1. SLED-V scaling and historical trace/state compression.
2. Expanded security mutation benchmark.
3. Provenance precision vs utility.
4. Real-model AgentDojo evaluation after a competency gate.
5. Planning utility recovery.
6. Optional Cedar differential and confidentiality fixtures.
7. Deterministic aggregation into paper tables/figures and conservative claim-ledger updates.

Before implementation, inspect the existing generators, result schemas, manifests, and retained run bundles. Reuse canonical infrastructure instead of creating parallel formats. If this package suggests a field or path that conflicts with the current repository, preserve the repository's canonical contract and adapt the experiment specification to it.

Work in atomic commits. Separate implementation from generated evidence. Every security/evaluation change needs tests and human-reviewable evidence. Never change canonical security semantics to improve results. Never drop failed/unavailable cells. Never hand-transcribe paper numbers. Never claim more than retained evidence supports.

Start with the smallest pilot that can falsify the experiment harness. For each track, produce safe and unsafe controls, verify expected verdicts, then scale. Run `python scripts/validate.py` before finalising implementation commits and again before integrating evidence.

At the end, produce a concise report containing:

- files changed;
- exact run commands;
- retained evidence paths;
- central numerical results;
- failed/unavailable cells;
- claim-strength interpretation;
- plots/tables generated;
- remaining blockers for SaTML submission.
