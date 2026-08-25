# Conflux Workshop Submission Readiness Review

**Date:** 25 August 2026\
**Repository reviewed:** `RayaBuckley/Conflux`, public `main` branch
(329 commits when inspected)\
**Primary assumed target:** NeurIPS 2026 *Who Verifies the Agents?*
workshop, submission deadline 29 August 2026 AoE\
**Secondary fit considered:** NeurIPS 2026 *Foundations of Language
Model Security* (deadline 27 August 2026 AoE)

## 1. Executive conclusion

Conflux is technically much stronger than its current workshop
manuscript makes it appear.

The repository now contains a coherent fail-closed ITES security kernel,
native finite-state SLED, a serialisable verification IR, Z3 bounded
model checking, a nuXmv subset, property-scoped cone-of-influence (COI)
reduction, observational-confidentiality self-composition, comparative
finite-model verification, argument-aware policy, disclosure/attribution
machinery, authenticated planning, and retained experimental evidence.
The manuscript, however, is still substantially the **31 July
project-status paper**. It contains multiple `generated result pending`
placeholders and says several experiments remain future work even though
`docs/evidence/STATUS.md` and `CLAIMS.md` now record completed results.

For a workshop reviewer, this creates the wrong impression: the paper
reads as a broad implementation/status report whose principal
contribution is not yet sharply identified, rather than as a focused
research paper with a clear question, method, evidence, and result.

The highest-value work in the remaining four days is therefore **not
adding another major subsystem**. It is:

1.  choose one paper thesis;
2.  synchronize the manuscript with retained evidence;
3.  turn the strongest existing evidence into 2--4 compact
    experiments/tables/figures;
4.  sharpen the formal claims and contribution boundary;
5.  strengthen the related-work comparison;
6.  produce an anonymized, workshop-compliant submission;
7.  run a reviewer-style pre-mortem against novelty, correctness,
    evidence, scope, and reproducibility.

My recommended paper thesis for *Who Verifies the Agents?* is:

> **SLED-V verifies system-level LLM-agent security independently of
> model behaviour by compiling explicit defence semantics into a shared
> transition model, checking security properties with explicit-state and
> solver-backed methods, and returning concrete counterexamples for
> defective defences. Conflux/ITES is the principal case study.**

This is stronger for that workshop than presenting the paper primarily
as "Conflux is a large secure-agent framework." It directly matches the
workshop's focus on verification, environment-grounded evaluation,
safety/robustness, benchmarks, and reliable agent development.

The corresponding security-workshop thesis, if targeting *Foundations of
Language Model Security*, should instead be:

> **Principal Context is a system-level security abstraction for
> multi-principal LLM agents: authority is derived conservatively from
> authenticated provenance and organisational policy, while SLED-V
> checks whether implementations and competing defence models preserve
> the resulting privilege-escalation invariant.**

The implementation can support both stories, but the submitted paper
should choose one.

------------------------------------------------------------------------

## 2. What the target workshop says it wants

### 2.1 Who Verifies the Agents?

The workshop explicitly frames verification as the bottleneck between
fragile prototypes and reliable agent systems. Its review scope
includes:

-   safety and robustness of verification;
-   adversarial robustness of verifiers/evaluation harnesses;
-   environment-grounded verification and simulators;
-   production observability and runtime verification;
-   benchmarks and environments that stress-test verification;
-   heterogeneous verifiable signals;
-   formal verification of agent-generated artefacts;
-   long-horizon and multi-step agent verification.

Papers may be 4--9 pages excluding references and appendices, use the
NeurIPS 2026 template, and are reviewed double blind. The workshop is
non-archival.

This is unusually good alignment for SLED-V. A reviewer is likely to
ask:

-   What exactly is being verified?
-   What is the specification/property?
-   Why is the verifier more meaningful than ordinary benchmark
    evaluation?
-   What assumptions make the result sound?
-   Is the checked model faithful to the implementation?
-   Does the method find real or seeded failures?
-   How does it scale?
-   Is it useful beyond ITES?
-   Does it provide actionable counterexamples?
-   Is the evaluation reproducible?

### 2.2 Foundations of Language Model Security

This workshop asks three especially relevant questions:

1.  How should LLM security be formalized?
2.  How can evaluation be reproducible/generalizable rather than an
    attack/defence arms race?
