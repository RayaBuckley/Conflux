# Master Coder Specification: Supervisor Feedback Revision

## Goal

Make the Conflux repository and publications substantially stronger, clearer, and more defensible without expanding the project into an unbounded collection of new mechanisms.

The primary deliverable is a coherent security story:

> ITES is a conservative zero-trust authority floor. Authenticated principal provenance determines the execution's influence context; the organisation's existing ACS determines effective authority; the intersection is maximally permissive subject to the PE definition. The same design intentionally has utility costs when genuine low-authority information determines privileged actions. Fine-grained provenance and planning can reduce unnecessary authority collapse or improve empirical task completion, while explicit delegation is required for intentional authority transfer.

## Priority order

### P0 - Semantics and correctness

1. Make empty/unknown Principal Context semantics explicit and fail-closed.
2. Separate provenance from read authority everywhere in the code and documentation.
3. Verify that parameterised authority-bearing arguments are checked against the ACS, not merely coarse tool/action names.
4. Make rich execution branch semantics deterministic and explicitly specified.
5. Make persistent derived objects and scheduled executions inherit influence so that cross-call laundering is impossible.
6. Keep model/planner code unable to arbitrarily narrow Principal Context.
7. Ensure every effectful operation is mediated by the same canonical ITES kernel.
8. Define the semantics of trusted influence-removal/delegation explicitly rather than silently allowing reset.

### P0 - Tests

Add regression tests for:

- authenticated external source with zero organisational privileges;
- authenticated external source sharing only a subset of user permissions;
- coarse vs fine-grained provenance;
- same-author/non-reader and same-reader/non-author cases;
- persistent derived artefact followed by a fresh assistant call;
- scheduling from a tainted context followed by privileged execution;
- sibling alternatives and sequential plans;
- parameter tampering after approval/certificate creation;
- ACS mutation between planning and execution;
- empty/unknown context;
- denied operations and safe recovery.

### P0 - Publication claims

Rewrite the paper so it no longer:

- presents ITES as if low-water-mark monotonicity itself were novel;
- calls the elementary policy characterisation a deep theorem;
- presents bounded historical SLED counts as evidence of unbounded correctness;
- claims other defences "violate PE" merely because PE is not their native objective;
- says authentication itself restores authority;
- implies ITES prevents harm within already-authorised authority;
- ambiguously attributes tool output to the user simply because the tool was invoked on the user's behalf.

## P1 - Paper structure

### Abstract

Use the following logical structure:

1. Problem: arbitrary model behaviour means security should not rely on model intent recognition.
2. ITES: authenticated principal provenance + existing ACS + intersection authority.
3. Contribution/novelty: principal-sensitive authority derivation and system-level evaluation/verification framing, not the abstract intersection operation.
4. Key limitation: genuine external influence can reduce utility.
5. Planning: observation ordering/isolation can recover some utility without weakening the invariant; protected planning can improve empirical utility under attack.
6. Evaluation: present only the evidence actually generated and bounded.

Prefer "maximally permissive for the stated PE property" to broad "maximal utility" language.

### Related work

Add and accurately distinguish:

- Biba/LOMAC;
- HiStar;
- Flume;
- Asbestos;
- Clark-Wilson;
- Wu, Cecchetti, Xiao;
- CaMeL;
- Progent;
- PACT.

Do not turn the section into a catalogue. Each citation should support a specific semantic comparison.

### ITES semantics

Define separately:

- authenticated provenance;
- Principal Context;
- read authorisation;
- action authorisation;
- parameter/argument authority;
- persistent object propagation;
- scheduling propagation;
- delegation/authority changes;
- trusted influence removal/endorsement if studied.

### Formal results

Retain the formal statements, but label their status honestly:

- effective-authority meet/intersection is maximally permissive for the stated PE definition;
- authority is monotone non-increasing as Principal Context grows;
- PE safety follows from complete mediation + the intersection rule + provenance assumptions.

If the proofs are elementary, move detail to an appendix and use the main text for assumptions and implications.

### Utility section

Add the external-email/calendar example.

Then distinguish three utility mechanisms:

- finer provenance;
- planning optimisation;
- explicit authority transfer.

Also note that CaMeL-style protected planning can improve empirical utility under attack by making attacker-driven plan deviation less likely. Do not imply that this provides the same guarantee as ITES.

## P1 - CaMeL comparison

### Required position

Use:

> CaMeL is a system-level defence with capability/dependency-aware policies and a protected planning/control-flow architecture. Its policy interface is programmable and can be extended with additional semantics, but its native/expected security objective is not the ITES PE property. A faithful ITES implementation would require principal attribution, influence propagation, persistence, and ACS integration beyond merely writing a Python predicate.

### Table 9

Rename to something like:

> Comparison of native influence/enforcement semantics.

