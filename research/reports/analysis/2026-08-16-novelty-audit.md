# Novelty Audit: Claims Affected by Classical IFC/Integrity Precedent

**Date:** 16 August 2026
**Status:** Research analysis; not a canonical specification
**Source:** Plan step 1 — search repository for claims made unsafe by classical IFC/integrity precedent
**Recommended repository path:**
`reports/analysis/2026-08-16-novelty-audit.md`

## Method

1. Enumerate all claims in `docs/evidence/CLAIMS.md`, `paper/iclr2026_conference.tex`,
   `manuscript/conflux_fourth_year_2026.tex`, `docs/research/RESEARCH_OVERVIEW.md`,
   `docs/reference/SECURITY_MODEL.md`, `docs/research/RELATED_WORK.md`, and
   `docs/decisions/012-foundational-security-lineage.md`.
2. For each claim, assess whether classical IFC/integrity precedent (Biba,
   LOMAC, Denning, decentralized IFC, taint/provenance systems, robust
   declassification, nonmalleable IFC) renders the claim unsafe, partially
   anticipated, or genuinely novel.
3. Classify each claim: **unsafe** (prior art directly contradicts or
   subsumes), **partially anticipated** (classical precedent provides a
   structural analogue but Conflux adds a distinguishable enrichment), or
   **survives** (no close prior art identified in current knowledge).
4. Record qualifications needed and remaining search actions.

## Audit results

### A1. "Authority decreases monotonically as influence accumulates"

**Location:** `paper/iclr2026_conference.tex:72`, Theorem 2 (Authority Monotonicity); `CLAIMS.md:06`

**Verdict: Partially anticipated**

Classical precedent: Biba low-water-mark policies reduce a subject's
effective integrity after it observes lower-integrity information,
restricting future high-integrity effects. This is the direct structural
ancestor. Conflux's monotonic authority intersection over permission sets
is a meet in the powerset lattice, a standard mathematical operation.

Qualification needed: The mathematical result (Theorem 2) remains correct.
Its *novelty* is unsafe. The dissertation should position monotonic authority
reduction as an instance of low-water-mark contamination enriched by
principal-sensitive provenance, not as a new mechanism class.

Remaining search: Determine whether any prior system computes the meet over
*permission sets derived from authenticated principal identities* rather
than *integrity labels*. If such a system exists, this drops to "unsafe."

### A2. "ITES is a provenance-based enforcement mechanism that derives effective authority from information provenance and existing access-control policies"

**Location:** `paper/iclr2026_conference.tex:81` (contribution 2); `paper/iclr2026_conference.tex:115`

**Verdict: Partially anticipated**

Classical precedent: Taint-tracking systems (LOMAC, Asbestos, HiStar, Flume,
LIO) combine source labels or provenance with policy to derive sink
permissions. Source-set taint produces combined label `{A, B}` from sources
A and B; Conflux then intersects their ACS permissions. The provenance-union
step is directly anticipated by taint/provenance literature. The
authority-intersection step is a meet over permission sets, structurally
analogous to low-water-mark.

However, the *specific combination* of authenticated principal identities
with existing-ACS-derived action authority may be distinguishable from
systems that use generic trust labels, integrity levels, or
application-specific policy languages. This distinction requires targeted
prior-art search against decentralized IFC, provenance-based authorization,
and compound-principal systems.

Qualification needed: Avoid presenting provenance-based restriction as
novel without qualification. The enrichment (principal identities + existing
ACS) is a candidate distinction but remains a hypothesis until prior-art
search confirms it.

Remaining search: provenance-based authorization systems; source-sensitive
access control; compound-principal authorization; decentralized IFC with
rich labels.

### A3. "ITES is the maximally permissive authorisation preserving PE safety" (Maximal Secure Authorisation)

**Location:** `paper/iclr2026_conference.tex:327-371` (Theorem 1); `SECURITY_MODEL.md`

**Verdict: Survives (within model)**

This is a mathematical result about the specific PE-safety definition and
the intersection rule. Within the stated model, the proof is correct: any
strict superset of the intersection admits PE. This is not a novelty claim
about a mechanism; it is a correctness proof about a specific construction.

