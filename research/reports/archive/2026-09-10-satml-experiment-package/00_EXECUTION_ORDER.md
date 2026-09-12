# Execution Order and Fast-Result Strategy

## Step 0: inspect before editing

Read, in this order:

1. `AGENTS.md`
2. `docs/AI_AGENT_GUIDE.md`
3. `docs/evidence/CLAIMS.md`
4. `docs/evidence/STATUS.md`
5. `docs/reference/SLED.md`
6. `docs/reference/SECURITY_MODEL.md`
7. `research/experiments/README.md`
8. existing manifests and retained runs for native SLED reproduction, COI scaling, Z3 agreement, AgentDojo, planning, Cedar preflight, direction readiness
9. the code that generated those bundles

Do not create parallel experiment infrastructure if a canonical generator/manifest/result path already exists. Extend the existing one.

## Phase A: quick deterministic evidence, target 1-2 coding sessions

### A1. SLED-V scaling

First implement parameterised synthetic fixture generation over the existing verification/native-SLED representation. Produce a tiny pilot with 3-5 scale points before adding the full grid. Required first result:

- show raw trace growth against canonical state growth;
- include the historical 1,462,607 -> 31 anchor;
- compare at least native canonical exploration, COI-reduced reference checking, and Z3 BMC where Z3 is available.

If exact historical trace enumeration is too expensive for larger generated fixtures, record timeout/censoring explicitly rather than reducing the workload silently.

### A2. Expanded mutation benchmark

Reuse the existing mutation infrastructure. Add mutants by property family, starting with the highest-value, easiest-to-express faults. A 20-mutant benchmark with principled coverage is more valuable than spending days reaching 40.

Minimum publishable target: >=20 distinct mutants across >=4 security-property families, all with explicit expected verdicts and minimal witness extraction where unsafe.

### A3. Provenance precision vs utility

This should be independent of real LLMs and therefore fast. Generate organisation/workflow fixtures in which the set of principals who *could* author data differs from the set of authenticated principals who actually contributed. Compare conservative may-have-written provenance with authenticated contribution provenance under exactly the same authorisation rule.

The experiment must not change ITES semantics. It changes only the precision of trusted provenance metadata.

## Phase B: live evidence

### B1. AgentDojo

Do not immediately launch a large matrix. First pick 3-5 representative tasks and validate that:

- benign utility is non-zero on the selected model;
- the evaluator's exact answer-format requirements are satisfied;
- raw upstream traces are retained;
- attacked and benign runs differ as expected;
- ITES annotations do not alter upstream success metrics except through mediated tool availability/execution.

Only after this pilot passes should the full selected subset run.

### B2. Planning

Expand the deterministic scenario suite first, then run live models. Ensure scenario success conditions are independent of planner mode. Run one strong enough model before adding weaker baselines.

## Phase C: cheap secondary evidence

Run Cedar differential parity if the pinned binary is available. Expand confidentiality fixtures using deterministic finite examples. Do not block the central paper evidence on either task.

## Phase D: freeze and aggregate

Once P0 experiment output is stable:

1. Freeze manifests.
2. Rerun deterministic experiments from a clean working tree.
3. Generate paper tables and plots only from retained raw bundles.
4. Update `docs/evidence/CLAIMS.md` conservatively.
5. Update manuscript generated inputs rather than manually transcribing numbers.
6. Produce one paper-evidence index mapping every numerical claim to run path, manifest, and generator commit.

## Stop conditions

Stop expanding a track if any of these occurs:

- it requires changing core security semantics to make results look better;
- it requires unvalidated reimplementation of another published system;
- it cannot produce a meaningful result before the submission window;
- it duplicates evidence already stronger elsewhere;
- the model is too weak for the task, in which case switch to a stronger available model rather than adding heuristic benchmark-specific post-processing;
- a result depends on manual cherry-picking or deleting failed cells.

## Minimum viable SaTML evidence set

If time becomes limited, finish these four deliverables first:

1. Scaling figure demonstrating trace/state compression and verification scaling.
2. Mutation table showing broad seeded-defect detection and witness generation.
3. Provenance-precision utility figure showing utility recovery without authority broadening.
4. AgentDojo table on a non-trivial task subset with at least no-defence and ITES conditions.

Planning, Cedar, and expanded confidentiality are bonuses after those four.
