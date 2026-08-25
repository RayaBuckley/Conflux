# FLMSec 2026: Immediate AI-Coder Implementation Plan

**Prepared:** 25 August 2026\
**Target:** NeurIPS 2026 Workshop on Foundations of Language Model
Security (FLMSec), Paris\
**Deadline:** 27 August 2026, 23:59 AoE\
**Immediate scope:** approximately two hours of AI-coder work before a
new review tomorrow around noon.

## 1. Mission

Produce a substantially submission-ready FLMSec manuscript without
broadening Conflux. Prioritize editorial consolidation, evidence
integration, related-work correction, submission compliance, and
lightweight deterministic paper tooling.

Use the previous ITES/SLED preprint as the prose/theorem backbone. Use
the current repository, claim ledger, status documents, and retained
artifacts as the source of truth for current implementation/evidence. Do
not treat the current fourth-year manuscript as the prose source of
truth: it is useful for newer work, but its project-status framing and
stale pending-result sections are unsuitable for FLMSec.

The intended paper is a focused security paper, not a repository report.

## 2. Fixed decisions

### Venue positioning

Directly address FLMSec's themes: 1. formalizing LLM security: privilege
escalation (PE) as a system-level property; 2.
reproducible/generalizable security evaluation: deterministic
enforcement plus SLED/SLED-V rather than attack success rates alone; 3.
fundamental limits: under a fixed PE definition and ACS, Principal
Context's intersection rule is maximally permissive; more utility
requires changing authority/policy, adding trusted mechanisms, or
changing the property.

Do not mention supervisor/workshop-personnel connections in the
anonymous manuscript.

### Working thesis

> LLM-agent security can be formulated at the system boundary as
> preventing privilege escalation under arbitrary model behaviour.
> Principal Context conservatively derives execution authority from
> authenticated provenance and an organisation's existing access-control
> system. Its intersection rule is maximally permissive under the stated
> PE objective and monotonically loses authority as influence
> accumulates. SLED/SLED-V provides finite-state and solver-backed
> evidence that implementations enforce the resulting system-level
> properties.

ITES remains the defence name; Principal Context is the underlying
abstraction. "Conflux" is not the primary scientific contribution.

### Working title

**Principal-Context Security for LLM Agents: Preventing Privilege
Escalation under Arbitrary Model Behaviour**

Do not spend this work block bikeshedding it.

### Contribution hierarchy

Main text: 1. PE security objective/threat model; 2. Principal Context /
ITES semantics; 3. maximal-safe-authorization and authority-monotonicity
results; 4. SLED/SLED-V reproducible validation evidence.

Argument-aware authorization may be a concise realism refinement.
Delegation belongs mainly in Discussion as a principled way to change
authority. Visibility, consent, attribution, planning, Cedar, AgentDojo
and provider architecture are not equal paper contributions.

### Claim strength

Never strengthen bounded evidence.

Use: - "prevents PE under the stated threat model" for the mathematical
result, conditional on correct provenance, ACS and enforcement; - "safe
within the stated finite model" for exhaustive finite-state evidence; -
"no counterexample through bound k" for BMC; - "unsafe" only with a
valid witness.

Do not claim arbitrary Python verification, unbounded implementation
security from BMC, complete noninterference, production readiness, full
external-defence equivalence, or AgentDojo efficacy from weak
small-model runs.

### Biba positioning

Fix the missing classical lineage. Do not claim low-water-mark authority
attenuation itself as novel.

Working framing:

> Principal Context follows a low-water-mark intuition: incorporating
> additional, potentially lower-authority influence cannot increase
> effective authority. Unlike classical Biba integrity levels, ITES
> tracks authenticated contributing principals and derives permitted
> parameterized actions by querying/intersecting their permissions in an
> external organisational ACS. Permissions may be incomparable and
> resource/argument sensitive.

Verify this against the primary Biba source before final
citation/wording. Discuss LOMAC only if primary-source verification is
easy and useful.

### Previous preprint

It was not published on arXiv or elsewhere. Reuse its prose directly
where appropriate.

## 3. Source-of-truth order

Inspect before editing: 1. `AGENTS.md`; 2. publication/manuscript
instructions; 3. current claim ledger; 4. `docs/evidence/STATUS.md`; 5.
canonical security model; 6. SLED/SLED-V docs; 7. current manuscript; 8.
retained result JSON/manifests; 9. previous preprint source if present;
10. repository literature/related-work material.

