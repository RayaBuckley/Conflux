# Conflux Human-Reviewable Evidence and Visualisation

**Status:** Proposed implementation specification  
**Target:** Current `main` branch  
**Primary objective:** Make correctness claims inspectable by humans rather than dependent on AI-generated prose  
**Priority:** High — research reliability and AI-assisted development workflow

## 1. Problem

Conflux already has strong machine-oriented validation:

- deterministic offline execution;
- schema-checked JSON results;
- native bounded SLED;
- solver-facing verification;
- unit/security/integration/reproducibility tests;
- strict typing and linting;
- repository audits;
- versioned output schemas.

However, most of this evidence is optimised for machines rather than human reviewers.

A typical AI-assisted workflow can therefore end with:

> Implemented X. Tests pass. Verification succeeds.

That is insufficient for a security-sensitive research project.

The reviewer should be able to inspect:

- what executions occurred;
- which Principals influenced them;
- how provenance propagated;
- which security checks were evaluated;
- why an action was allowed or blocked;
- what state space SLED explored;
- what counterexample a verifier found;
- what a reduction removed;
- how a plan changes authority and information exposure;
- whether a code change altered any of these behaviours.

The desired workflow is:

```text
implementation
      │
      ▼
machine validation
      │
      ▼
authoritative structured evidence
      │
      ├──────────────┐
      ▼              ▼
machine checking   deterministic
                  visualisation
                       │
                       ▼
                  human review
                       │
                       ▼
                 AI explanation
```

The AI explanation is the final layer.

It must never be the primary evidence that the implementation works.

---

# 2. Core design principle

Adopt the following repository-wide rule:

> Machine-checkable structured evidence is authoritative. Human-readable diagrams and reports are deterministic projections of that evidence. AI-generated explanations may explain evidence but must never replace it.

Consequences:

1. Visualisation code must not independently reconstruct security semantics.
2. A diagram must be reproducible from a stored structured result.
3. Every visual element should map to a structured evidence object.
4. Visualisation failure must never affect security decisions.
5. Visualisation must not silently omit security-relevant information.
6. `SAFE`, `UNSAFE`, `UNKNOWN`, `BLOCKED`, `ALLOWED`, and `UNAVAILABLE` must remain visibly distinct.
7. Bounded evidence must visibly state its bounds.
8. Generated evidence must identify the code/configuration that generated it.

---

# 3. Scope

Implement visual evidence for four principal subsystems.

## 3.1 ITES

Visualise:

- execution hierarchy;
- Principal Context;
- provenance;
- proposed actions;
- action authorisation;
- argument authorisation;
- read decisions;
- visibility decisions;
- consent decisions;
- delegation decisions where applicable;
- final allow/block decision;
- decision certificates;
- nested executions.

## 3.2 Native SLED

Visualise:

- explored states;
- transitions;
- revisited/canonical states;
- terminal states;
- violations;
- shortest counterexamples;
- bounds;
- exploration statistics.

## 3.3 SLED-V / verification

Visualise:

- VerificationIR;
- state variables;
- transition dependencies;
- safety invariants;
- cone-of-influence reductions;
- solver verdicts;
- counterexamples;
- assumptions;
- bounds;
- witness lifting.

## 3.4 Planning

Visualise:

- plan graph;
- operation nodes;
- success transitions;
- error transitions;
- observations;
- Principal Context evolution;
- required permissions;
- required reads;
- sensitive information exposure;
- delegation/approval transitions;
- irreversible effects;
- execution state.

---

# 4. Non-goals

Do not initially implement:

- a React application;
- a web server;
- persistent database-backed observability;
- live distributed tracing infrastructure;
- AI-generated diagrams;
- automatic natural-language interpretation of traces;
- arbitrary graph querying;
- a replacement for existing JSON evidence;
- visualisation-specific security semantics;
- a general-purpose observability platform.

The first implementation should be static, deterministic and offline.

Preferred outputs:

```text
SVG
HTML
JSON
```