For each defence, record only claims supported by the primary source or checked implementation.

For CaMeL specifically:

- acknowledge source/provenance capabilities;
- acknowledge STRICT dependency propagation;
- describe protected control flow accurately;
- do not assert that arbitrary policy logic is absent;
- do not assert that CaMeL cannot be extended;
- test whether its native guarantees imply PE under the ITES influence definition.

The correct negative result is:

> native CaMeL does not imply the ITES PE predicate for the selected witness.

Not:

> CaMeL violates PE.

## P1 - SLED/SLED-V

The paper should present two roles clearly:

1. SLED as a general worst-case black-box/system-level evaluator that can test arbitrary defences at the interface level.
2. ITES+SLED as a conformance/sanity-check case study.

Do not use the ITES run as if it validates the theorem. The theorem comes from the semantics; SLED checks an implementation within a finite model/bound.

For historical 1.46M/1.5M results:

- explicitly state the environment count;
- state the depth bound;
- state incomplete traces;
- state any canonical-state reduction;
- distinguish raw traces from canonical states;
- identify it as historical bounded evidence;
- keep implementation-conformance claims separate from unbounded proof claims.

For SLED-V, separate verdicts such as:

- SAFE;
- UNSAFE with counterexample;
- SAFE WITHIN BOUND;
- UNKNOWN/UNSUPPORTED.

Never silently upgrade a bounded result to an unbounded security claim.

## P1 - Planning

Add planning as a utility mechanism, not a new security theorem.

### Planning optimisation

Model planning as choosing an execution decomposition/ordering that minimises unnecessary contamination while preserving the task.

Examples:

- do a user-only subtask before reading external content;
- isolate a low-authority source in a restricted subtask;
- avoid supplying unrelated inputs to the same execution;
- postpone observing sensitive data until the plan proves it is required;
- split tasks so that a privileged action is not performed by an execution whose context contains unnecessary low-authority influencers.

The planner must never remove real influence after it has entered the context.

### CaMeL-style protected planning

Separately, evaluate whether protecting plan/control flow from untrusted observations increases the empirical probability of reaching the intended goal under attack.

This is a utility/robustness measurement, not a replacement for ITES.

Report:

- benign task completion;
- adversarial task completion;
- attack-induced task deviation;
- security violations;
- authority-context size;
- number of observed sources;
- call count/latency.

## P1 - Delegation

Model delegation as an explicit ACS-authorised state transition followed by an ordinary action transition.

Do not imply that a principal authorised to perform action `a` is automatically authorised to delegate `a`.

Delegation should specify, where applicable:

- delegator;
- delegatee;
- exact actions/arguments/resources;
- expiry;
- invocation count;
- redelegation policy;
- revocation conditions;
- provenance binding.

SLED-V should eventually verify the combined transition relation.

## P2 - Evidence generation

Produce one reproducible end-to-end benchmark before adding further benchmark families.

Each experiment must record:

- repository commit;
- environment manifest;
- policy/ACS version/hash;
- model and model configuration;
- seed where applicable;
- raw outputs/traces;
- derived metrics;
- exclusions/incomplete runs;
- scripts used to regenerate tables/figures.

## P2 - Repo hygiene

Update any repository audits that still reference obsolete package names/paths.

Every security-relevant rule should have:

1. canonical documentation;
2. executable implementation;
3. targeted tests;
4. evidence/claim entry where an empirical claim is made.

Remove stale compatibility code only after all callers have migrated.

## Acceptance criteria

The task is complete only when:

- the paper and repository use one consistent definition of influence;
- external input semantics are explicit;
- provenance authentication is described as enabling accurate attribution, not granting authority;
- persistent/scheduled influence propagation is tested;
- CaMeL comparison uses native semantics and primary-source-supported statements;
- Table 9 is rewritten around influence/enforcement semantics;
- historical SLED evidence is bounded and labelled correctly;
- planning utility recovery is discussed and, where implemented, measured;
- the external-email example appears in the paper and tests;
- the formal claims are stated at the right strength;
- all security-sensitive tests pass;
- repository validation passes;
- generated publication claims are traceable to repository evidence.

## Suggested execution order

1. Read this spec and the corrigendum.
2. Inspect current `main` and identify any mismatch between the spec and implementation.
3. Write/update a semantic specification/ADR before changing code.
4. Implement P0 semantics and regression tests.
5. Run repository validation.
6. Update the paper's threat model, ITES semantics, limitations, and worked example.
7. Rewrite related work and the comparison table.
8. Update SLED/SLED-V wording and evidence ledger.
9. Implement/measure planning utility improvements if already supported by the current architecture; otherwise document the exact future-work boundary.
10. Re-run all validation and regenerate publication artefacts from canonical evidence.
11. Do not claim success unless the checks/evidence were actually produced.
