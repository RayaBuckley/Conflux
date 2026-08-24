# Conflux AI-Assisted Development Workflow Improvement Specification

**Purpose:** Implementation brief for an AI coding agent\
**Target repository:** `RayaBuckley/Conflux`\
**Date:** 24 August 2026\
**Status:** Proposed workflow/governance change; implementation should
preserve existing canonical ownership rules.

## 1. Objective

Conflux is developed primarily with AI coding tools. The repository
already has a strong deterministic validation and evidence architecture:
strict typing, linting, tests, schema validation, repository audits,
reproducible evidence, bounded/formal verification,
mutation/negative-control evidence, and explicit claim-strength
tracking.

The next workflow improvement is to make the *development process
itself* follow the same philosophy:

> Use AI aggressively for discovery, research, design exploration,
> implementation, and adversarial review; use deterministic evidence
> wherever a reliable oracle exists; reserve human judgement for
> research significance, normative decisions, assumptions, and ambiguous
> trade-offs.

The current informal loop is approximately:

1.  ask an AI coder to inspect/review the repository;
2.  inspect its suggestions manually;
3.  accept or reject suggestions;
4.  ask the coder to implement accepted suggestions;
5.  run validation.

Replace this with a staged, evidence-oriented workflow:

**Discover → Falsify → Research → Specify → Human gate → Implement →
Verify → Adversarial review → Human gate → Commit/evidence →
Claims/literature synchronisation.**

The implementation should improve reliability without creating excessive
bureaucracy, parallel sources of truth, or large amounts of manually
maintained metadata.

## 2. Existing repository constraints to preserve

Before changing anything, inspect the current versions of at least:

-   `AGENTS.md`
-   `WORKFLOW.md`
-   `docs/AI_AGENT_GUIDE.md`
-   `docs/DEVELOPMENT.md`
-   `docs/evidence/CLAIMS.md`
-   `docs/evidence/STATUS.md`
-   `docs/evidence/task-registry.json`
-   `scripts/audit_repository.py`
-   `scripts/validate.py`
-   relevant schemas and tests.

Current repository guidance already establishes several important rules
that must remain intact:

-   security-model correctness is the highest priority;
-   provenance is not silently discarded;
-   Principal Context is evaluated at action time;
-   authorisation, visibility, read access, and consent remain distinct;
-   consent/model output cannot manufacture authority;
-   unsupported security-sensitive behaviour fails closed;
-   benchmark behaviour stays outside the domain/ITES kernel;
-   foundational changes require decision-complete specifications;
-   canonical documentation owners must be updated rather than
    duplicated;
-   implementation, bounded evidence, empirical results, and hypotheses
    must remain distinct;
-   generated evidence is committed separately from the implementation
    that generates it;
-   `python scripts/validate.py` is the pre-commit validation gate.

Do not replace these rules with a new workflow document that competes
with `docs/AI_AGENT_GUIDE.md`. Extend the existing ownership structure.

## 3. Design principles

### 3.1 Determinism governs acceptance, not exploration

Do not constrain the AI into being deterministic during discovery. The
model should be free to propose unusual defects, research connections,
counterexamples, simplifications, and designs.

Deterministic checks should instead govern whether claims become
repository facts.

Examples:

-   a suspected implementation bug should ideally become a failing test
    or counterexample;
-   a security bug should ideally become a SLED/solver witness or
    negative-control case;
-   a schema problem should become a schema failure;
-   a reproducibility problem should become a byte/hash mismatch;
-   an architecture violation should become an import/audit failure;
-   a literature citation should be backed by a verified primary source;
-   a novelty claim cannot be established by a deterministic checker and
    remains a research judgement.

### 3.2 Distinguish kinds of authority

Make the repository guidance explicitly distinguish:

**Descriptive authority --- what currently happens** 1. retained
runtime/generated evidence; 2. executable code, tests, and schemas; 3.
maintained descriptive documentation.