PNG may optionally be generated for convenience, but SVG is preferred because it is inspectable, scalable and diffable.

---

# 5. Proposed package architecture

Add:

```text
src/conflux/visualisation/
    __init__.py

    model.py
    normalise.py
    renderer.py
    html.py
    diff.py

    ites.py
    provenance.py
    sled.py
    verification.py
    planning.py

    graph/
        __init__.py
        model.py
        graphviz.py
        layout.py

    templates/
        report.html
```

Do not make this package part of the security kernel.

Dependency direction should be:

```text
domain / ITES / evaluation / verification / planning
                     │
                     ▼
              evidence schemas
                     │
                     ▼
              visualisation
```

Never:

```text
ITES → visualisation
policy → visualisation
domain → visualisation
```

Security-critical code must not depend on rendering.

---

# 6. Intermediate visualisation model

Do not make each renderer consume arbitrary subsystem objects directly.

Introduce a small subsystem-independent graph representation.

Example conceptual types:

```python
@dataclass(frozen=True)
class VisualNode:
    id: str
    kind: NodeKind
    label: str
    fields: tuple[VisualField, ...]
    status: VisualStatus | None
    source_ref: EvidenceReference


@dataclass(frozen=True)
class VisualEdge:
    source: str
    target: str
    kind: EdgeKind
    label: str | None
    source_ref: EvidenceReference | None


@dataclass(frozen=True)
class VisualGraph:
    graph_id: str
    title: str
    nodes: tuple[VisualNode, ...]
    edges: tuple[VisualEdge, ...]
    metadata: VisualMetadata
```

`EvidenceReference` must point back to the authoritative evidence.

For example:

```text
result.json#/executions/3/actions/2
```

or an equivalent stable identifier.

The visual graph must never become the canonical security record.

---

# 7. Stable visual statuses

Define a common status vocabulary.

At minimum:

```text
ALLOWED
BLOCKED
SAFE
UNSAFE
UNKNOWN
UNAVAILABLE
INCOMPLETE
PRUNED
REVISITED
ACTIVE
SUCCESS
FAILED
NOT_APPLICABLE
```

Do not encode status exclusively through colour.

Every status must have:

- text;
- icon/shape distinction where practical;
- optional colour.

This improves accessibility and prevents ambiguous screenshots.

---

# 8. ITES execution visualisation

## 8.1 Required view

Add an ITES execution graph.

Example:

```text
Artifact A
authors={Alice}
      │
      ▼
┌────────────────────┐
│ Execution E0       │
│ PC={Alice}         │
└─────────┬──────────┘
          │ reads
          ▼
Artifact B
authors={Bob}
          │
          ▼
┌────────────────────┐
│ Execution E1       │
│ PC={Alice,Bob}     │
└─────────┬──────────┘
          │ proposes
          ▼
┌──────────────────────────────┐
│ send_email                   │
│                              │
│ Action       ALLOW           │
│ Arguments    ALLOW           │
│ Read         ALLOW           │
│ Visibility   BLOCK           │
│ Consent      ALLOW           │
│                              │
│ FINAL        BLOCK           │
└──────────────────────────────┘
```

## 8.2 Execution nodes

Each execution node should expose:

- execution ID;
- parent execution ID;
- depth;
- Principal Context;
- input artifact IDs;
- model/adapter identifier where relevant;
- proposal count;
- result status.

Do not put full content into the graph by default.

Sensitive values should use:

- identifiers;
- hashes;
- safe labels;
- provenance metadata.

## 8.3 Action nodes

Each proposed effectful/observable action should display independent decision dimensions.

Required fields:

```text
operation
action decision
argument decision(s)
read decision(s)
visibility decision
consent decision
delegation decision if applicable
final decision
reason code
certificate ID
```

Do not collapse:

```text
Action: BLOCKED
```

when the underlying evidence can instead show:

```text
Action authority       ALLOW
Argument authority     ALLOW
Read policy            ALLOW
Visibility             DENY
Consent                ALLOW
Final                   BLOCK
```