3.  What security--utility trade-offs or provable guarantees are
    fundamental?

Its topics explicitly include formal security frameworks,
secure-by-design architectures, provable security, reproducible
evaluation, system-level prompt-injection defences, worst-case
guarantees, and compositional security.

Conflux is almost perfectly topically aligned. However, this workshop
has an earlier 27 August deadline and strict double-blind rules,
including anonymized linked code/data.

------------------------------------------------------------------------

## 3. Current manuscript: the main problem

The canonical manuscript is
`research/publications/manuscript/conflux_fourth_year_2026.tex`.

It currently identifies itself as:

> "Conflux: Principal-Context Security, Evaluation and Verification for
> LLM Agents --- Work-in-progress fourth-year paper"

and is dated 31 July 2026.

The abstract is mostly an implementation inventory. It says
architectural repair and the offline slice are tested, while real-model,
external-benchmark and solver-binary claims remain gated. That was
reasonable on 31 July, but it is no longer an accurate summary of the
repository.

The Results section still contains:

-   `Semantic conformance: generated result pending`
-   `Native SLED: generated result pending`
-   `SLED-MC/SLED-V: generated result pending`
-   `Real models and AgentDojo: generated result pending`

Yet current retained evidence includes:

-   native SLED reproduction and seeded-defect detection;
-   COI safe/unsafe fixtures;
-   Z3 BMC agreement with the reference interpreter;
-   canonical SLED runs;
-   delegation mutation evidence;
-   observational-confidentiality self-composition;
-   comparative finite-model verification;
-   a completed eight-cell Qwen planning pilot;
-   a completed six-cell Qwen AgentDojo experiment.

This mismatch is currently the single biggest paper-quality problem.

### Required action

Treat the manuscript as stale and regenerate its research narrative from
the claim ledger and retained results. Do **not** merely replace the
words "pending" with numbers. The paper's argument should be redesigned
around the evidence that now exists.

------------------------------------------------------------------------

## 4. Likely reviewer scorecard

A workshop reviewer will normally form an opinion along approximately
these dimensions even when the form uses different names.

  ------------------------------------------------------------------------------
  Dimension               Current likely          Target before submission
                          impression              
  ----------------------- ----------------------- ------------------------------
  Relevance               Very high               Very high

  Novelty                 Interesting but diffuse One crisp contribution +
                                                  clearly delimited supporting
                                                  contributions

  Technical correctness   Promising, carefully    Precise
                          scoped                  property/model/assumptions +
                                                  evidence

  Empirical evidence      Appears incomplete from Compact, retained,
                          manuscript              reproducible experiments

  Formal evidence         Appears mostly planned  Explicit finite/bounded
                                                  results and counterexamples

  Comparison              Related work named,     At least one aligned
                          little direct evidence  comparative verification

  Clarity                 Architecture/status     Research-question driven
                          heavy                   

  Reproducibility         Repository unusually    Surface it explicitly in paper
                          strong                  

  Scope discipline        Too broad               Core story + supporting system

  Workshop fit            Strong                  Obvious from
                                                  title/abstract/introduction

  Confidence              Moderate                High enough to accept as
                                                  workshop research
  ------------------------------------------------------------------------------

The paper does not need a full top-conference evaluation in four days. A
workshop paper can present ongoing work. But it must make the
**completed contribution legible**.

------------------------------------------------------------------------

## 5. Recommended paper thesis

### Primary recommendation: make SLED-V the workshop contribution

For *Who Verifies the Agents?*, restructure the paper around:

**Problem.** Empirical prompt-injection benchmarks test finite
model/attack combinations. System-level defences instead make
deterministic claims about which effects their reference monitor can
permit. Those claims are suitable for formal verification, but current
agent benchmarks do not provide a common verification model.

**Method.** SLED-V represents a defence as a finite serialisable
transition system with explicit adversarial proposals and checks
security properties using: - explicit-state exploration; - a reference
interpreter; - solver-backed bounded checking; - property-scoped COI
reduction; - counterexample reconstruction/lifting.

**Case study.** Encode ITES/Principal Context and selected
comparison/defective controllers.

