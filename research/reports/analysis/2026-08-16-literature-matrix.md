# Classical Integrity and IFC Literature Matrix

**Date:** 16 August 2026
**Status:** Research analysis; not a canonical specification
**Source:** Plan step 2 — structured comparison of classical integrity/IFC works
**Recommended repository path:**
`reports/analysis/2026-08-16-literature-matrix.md`

## Purpose

This matrix supports the novelty audit (`2026-08-16-novelty-audit.md`) and
manuscript positioning by systematically comparing classical integrity and
information-flow-control works against Conflux. Each entry records the
relationship to Conflux and the novelty risk (whether the work anticipates a
Conflux mechanism).

Fields follow the foundational literature analysis
(`2026-08-13-foundational-security-literature.md` §31 and §29).

Primary-source verification is recorded explicitly; entries marked
`unverified` have not been checked against the original publication.

## Priority A works

### 1. Biba (1977) — Integrity Considerations for Secure Computer Systems

| Field | Value |
|---|---|
| Work | Biba, K. J. |
| Year | 1977 |
| Stream | Integrity models |
| Security objective | Prevent contamination of high-integrity objects by low-integrity information |
| Label/provenance model | Integrity levels assigned to subjects and objects; hierarchical classification |
| Authority model | High-integrity subjects may write high-integrity objects; low-water-mark reduces subject integrity after reading lower-integrity information |
| Downgrading model | Not addressed in original (no endorsement mechanism) |
| Formal guarantee | No-unauthorised-write under integrity lattice |
| Implementation | Theoretical model; no direct implementation |
| Relation to Conflux | Direct structural ancestor of ITES authority intersection. Low-water-mark variant: consuming lower-integrity information reduces future effects. Conflux enriches with principal identities + existing ACS. |
| Novelty risk | High — core contamination mechanism is directly anticipated |
| Primary source verified | No (unverified) |

### 2. LOMAC — Low-Water-Mark Integrity for Commodity Operating Systems

| Field | Value |
|---|---|
| Work | Fraser, T. |
| Year | 1999–2000 |
| Stream | Dynamic integrity enforcement |
| Security objective | Prevent low-integrity processes from modifying high-integrity objects in commodity OS |
| Label/provenance model | Dynamic integrity labels on processes; demoted after reading low-integrity data |
| Authority model | Process integrity level determines write authority; low-water-mark demotion after read |
| Downgrading model | Not directly addressed; label creep is the primary engineering concern |
| Formal guarantee | No-unauthorised-write under dynamic integrity policy |
| Implementation | Linux kernel module; deployed in commodity OS |
| Relation to Conflux | Closest systems-level analogue. Label creep in LOMAC directly corresponds to Principal Context contamination in Conflux. Conflux adds per-principal identity, action-specific authority, and planning to avoid contamination. |
| Novelty risk | High — dynamic contamination tracking with label creep is directly anticipated |
| Primary source verified | No (unverified) |

### 3. Denning (1976) — A Lattice Model of Secure Information Flow

| Field | Value |
|---|---|
| Work | Denning, D. E. |
| Year | 1976 |
| Stream | Confidentiality / information-flow control |
| Security objective | Prevent information flow from high to low security classes |
| Label/provenance model | Security classes form a lattice; flows must respect the partial order |
| Authority model | Flow policy: information may flow only to dominating classes |
| Downgrading model | Not addressed (original formulation) |
| Formal guarantee | Lattice-based noninterference for flows |
| Implementation | Theoretical model |
| Relation to Conflux | Conflux's authority intersection over permission sets is a meet in the powerset lattice. The lattice structure is not unique to Conflux. Denning provides the mathematical vocabulary for combined labels. |
| Novelty risk | Medium — lattice structure is anticipated; application to permission sets is a standard instance |
| Primary source verified | No (unverified) |

### 4. Sabelfeld & Myers (2003) — Language-Based Information-Flow Security

| Field | Value |
|---|---|
| Work | Sabelfeld, A. & Myers, A. C. |
| Year | 2003 |
| Stream | Language-based IFC |
| Security objective | Prevent explicit and implicit information flows from high to low |
| Label/provenance model | Security labels on variables/channels; static or dynamic enforcement |
| Authority model | Program operations respect label ordering; declassification is explicit |
| Downgrading model | Declassification: controlled relaxation of confidentiality (what, who, where, when) |
| Formal guarantee | Noninterference (with exceptions for declassification) |
| Implementation | Jif (Java + IFC), FlowCaml, etc. |
| Relation to Conflux | Provides vocabulary for explicit/implicit flows, overapproximation vs. exact influence, and the three-way distinction (security provenance / exposure / attribution). Conflux's "influence" is an intentional overapproximation in Sabelfeld-Myers terms. |
| Novelty risk | Medium — vocabulary and conceptual framework directly applicable; Conflux's specific overapproximation is consistent with IFC practice |
| Primary source verified | No (unverified) |