The purpose is diagnosis.

## 8.4 Principal Context delta

Every child execution should optionally show:

```text
PC parent: {Alice}
Added:     {Bob}
PC child:  {Alice, Bob}
```

This is important for detecting provenance propagation errors.

---

# 9. Provenance graph

Implement a dedicated provenance view.

Use node categories:

```text
Principal
Artifact
Execution
Action
```

Use explicit edge types:

```text
AUTHORED
DERIVED_FROM
INPUT_TO
OUTPUT_OF
INFLUENCES
PROPOSED
EXECUTED
OBSERVABLE_TO
```

Example:

```text
Alice ─AUTHORED─▶ A
                   │
                INPUT_TO
                   ▼
                  E0
                   │
               OUTPUT_OF
                   ▼
                   B
                   │
                INPUT_TO
                   ▼
                  E1 ◀─INPUT_TO─ C ◀─AUTHORED─ Bob
                   │
                   ▼
              PC={Alice,Bob}
```

## 9.1 Review invariants

The renderer should optionally annotate suspicious structural situations.

Examples:

```text
derived artifact has empty provenance
child Principal Context omits parent Principal
artifact contributor absent from resulting context
unknown Principal referenced
missing source artifact
```

Important:

These should be structural diagnostics.

Do not duplicate security-policy decisions inside the renderer.

If these conditions are security invariants, the authoritative validation should exist outside the renderer and the renderer should display its result.

---

# 10. Native SLED state-space visualisation

## 10.1 Small state spaces

For state spaces below a configurable threshold, render the complete graph.

Default threshold:

```text
250 states
```

Make this configurable.

Node fields:

```text
state ID
depth
Principal Context summary
environment-state summary
pending work
terminal status
violation status
```

Edge fields:

```text
transition ID
proposal/action
outcome
```

Distinguish:

- initial state;
- ordinary state;
- safe terminal state;
- violating state;
- incomplete/boundary state;
- revisited canonical state.

## 10.2 Large state spaces

Never attempt to render millions of nodes.

For larger runs, generate:

```text
summary.svg
counterexample.svg      if UNSAFE
depth_histogram.svg
transition_summary.svg
```

The summary should show:

```text
reachable states
explored transitions
maximum depth
revisited states
terminal states
violations
incomplete/bounded states
runtime
```

Example:

```text
SLED bounded exploration

States                 18,421
Transitions            73,992
Revisited              41,202
Safe terminals          2,194
Violations                  0
Bound hits                214
Maximum depth               8

Verdict:
NO VIOLATION WITHIN MODEL/BOUNDS
```

Do not label this simply:

```text
SAFE
```

unless the underlying SLED result schema already defines that exact meaning.

The visual wording must preserve the semantic strength of the authoritative verdict.

---

# 11. SLED shortest-counterexample view

If native SLED finds a violation, automatically generate a minimal counterexample diagram.

Example:

```text
S0
PC={Alice}
 │
 │ observe BobArtifact
 ▼
S1
PC={Alice,Bob}
 │
 │ propose DeletePrivateFile
 ▼
S2
 │
 │ incorrect allow
 ▼
S3
UNAUTHORISED EFFECT
```

Each transition should include:

- transition ID;
- action/proposal;
- security-relevant state delta;
- decision/certificate reference where available.

The graph must link back to the raw counterexample evidence.

---

# 12. VerificationIR visualisation

Add:

```text
conflux verify visualise ...
```

or integrate with the general visualisation command described later.

Generate a dependency graph containing:

```text
StateVariable
TransitionRule
SafetyInvariant
Assumption
```

Example:

```text
principal_context ───────┐
                         ▼
permission_state ───▶ execute_action ───▶ action_executed
                                               │
                                               ▼
                                     NoPrivilegeEscalation
```

The graph should make it possible to inspect why a variable affects a property.

---

# 13. Cone-of-influence view

This should be a first-class output because Conflux already has property-scoped COI reduction.