Evidence precedence: retained machine-readable results \> claim ledger
\> status \> prose docs \> old manuscript.

If sources disagree, use the more conservative claim and record the
mismatch for tomorrow.

If old preprint LaTeX is absent, do not reconstruct it from PDF. Reuse
repository prose and leave a non-rendering handoff note for
human/preprint-source insertion.

## 4. Required deliverables

### D1 --- Dedicated FLMSec source

Create a workshop entry point following repository conventions,
preferably `research/publications/flmsec_2026/main.tex`. Do not
overwrite the fourth-year manuscript.

### D2 --- Anonymous default build

No author/institution names, acknowledgements, identifying emails,
public identifying GitHub URL, or identifying PDF metadata. Provide a
separate camera-ready mode only if trivial; anonymous is the tested
default.

### D3 --- `SUBMISSION_CHECKLIST.md`

Include: - \<=8 main-text pages excluding references/appendix; - double
blind; - anonymous supplementary/linked material; - no
acknowledgements; - anonymized self-citations; - OpenReview
conflicts/metadata; - NeurIPS paper checklist present; - PDF metadata
audit; - no placeholders; - citations resolve; - claims
evidence-backed; - clean build.

Current NeurIPS 2026 guidance says the checklist is mandatory and
omission can cause desk rejection. Keep it unless the actual FLMSec
submission template/OpenReview instructions explicitly override this.

### D4 --- Claim/evidence map

Map:
`claim -> manuscript location -> evidence artifact -> allowed wording -> limitation`.

### D5 --- `NEXT_REVIEW_2026-08-26.md`

List only unresolved high-value issues, uncertain citations,
page-pressure decisions, failed tasks, evidence not yet integrated, and
questions for tomorrow's review.

## 5. Manuscript implementation specification

### Abstract

Target \~170--220 words, heavily reuse the preprint.

It must cover: 1. multi-principal inputs + privileged actions; 2. why
model-level PI resistance does not establish stable system security
under arbitrary model behaviour; 3. PE as the system-boundary objective;
4. Principal Context/ITES; 5. maximality + monotonicity; 6. SLED/SLED-V;
7. only current, retained evidence; 8. exact scope.

Do not enumerate repository subsystems. If quantitative evidence cannot
be safely generated tonight, omit numbers rather than invent/manual-copy
them.

### Introduction

Reuse the preprint's arc:

1.  Agents consume multi-origin information and take externally visible
    actions.
2.  Adaptive PI motivates security independent of malicious-language
    recognition.
3.  Reframe PI as one route to PE.
4.  Principal Context: every influencing principal constrains authority.
5.  Fundamental-limit angle: allowing an action outside the permission
    intersection violates the stated PE objective; extra utility
    requires changed authority/policy/property.
6.  SLED/SLED-V validates system-level semantics independently of
    attack-string success.
7.  Exactly 3--4 contribution bullets.

Remove "fourth-year", Part B and project-history framing.

### Related work

Repair substantially.

**Classical integrity/IFC/access control:** Biba prominently;
distinguish integrity labels, access control, provenance and Principal
Context. Add LOMAC only if useful and verified.

**System-level LLM security:** verify primary sources for Dual
LLM/design patterns, CaMeL, Progent, PACT, and FORGE/PCAS if exact
claims are available. For each ask: property, tracked information,
authority source, trusted components, model dependence,
proof/evaluation.

**Evaluation/verification:** contrast finite attack benchmarks with
property checking. AgentDojo is complementary empirical evaluation, not
something SLED "replaces".

Avoid priority claims and survey sprawl.

### Security model

Reuse preprint formalism unless current canonical semantics require
correction.

Define `U, A, D, P, W, R, E`, Principal Context/influence, and PE.

State TCB explicitly: - authenticated/conservatively sound provenance; -
correct ACS answers; - correct reference monitor/effect mediation; -
arbitrary/untrusted LLM.

State out-of-scope items: forged provenance/identity, ACS
misconfiguration, mediator bypass, DoS/side channels unless modeled, and
user-intent correctness.

### ITES / Principal Context