**Normative authority --- what should happen** 1. accepted
specification/ADR/security model; 2. implementation and tests should
conform to it.

**Scientific authority --- what may be claimed** 1. retained
reproducible evidence plus explicit assumptions; 2. claim ledger; 3.
manuscript prose.

A disagreement between these layers is a defect to investigate; passing
tests do not override a normative security specification, and prose does
not override retained evidence.

### 3.3 Evidence before repair

A review finding should normally be classified as one of:

-   `confirmed_defect`: reproducible evidence demonstrates a
    discrepancy;
-   `research_gap`: a justified missing experiment, comparison, proof,
    or literature area;
-   `design_hypothesis`: plausible improvement without sufficient
    evidence yet;
-   `documentation_drift`: canonical sources disagree;
-   `cleanup`: non-semantic maintainability improvement;
-   `rejected`: falsification/review indicates no change is justified.

Do not silently turn speculative review suggestions into implementation
tasks.

### 3.4 Smallest useful automation

Automate repeated objective decisions. Do not encode subjective research
judgement merely to increase the number of deterministic checks.

## 4. Staged AI roles

The roles below are logical stages. They do not require different model
providers or a multi-agent framework. Fresh contexts/prompts are
sufficient.

### 4.1 Scout

Purpose: maximise useful discovery.

The Scout is read-only. It may inspect the repository, history,
evidence, documentation, and---when the task calls for it---external
literature.

For each candidate finding, return:

-   concise title;
-   category;
-   affected canonical owner(s);
-   evidence already observed;
-   relevant invariant/claim;
-   why it matters;
-   proposed falsification route;
-   confidence;
-   likely scope;
-   whether external research is needed.

The Scout must not implement findings.

Prefer differential review over repeatedly reviewing the whole
repository. Use: - per-change review for normal work; -
subsystem/milestone review for SLED-V, ITES, planning, evaluation,
etc.; - occasional whole-repository audits.

### 4.2 Skeptic

Purpose: try to make each Scout finding disappear.

For each candidate: - inspect the alleged authoritative sources; - look
for an existing test/check/specification that resolves it; - try to
construct a minimal reproducer; - distinguish actual semantic failure
from documentation ambiguity; - search for rejected alternatives/ADRs; -
identify hidden assumptions in the Scout's reasoning; - downgrade
unsupported findings.

The Skeptic should favour precision over recall.

A finding that survives becomes a candidate for specification. A finding
that cannot be deterministically falsified may still proceed as a
research/design hypothesis, but must be labelled accordingly.

### 4.3 Researcher

Activate when a finding affects: - novelty; - threat model; - security
semantics; - evaluation methodology; - formal methods; - comparison with
another defence; - planning; - provenance/IFC/access-control theory; -
empirical benchmark design.

The Researcher should search adversarially, not merely for supportive
papers.

For a proposed contribution, explicitly ask:

> Assume this is not novel. What is the strongest prior work that
> already implements, formalises, proves, or evaluates it?

Record: - primary source; - bibliographic identity; - relevant claim; -
closest overlap with Conflux; - material difference; - whether the
difference is implemented, proposed, or merely rhetorical; -
implications for the Conflux claim; - evidence/experiment needed to
distinguish the work.

### 4.4 Implementer

The Implementer receives: - accepted finding; - evidence/reproducer; -
decision-complete specification; - affected invariants; - accepted
scope/non-goals; - validation expectations; - commit plan.

It should not reopen the research question unless implementation exposes
a contradiction. If it does, stop and return to specification/human
review.

Implement the smallest coherent change.

### 4.5 Auditor

Use a fresh context where practical.

The Auditor receives: - accepted specification; - final diff; - relevant
tests/evidence; - validation output.

Its objective is to reject the change if possible.

