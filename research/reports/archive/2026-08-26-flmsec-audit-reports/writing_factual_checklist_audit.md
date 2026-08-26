# FLMSec Writing, Factual-Correctness, and NeurIPS-Checklist Audit

**26 August 2026 --- AI-coder handoff**

## Executive assessment

The current FLMSec manuscript is recognizably a research paper and its
core Principal Context/ITES story is strong. Its remaining risks are
sentence-level writing texture, factual/claim precision, and checklist
substantiation.

The prose has a **moderate AI-writing signal**, not because it is
generic or incoherent, but because it is uniformly polished, heavily
qualified, highly symmetric, and often sounds like repository
claim-management documentation. Do not try to defeat AI detectors. Make
the prose more economical and scientific: reuse the older preprint's
direct voice, let equations/results carry arguments, remove redundant
signposting, and replace repository/process vocabulary with ordinary
research prose.

The highest factual risks are: 1. comparative-defence claims must be
backed by retained models/evidence; 2. Biba should not be simplified as
inherently a "total order"; 3. monotonicity should be stated for a fixed
ACS state if delegation/policy mutation is possible; 4. "arbitrary model
behaviour" must mean arbitrary admitted/well-typed proposals under the
system model; 5. canonical-state SLED should not be described as
materializing every syntactically distinct trace; 6. authorized-read
safety must not be conflated with full confidentiality/noninterference;
7. SLED-V verifies the finite model/IR, not arbitrary Python unless
refinement evidence is added.

## 1. AI-writing audit

### Overall verdict

Moderate signal, readily fixable. The technical terminology is
consistent and citations are not obviously synthetic. The signal comes
from almost every paragraph following the same pattern: clean topic
sentence → distinction → several balanced qualifications →
mini-conclusion. A human technical paper normally has more variation and
relies more heavily on equations, results, and terse factual statements.

### Search and review these patterns

Do not mechanically delete them, but reduce repetition:

-   "This distinction is important because..."
-   "Importantly"
-   "Notably"
-   "Consequently"
-   "More broadly"
-   repeated "By contrast"
-   repeated "Rather than X, we Y"
-   exhaustive three-item lists where the third item adds little
-   repeated local caveats about finite models/BMC/IR abstraction
-   generic verbs: "provides", "enables", "demonstrates", "highlights"
-   generic nouns: "framework", "approach", "mechanism" where a concrete
    noun works.

### Remove repository-document language

Main-paper prose should rarely say: - retained evidence; - claim
boundary; - canonical implementation; - current repository; - evidence
artifact; - current implementation supports; - claim is scoped to.

Prefer: - "In our experiments..." - "We evaluate..." - "The model
includes..." - "This result applies to..."

If a sentence would fit naturally in `STATUS.md` or `CLAIMS.md`,
reconsider it.

### Preserve the old preprint voice

The old preprint's direct lines are often stronger, e.g. the simple
distinction that prompt injection is one mechanism for PE, not the
objective itself. Prefer an older correct/plain sentence over a newer
exhaustive synthesis sentence.

Do not add slang, contractions, deliberate errors, or personal anecdotes
to sound human. The target is economical academic prose.

## 2. Core factual audit

### PE definition

Present it as this work's definition:

> "We define privilege escalation for this setting as..."

not as the universal definition of PE.

### Maximal-safe-authorization theorem

Correct relative to the stated PE definition and a fixed ACS/action
model.

Use:

> "maximally permissive with respect to Definition X for a fixed ACS."

Do not say globally optimal/maximally secure in general.

### Authority monotonicity

State the ACS snapshot explicitly if the broader system allows
delegation/revocation:

`I1 subseteq I2 => Permitted_sigma(I2) subseteq Permitted_sigma(I1)`

for fixed ACS state `sigma`.

Otherwise an intervening policy mutation can invalidate an unqualified
temporal reading.

### Biba

The relationship is structural, not an equivalence.

Safe framing:

> Low-water-mark integrity attenuates effective integrity after
> lower-integrity influence. Principal Context instead retains
> conservatively influencing principal identities and computes permitted
> parameterized actions from the intersection of their current ACS
> permissions.

Avoid "Biba uses a total order." If useful, say that permission sets
ordered by inclusion have intersection as their meet.

Do not imply Biba proves the ITES theorem.

### LOMAC

Relevant operational precedent for low-water-mark/taint-style
degradation. Verify exact primary citation and do not present it as the
source of the exact permission-intersection construction.

### Arbitrary model behaviour

Define once as arbitrary well-typed/admitted proposals under the modeled
interface. Otherwise readers may interpret "arbitrary" as malformed
protocol behavior, arbitrary code execution, side channels, or
reference-monitor bypass.

The title may keep "arbitrary model behaviour" if the abstract defines
the abstraction immediately.

### SLED exhaustiveness