**Questions.** - Does SLED-V agree across independent checking paths? -
Does it detect deliberately seeded monitor defects? - Can it distinguish
a defence's native invariant from the stronger privilege-escalation
property? - Does COI preserve verdicts while reducing models? - What
claims remain bounded/model-specific?

**Result.** The retained repository already supports much of this story.

This is a coherent workshop paper even if the real-model AgentDojo
utility result is weak.

### Secondary recommendation: Principal Context paper

If the intended target is instead *Foundations of Language Model
Security*, make Principal Context the centre:

-   define the PE property;
-   relate it explicitly to Biba/low-water-mark integrity and
    information-flow security;
-   explain why authenticated Principal provenance plus existing
    organisational policy gives a useful authority abstraction;
-   present argument-level authority and read/visibility as refinements;
-   use SLED-V as implementation/defence validation;
-   include the comparative Dual-LLM finite model as an example of
    property mismatch.

------------------------------------------------------------------------

## 6. The strongest evidence already in the repository

### 6.1 Seeded-defect detection

The claim ledger records that the native reproduction detects five of
five defective monitors, each with a one-step witness, under the fixed
finite fixtures/bounds.

This is excellent workshop evidence because it demonstrates that the
verifier does more than certify the intended implementation: it produces
useful counterexamples when the implementation is wrong.

**Paper treatment:** make this a table.

Suggested columns:

  -------------------------------------------------------------------------
  Mutant        Violated rule Verdict         Minimal witness Expected?
                                                       length 
  ------------- ------------- ------------- ----------------- -------------

  -------------------------------------------------------------------------

Include the exact finite scope/bounds in the caption.

### 6.2 Independent verifier agreement

The repository records four IR fixtures where Z3 bounded checking agrees
with the reference interpreter, including safe and unsafe cases.

This is stronger than a single checker saying its own model is safe.

**Paper treatment:** table showing: - fixture; - reference verdict; - Z3
verdict; - bound; - reduced/unreduced agreement; - witness lifted.

### 6.3 COI reduction

The current evidence shows property-scoped COI removes irrelevant
variables/rules in at least the safe-noise and unsafe-control fixtures
while preserving verdicts and lifting the unsafe witness.

This is a concrete verification contribution, but current evidence is
small.

**Four-day improvement:** create a scaling family automatically by
adding increasing numbers of irrelevant variables/rules. Measure: -
original variables/rules; - reduced variables/rules; - reachable states
or solver time; - reduction time; - total verification time; - verdict
equality.

Even a synthetic scaling experiment is useful if clearly labelled. It
directly tests the reduction rather than claiming production-scale
performance.

### 6.4 Comparative defence verification

The current status says finite IR models exist for: - Dual-LLM; - its
native property Q ("processor never executes"); - ITES; - a defective
requester-only controller.

It reports that Dual-LLM satisfies Q but violates the Conflux PE
property in the finite model, whereas ITES preserves PE.

This may be the **most interesting current research result** if
carefully framed.

It demonstrates an important methodological point:

> A defence can satisfy the property it was designed for while failing a
> different system-level security property.

Do not present this as "Dual-LLM is insecure" generally. Present it as a
property-relative verification example under a stated abstraction.

**Paper treatment:** one diagram plus one counterexample trace.

### 6.5 Observational confidentiality

Self-composition with Z3 BMC now distinguishes safe fixtures from unsafe
observation-divergence fixtures.

This is useful evidence that SLED-V can go beyond single-trace safety
properties, but it is bounded evidence rather than a noninterference
proof.

This should probably be a compact extension/result rather than the
central story unless the experiment can be strengthened quickly.

### 6.6 AgentDojo

The six-cell 1.5B run proves the integration pipeline executes, but it
does not provide convincing efficacy evidence because utility is false
and the attacked configuration reports security false.

Use this as **integration evidence**, not a headline result.

Do not spend the paper defending a weak 1.5B benchmark result.

If a larger model can be made to work reliably in the next 1--2 days,
add it. Otherwise, keep AgentDojo to a small paragraph or appendix.

### 6.7 Planning

Likewise, the eight-cell 1.5B experiment demonstrates an end-to-end
pipeline but not a useful utility result.

Planning is currently a distraction from a verification workshop paper
unless it directly becomes an object of verification.

Move most planning detail to the appendix/system section.

------------------------------------------------------------------------