Ask: - Did the implementation actually satisfy the specification? - Did
authority broaden? - Was provenance lost? - Did a fail-closed case
become permissive? - Can tests pass despite a plausible defect? - Did
benchmark-specific behaviour enter trusted code? - Did an assumption
become stronger without documentation? - Did a generated result get
presented as stronger evidence than it is? - Is there a simpler
counterexample? - Did documentation or manuscript claims become stale?

Do not give the Auditor the Implementer's chain of reasoning; minimise
anchoring on the implementation rationale.

## 5. Human gates

AI autonomy should be high in search and implementation but limited at
normative/research decisions.

Require human approval before: - accepting a new/changed security
invariant; - broadening authority; - weakening fail-closed behaviour; -
activating delegation; - changing threat-model assumptions; - changing a
publication novelty claim; - interpreting ambiguous literature as
establishing novelty; - accepting a benchmark metric as measuring a
security guarantee; - introducing a substantial new abstraction or
subsystem solely from an AI review.

Routine implementation of an already accepted specification may proceed
without another design discussion.

## 6. Finding/evidence format

Prefer a small structured format that can be validated.

Suggested conceptual schema:

``` yaml
id: review-...
title: ...
category: confirmed_defect | research_gap | design_hypothesis | documentation_drift | cleanup | rejected
scope:
  - ...
canonical_owners:
  - ...
invariants:
  - ...
claim_ids:
  - ...
evidence:
  type: test | solver | sled | mutation | schema | diff | documentation | literature | benchmark | none
  location: ...
falsification:
  method: ...
  result: confirmed | refuted | inconclusive
research_required: true | false
confidence: high | medium | low
human_decision: accepted | rejected | deferred | pending
```

Do not create a second durable task tracker. If the repository already
has an accepted task registry representation suitable for this
information, integrate or link findings there. Otherwise keep transient
review output outside canonical programme state and only persist
accepted work.

## 7. Change-impact manifest

For non-trivial accepted work, require a compact impact declaration
before implementation:

``` text
Task:
Research question affected:
Security invariants affected:
Canonical source files:
Expected implementation files:
Expected tests:
Expected evidence:
Claims potentially affected:
Literature potentially affected:
Threat-model assumptions affected:
Explicit non-changes:
Commit plan:
```

The purpose is not paperwork; it makes omissions mechanically
discoverable.

Add audit rules only where the relationship is objective and stable.
Candidate examples:

-   changes to security-kernel packages require an explicit
    security-impact declaration;
-   changes to verification semantics require relevant verification
    tests/docs to be considered;
-   changes to evidence schemas require regeneration/schema tests;
-   changes to manuscript numerical claims require retained evidence
    references;
-   security semantics cannot be changed solely by editing descriptive
    documentation.

Avoid brittle rules based merely on filename matching if semantic
ownership cannot be inferred reliably.

## 8. Negative controls and mutation testing

Expand the existing negative-control philosophy.

For each major security property, maintain deliberately defective
implementations/models where practical. Candidate defect families:

-   requester-only authority;
-   permission union instead of intersection;
-   lost nested provenance;
-   provenance removed after summarisation;
-   consent treated as authority;
-   author set treated as reader ACL;
-   missing authority-bearing argument provenance;
-   stale policy/certificate accepted;
-   sibling branch influence leakage;
-   expired delegation accepted;
-   delegation reused;
-   revocation ignored;
-   sensitive value copied into an audience-visible error;
-   plan remains executable after permission revocation;
-   benchmark oracle leaks into defence behaviour.

The acceptance target should increasingly be:

> Correct implementation passes, and representative plausible incorrect
> implementations fail.

Do not add mutants merely to increase a mutation score. Each retained
mutant should correspond to a meaningful threat-model or implementation
mistake.

## 9. Commit guidance to add to `AGENTS.md`

`AGENTS.md` currently points to `WORKFLOW.md` and
`docs/AI_AGENT_GUIDE.md`, while the detailed commit convention lives in
the AI Agent Guide. Keep that single-source structure, but add a concise
high-salience commit policy to `AGENTS.md` so coding agents see it
without following another link.