Prefer:

> "SLED exhaustively explores the reachable finite transition system
> under the configured proposal model."

Do not say it materializes every execution trace when canonical states
are memoized/deduplicated.

If the raw Part B reproduction exists, explicitly distinguish raw
decision-path enumeration from canonical reachable-state exploration.

### SLED-V

Use:

> "SLED-V verifies properties of the finite transition model used to
> represent the defence."

Avoid:

> "SLED-V formally verifies Conflux."

unless runtime↔IR refinement has actually been proved.

### Comparative defence claims

Highest-risk factual section.

For every Dual-LLM/CaMeL/Progent/PACT/FORGE claim: - verify the source
paper; - define the exact finite abstraction; - define its native
property; - retain generated native-property and PE verdicts; - call it
"our finite abstraction of X"; - do not imply testing of upstream
implementations.

A single defensible Dual-LLM comparison is enough to establish that
native property Q need not imply PE. Remove extra systems if their
abstraction cannot be defended.

### Confidentiality/exfiltration

Do not revive the older implication that authorized reads alone prove no
information exfiltration.

Separate: - per-trace authorized-read safety; - bounded observational
confidentiality/self-composition; - general noninterference, which is
not established unless actually proved.

### AgentDojo/planning

Current small-model runs are integration/pipeline evidence, not efficacy
evidence. Prefer omission from main FLMSec results.

## 3. Related-work audit

Order: 1. classical integrity/IFC; 2. system-level LLM defences; 3.
evaluation/verification.

This makes the Biba lineage explicit before modern comparisons.

For each comparison-table cell, retain an internal source note. Audit
especially: - model trusted?; - policy source; - formal guarantee; -
verification; - provenance granularity.

Prefer qualified phrases over Yes/No where the truth is conditional.

Safe novelty language: - ITES combines authenticated principal
provenance with existing organizational authorization to derive
collective execution authority. - SLED evaluates deterministic
system-level properties under nondeterministic model proposals. - SLED-V
provides a common finite transition representation and multiple checking
paths.

Avoid unsupported "first system-level/provenance/formal framework"
priority claims.

## 4. NeurIPS checklist audit

Treat the checklist as verification, not boilerplate.

### Claims

Likely YES only after every abstract/conclusion statement maps to
theorem, experiment, or source. Point to Introduction/Security
Model/Limitations.

### Limitations

Should be YES if the paper visibly includes: - provenance correctness; -
ACS correctness; - complete mediation; - finite/bounded verification; -
IR abstraction gap; - conservative influence overapproximation; - no
user-intent guarantee; - no general noninterference; - comparative
models are abstractions, not upstream implementation evaluations.

Do not hide these only in the checklist.

### Theory assumptions/proofs

YES only if every theorem is numbered, assumptions are stated, and
proof/proof sketch is present. Put longer detail in appendix if needed.

Add the fixed-ACS-state qualifier to monotonicity.

### Reproducibility

Conditional. The public GitHub repository cannot simply be linked in
double-blind material.

For deterministic experiments provide in paper/supplement: -
fixture/model definitions; - bounds; - solver/backend versions; -
commands/pseudocode; - result-generation procedure.

If no anonymous artifact exists, do not answer as if reviewers can
access the public repository.

### Code/data availability

Do not include the identifying `github.com/RayaBuckley/Conflux` link. If
allowed, provide an anonymous artifact; otherwise state
release-after-review accurately.

### Experimental details

For SLED/SLED-V document: - environment sizes; - depth/bounds; -
proposal grammar; - finite state variables; - solver version; -
timeouts; - COI configuration; - mutation definitions.

If Part B reproduction is reported, document its exact historical
proposal grammar.

### Statistical significance/error bars

For deterministic exhaustive/model-checking results: likely N/A, with
explanation.

If stochastic LLM results appear, handle them separately; do not let the
deterministic N/A answer cover them.

### Compute

Report it. Small deterministic experiments still use compute. Include
CPU/GPU where relevant, runtime, memory if material, solver/backend. Do
not mark N/A just because the experiments are cheap.

### Hyperparameter search

Likely N/A. Explain model-checking bounds/configuration separately.

### Dataset documentation

SLED fixtures are synthetic formal environments, not a conventional
dataset. Explain construction/purpose. AgentDojo obligations matter only
if its results are included.

### Human subjects

N/A for current headline evidence.

### Societal impact

Do not say none. Briefly note: - conditional guarantees may be
overinterpreted as deployment security; - bad provenance/ACS
configuration invalidates guarantees; - conservative enforcement can
deny useful actions; - extensions such as delegation can weaken
assumptions if misconfigured.

### Licenses

If external artifacts/fixtures are redistributed, document licenses. If
not, say so.

## 5. Create `CHECKLIST_EVIDENCE.md`