## 7. What is currently missing from the manuscript

### 7.1 A crisp contribution list

The paper currently transitions from introduction into previous-year
work without a conventional contribution paragraph.

Add 3--4 contributions only.

Recommended version:

1.  **Verification formulation.** A finite transition-system abstraction
    for system-level LLM-agent defences under arbitrary well-typed model
    proposals.
2.  **SLED-V.** Explicit-state and solver-backed checking with
    replayable counterexamples and property-scoped COI reduction.
3.  **Principal-Context case study.** A canonical ITES reference monitor
    whose PE invariant is evaluated through the shared model.
4.  **Evidence.** Cross-checking, mutation/counterexample experiments,
    reduction measurements, and comparative finite-model analysis.

Do not list every repository subsystem as a contribution.

### 7.2 Research questions

Explicit RQs will greatly improve the paper.

Recommended:

**RQ1:** Can SLED-V reliably distinguish safe and defective finite
models of system-level agent defences?

**RQ2:** Do independent verification paths agree on safe and unsafe
instances?

**RQ3:** Can property-scoped COI reduce verification models without
changing verdicts or losing counterexamples?

**RQ4:** What does property-relative verification reveal when comparing
Principal Context with another system-level defence abstraction?

Optional RQ5 only if strong results exist: **RQ5:** How does
verification cost scale with principals, resources, actions, and
irrelevant state?

### 7.3 Threat model / trusted computing base

The current limitations state assumptions, but reviewers should see them
earlier.

Create a compact box/table:

**Adversarial/untrusted** - LLM proposals; - prompt/document/tool
content; - principals without required permissions.

**Trusted** - principal authentication; - provenance attachment; -
policy decision point; - reference monitor / transition semantics; -
effect mediation; - provider mapping within its declared contract.

**Not proved** - provenance correctness; - ACS correctness; - unbounded
deployment security; - arbitrary Python equivalence; - provider
isolation; - subjective user intent.

This will prevent reviewers from attacking claims the paper does not
make.

### 7.4 Formal definitions

The paper currently gives the core `Allow(PC,a)` equation, but for a
verification paper it needs at least:

-   state definition;
-   transition relation;
-   proposal nondeterminism;
-   bad-state predicate;
-   PE property;
-   bounded-safe/unsafe/unknown semantics;
-   relationship between runtime kernel and IR.

A small formal core is more valuable than several paragraphs of
architecture.

### 7.5 A model-to-implementation diagram

Add one figure:

``` text
Untrusted proposal
      |
      v
Canonical ITES transition kernel
      |                \
      |                 \ serialize/abstract
      v                  v
Runtime effect        SLED-V IR
certificate              |
      |          +-------+--------+
      v          v                v
Executor      explicit-state     Z3/nuXmv
                 |                |
                 +------v---------+
                    verdict /
                  counterexample
```

Annotate the trust boundary and which arrows are tested for conformance.

### 7.6 A single motivating example

Use one small example consistently through the paper.

Example: - Alice requests an operation. - Mallory-authored content
influences an authority-bearing recipient/resource selector. - Alice may
perform the operation; Mallory may not. - requester-only control allows
it; - Principal Context blocks it; - SLED-V finds the one-step
counterexample for the defective controller.

This makes the security property concrete and gives reviewers an
intuitive witness.

------------------------------------------------------------------------

## 8. Related work: what a reviewer will challenge

The current manuscript's related-work section is only a short paragraph.
That is insufficient for the current landscape.

At minimum compare:

-   CaMeL;
-   Dual-LLM / design-pattern work;
-   Progent;
-   PACT;
-   FORGE/PCAS;
-   AgentDojo;
-   classical Biba/LOMAC low-water-mark integrity;
-   IFC/declassification/endorsement where relevant;
-   recent formal/verification-oriented agent work if primary sources
    are verified.

The repository's own related-work document correctly acknowledges that
Principal Context has classical precedent: its authority attenuation is
structurally analogous to low-water-mark integrity. This should appear
in the paper itself.

A reviewer familiar with Biba should not be the person who first tells
the paper this.

### Suggested comparison dimensions

  -----------------------------------------------------------------------------------------------
  System     Security   Provenance    Authority   Model      Policy     Verification/evaluation
             property   granularity   source      trusted?   language   
  ---------- ---------- ------------- ----------- ---------- ---------- -------------------------

  -----------------------------------------------------------------------------------------------