### 5. Myers & Liskov — Decentralized Information-Flow Control

| Field | Value |
|---|---|
| Work | Myers, A. C. & Liskov, B. |
| Year | 1997 (conference), 2000 (journal) |
| Stream | Decentralized IFC |
| Security objective | Allow multiple principals to control information flow without centralised authority |
| Label/provenance model | Labels contain owners and readers; principals control their own policies; acts-for hierarchy |
| Authority model | Each principal controls who may read its data; declassification requires owner authority |
| Downgrading model | Declassification by data owners; acts-for delegation of authority |
| Formal guarantee | Decentralized noninterference (with declassification) |
| Implementation | Jif (Java + decentralized labels) |
| Relation to Conflux | Closest IFC system to "principal-sensitive authority." Decentralized IFC retains principal identities in labels and derives access from policy. Key question: does Jif's acts-for hierarchy + owner-controlled declassification anticipate Conflux's principal-identity + ACS-derived authority? This is the most important prior-art comparison. |
| Novelty risk | High — may contain prior art for "principal identities in labels + authority from policy" |
| Primary source verified | No (unverified) |

### 6. Sabelfeld & Sands — Declassification

| Field | Value |
|---|---|
| Work | Sabelfeld, A. & Sands, D. |
| Year | ~2001 (survey), various dates |
| Stream | Declassification |
| Security objective | Controlled relaxation of confidentiality policies |
| Label/provenance model | Extends IFC labels with declassification dimensions (what, who, where, when) |
| Authority model | Declassification requires designated authority; controlled release beyond confinement |
| Downgrading model | Central topic: taxonomy of declassification dimensions and security guarantees |
| Formal guarantee | Various: noninterference modulo declassification, intransitive noninterference |
| Implementation | Conceptual framework |
| Relation to Conflux | Directly maps to Conflux's visibility/disclosure hierarchy. Level 3 (controlled release) is declassification. The "who may authorise" dimension maps to release authority; robust declassification (Zdancewic) adds attacker-influence conditions. |
| Novelty risk | Medium — the conceptual mapping is strong; Conflux's specific mechanism for controlled release is future work |
| Primary source verified | No (unverified) |

### 7. Zdancewic & Myers — Robust Declassification

| Field | Value |
|---|---|
| Work | Zdancewic, S. & Myers, A. C. |
| Year | 2001 (workshop), later dates |
| Stream | Robust declassification |
| Security objective | Prevent attackers from manipulating what/when trusted code declassifies |
| Label/provenance model | Extends IFC with robustness condition: attacker cannot influence declassification decisions |
| Authority model | Declassification authority must be independent of attacker influence |
| Downgrading model | Robust declassification: controlled release that resists adversarial influence |
| Formal guarantee | Robustness: attacker cannot cause declassification |
| Implementation | Conceptual framework; some Jif integration |
| Relation to Conflux | Directly relevant to prompt injection. A trusted user may be authorised to release information, but an attacker-authored document should not influence the LLM into exercising that authority. A future disclosure rule should ask both whether release is authorised and which principals may influence the decision. |
| Novelty risk | Low-Medium — concept is directly applicable; Conflux does not yet implement a robustness condition for disclosure |
| Primary source verified | No (unverified) |

### 8. Askarov & Myers — Attacker Control and Impact

| Field | Value |
|---|---|
| Work | Askarov, A. & Myers, A. C. |
| Year | 2007 (CSF), later |
| Stream | Attacker influence / IFC |
| Security objective | Characterise what attackers can control and what impact that control has on confidentiality |
| Label/provenance model | Extends IFC with attacker-control and attacker-impact classifications |
| Authority model | Distinguishes what an attacker can influence from what information is released |
| Downgrading model | Relevant to controlled exceptions to monotonicity |
| Formal guarantee | Attacker-control / attacker-impact classification |
| Implementation | Conceptual framework |
| Relation to Conflux | Directly relevant to Principal Context, attribution, trusted transformations, and prompt injection. Asks whether adversarial influence can control policy exceptions. Maps to the question of whether delegation/disclosure can be exploited. |
| Novelty risk | Medium — the attacker-control framework is directly applicable to Conflux's multiple exceptions to monotonicity |
| Primary source verified | No (unverified) |