For each selected invariant display:

```text
Original variables:      42
Retained variables:      11
Removed variables:       31

Original transitions:    27
Retained transitions:     9
```

Generate a dependency graph where retained components are visible and omitted components are summarised.

Also include:

```text
selected invariant
reduction algorithm/version
assumptions introduced
stable rule IDs
witness-lifting information
```

The visual must make it impossible to confuse:

```text
SAFE on reduced model
```

with:

```text
SAFE on original model
```

unless the evidence establishes the preservation relation required for that claim.

---

# 14. Solver counterexample visualisation

For:

```text
UNSAFE
```

from Z3/nuXmv/another backend, render the witness.

Prefer state-delta rendering.

Instead of:

```text
State 0:
x=False
y=False
z=False

State 1:
x=False
y=True
z=False
```

display:

```text
S0
 │
 │ transition: observe_untrusted_input
 │ y: false → true
 ▼
S1
```

Unchanged variables should be collapsed by default.

Provide an expandable full-state table in HTML.

---

# 15. Solver verdict card

Every formal verification visual should prominently display:

```text
Property
Backend
Verdict
Bound, if applicable
Assumptions
Model hash
Evidence schema version
Commit SHA
```

Example:

```text
Property: NoPrivilegeEscalation
Backend: Z3 BMC
Verdict: NO COUNTEREXAMPLE
Bound: 12 transitions

THIS IS A BOUNDED RESULT
```

versus:

```text
Property: NoPrivilegeEscalation
Backend: PDR
Verdict: SAFE
Scope: encoded transition system

Inductive invariant: available
```

versus:

```text
Property: NoPrivilegeEscalation
Backend: nuXmv
Verdict: UNKNOWN

Reason:
backend unavailable
```

These must be visually distinct.

---

# 16. Planning visualisation

Render plans as directed graphs.

Node categories:

```text
operation
observation
decision
approval request
delegation request
safe terminal
goal
failure
```

Edge categories:

```text
success
error
provider outcome
approval
delegation
retry
```

Example:

```text
Read invoice
     │
 success
     ▼
Extract destination
     │
     ▼
Send payment
 ┌───┴────────────┐
 │                │
success      PermissionDenied
 │                │
 ▼                ▼
Goal       RequestApproval
```

---

# 17. Authority overlay for plans

Each plan node should optionally display:

```text
Principal Context
required action permission
authority-bearing arguments
required reads
observers
consent requirements
delegation requirements
```

Calculate visual metrics from authoritative evidence:

```text
Principal Context size
new Principals introduced
sensitive artifacts observed
effectful operations
irreversible operations
approval transitions
delegation transitions
```

Do not call these metrics "risk" unless a formally defined risk metric exists.

Prefer descriptive names such as:

```text
authority footprint
observation footprint
effect footprint
```

---

# 18. Information-observation timeline

Add a compact plan/execution timeline showing when information enters Principal Context.

Example:

```text
Step   Observation          PC
0      user prompt          {Alice}
1      project index        {Alice}
2      Bob document         {Alice,Bob}
3      public metadata      {Alice,Bob}
4      action               {Alice,Bob}
```

This can reveal unnecessary early observation.

It is particularly useful for evaluating planning optimisation.

---

# 19. Evidence report

Implement a static HTML report.

Suggested output:

```text
research/output/runs/<run-id>/
    result.json

    evidence/
        index.html

        execution.svg
        provenance.svg

        sled/
            summary.svg
            state-space.svg
            counterexample.svg

        verification/
            ir.svg
            coi-NoPrivilegeEscalation.svg
            counterexample.svg

        planning/
            plan.svg
            authority.svg

        manifest.json
```

Not every run needs every artifact.

The manifest should explicitly record which views exist.

---

# 20. HTML report structure

The report should be static and self-contained where practical.

Suggested navigation:

```text
Overview
Execution
Security Decisions
Provenance
SLED
Verification
Planning
Raw Evidence
```

## Overview

Display:

```text
run ID
timestamp
commit SHA
dirty-tree status
command
scenario
result
schema versions
Python/package version
```

Then:

```text
Security
Utility
Verification
Warnings
```

Avoid an overall green "PASS" when some components are:

```text
UNKNOWN
INCOMPLETE
UNAVAILABLE
```

---

# 21. Raw evidence linkage

Every graph node should have an evidence reference.

In SVG:

- tooltip;
- element ID;
- source-reference metadata where feasible.

In HTML:

clicking a node should show:

```text
Node
Source object
Relevant structured fields
```

Example:

```text
Action: send_email
Evidence:
result.json#/executions/2/proposals/4
```

This makes diagrams auditable.

---

# 22. CLI design

Preferred general interface:

```text
conflux visualise <result.json>
```

Default:

```text
conflux visualise \
    research/output/runs/demo/result.json
```

Output:

```text
research/output/runs/demo/evidence/
```

Options:

```text
--format svg
--format html
--view execution
--view provenance
--view sled
--view verification
--view planning
--all
--output PATH
--max-nodes N
```

Also integrate visual output into:

```text
conflux report
```

Possible interface:

```text
conflux report result.json --visual
```

Do not make graph-generation dependencies mandatory for core Conflux execution unless they are lightweight and reliable.

If Graphviz is unavailable:

```text
visualisation status: UNAVAILABLE
reason: graphviz executable not found
```

Core execution must still succeed.

---

# 23. Determinism

Visual outputs must be reproducible.

Requirements:

- stable node ordering;
- stable edge ordering;
- stable identifiers;
- fixed layout options where practical;
- no timestamps inside SVG unless explicitly requested;
- no random IDs;
- canonical field ordering;
- canonical Principal ordering;
- canonical artifact ordering.

Add a test that renders the same evidence twice and verifies semantically identical output.

If Graphviz introduces non-semantic serialization differences, canonicalise SVG before comparison or compare a normalised representation.

---

# 24. Evidence schemas

Do not make the visualiser depend on undocumented Python object internals.

Prefer:

```text
existing schema-validated result
        │
        ▼
visualisation adapter
        │
        ▼
VisualGraph
```

If existing schemas lack required information, extend them explicitly.

Possible new schemas:

```text
visualisation-manifest.schema.json
visual-graph.schema.json
evidence-diff.schema.json
```

Only add schemas where they provide a real machine-checkable contract.

Avoid schema proliferation solely for rendering convenience.

---

# 25. Baseline-versus-candidate diffing

This is a high-value second-stage feature.

CLI:

```text
conflux visualise diff \
    baseline/result.json \
    candidate/result.json
```

Generate:

```text
diff.html
execution-diff.svg
provenance-diff.svg
verification-diff.svg
```

Compare semantic identifiers, not graph-layout coordinates.

Report:

```text
actions added
actions removed
decision changes
Principal Context changes
provenance changes
state-count changes
transition-count changes
solver-verdict changes
plan changes
```

Example:

```text
SECURITY-RELEVANT CHANGE

Action:
send_email

Before:
PC={Alice}
FINAL=ALLOW

After:
PC={Alice,Bob}
FINAL=BLOCK

Reason:
Bob introduced through artifact invoice-17
```

This should make reviewing AI-generated changes substantially easier.

---

# 26. Golden visual fixtures

Add a small curated fixture set.

Suggested scenarios:

```text
ites-simple-allow
ites-mixed-principal-block
ites-visibility-block
ites-consent-block
ites-argument-block
ites-nested-context
sled-safe-small
sled-counterexample
verification-safe
verification-unsafe
verification-unknown
coi-reduction
plan-success
plan-error-recovery
```

Do not commit visual output for every test.

Commit a deliberately small set of representative golden artifacts.

---

# 27. Testing strategy

## Unit tests

Test:

- evidence → VisualGraph conversion;
- stable node IDs;
- stable edge IDs;
- status mapping;
- Principal ordering;
- state delta calculation;
- provenance edge generation;
- evidence references.