Avoid binary "better/worse" comparisons. The key point is that the
systems secure **different properties under different assumptions**.

### Novelty language

Avoid: - first system-level defence; - first provenance-based defence; -
first privilege-control approach; - unique formal security guarantee.

Prefer: - "We study collective Principal Context as a conservative
authority abstraction..." - "We use a common transition model to verify
property-relative claims..." - "Our contribution is not provenance
tracking per se, but the combination of authenticated principal
provenance, organisational policy, and verification under arbitrary
proposal behaviour."

------------------------------------------------------------------------

## 9. System improvements that directly strengthen the paper

Only implement changes that create evidence or close a reviewer-visible
correctness gap.

### P0 --- manuscript/evidence synchronization

Create a deterministic paper-results generator that consumes retained
result JSON and emits LaTeX tables/macros.

Acceptance: - no manual experimental numbers; - all current
`generated result pending` placeholders either replaced or explicitly
removed; - manuscript build fails if required evidence is
absent/stale; - each generated table records experiment/commit
identifiers in a comment or caption.

### P0 --- anonymized submission build

The current manuscript contains the author name and public repository
paths are identity revealing.

For double-blind review: - create `submission.tex` or a build flag; -
remove author identity; - remove "fourth-year" wording; - remove
Oxford/project-history language where identifying; - ensure
repository/data links are anonymous or omit them; - anonymize
self-citations; - remove acknowledgements; - verify PDF metadata.

This is a potential desk-rejection issue, not polish.

### P0 --- reviewer-facing results bundle

Generate one compact bundle containing: - exact manuscript commit; -
experiment manifests; - checksums; - generated tables; - generated
figures; - machine-readable summary; - claim-to-evidence map.

### P0 --- run a scaling experiment for SLED-V/COI

This is the highest-value new experiment that is likely feasible within
four days because it is deterministic and does not depend on a large
LLM.

Generate parameterized finite models varying: - number of principals; -
resources; - actions; - irrelevant state variables/rules; - perhaps
provenance depth.

Measure: - model size; - reduced size; - reachable states; -
explicit-state runtime; - Z3 runtime; - COI runtime; - witness length; -
verdict.

Use repeated runs only if timing variance matters.

### P0 --- comparative counterexample

Produce a human-readable shortest witness for the Dual-LLM finite
abstraction and requester-only controller.

The output should answer: 1. initial Principal Context; 2. proposal; 3.
defence decision; 4. executed effect; 5. violated PE predicate.

Generate a diagram automatically if possible.

### P1 --- implementation/IR conformance evidence

The largest formal weakness is the gap between the verified IR and the
production Python kernel.

A feasible four-day improvement is not full formal refinement.
Instead: - generate a corpus of canonical runtime transitions; -
translate each to the IR; - execute both from equivalent states; -
compare next-state and decision observations; - include
negative/mutation cases.

Report this honestly as **differential conformance testing**, not proof.

This materially strengthens "we verify the system" against the obvious
reviewer objection "you verify a hand-written model."

### P1 --- property catalogue

Add a versioned table mapping: - property name; - formal predicate; -
checker backend; - scope; - evidence status; - counterexample type.

This should include PE, unauthorized read, provenance monotonicity,
implicit delegation, bounded resources, and bounded observational
confidentiality.

### P1 --- one-page reproduction command

A reviewer should be able to run something like:

``` sh
python scripts/validate.py
conflux verify reproduce --paper
```

and regenerate the deterministic workshop tables/figures.

If no such command exists, add one.

### P2 --- larger AgentDojo model

Attempt only if hardware/time allows and only after deterministic paper
evidence is complete.

Priority: 1. structured-output reliability; 2. benign utility \> 0; 3.
attacked comparison; 4. retained raw outputs.

If this remains unreliable, do not let it consume submission-critical
time.

### Explicitly defer

Do not spend the four days on: - activating delegation; - full Cedar
integration unless it is one command away; - new cloud providers; -
production hardening; - persistent memory; - arbitrary generated-program
verification; - another benchmark family; - major planning redesign.

These may improve Conflux but are unlikely to improve this workshop
submission as much as stronger evidence and presentation.