Preserve preprint: - provenance accumulation; - authorization
intersection; - read rule; - maximal-safe-authorization theorem; -
authority monotonicity; - PE-prevention corollary.

Add a concise Biba relationship paragraph near monotonicity.

Only add argument-sensitive authorization if it fits without
destabilizing notation: parameterized actions already allow the ACS
decision to include resource/argument selectors, and provenance of
authority-bearing values must not be discarded.

### SLED / SLED-V

Keep the preprint's SLED motivation, but update implementation
description.

Separate: - SLED: explicit finite operational/state exploration; -
SLED-V: verification IR, solver-backed checks, reductions/property
checks.

Use exact repository verdict terminology. Do not imply every backend
proves unbounded safety.

### Evaluation

Integrate only retained evidence, in this priority: 1. canonical ITES
finite-model result; 2. seeded defective monitors and shortest
counterexamples; 3. reference-interpreter/Z3 agreement; 4. COI verdict
preservation/witness lifting; 5. property-relative comparative finite
model if unambiguous; 6. bounded observational confidentiality if
concise; 7. AgentDojo/planning only in appendix/supporting discussion.

The original \~1.5M trace result can remain as historical/reproduction
evidence but should not carry the main security argument.

Prefer one compact main table:
`Check | Scope | Expected | Result | Evidence type`.

Every row must be generated from or directly traceable to retained
evidence.

### Discussion

Must cover:

**Security--utility frontier:** under fixed `P` and PE, the intersection
is maximal. Recovering more utility requires explicit delegation/ACS
mutation, trusted declassification/endorsement, or a different security
objective.

**Biba relationship:** similarity and precise difference, without
novelty inflation.

**Model-level vs system-level:** complementary; model robustness can
improve utility while authorization security remains system-enforced.

**Limitations:** provenance/ACS TCB, abstraction/conformance gap,
bounded verification where applicable, conservatism.

### Conclusion

Reuse and shorten preprint conclusion. End on the formal objective,
authority from provenance + ACS, maximality/fundamental trade-off, and
reproducible verification.

## 6. Citation work

Do not conduct another broad landscape search tonight.

P0 primary-source checks: 1. Biba 1977; 2. CaMeL; 3. Dual
LLM/design-pattern source used; 4. Progent; 5. PACT; 6.
benchmark/evaluation source if used; 7. preserve existing PI citations
unless clearly incorrect.

Use original papers/proceedings. Never cite AI-generated reports. Omit a
contemporary system if its exact characterization cannot be verified.

## 7. NeurIPS checklist preparation

Use the 2026 template. Answer accurately, not strategically.

Ensure: - claims and abstract match evidence; - limitations section
exists; - theorem assumptions/proofs are stated, with long proofs in
appendix if needed; - exact finite models, bounds, solver/backend
versions and reproduction commands are documented; - identifying GitHub
is not linked during double-blind review; - deterministic verification
may make statistical significance N/A, with explanation; - any
stochastic LLM result changes that answer; - compute details correspond
only to experiments actually reported; - societal-impact note
acknowledges conditional guarantees and deployment risk from incorrect
provenance/ACS.

## 8. Lightweight submission tooling

### Placeholder audit

Fail if rendered/source manuscript contains `TODO`, `TBD`, `FIXME`,
`generated result pending`, `citation needed`, `???`, or obvious
placeholder markers. Permit only explicitly whitelisted non-rendering
internal comments.

### Anonymity audit

Fail on author names, Oxford/Keble, identifying emails, `RayaBuckley`,
public identifying GitHub URLs, acknowledgements, and identifying
project-history text. Keep allowlist narrow.

### Quantitative-result handling

Prefer LaTeX macros generated from retained JSON. If this cannot be
implemented quickly, do not build a large framework: either make a tiny
checked extractor or omit numbers until tomorrow.

### One paper command

Document one command that validates source, runs anonymity/placeholder
checks, builds PDF, reports page count, and checks checklist presence.
Full repository validation can remain a separate final command.

## 9. Explicit non-goals tonight

Do not: - activate delegation; - redesign planning; - add
benchmarks/providers; - refactor SLED; - add solver backends; - chase an
unbounded proof; - run expensive LLM experiments before the manuscript
gate; - cosmetically refactor the repository; - rewrite already-good
preprint prose for novelty's sake; - turn the paper into a feature
list; - invent citations/results/theorem claims; - link identifying
GitHub material.

