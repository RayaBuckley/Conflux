# Literature Landscape: Cluster Summaries

**Date:** 30 August 2026
**Status:** Research analysis; not a canonical specification
**Corpus:** `research/reports/analysis/literature_corpus.json` (123 entries)

This document groups the 123 tracked sources into six clusters and
summarises each cluster's state of the art, the closest system to
Conflux, and the gap Conflux fills.

## Cluster 1: Classical IFC and Integrity (14 sources)

**Priority A (9):** Biba, LOMAC, Denning, Sabelfeld-Myers, Myers-Liskov,
Sabelfeld-Sands, Zdancewic-Myers, Askarov-Myers, Cecchetti et al.
**Priority C (5):** Saltzer-Schroeder, Bell-LaPadula, Clark-Wilson,
Goguen-Meseguer, Rushby, HRU, Hardy (confused deputy), Lampson
(capabilities).

**State of the art:** Classical IFC provides the formal vocabulary for
information flow, noninterference, declassification, endorsement,
robustness, and nonmalleability. The low-water-mark integrity model
(Biba/LOMAC) is the direct structural ancestor of Conflux's monotonic
authority attenuation. Decentralized IFC (Myers-Liskov) is the closest
classical system to principal-sensitive authority. Attacker-control
theory (Askarov-Myers) and nonmalleable IFC (Cecchetti et al.) provide
the formal framework for reasoning about exceptions to monotonicity.

**Closest to Conflux:** Myers-Liskov's decentralized label model — it
retains principal identities in labels and uses an acts-for hierarchy
for delegation. The key distinction: Conflux derives authority from an
existing organisational ACS rather than introducing a new program-level
policy language.

**Gap Conflux fills:** No classical IFC system connects principal
provenance to an existing organisational ACS, provides argument-level
authority, or addresses LLM-agent prompt injection.

**Verification status:** Askarov-Myers verified to full text; Cecchetti
et al. verified to abstract; 7 papers at scholar_metadata; 5 Priority C
papers unverified.

## Cluster 2: Dynamic IFC Systems (6 sources)

**Priority B:** Asbestos, HiStar, Flume, DStar, LIO, CamFlow.

**State of the art:** OS-level dynamic IFC systems implement information
flow tracking in the kernel, attaching labels to processes, files, and
network endpoints. Label propagation occurs at every system call. These
systems demonstrate that IFC is deployable in practice, not just in
language-level type systems.

**Closest to Conflux:** Flume — applies IFC to standard Unix
abstractions (processes, pipes, files) which parallels Conflux's
application of IFC concepts to agent tool calls. DStar extends IFC
across distributed boundaries with principal delegation.

**Gap Conflux fills:** No OS-level IFC system addresses LLM agents,
prompt injection, or argument-level provenance. All use scalar or
hierarchical labels, not principal-identity-based authority derived from
an existing ACS.

**Verification status:** All 6 unverified; flagged for operator PDF
download. Not available on arXiv.

## Cluster 3: Agent Defences (10 sources)

**Priority A modern (8):** CaMeL, AgentDojo, StruQ, Spotlighting, Progent,
PACT, FORGE, SecAlign.
**Additional:** Design Patterns.

**State of the art:** The agent defence landscape has converged on
system-level mediation (CaMeL, Progent, FORGE), argument-level
provenance (PACT), and model-level fine-tuning (StruQ, SecAlign,
Spotlighting). CaMeL separates control and data flows with capabilities.
Progent uses SMT-verified monotonic confinement. PACT tracks semantic
roles for argument provenance. FORGE enforces Datalog policies via AOP
reference monitoring.

**Closest to Conflux:** PACT — it recognises that prompt injection
becomes dangerous when untrusted content determines an
authority-bearing argument, tracks provenance across replanning steps,
and checks role-specific trust contracts. CaMeL is the strongest
system-level predecessor. Progent's monotonic confinement is the closest
analogue to ITES authority intersection.

**Gap Conflux fills:** No agent defence derives authority from an
existing organisational ACS using named principal identities, provides
bounded formal verification of the security layer, or treats
authorisation, visibility, and consent as separate decisions.

**Verification status:** All 10 verified to primary_source /
abstract_and_key_sections via arXiv abstracts.

## Cluster 4: Benchmarks and Evaluation (5+ sources)

**AgentDojo** (primary), **ASB**, **InjecAgent**, plus several
attack-evaluation and benchmark papers in the corpus.

**State of the art:** AgentDojo (97 tasks, 629 security test cases) is
the primary extensible benchmark for prompt injection attacks and
defences. ASB provides a formal security benchmark. The landscape is
evolving toward adaptive attacks and dynamic evaluation.

**Closest to Conflux:** AgentDojo — Conflux uses it as its primary
comparative benchmark, adding ACS/principal overlays rather than
changing task semantics.

**Gap Conflux fills:** No benchmark measures principal-sensitive
authority, ACS-derived permissions, or bounded verification guarantees.
Conflux adds these as evaluation overlays.

**Verification status:** AgentDojo verified to primary_source.

## Cluster 5: Provenance Systems (3+ sources)

**CamFlow**, **W3C PROV**, **database provenance** papers in corpus.

**State of the art:** Whole-system provenance capture (CamFlow) records
causal history of execution. W3C PROV provides a standard provenance
model. Database provenance tracks data lineage for queries.

**Closest to Conflux:** CamFlow — kernel-level provenance capture that
could inform Conflux's runtime provenance tracking.

**Gap Conflux fills:** No provenance system uses provenance to derive
security authority from an existing ACS. Conflux treats provenance as
authority-bearing context, not just audit trail.

**Verification status:** CamFlow unverified; W3C PROV in corpus.

## Cluster 6: Policy Engines (6+ sources)

**Cedar**, **OPA/Rego**, **Spice/Relationship-based access control**,
**ABAC**, **cloud IAM**.

**State of the art:** Production policy engines (Cedar, OPA) provide
declarative, auditable authorisation. Cedar is designed for
fine-grained ABAC with principal-based policies. OPA provides
general-purpose policy as code.

**Closest to Conflux:** Cedar — its principal-based policy model and
schema validation are the closest production system to Conflux's
principal-sensitive authority. Conflux has a Cedar adapter for live
policy enforcement.

**Gap Conflux fills:** No policy engine provides provenance-derived
authority or bounded verification of the security layer under arbitrary
model proposals.

**Verification status:** Cedar adapter tested; OPA referenced in corpus.

## Summary

| Cluster | Sources | Verified | Closest to Conflux | Key gap |
|---|---|---|---|---|
| Classical IFC | 14 | 2 primary, 7 scholar | Myers-Liskov DLM | No ACS connection, no agents |
| Dynamic IFC | 6 | 0 | Flume | No LLM agents, scalar labels |
| Agent defences | 10 | 10 primary | PACT/CaMeL | No ACS, no verification |
| Benchmarks | 5+ | 1 primary | AgentDojo | No principal-sensitive metrics |
| Provenance | 3+ | 0 | CamFlow | No authority derivation |
| Policy engines | 6+ | 0 | Cedar | No provenance-derived authority |

The Conflux contribution sits at the intersection of all six clusters:
classical IFC provides the formal foundations, dynamic IFC provides
implementation experience, agent defences provide the application
context, benchmarks provide evaluation, provenance provides the tracking
mechanism, and policy engines provide the production integration target.
No existing system spans all six.