## Structural tests

For every graph:

- every edge endpoint exists;
- every source reference resolves;
- every action has a final status;
- every displayed policy decision corresponds to evidence;
- no fabricated Principal exists;
- no fabricated transition exists.

## Determinism tests

Same evidence twice:

```text
same normalised VisualGraph
same semantic SVG
```

## Golden tests

Compare selected fixtures against expected graph representations.

Prefer testing normalised graph structures rather than huge raw SVG strings.

## Integration tests

Execute:

```text
conflux demo ...
conflux visualise result.json
```

and verify expected artifacts exist.

Repeat for:

```text
sled
verification
planning
```

---

# 28. Security requirements

Visualisation is an information-release surface.

Treat this seriously.

## 28.1 Sensitive contents

Default diagrams must not embed:

- raw document contents;
- secrets;
- credentials;
- full prompts;
- confidential payloads;
- private tool responses.

Use:

```text
artifact ID
safe label
content hash
classification
size
provenance
```

Full values should appear only under an explicit opt-in mode.

For example:

```text
--include-values
```

Document that this may create sensitive evidence.

## 28.2 HTML safety

Escape all untrusted labels.

Never insert raw:

```text
artifact name
tool output
model output
prompt
```

into HTML.

No untrusted HTML execution.

## 28.3 SVG safety

Treat SVG as potentially active content.

Do not insert unescaped user-controlled markup.

Prefer renderer APIs that escape labels.

Add security tests with hostile labels such as HTML/script-like strings.

---

# 29. Accessibility

Do not rely solely on colour.

Use:

```text
ALLOW       ✓ ALLOW
BLOCK       ✕ BLOCK
UNKNOWN     ? UNKNOWN
INCOMPLETE  … INCOMPLETE
```

or equivalent accessible text/shape semantics.

SVG should include useful titles/descriptions where practical.

HTML should remain usable without JavaScript.

---

# 30. Performance

Visualisation must not materially slow normal execution.

Rendering should happen after authoritative evidence generation.

For large SLED results:

```text
if states <= threshold:
    full graph
else:
    summary + witness + aggregates
```

Never accidentally create a multi-gigabyte SVG.

Set explicit limits for:

```text
nodes
edges
labels
counterexample length
```

If truncation occurs, state it visibly:

```text
VISUALISATION TRUNCATED
Showing 250 / 18,421 states
```

This is a rendering limitation, not a verification limitation.

---

# 31. AI-agent workflow changes

Update `AGENTS.md` and `docs/AI_AGENT_GUIDE.md`.

The current repository already instructs agents to prioritise security correctness, reproducibility and validation. The new requirement should extend that contract to human-reviewable evidence.

Add a rule approximately equivalent to:

> For changes affecting security semantics, evaluation, verification, planning, provenance, policy composition, or execution behaviour, passing tests alone is not sufficient evidence. Where a deterministic evidence scenario exists, generate or update human-reviewable evidence and report its location.

Require agents to distinguish:

```text
implemented
tested
verified
visually reviewed
```

These are not synonyms.

---

# 32. Required AI completion report

For substantial changes, require:

```text
Summary:
<what changed>

Validation:
<commands run>

Machine evidence:
<result files>

Human-reviewable evidence:
<visual files>

Expected semantic change:
<what should differ>

Observed semantic change:
<what actually differs>

Unexpected differences:
<none or list>

Verification limitations:
<bounds / UNKNOWN / unavailable backend / assumptions>
```

Example:

```text
Summary:
Fixed sibling Principal Context isolation.

Validation:
python scripts/validate.py

Machine evidence:
research/output/runs/branch-isolation/result.json

Human-reviewable evidence:
evidence/execution.svg
evidence/provenance.svg

Expected semantic change:
Sibling B must no longer inherit Bob from sibling A.

Observed:
Before: B PC={Alice,Bob}
After:  B PC={Alice}

Unexpected differences:
None.

Verification limitations:
Native SLED depth bound 8.
```