The final wording should be adapted to current repository conventions,
but it should encode these requirements:

### Proposed `AGENTS.md` commit rules

-   Before editing a multi-file or non-trivial task, formulate an atomic
    commit plan.
-   One commit should represent one coherent concern that can be
    understood and reverted independently.
-   Each implementation commit must pass the checks appropriate to that
    commit independently; do not rely on a later commit to repair an
    earlier broken state.
-   Separate semantic implementation, refactoring, documentation-only
    changes, and generated experimental/evidence artifacts when they are
    independently meaningful.
-   In particular, do not commit generated evidence in the same commit
    as the implementation that generates it; generate and retain
    evidence only after the generator/implementation commit exists.
-   Do not mix opportunistic unrelated cleanup into a research/security
    change. Record it separately.
-   Review the staged diff before every commit for authority broadening,
    provenance loss, hidden trust assumptions, benchmark shortcuts,
    secrets, accidental generated files, and stale canonical
    documentation.
-   Use the repository commit message convention and always state
    `Security impact: ...` or `Security impact: none`.
-   For security-sensitive changes, the security-impact line should name
    the invariant or boundary affected rather than merely saying
    "tested".
-   Do not claim stronger scientific evidence in a commit message than
    the retained artifacts support.
-   Do not rewrite or squash away an implementation commit that is
    already referenced by retained evidence unless the evidence is
    intentionally invalidated/regenerated according to repository
    policy.
-   Do not commit or push when the user/current orchestration explicitly
    forbids it. If commit authority is ambiguous, prepare the atomic
    commit plan and staged changes, then report the proposed commits
    instead of assuming permission.
-   Before the final commit/handoff, run `python scripts/validate.py`
    unless the environment prevents it; report unavailable checks
    explicitly rather than silently skipping them.

Keep `docs/AI_AGENT_GUIDE.md` as the detailed owner. Update it if
necessary so the two documents are consistent, and ensure `WORKFLOW.md`
continues to point to the canonical detailed workflow rather than
duplicating it.

### Commit shape

Continue the existing format:

``` text
<one-line summary>

Security impact: <specific impact or "none">

<optional rationale/evidence detail>
```

Examples:

``` text
fix(ites): preserve argument provenance during binding

Security impact: preserves Principal Context completeness for authority-bearing arguments

Adds a regression test and requester-only negative control.
```

``` text
refactor(verification): isolate IR rule canonicalisation

Security impact: none

No transition semantics or property interpretation changed.
```

``` text
evidence(sled): retain COI comparison run

Security impact: none

Generated from implementation commit <hash>; records bounded evidence only.
```

Do not require Conventional Commits unless the repository explicitly
decides to adopt them; the current security-impact convention is more
important than introducing another naming scheme.

## 10. Literature landscape workflow

### 10.1 Goal

Replace episodic prose-only literature searches with a living, auditable
corpus.

The corpus should support: - deduplication; - primary-source
verification; - search provenance; - classification; - claim-to-paper
relationships; - forward/backward snowballing status; - manuscript
citation checks; - stale-search detection.

### 10.2 Literature lanes

At minimum maintain coverage of:

1.  prompt injection and LLM agent security;
2.  system-level agent defences;
3.  information-flow control;
4.  integrity models including Biba/LOMAC/endorsement;
5.  provenance/taint/dependency tracking;
6.  RBAC/ABAC/capability systems;
7.  delegation and authority transfer;
8.  declassification/confidentiality;
9.  causal provenance/attribution;
10. model checking;
11. symbolic execution/abstract interpretation;
12. runtime verification/reference monitors;
13. controller synthesis and planning;
14. security automata;
15. hyperproperties/noninterference;
16. persistent-memory security;
17. multi-agent security/authority;
18. agent-security benchmarks;
19. agent protocols/tool ecosystems;
20. AI-assisted software/research methodology where it informs the
    project workflow.