Potential subtlety: the result holds *for the given definition of PE*.
If a different security objective (e.g., noninterference) is adopted, the
intersection rule may not be maximal. The paper should be clear about which
security objective the maximality claim refers to.

Qualification needed: None for the mathematical claim. Ensure that
maximality is stated relative to the PE definition, not as a general
optimality claim.

### A4. "ITES prevents privilege escalation regardless of how influence was introduced"

**Location:** `paper/iclr2026_conference.tex:419`

**Verdict: Partially anticipated (as a reference monitor)**

The guarantee follows from complete mediation under the stated assumptions
(correct enforcement, provenance, ACS). This is the classical reference
monitor argument applied to LLM agents. The guarantee is sound within the
model but the architectural pattern (untrusted code → mediation boundary →
trusted execution) is standard.

Qualification needed: Position ITES as a reference monitor for LLM agents
with principal-sensitive authority, not as a fundamentally new security
architecture. The contribution is the *instantiation* of reference-monitor
principles for the LLM-agent setting with a specific contamination model,
not the reference-monitor concept itself.

### A5. "Security depends only upon correct provenance tracking, access-control enforcement, and the access-control system itself. Language-model behaviour affects utility but not security."

**Location:** `paper/iclr2026_conference.tex:113`

**Verdict: Survives (as a design property)**

This is a design property of the ITES architecture, not a novelty claim.
It is the natural consequence of the reference-monitor structure and the
worst-case threat model. It is correct within the stated assumptions. No
classical precedent makes this claim "unsafe" — it is simply the
security-by-design consequence of complete mediation under worst-case model
behaviour.

Qualification needed: None. This is accurately stated.

### A6. "Authority-bearing action arguments cannot borrow authority from content or consent"

**Location:** `CLAIMS.md:12`

**Verdict: Survives**

This is a fourth-year implementation claim about trusted argument roles and
pointwise Principal checks. It addresses the confused-deputy problem at the
argument level. While capability-based approaches address the confused deputy
more broadly, the specific mechanism (trusted argument roles with
selector-level policy checks) is a concrete implementation contribution.

Qualification needed: Position against capability-based confused-deputy
approaches and argument-sensitive IFC. The implementation is novel in its
specific form; the general principle of least authority at the argument
level has prior art.

### A7. "Provenance is not a read ACL" (read policy is independent from provenance)

**Location:** `CLAIMS.md:07`; `CHANGE_CATALOG.md` (BUG-002)

**Verdict: Survives**

This is an implementation invariant: read access and provenance-based
authority are separate decisions. Classical IFC systems sometimes conflate
read access with information flow; Conflux explicitly separates them. This
is a design decision, not a novelty claim.

Qualification needed: None. Accurately stated as an implemented invariant.

### A8. "Influence is never silently removed by nested execution" (Provenance monotonicity)

**Location:** `CLAIMS.md:06`

**Verdict: Partially anticipated**

Classical precedent: Conservative information-flow tracking (Biba, LOMAC,
taint systems) does not silently remove labels. Confluence of provenance is
the standard conservative assumption. The specific mechanism (immutable
provenance in nested LLM/tool/plan execution) is an instantiation.

Qualification needed: Acknowledge that conservative label/flow propagation
is standard. The contribution is applying it with authenticated principal
identities in the LLM-agent execution model.

### A9. "SLED evaluates defences independently of language-model behaviour"

**Location:** `paper/iclr2026_conference.tex:83` (contribution 3)

**Verdict: Partially anticipated**

Model checking and exhaustive state-space exploration for security
properties are well-established. SLED's specific contribution is treating
the LLM as an adversarial component and exhaustively exploring the *system*
state space under worst-case model behaviour. The general technique
(exhaustive exploration of a finite transition system) is standard model
checking. The application to evaluating LLM-agent system-level defences is
a specific instantiation.

Qualification needed: Position SLED as a bounded model checker for
LLM-agent defences, not as a fundamentally new evaluation paradigm. The
contribution is the adversarial-model abstraction and the specific
transition-system design for the LLM-agent setting.

### A10. "Authorised reads do not establish noninterference"

**Location:** `EVALUATION.md` (Confidentiality hierarchy Level 1 vs Level 2); `RELATED_WORK.md`

**Verdict: Survives (as a non-claim)**