This is substantially more reviewable than:

```text
Fixed. Tests pass.
```

---

# 33. CI integration

After the local feature is stable, add CI evidence generation.

Do not generate every possible diagram.

Generate a small review pack from curated scenarios.

Example:

```text
CI
 │
 ├── validation
 │
 ├── deterministic scenarios
 │
 └── visual evidence pack
```

Upload as CI artifacts:

```text
conflux-review-evidence.zip
```

Contents:

```text
index.html
selected SVGs
result JSON
manifest
```

If a pull request changes security-relevant behaviour, reviewers can inspect the evidence pack.

---

# 34. Optional PR summary

A later enhancement may generate a Markdown summary suitable for a PR:

```text
## Conflux evidence

Validation: PASS

ITES scenarios:
12 unchanged
1 intentionally changed
0 unexpected

SLED:
states: 1,842 → 1,431
verdict unchanged

Verification:
NoPrivilegeEscalation: SAFE → SAFE
NoUnauthorisedRead: SAFE → SAFE

Visual evidence:
CI artifact: conflux-review-evidence
```

The summary must be generated from structured evidence.

Do not ask an LLM to produce the authoritative diff.

---

# 35. Implementation phases

## Phase 0 — inspect and specify

Before coding:

1. inventory existing result schemas;
2. inventory ITES trace/certificate structures;
3. inventory native SLED evidence;
4. inventory VerificationIR and result types;
5. inventory plan result types;
6. identify stable identifiers already available;
7. identify missing evidence required by diagrams.

Produce a short implementation note before changing schemas.

Do not redesign security-domain types merely to simplify rendering.

---

## Phase 1 — common graph model

Implement:

```text
visualisation/model.py
visualisation/graph/model.py
```

Add:

- nodes;
- edges;
- evidence references;
- statuses;
- deterministic ordering.

No Graphviz yet.

Test thoroughly.

---

## Phase 2 — ITES and provenance adapters

Implement:

```text
visualisation/ites.py
visualisation/provenance.py
```

Produce `VisualGraph`.

Add fixtures for:

- allow;
- authorisation block;
- argument block;
- read block;
- visibility block;
- consent block;
- nested Principal Context.

This phase provides the highest immediate review value.

---

## Phase 3 — Graphviz SVG

Implement:

```text
visualisation/graph/graphviz.py
```

Requirements:

- deterministic input ordering;
- safe label escaping;
- status text;
- source IDs;
- SVG output.

Keep the abstraction sufficiently generic that Mermaid or another renderer could later be added without changing evidence adapters.

---

## Phase 4 — native SLED

Implement:

```text
visualisation/sled.py
```

Support:

- full small-state graph;
- large-run summary;
- shortest counterexample;
- explicit bound information.

Do not change SLED semantics.

---

## Phase 5 — verification

Implement:

```text
visualisation/verification.py
```

Support:

- IR graph;
- invariant dependency;
- COI;
- solver witness;
- verdict card.

This phase should use existing stable transition IDs and reduction evidence wherever possible.

---

## Phase 6 — planning

Implement:

```text
visualisation/planning.py
```

Support:

- plan topology;
- success/error transitions;
- authority overlay;
- observation timeline.

---

## Phase 7 — static HTML report

Implement:

```text
visualisation/html.py
```

Combine existing views into one review page.

No frontend framework.

Use minimal static CSS and optional minimal vanilla JavaScript only where it materially improves navigation.

The report must remain useful with JavaScript disabled.

---

## Phase 8 — semantic diff

Implement:

```text
visualisation/diff.py
```

Do not diff SVG files.

Diff structured evidence.

Then visualise the semantic diff.

---

## Phase 9 — AI workflow and CI

Update:

```text
AGENTS.md
docs/AI_AGENT_GUIDE.md
docs/DEVELOPMENT.md or current equivalent
```

Add curated CI evidence generation.

---

# 36. Acceptance criteria

The project is complete when all of the following hold.

