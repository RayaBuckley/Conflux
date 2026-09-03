# Conflux Glossary

| Term | Meaning | Canonical owner |
|---|---|---|
| Principal | Authenticated identity; authority is supplied by policy | `domain.identity` |
| Principal Context | Conservative set of Principals influencing a decision | `domain.identity`, `ites.state` |
| Provenance | Origin and derivation, never a read ACL | `domain.provenance` |
| Artifact | Immutable value paired with provenance | `domain.artifacts` |
| Resource | Stable protected-object reference | `domain.resources` |
| Action | Declarative proposal that performs no side effect itself | `domain.actions` |
| Authority intersection | Effective permission is the intersection of all influencing Principals' permissions; additional influence can only reduce authority | `ites`, SEM-009 |
| Authorisation | Pointwise organisational policy decision | policy ports |
| Readability | Independent decision about observing an artifact | read policy port |
| Visibility | Decision about an action's observation channel | visibility policy port |
| Consent | Approval that can restrict but never grant authority | consent policy port |
| Confused deputy | A privileged component tricked by untrusted input into misusing its authority; prompt injection is a modern instance | research vocabulary |
| Decision certificate | Binding of action, context, branch, and policy versions | `ites.state` |
| ITES | Sole provenance-aware mediation transition kernel | `ites` |
| SLED | Bounded explicit-state security verifier | `evaluation` |
| Security outcome | Whether executed behavior satisfies policy | ITES/SLED reports |
| Utility outcome | Whether a task objective was achieved | benchmark adapter result |
| Contamination | Reduction of authority after consuming lower-authority information; classical term from Biba/LOMAC | research vocabulary |
| Low-water-mark integrity | Biba integrity policy where a subject's effective integrity is lowered after observing less-trusted information | research vocabulary |
| Noninterference | Varying secret information does not alter unauthorised observations; stronger than read-access safety | research vocabulary |
| Declassification | Controlled release of information beyond strict confidentiality confinement | research vocabulary |
| Endorsement | Accepting untrusted information as sufficiently trustworthy; integrity analogue of declassification | research vocabulary |
| Robust declassification | An attacker cannot control what trusted code declassifies | research vocabulary |
| Observational confidentiality | Relational property: executions differing only in secrets produce equivalent observations for unauthorised principals | research vocabulary |
| Modeled program | Inert graph of declared effects with no execution boundary; used for static analysis and verification IR abstraction | `planning.modeled_program` |
| Cone of influence reduction | Variable-reduction technique that removes state variables irrelevant to a given safety property before model checking | `verification.reduction` |
| Direction readiness | Pre-flight assessment of whether an experiment direction has all required evidence, manifests, and schemas in place | `experiments.direction_evidence` |
| PARC translation | Mapping of external benchmark results (e.g. AgentDojo) into the native Conflux result schema for comparison | `adapters.benchmarks` |
| Capability envelope | Declaration of a code-execution capability including its required permission, resource scope, and declared effects | `planning.code_execution` |
| Plan patch | Structured edit (add, replace, remove) applied to a dynamic plan graph during continuation | `planning.continuation` |
| Modeled effect | Declared read/write dependency of a planned action on named artifact bindings | `planning.modeled_program` |
| Plan execution state | Mutable snapshot of node statuses, outputs, and trace events during dynamic plan execution | `planning.state` |
| Verification IR | Serializable intermediate representation of a transition system for formal verification backends | `verification.ir` |
| Differential conformance | Comparison of runtime transition behaviour against the verification IR to detect divergence | `verification.interpreter` |
| Delegation grant | Scoped, time-bound authorisation transfer from one Principal to another that cannot manufacture authority | `domain.delegation` |
| Defence model | A finite IR abstraction of a contemporary agent defence (e.g. CaMeL, Progent, PACT) used for comparative verification; not implementation-conformance evidence | `verification.defence_models` |
| PARC (Cedar) | Pointwise Authorisation Request Corpus — the translated request format used by the Cedar adapter for differential testing | `adapters.benchmarks` |
| Part B | The previous project phase that introduced ITES, Principal Context, SLED, and bounded experiments over ~1.5M traces; archived under `research/reports/archive/` and `research/publications/paper/` | research vocabulary |
| Part C | The current fourth-year project extending Part B with formal verification (SLED-V), comparative defence analysis, planning, and finer-grained authority semantics | research vocabulary |
| PE (Privilege Escalation) | Executed action where at least one influencing principal lacks organisational permission; the core security property ITES prevents | `ites`, research vocabulary |
| PE-safe | A controller is PE-safe if no executed action violates PE under the stated threat model | research vocabulary |
| Reference monitor | A small, analysable, tamper-resistant mechanism providing complete mediation of privileged effects; ITES is the reference monitor for Conflux | `ites` |
| TCB (Trusted Computing Base) | Components whose correct operation is assumed by the security guarantee; listed in `SECURITY_MODEL.md` | `SECURITY_MODEL.md` |
| Trusted transformation | An explicitly modelled operation that may conservatively reduce Principal Context influence; future work, not yet activated | `SECURITY_MODEL.md`, ADR-024 |

Use "human user" only for an explicitly human interface actor. Otherwise, use
Principal.