## 10. Two-hour execution order

### 0--15 min: inspect/freeze evidence

Read canonical instructions, locate manuscript/preprint, inspect claim
ledger/status, identify retained headline artifacts, create FLMSec
structure and claim map.

### 15--40 min: establish paper

Reuse preprint structure/prose, set working title, anonymous author
block, update abstract/contributions, remove project-status framing.

### 40--70 min: Biba/related-work repair

Verify Biba primary source, add low-water-mark lineage, update only
high-value system-level comparisons, tighten novelty.

### 70--95 min: evidence integration

Replace stale results; insert one traceable table; include
defects/checker agreement and comparative result only if unambiguous;
state bounds precisely.

### 95--110 min: compliance

Add checklist, internal submission checklist, anonymity/placeholder
audit, build and page-count check.

### 110--120 min: handoff

Run manuscript validation and create `NEXT_REVIEW_2026-08-26.md` with
page count, build status, unresolved citations, uncertain claims,
missing results, proposed cuts and top questions. Commit as one coherent
workshop-preparation commit following repository guidance.

If time expires, stop at a coherent checkpoint rather than starting
another subsystem.

## 11. Minimum acceptance gate

-   [ ] Dedicated FLMSec manuscript exists and builds.
-   [ ] Anonymous by default.
-   [ ] Preprint's polished theory narrative is the backbone.
-   [ ] Biba/low-water-mark lineage is accurate and explicit.
-   [ ] No stale "results pending" statements.
-   [ ] PE definition and TCB explicit.
-   [ ] Maximality and monotonicity present.
-   [ ] SLED/SLED-V distinction accurate.
-   [ ] Strongest deterministic retained evidence integrated.
-   [ ] Finite/bounded scope stated for all relevant claims.
-   [ ] Main paper \<=8 pages excluding references/appendix.
-   [ ] NeurIPS checklist present/prepared.
-   [ ] No identifying repository link or author information.
-   [ ] Submission checklist exists.
-   [ ] Claim/evidence map exists.
-   [ ] Noon-review handoff exists.

Stretch goals only after this gate: related-work comparison table,
generated result macros, counterexample figure, COI scaling experiment,
anonymous supplementary artifact.

## 12. Default answers to likely coder questions

**Preprint or fourth-year manuscript?** Preprint for prose/theory;
current repository for semantics/evidence.

**Call the paper Conflux?** No. Principal Context/ITES + SLED/SLED-V are
the research objects.

**Make SLED-V primary?** No for FLMSec. Principal Context and the
fundamental security--utility result are primary; SLED-V strengthens
validation/reproducibility.

**Does Biba undermine novelty?** No, but it constrains the novelty
claim. Treat Biba as the classical foundation and state the exact
adaptation.

**Fully formalize newer extensions?** No.

**Delegation?** Discussion only as explicit ACS/authority change.

**AgentDojo main experiment?** No with current weak small-model utility.

**Keep 1.5M traces?** Yes if useful, but not as primary security
evidence.

**New large experiment?** No until the manuscript/compliance/evidence
gate is complete.

**Link GitHub?** No identifying link under double blind.

**Checklist?** Yes under current NeurIPS 2026 guidance unless FLMSec
explicitly overrides it.

**Appendix?** Proof details/configuration yes; essential acceptance
arguments no.

**Uncertainty?** Fail closed: conservative wording + noon-review
handoff.

## 13. Questions deliberately deferred to tomorrow's review

1.  Is the Biba distinction technically precise enough?
2.  Is maximal safe authorization the best theorem to foreground?
3.  Does PE need refinement for delegation/consent/authority-bearing
    arguments in this paper?
4.  Which contemporary systems belong in main text?
5.  Which SLED-V result belongs in the abstract?
6.  Is the comparative Dual-LLM abstraction fair enough?
7.  Is COI scaling worth remaining time?
8.  Is runtime↔IR differential conformance needed before submission?
9.  What should be cut for the eight-page limit?
10. Are checklist answers fully supported?
11. Should an anonymous evidence/code artifact be prepared?
12. What final title/abstract best matches the finished evidence?

The overnight objective is to make tomorrow's review about these
research-level finishing decisions, not manuscript migration, stale
prose, anonymity, missing Biba context, or evidence synchronization.