------------------------------------------------------------------------

## 10. Recommended experiment section

A strong workshop evaluation can be compact.

### Experiment 1 --- Defect detection

**Question:** Does SLED-V expose incorrect security monitors?

Use canonical + seeded mutants.

Report: - safe canonical verdict; - mutants detected / total; - shortest
witness length; - property violated.

### Experiment 2 --- Independent checker agreement

**Question:** Are verdicts artefacts of one implementation?

Compare: - reference interpreter; - explicit-state checker where
applicable; - Z3 BMC; - reduced/unreduced IR.

Report agreement and scope.

### Experiment 3 --- Reduction/scaling

**Question:** Does COI make verification cheaper without changing the
result?

Use parameterized irrelevant-state families and, if possible, one
realistic Conflux-derived model.

Plot: - unreduced vs reduced state/model size; - verification time; -
perhaps reachable states.

### Experiment 4 --- Property-relative comparison

**Question:** Can SLED-V reveal the difference between a defence's
native invariant and PE?

Show: - Dual-LLM finite abstraction satisfies its native Q; - same
abstraction has a PE counterexample under the Conflux property; - ITES
finite abstraction satisfies PE within the checked model; - defective
requester-only controller fails PE.

State repeatedly that this is **model comparison, not
implementation-level evaluation of the published systems**.

### Optional Experiment 5 --- AgentDojo integration

Only as supporting evidence unless a better model is available.

------------------------------------------------------------------------

## 11. Figures that would materially improve reviewability

Produce these automatically from evidence where possible.

### Figure 1 --- Security/verification architecture

One clean diagram showing: - principals/data; - provenance; - Principal
Context; - policy; - ITES; - effect certificate; - SLED-V model; -
checker backends.

### Figure 2 --- Minimal counterexample

A 3--5-node trace showing a defective requester-only or Dual-LLM
abstraction reaching a bad state.

### Figure 3 --- COI reduction

Show the original dependency graph, invariant cone, and removed
irrelevant state.

### Figure 4 --- Scaling

One simple plot of verification cost/model size against irrelevant-state
count or total state dimension.

Four clear figures are more useful than screenshots of CLI output.

------------------------------------------------------------------------

## 12. Paper structure recommended for a 6--8 page submission

### 1. Introduction

\~0.75 page

-   multi-principal agent problem;
-   why finite attack benchmarks do not validate deterministic reference
    monitors;
-   SLED-V thesis;
-   contributions.

### 2. Security model and Principal Context

\~1 page

-   principals/provenance;
-   PE definition;
-   ITES rule;
-   threat model/TCB;
-   one motivating example.

### 3. SLED-V

\~1.5 pages

-   transition IR;
-   nondeterministic model proposals;
-   properties/verdicts;
-   explicit-state checking;
-   solver checking;
-   COI;
-   counterexamples;
-   implementation-conformance boundary.

### 4. Evaluation

\~2 pages

-   RQs;
-   fixtures/models;
-   mutation detection;
-   checker agreement;
-   COI/scaling;
-   comparative model.

### 5. Related work

\~1 page

-   classical integrity/IFC;
-   modern system-level agent defences;
-   agent evaluation/verification.

### 6. Limitations and discussion

\~0.5 page

-   bounded results;
-   TCB;
-   abstraction fidelity;
-   property-relative comparison;
-   no general noninterference/unbounded deployment claim.

### 7. Conclusion

\~0.25 page

Planning, AgentDojo plumbing, Cedar, disclosure implementation detail,
and delegation lifecycle can move to appendix/supplement unless directly
needed.

------------------------------------------------------------------------

## 13. Abstract rewrite specification

The final abstract should answer five questions in roughly 150--200
words:

1.  What problem?
2.  Why do current evaluations not answer it?
3.  What is SLED-V?
4.  What concrete evidence/results?
5.  What is the exact scope of the claim?

It should contain actual results, not repository inventory.

Do not lead with: - "the repository has..." - "current implementation
includes..." - "future work..."

Lead with the research problem and result.

------------------------------------------------------------------------

## 14. Reviewer pre-mortem

Before submission, simulate at least three reviewers.

### Reviewer A --- formal methods/security