### 9. Cecchetti, Myers & Arden — Nonmalleable Information Flow

| Field | Value |
|---|---|
| Work | Cecchetti, E., Myers, A. C. & Arden, O. |
| Year | 2017 (POPL), later |
| Stream | Nonmalleable IFC |
| Security objective | Prevent attackers from exploiting both confidentiality and integrity downgrading simultaneously |
| Label/provenance model | Extends IFC with nonmalleability condition |
| Authority model | Prevents adversarial manipulation of both declassification and endorsement |
| Downgrading model | Central topic: coordinated integrity + confidentiality exceptions must not be exploitable |
| Formal guarantee | Nonmalleability: attacker cannot exploit downgrading |
| Implementation | Jif extensions |
| Relation to Conflux | Conflux is moving toward multiple exceptions to simple monotonicity (delegation, disclosure, trusted transformations, consent, policy updates). Nonmalleable IFC asks whether these exceptions can be exploited by adversarial influence. Relevant to future verification of delegation/disclosure. |
| Novelty risk | Low-Medium — conceptually applicable; Conflux has not yet implemented nonmalleability checks |
| Primary source verified | No (unverified) |

## Priority B works (summary)

| Work | Year | Stream | Key relevance to Conflux | Novelty risk |
|---|---|---|---|---|
| Asbestos (Vandebogart et al.) | 2007 | Dynamic IFC OS | Process-level labels; label demotion on read | Medium |
| HiStar (Zeldovich et al.) | 2006 | Dynamic IFC OS | Decentralised labels in OS; information containment | Medium |
| Flume (Krohn et al.) | 2007 | IFC for distributed systems | Pipe-based label propagation; policy modules | Medium |
| DStar (Zeldovich et al.) | 2008 | Distributed IFC | Decentralised labels across nodes | Low-Medium |
| LIO (Stefan et al.) | 2011 | Dynamic IFC (Haskell) | Labeled IO monad; floating-label approach similar to LOMAC | Medium |
| CamFlow (Pasquier et al.) | 2017 | Provenance capture | Linux-level provenance for policy enforcement | Medium |

Each Priority B system implements some form of dynamic label propagation
with authority restriction after reading sensitive data. The engineering
tension (security vs. utility/label creep) is shared with Conflux. A
targeted search should check whether any Priority B system computes sink
permissions from *named source principals' existing authorisation*.

## Priority C works (summary)

| Work | Stream | Key relevance to Conflux |
|---|---|---|
| Saltzer & Schroeder (1975) | Security principles | Complete mediation, least privilege, reference-monitor principles |
| Harrison-Ruzzo-Ullman | Access-control safety | Safety undecidability for unrestricted dynamic ACS; supports SLED-V's restricted fragment |
| Confused deputy (Hardy, 1988) | Capability security | Conflux attenuates deputy's authority by provenance; parallels capability-based approaches |
| Capability attenuation | Object capability model | Scoped delegation is analogous to attenuated capabilities |
| Rushby — Noninterference | Formal verification | Channel-control security policies; relevant to observational confidentiality |

## Novelty risk summary

| Risk level | Works | Implication for Conflux |
|---|---|---|
| High | Biba, LOMAC, Myers & Liskov (Dec-IFC) | Core mechanism (monotonic contamination with principal identity) is directly anticipated or closely paralleled. Must acknowledge and identify specific enrichments. |
| Medium | Denning, Sabelfeld & Myers, Sabelfeld & Sands, Askarov & Myers, Priority B systems | Vocabulary, concepts, and some mechanisms are anticipated. Conflux's specific combination and application may be distinguishable but requires careful argument. |
| Low-Medium | Zdancewic & Myers, Cecchetti et al., Priority C | Concepts are applicable but Conflux has not yet implemented the corresponding mechanisms. No direct prior art for the specific Conflux instantiation. |

## Open questions for targeted search

1. Does any Dec-IFC system (Jif, etc.) compute effective authority as the
   intersection of *named principals' existing ACS permissions*?
2. Does any dynamic IFC system (LOMAC, LIO, Asbestos, HiStar) use
   *authenticated source identities* rather than *integrity labels* to
   derive *sink permissions*?
3. Has anyone applied low-water-mark policies over *permission sets from an
   existing organisational ACS* rather than *integrity levels*?
4. Are there compound-principal or conjunctive-principal authorization
   systems that intersect permissions from named principals?
5. Do any provenance-based authorization systems derive action authority
   from the *current* ACS state of identified source principals?

Until these questions are resolved, Conflux's candidate distinctions
(principal identities + existing ACS + parameterised authority) remain
hypotheses, not established novelty.