### 10.3 Search protocol

For each lane: 1. define keyword/semantic searches; 2. identify seminal
works; 3. identify current/recent works; 4. perform backward citation
traversal from closest papers; 5. perform forward citation traversal
from seminal and closest papers; 6. search authors/research groups
responsible for closest systems; 7. search relevant venues; 8. search
explicitly for work contradicting Conflux novelty/assumptions; 9. record
date and coverage status.

Do not infer completeness from a large paper count.

### 10.4 Corpus structure

Prefer a machine-readable canonical corpus (JSONL/JSON/CSV according to
repository conventions) plus generated human-readable views.

Each entry should support at least:

-   stable internal ID;
-   title;
-   authors;
-   year/date;
-   venue;
-   DOI/arXiv/primary URL;
-   primary-source verification status;
-   literature lanes;
-   Conflux concepts affected;
-   concise contribution;
-   assumptions/threat model;
-   formal guarantee type;
-   evaluation type;
-   closest relationship to Conflux;
-   limitations relevant to Conflux;
-   backward/forward snowball status;
-   last checked date;
-   manuscript citation status.

Do not automatically copy AI summaries into publication prose without
primary-source verification.

### 10.5 Claim-to-literature map

For each important research claim, record:

``` text
Claim:
Conflux component:
Closest prior work:
Strongest novelty threat:
Supporting prior work:
Material difference:
Is the difference implemented?
Evidence distinguishing Conflux:
Remaining uncertainty:
Last adversarial search:
```

The Researcher should try to destroy the novelty claim before
strengthening it.

Examples of claims requiring this treatment: - Principal Context
contribution boundaries; - pointwise argument-sensitive authority; -
visibility/confidentiality extension; - delegation semantics; - SLED-V
verification contribution; - defence-independent verification; -
Principal-Context-specific reductions; - comparative formal
verification; - secure/controller-synthesis planning; -
attribution/information-exposure metrics.

### 10.6 Deterministic literature checks

Add deterministic checks only for process facts, for example:

-   every manuscript citation resolves to a corpus entry;
-   every "closest prior work" claim has a primary-source record;
-   duplicate DOI/arXiv IDs are rejected;
-   required bibliographic fields are present;
-   novelty-critical entries record a last-checked date;
-   search lanes record their last search/snowball status;
-   generated bibliography/view files reproduce deterministically.

Do **not** make a checker assert that a contribution is novel.

## 11. Repository understanding workflow for the human researcher

The workflow should optimise not only code correctness but also the
researcher's ability to explain the system.

For every substantial accepted change, produce or surface a concise
learning packet:

-   What changed?
-   Why does it exist?
-   Which invariant/claim does it affect?
-   Where is the authoritative implementation?
-   What is the execution/data flow?
-   What would fail if the change were removed?
-   Which test/evidence demonstrates that?
-   What assumptions remain?
-   What is still unresolved?

Avoid creating a permanent new document per change. Prefer generating
this from the task/spec/diff at hand or attaching it to an existing
task/change record.

### Examiner mode

Document an optional recurring review procedure:

1.  start a fresh AI context;
2.  give it the public/current repository, not prior explanatory chat;
3.  ask it to act as a project examiner;
4.  have it ask one question at a time about security semantics,
    implementation, formal verification, evaluation, literature,
    limitations, and novelty;
5.  the researcher answers without AI assistance;
6.  the examiner checks the answer against the repository and primary
    sources;
7.  misunderstandings become learning targets; repository-unverifiable
    correct answers become documentation discoverability candidates.

This should remain a human workflow, not a CI requirement.

## 12. Review scopes

Define three review modes.

### Change review

Default. Inspect: - diff; - specification; - direct/transitive semantic
dependencies; - relevant tests/evidence; - affected claims/docs.