For every NeurIPS checklist question record:

``` text
question
draft answer: Yes / No / N/A
paper section supporting it
artifact supporting it
remaining action
```

The checklist answer must reflect evidence available to the reviewer,
not merely something existing privately in the repository.

## 6. Sentence-level coder procedure

### Pass A --- strong-word grep

Search:
`first, novel, unique, formal, prove, proven, verify, verified, guarantee, arbitrary, exhaustive, complete, maximal, optimal, fundamental, independent, faithful, equivalent, secure, confidentiality, exfiltration`.

For each occurrence label internally: - theorem-backed; -
experiment-backed; - source-backed; - rhetorical/unnecessary.

Delete/weaken the fourth category.

### Pass B --- AI-style grep

Search:
`importantly, notably, consequently, more broadly, by contrast, in particular, this distinction, rather than, provides, enables, demonstrates, highlights, framework, robust, comprehensive`.

Review for repetitive synthetic rhythm. Do not mechanically purge.

### Pass C --- paragraph purpose

Temporarily annotate each paragraph:

`% PURPOSE: <one sentence>`

Merge/delete paragraphs with duplicate purposes. Remove comments before
submission.

### Pass D --- equation-first compression

If prose restates exactly what an equation says, cut the duplication.
Let the theorem/counterexample carry the argument.

### Pass E --- sentence complexity

Break sentences with three or more independent qualifications. Prefer
one clear caveat to nested parentheticals.

## 7. Preferred writing transformations

Documentation-like:

> "The current implementation provides multiple independent checking
> paths while maintaining explicit claim boundaries."

Paper-like:

> "We check the same finite IR with a reference interpreter and Z3
> bounded model checking."

Documentation-like:

> "This result should be interpreted within the finite abstraction and
> does not establish implementation-level security."

Paper-like:

> "The result applies to the finite abstraction; we do not prove
> refinement from the Python implementation."

Over-signposted:

> "Importantly, this distinction highlights a fundamental difference
> between the two approaches."

Paper-like:

> "The two approaches enforce different properties."

## 8. P0 factual fixes

-   [ ] Correct requester/influencer roles in the motivating example.
-   [ ] Audit/remove unsupported CaMeL/Progent/PACT comparative results.
-   [ ] Remove the "Biba = total order" simplification.
-   [ ] Qualify monotonicity by fixed ACS state where necessary.
-   [ ] Define arbitrary model behavior as arbitrary admitted/well-typed
    proposals.
-   [ ] Replace "every execution trace" language for canonical-state
    SLED.
-   [ ] Do not call read safety full confidentiality.
-   [ ] Make SLED-V verification explicitly model/IR scoped.
-   [ ] Verify every comparison-table cell against primary sources.
-   [ ] Remove/fix uncertain or unused bibliography entries.

## 9. P0 writing fixes

-   [ ] Remove repository/status vocabulary from paper prose.
-   [ ] Centralize repeated caveats instead of restating them every
    paragraph.
-   [ ] Cut redundant signposting.
-   [ ] Prefer old preprint prose when equally accurate.
-   [ ] Reduce named subsystem count.
-   [ ] Delete generic "framework provides/enables/demonstrates"
    sentences without concrete information.
-   [ ] Do not optimize for AI-detector scores; optimize for concise
    scientific prose.

## 10. P1 evidence/checklist fixes

-   [ ] Integrate Part B reproduction only if retained evidence now
    exists.
-   [ ] Distinguish independent-backend agreement from COI preservation.
-   [ ] Add exact runtime/compute details for headline experiments.
-   [ ] Ensure quantitative paper values are generated/traceable.
-   [ ] Build and reconcile `CHECKLIST_EVIDENCE.md`.
-   [ ] Ensure anonymous code/data answer does not reveal author
    identity.

## 11. Recommended morning order

1.  Compile latest manuscript and freeze page count.
2.  Apply P0 factual fixes.
3.  Audit comparative models against retained evidence and primary
    papers.
4.  Correct Biba/monotonicity/SLED wording.
5.  Build `CHECKLIST_EVIDENCE.md` and reconcile checklist answers.
6.  Run strong-word factual grep.
7.  Run AI-style prose pass.
8.  Regenerate paper.
9.  Run anonymity/placeholder/citation checks.
10. Read abstract → introduction → theorem statements → evaluation
    conclusions → limitations → conclusion → checklist as one continuous
    claim chain.
11. Put only unresolved items into the noon handoff.

## Final standard

Do not try to make the manuscript sound less like AI by making it
casual.

It should sound like a security paper whose authors know exactly: - what
property they define; - what assumptions they make; - what they prove; -
what they model-check; - what they only test; - what prior work
established; - where their contribution ends.

That will reduce the current AI-writing signal while simultaneously
improving factual correctness and NeurIPS-checklist compliance.