Likely objections: - "This is bounded model checking, not proof." -
"What exactly is the state machine?" - "Why should I trust the
abstraction?" - "Where is the implementation-refinement argument?" -
"Biba already resembles this."

Required answers: - explicit bounded claim language; - formal
transition/property definitions; - differential conformance evidence; -
explicit Biba/LOMAC lineage; - no unbounded claim.

### Reviewer B --- LLM-agent security

Likely objections: - "How does this compare with
CaMeL/Progent/PACT/FORGE?" - "Does it work on realistic agents?" -
"Where is AgentDojo?" - "Is Principal Context too conservative?"

Required answers: - comparison table; - realistic motivating example; -
AgentDojo integration clearly scoped; - security--utility discussion; -
argument-level authority and visibility extensions.

### Reviewer C --- agent evaluation

Likely objections: - "Why is this an agent verifier rather than ordinary
software model checking?" - "Does it generalize beyond ITES?" - "Where
is the benchmark/evaluation contribution?"

Required answers: - arbitrary well-typed LLM proposal semantics; -
comparative defence models; - reusable IR/property interface; - mutation
and counterexample experiments; - environment-grounded state.

Have the AI coder create a `WORKSHOP_REVIEW_PREMORTEM.md` containing
these reviews and ensure every major objection is answered in the paper
or explicitly acknowledged.

------------------------------------------------------------------------

## 15. Four-day execution plan

### Day 1 --- freeze the story

1.  Confirm target workshop.
2.  Create submission branch/tag.
3.  Choose SLED-V or Principal-Context thesis.
4.  Rewrite title, abstract, intro, contributions and RQs.
5.  Synchronize claim ledger → manuscript.
6.  Implement anonymized build.
7.  Create experiment/table generation skeleton.

**End-of-day gate:** no stale "pending" statements about completed
evidence.

### Day 2 --- deterministic experiments

1.  Regenerate mutation evidence.
2.  Regenerate checker-agreement evidence.
3.  Run COI scaling family.
4.  Generate comparative counterexample.
5.  Run runtime↔IR differential conformance corpus if feasible.
6.  Generate plots/tables.

**End-of-day gate:** all headline results exist as retained JSON plus
generated paper assets.

### Day 3 --- paper integration

1.  Rewrite formal-method section.
2.  Expand related work.
3.  Add Biba/LOMAC/IFC lineage.
4.  Add diagrams.
5.  Rewrite evaluation around RQs.
6.  Tighten limitations.
7.  Move system breadth to appendix.
8.  Compile in NeurIPS template and check page limit.

**End-of-day gate:** complete submission-quality PDF, no placeholders.

### Day 4 --- adversarial review

1.  Run full repository validation.
2.  Regenerate paper from clean checkout.
3.  Run citation/claim audit.
4.  Run anonymization audit.
5.  Conduct three reviewer pre-mortems.
6.  Fix only acceptance-critical issues.
7.  Verify OpenReview profile/submission metadata.
8.  Freeze checksum of submitted PDF and evidence manifest.

Do not use the final day for new architecture.

------------------------------------------------------------------------

## 16. Concrete AI-coder backlog

### WS-P0-01 --- Workshop manuscript synchronization

**Goal:** Replace the 31 July status narrative with current retained
evidence.

**Acceptance criteria:** - no completed result is described as
pending; - no result appears without a claim-ledger/evidence
reference; - all numerical results are generated; - limitations remain
synchronized with `CLAIMS.md`.

### WS-P0-02 --- Submission anonymization

**Goal:** Produce a double-blind build.

**Acceptance criteria:** - no author/institution/project-identifying
metadata; - no identity-revealing URLs; - anonymized self-citations; -
PDF metadata inspected; - automated grep/audit for identifying strings.

### WS-P0-03 --- Paper evidence generator

**Goal:** Generate LaTeX tables/macros/figures from retained JSON.

**Acceptance criteria:** - deterministic byte-for-byte regeneration; -
schema validation; - input checksums; - build fails on stale/missing
required evidence.

### WS-P0-04 --- SLED-V scaling suite

**Goal:** Quantify verification and COI behaviour.

**Acceptance criteria:** - parameterized model family; - safe and unsafe
cases; - unreduced/reduced equivalence checked; - runtime/model-size
metrics retained; - generated plot/table.

### WS-P0-05 --- Comparative witness