Questions: - What did this intend to change? - What else changed? -
Which invariant became weaker? - Which assumption became stronger? -
Could tests pass despite a defect? - Which claim/document is stale?

### Subsystem review

Run at milestones for ITES, SLED-V, planning, policy adapters,
evaluation, etc.

Focus on: - architecture; - duplicated semantics; - TCB; - invariant
coverage; - negative controls; - evidence gaps; - literature comparison.

### Global review

Occasional, not routine.

Use it to find: - cross-subsystem drift; - stale canonical ownership; -
abandoned scaffolding; - contradictory claims; - systemic
reproducibility problems; - missing research directions.

Avoid asking for full-repository reviews after every small change.

## 13. Workflow metrics

Add lightweight measurement so the process can be evaluated rather than
assumed effective.

For significant review/implementation tasks, optionally record:

-   findings proposed;
-   findings confirmed;
-   findings rejected;
-   findings deferred;
-   defects with deterministic reproducers;
-   tests/negative controls added;
-   mutants killed;
-   validation failures during implementation;
-   defects found by post-implementation Auditor;
-   number of implementation iterations;
-   later regressions attributable to the change.

Do not turn this into a burdensome mandatory log for trivial changes.

After a useful sample of tasks, analyse: - false-positive rate of AI
review; - incremental value of the Skeptic; - incremental value of the
Auditor; - whether specification-first work reduces rework; - which
checkers catch real defects; - whether whole-repo reviews justify their
cost.

## 14. Deterministic checker expansion strategy

Before adding a checker, require:

1.  a stable property with a reasonably objective oracle;
2.  a demonstrated or plausible failure mode;
3.  low risk of blocking legitimate research iteration;
4.  a clear canonical owner;
5.  a test of the checker itself where practical.

Prioritise:

-   architectural dependency constraints;
-   evidence/claim consistency;
-   schema/version drift;
-   deterministic regeneration;
-   negative controls/mutations;
-   model/IR conformance;
-   stale policy/certificate cases;
-   literature corpus integrity;
-   manuscript-evidence references.

Avoid: - subjective architecture-style scoring; - automated novelty
verdicts; - forcing every research hypothesis to have a test before
exploration; - enormous brittle audits that simply duplicate prose
rules.

## 15. Suggested implementation sequence

### Phase 1 --- guidance and commit discipline

1.  Update `AGENTS.md` with concise commit guidance from Section 9.
2.  Update `docs/AI_AGENT_GUIDE.md` with the staged workflow and
    authority distinction.
3.  Keep `WORKFLOW.md` as a pointer unless a small wording update is
    needed.
4.  Add/adjust repository-audit tests so these canonical files cannot
    drift in obvious ways.
5.  Validate.

This should be the first atomic implementation commit.

### Phase 2 --- review/falsification templates

1.  Add the smallest reusable template/schema for Scout findings and
    change-impact manifests.
2.  Integrate with existing task/specification ownership rather than
    creating a second tracker.
3.  Add validation/schema checks.
4.  Add examples only if they materially improve agent compliance.

Separate this from Phase 1 if independently revertible.

### Phase 3 --- negative-control programme

1.  Inventory existing mutants/seeded defects.
2.  Map them to security invariants.
3.  Identify high-value missing defect families.
4.  Add a small number of meaningful mutants.
5.  Ensure each is killed by a specific checker/test.
6.  Document what mutation evidence does and does not establish.

### Phase 4 --- literature corpus

1.  Inspect existing `docs/research`, reports, bibliography, and
    literature artifacts.
2.  Design a canonical corpus schema that does not duplicate
    manuscript/reference ownership.
3.  Import existing verified literature.
4.  Add search-protocol metadata.
5.  Add claim-to-literature relationships.
6.  Add integrity checks.
7.  Generate human-readable views where useful.
8.  Do not silently strengthen novelty claims during migration.

### Phase 5 --- understanding/examiner workflow