This is explicitly stated as a *limitation*, not a novelty claim. The
current visibility model provides access safety (Level 1); observational
confidentiality (Level 2) and controlled release (Level 3) are proposed
future work. The hierarchy correctly distinguishes these.

Qualification needed: Ensure no documentation implies that authorised reads
*do* establish noninterference. The archived paper's confidentiality
mechanism (read-access check) should be clearly labelled as access safety,
not end-to-end confidentiality.

### A11. "More broadly, ITES is inspired by information-flow tracking, but differs in using provenance to derive effective authority under an existing access-control system rather than preventing information flows themselves."

**Location:** `paper/iclr2026_conference.tex:115`

**Verdict: Partially anticipated**

The distinction between "preventing flows" and "deriving authority from
provenance" is meaningful but may not be sharp. Decentralized IFC and
provenance-based authorization systems also use principal/label information
to make access decisions. The specific difference — deriving authority from
*existing* ACS permissions rather than introducing a *new* policy language
or trust classification — is a candidate distinction, but decentralized IFC
systems can also reference existing organisational structures (acts-for
relations, principal hierarchies).

Qualification needed: This claim needs careful comparison against
decentralized IFC (Myers & Liskov), Jif, and systems where labels encode
principal identities and policies reference organisational authority. The
distinction "no new policy language" may not hold if decentralized IFC
systems also derive decisions from organisational structures.

Remaining search: Decentralized IFC with organisational authority;
Jif label policies; acts-for hierarchies; provenance-based authorization
systems that derive sink permissions from source identities.

### A12. "Conflux therefore does not claim priority for system-level mediation, provenance or privilege control"

**Location:** `manuscript/conflux_fourth_year_2026.tex:62`

**Verdict: Survives (as an explicit non-claim)**

The fourth-year manuscript already disclaims priority for these broad
categories. This is correct and should be retained.

### A13. "Privilege escalation, rather than prompt injection, is the appropriate system-level security objective"

**Location:** `paper/iclr2026_conference.tex:79` (contribution 1)

**Verdict: Partially anticipated**

Reframing prompt injection as a privilege-escalation instance is a useful
contribution to the LLM-agent literature. However, privilege escalation as
a security objective is standard in systems security. The contribution is
the *application* of this reframing to LLM agents, not the concept of
privilege escalation itself.

Qualification needed: Acknowledge that privilege escalation is a classical
security objective. The contribution is identifying it as the appropriate
system-level objective for LLM-agent security and defining it precisely in
terms of influencing principals and existing ACS permissions.

### A14. "Delegation should not be called endorsement; delegation changes authority, endorsement changes the integrity status of information"

**Location:** `ADR 012`; `RELATED_WORK.md`; `foundational-security-literature.md`

**Verdict: Survives**

This is a conceptual distinction, not a novelty claim. It correctly
identifies that delegation and endorsement operate on different things
(authority vs. information trust). This is consistent with the classical
literature.

Qualification needed: None. This is an accurate terminological distinction.

### A15. Candidate distinctions that "may survive prior-art search"

**Location:** `ADR 012:46-52`; `RESEARCH_OVERVIEW.md:200-205`

These are explicitly stated as hypotheses:
1. Retaining authenticated principal identities (not just trust labels)
2. Deriving effective authority from the organisation's current ACS
3. Parameterised and argument-sensitive action authority
4. Verifying the security layer under arbitrary model proposals

**Verdict: Provisional — require prior-art search**

Each is a candidate distinction, not an established novelty claim. The
foundational literature analysis correctly identifies them as requiring
targeted search. Until such searches are complete, they must not be
presented as established contributions.

## Unsafe formulations to avoid

The following formulations are directly contradicted or subsumed by
classical precedent and must not appear in the dissertation or any
canonical documentation:

1. **"ITES introduces the idea that consuming untrusted information should
   reduce future authority."**
   — Unsafe: Biba low-water-mark (1977), LOMAC.

2. **"Once low-privilege information influences a computation, privilege
   cannot later increase."**
   — Unsafe: Low-water-mark contamination is exactly this.

3. **"Using information provenance to constrain subsequent privileged effects
   has no classical precedent."**
   — Unsafe: Taint tracking, provenance-based authorization, LOMAC.

4. **"Permission intersection is fundamentally outside lattice-based IFC."**
   — Unsafe: Intersection is a standard meet in the powerset lattice.