**Goal:** Produce a reviewer-readable property-relative counterexample.

**Acceptance criteria:** - Dual-LLM/native-Q and PE properties
separately reported; - ITES comparison under aligned finite model; -
shortest witness serialized; - no claim about full external
implementation security.

### WS-P1-01 --- Runtime/IR differential conformance

**Goal:** Reduce the abstraction-gap objection.

**Acceptance criteria:** - canonical transition corpus; - runtime and IR
next-state/decision comparison; - negative cases; - mismatch is hard
failure; - retained report.

### WS-P1-02 --- Workshop figures

**Goal:** Generate four publication-quality figures.

**Acceptance criteria:** - architecture; - counterexample; - COI; -
scaling; - deterministic generation where practical; - legible in
grayscale and at paper column width.

### WS-P1-03 --- Related-work audit

**Goal:** Make novelty claims defensible.

**Acceptance criteria:** - primary-source verification for every cited
contemporary system; - Biba/LOMAC lineage included; - comparison
dimensions explicit; - no unsupported priority claims.

### WS-P1-04 --- Reviewer pre-mortem

**Goal:** Simulate rejection arguments before submission.

**Acceptance criteria:** - formal-method reviewer; - agent-security
reviewer; - evaluation reviewer; - each objection mapped to paper
section, fix, or acknowledged limitation.

------------------------------------------------------------------------

## 17. Things the AI coder should not do

Until submission:

-   do not activate delegation;
-   do not refactor package structure unless required by a paper
    experiment;
-   do not add another benchmark;
-   do not add another policy provider;
-   do not broaden the threat model;
-   do not attempt full arbitrary-Python verification;
-   do not manually type result numbers into LaTeX;
-   do not claim unbounded security from BMC;
-   do not describe finite comparison models as faithful implementations
    without evidence;
-   do not make AgentDojo the headline result with the current 1.5B
    utility;
-   do not leave public identity-bearing repository links in a
    double-blind submission.

------------------------------------------------------------------------

## 18. Submission-level claim discipline

The strongest defensible claims today are approximately:

**Can claim** - Conflux implements a canonical fail-closed
Principal-Context reference monitor. - Native SLED explores finite
operational models and returns shortest counterexamples. - SLED-V has a
serialisable IR and independent/reference checking paths. - Z3 BMC
agrees with the reference interpreter on retained safe/unsafe
fixtures. - Property-scoped COI preserves verdicts on retained fixtures
and can lift unsafe witnesses. - Seeded monitor defects are detected
under recorded finite scopes. - Finite comparative models can expose a
mismatch between a defence-native property and PE. - Bounded
self-composition can detect observational divergence in finite fixtures.

**Must qualify** - "secure" → secure with respect to the stated
property/model/bound. - "verification" → finite/bounded unless an
unbounded backend result exists. - "comparison with Dual-LLM" →
comparison of explicit finite abstractions, not implementation
evaluation. - "AgentDojo efficacy" → current small-model run establishes
pipeline execution but weak utility. - "planning improves utility" → not
supported strongly by current 1.5B pilot.

**Do not claim** - unbounded deployment security; - complete
noninterference; - faithful verification of arbitrary Python; -
production provider isolation; - Cedar parity; - active secure
delegation; - realistic AgentDojo efficacy from the current 1.5B result.

------------------------------------------------------------------------

## 19. Final recommendation

The repository is already broad enough for a strong workshop submission.
The paper is not currently exploiting that strength.

The submission should stop reading like a fourth-year project inventory
and become a focused research argument. For the 29 August *Who Verifies
the Agents?* deadline, the cleanest argument is:

> **System-level agent defences expose deterministic security semantics
> that can be verified independently of LLM behaviour. SLED-V turns
> those semantics into a common finite transition model, checks explicit
> security properties through independent verification paths, reduces
> models with property-scoped COI, and returns minimal counterexamples.
> Principal Context/ITES demonstrates the approach, while comparative
> finite models show why security claims must be property-relative.**

The next four days should be spent making that claim easy for a reviewer
to verify.

The single most important engineering principle until submission is:

> **Every code change must either produce a paper result, make a paper
> claim more defensible, improve reproducibility, or remove a submission
> risk.**

Anything else can wait until after the deadline.