1.  Add a short documented human procedure, likely under existing
    development/research guidance.
2.  Provide reusable prompts for learning packet/examiner mode if
    appropriate.
3.  Do not add CI or persistent artifacts unless they have a clear
    owner.

### Phase 6 --- workflow measurement

Only after the new process has been used enough to justify
measurement: 1. define minimal metrics; 2. avoid logging private model
reasoning; 3. retain only useful aggregate/task-level outcomes; 4.
review whether the extra process improves defect yield and rework.

## 16. Acceptance criteria

The implementation is complete when:

-   `AGENTS.md` exposes concise, unambiguous atomic commit guidance;
-   detailed workflow ownership remains in `docs/AI_AGENT_GUIDE.md`;
-   the workflow explicitly separates discovery, falsification,
    research, implementation, verification, and adversarial review;
-   normative/descriptive/scientific authority are distinguished without
    contradicting current trust rules;
-   speculative findings cannot silently become "confirmed defects";
-   non-trivial changes have a lightweight impact/commit plan;
-   generated evidence remains separate from generator implementation
    commits;
-   negative controls are treated as a first-class reliability
    mechanism;
-   literature review has a proposed/implemented machine-readable corpus
    and adversarial search protocol;
-   deterministic literature checks validate provenance/process, not
    novelty;
-   no parallel roadmap/status/claim ledger is introduced;
-   all new schemas/scripts/tests are covered by repository validation;
-   `python scripts/validate.py` passes, or unavailable checks are
    explicitly reported;
-   documentation states what the workflow guarantees and what remains
    human judgement.

## 17. Non-goals

Do not:

-   build a complex autonomous multi-agent orchestration framework
    merely to represent the logical roles;
-   require a separate model/provider for every role;
-   create a second issue tracker;
-   create a second claim ledger;
-   create a second status page;
-   encode novelty/significance as deterministic truth;
-   force formal verification for ordinary refactors;
-   require full-repository review for each change;
-   store model chain-of-thought;
-   allow AI-generated literature summaries to become publication claims
    without primary-source checking;
-   use passing tests as justification for changing the normative
    security model;
-   increase workflow bureaucracy without a measurable reliability
    benefit.

## 18. Recommended AI-coder execution prompt

Use this report as an implementation specification. Before editing:

1.  inspect the current repository and identify the canonical owners
    affected by each phase;
2.  report any conflicts between this proposal and current accepted
    specifications/ADRs;
3.  produce an atomic commit plan, including expected files and
    validation for each commit;
4.  implement the smallest coherent subset in order, beginning with
    guidance/commit discipline;
5.  do not invent a parallel status/task/claim system;
6.  preserve all existing Conflux security invariants and fail-closed
    defaults;
7.  add deterministic checks only where the oracle is objective;
8.  keep literature novelty conclusions human-reviewed;
9.  run focused tests during implementation and
    `python scripts/validate.py` before each independently complete
    implementation commit where feasible;
10. use a fresh adversarial review pass before final handoff;
11. report changed files, validation evidence, unresolved hypotheses,
    and proposed commits.

If implementation exposes a normative ambiguity, a potential authority
broadening, or a conflict with an accepted ADR/specification, stop that
portion and request a human decision rather than choosing a convenient
interpretation.

## 19. Expected outcome

After implementation, Conflux's AI-assisted workflow should have the
same basic shape as its security research:

-   nondeterministic/creative components propose possibilities;
-   trusted boundaries restrict what becomes an effect;
-   evidence is explicit and classified by strength;
-   known failure modes have negative controls;
-   durable claims are traceable to reproducible evidence;
-   human judgement remains at the boundaries that cannot be reduced to
    a trustworthy deterministic oracle.

The intended result is not less AI involvement. It is greater AI
autonomy in the stages where exploration is useful, combined with
stronger barriers against plausible-but-unsupported changes becoming
code, evidence, or research claims.