5. **"Existing systems use only binary trust labels whereas Conflux first
   tracks richer security context."**
   — Unsafe: Decentralized IFC, provenance systems, dynamic IFC systems
   use rich labels with multiple principals.

6. **"Authorised reads establish confidentiality."**
   — Unsafe: Authorised reads do not establish noninterference.

7. **"Conflux is the first generalisation of Biba to arbitrary permission
   sets."**
   — Unsafe until targeted prior-art search confirms no prior system
   computes authority as a meet over permission sets from named principals.

## Defensible formulations

1. **"Conflux applies low-water-mark-style contamination to tool-using AI
   agents using authenticated principal provenance and an organisation's
   existing authorization relation. Rather than assigning each input only a
   global integrity level, it retains the principals that may have influenced
   an execution and derives action-specific effective authority from their
   current permissions."**

2. **"Building on this foundation, the project investigates how
   principal-sensitive authority interacts with fine-grained action arguments,
   explicit delegation and consent, controlled disclosure, secure planning,
   attribution, and formal verification under arbitrary model proposals."**

3. **"ITES is a reference monitor for tool-using AI agents: it provides
   complete mediation of privileged effects by a small, analysable mechanism
   that separates untrusted proposal generation from trusted effect
   execution, using principal-sensitive provenance to derive effective
   authority from the organisation's existing ACS."**

These formulations acknowledge the classical lineage while identifying
specific enrichments and the fourth-year research programme. They remain
hypotheses until prior-art search is complete.

## Summary of novelty risk by claim

| ID | Claim | Risk | Action |
|---|---|---|---|
| A1 | Authority decreases monotonically | Partially anticipated | Acknowledge Biba/LOMAC; state enrichment |
| A2 | Provenance-based authority from ACS | Partially anticipated | Search decentralized IFC, provenance authz |
| A3 | Maximal secure authorisation | Survives (math) | State relative to PE definition |
| A4 | Prevents PE regardless of influence source | Partially anticipated | Position as reference monitor instance |
| A5 | Security independent of model behaviour | Survives | Design property, not novelty |
| A6 | Argument authority isolation | Survives | Position against capability approaches |
| A7 | Read policy independent from provenance | Survives | Implementation invariant |
| A8 | Provenance never silently removed | Partially anticipated | Acknowledge conservative IFC |
| A9 | SLED independent of model behaviour | Partially anticipated | Position as bounded model checker instance |
| A10 | Authorised reads ≠ noninterference | Survives (non-claim) | Maintain as limitation |
| A11 | ITES differs from IFC by using provenance for authority | Partially anticipated | Search Dec-IFC, Jif, provenance authz |
| A12 | No claim of priority for mediation/provenance | Survives | Retain |
| A13 | PE as appropriate system-level objective | Partially anticipated | Acknowledge classical PE concept |
| A14 | Delegation ≠ endorsement | Survives | Terminological distinction |
| A15 | Candidate distinctions | Provisional | Require prior-art search |

## Remaining search actions

Before finalising novelty:

1. Search for **provenance-based authorization systems** where sink
   permissions depend on source identities.
2. Search for **compound-principal / conjunctive-principal authorization**
   in decentralized IFC and capability systems.
3. Search for **low-water-mark policies over rich labels or permission
   sets** in dynamic IFC systems (LOMAC, Asbestos, HiStar, Flume, LIO).
4. Search for **source-sensitive access control** in taint and provenance
   enforcement.
5. Search for **decentralized integrity policies** with principal identities
   rather than scalar labels.
6. Re-audit **PACT, Progent, CaMeL, and causal-provenance systems** for
   principal-sensitive authority mechanisms.

Until these searches are complete, no claim should assert the absence of
classical precedent for any mechanism in the "partially anticipated" or
"provisional" categories.

## Relationship to existing documentation

This audit is consistent with and extends:
- `docs/evidence/CLAIMS.md` (Novelty qualification section)
- `docs/decisions/012-foundational-security-lineage.md`
- `docs/research/RELATED_WORK.md` (Foundational security lineage)
- `docs/research/RESEARCH_OVERVIEW.md` (Classical security foundations)
- `reports/analysis/2026-08-13-foundational-security-literature.md` (§20, §31)