### ITES

Given a deterministic scenario, a reviewer can determine from the generated report:

- what was proposed;
- which Principals influenced it;
- what provenance produced that context;
- which policy dimension blocked or permitted it;
- what final decision occurred.

Without reading raw Python logs.

### SLED

Given a small scenario, a reviewer can inspect the reachable state graph.

Given an unsafe scenario, a reviewer can inspect the shortest counterexample.

Given a large scenario, the renderer produces a bounded summary rather than an unusable graph.

### Verification

A reviewer can determine:

- property;
- backend;
- verdict;
- assumptions;
- bounds;
- model identity;
- relevant variables;
- counterexample if present.

`UNKNOWN` cannot be visually mistaken for `SAFE`.

### Planning

A reviewer can inspect:

- plan topology;
- error branches;
- observations;
- authority changes;
- effectful actions.

### Provenance

A reviewer can visually trace:

```text
Principal → artifact → execution → derived artifact → action
```

### Reproducibility

Running the visualiser twice on identical evidence produces semantically identical output.

### Security

No raw sensitive value appears by default.

Untrusted strings cannot inject HTML/SVG content.

### Architecture

No security-critical package imports the visualisation package.

---

# 37. Definition of done for each implementation phase

Every phase must include:

1. implementation;
2. tests;
3. schema changes if necessary;
4. documentation;
5. one curated example;
6. full repository validation;
7. generated review evidence;
8. explicit statement of remaining limitations.

Do not merge a large implementation followed by one final visualisation commit.

Each subsystem should become independently usable.

---

# 38. Suggested first milestone

The first milestone should be deliberately narrow:

## `M1: ITES Review Pack`

Input:

```text
conflux demo --scenario ...
```

Existing output:

```text
result.json
```

New command:

```text
conflux visualise result.json
```

New output:

```text
evidence/
    index.html
    execution.svg
    provenance.svg
    manifest.json
```

The report must answer:

1. Which Principals entered each Principal Context?
2. Why?
3. What actions were proposed?
4. Which action/argument/read/visibility/consent decisions occurred?
5. Which action was finally allowed or blocked?
6. Where in `result.json` is the evidence for every displayed claim?

Do this well before implementing SLED or solver visualisation.

---

# 39. Suggested second milestone

## `M2: Verification Review Pack`

Add:

```text
sled-summary.svg
counterexample.svg
verification-ir.svg
coi.svg
solver-witness.svg
```

At this point the repository should support a review workflow where a supervisor can inspect both:

```text
runtime security behaviour
```

and:

```text
formal verification behaviour
```

without trusting an AI summary.

---

# 40. Research implications

Keep the engineering claim separate from the research claim.

The visualisation layer itself is primarily research infrastructure.

Potential fourth-year research questions arise from it:

- How small can counterexample evidence become while preserving diagnostic usefulness?
- Do Principal-Context-specific reductions reduce both verification cost and proof-review complexity?
- Can authority/provenance visualisations reveal implementation/specification divergence effectively?
- Can proof-carrying plans expose enough evidence for practical human approval?
- How does evidence complexity scale with Principal count, provenance depth and plan depth?

Do not make these claims merely because the visualiser exists.

They require experiments.

---

# 41. Final implementation principle

The repository should move from:

```text
AI implements change
        ↓
tests pass
        ↓
AI says it works
        ↓
human trusts summary
```

to:

```text
AI implements change
        ↓
deterministic validation
        ↓
schema-checked evidence
        ↓
deterministic visual evidence
        ↓
human inspects behaviour
        ↓
AI explains discrepancies
```

For Conflux specifically, the most important review surfaces are:

1. Principal Context evolution;
2. provenance propagation;
3. independent ITES policy decisions;
4. SLED state exploration and shortest counterexamples;
5. SLED-V invariants, reductions and witnesses;
6. plan topology and authority/information footprints;
7. semantic before/after diffs.

The implementation should optimise for those seven surfaces rather than for generic observability.