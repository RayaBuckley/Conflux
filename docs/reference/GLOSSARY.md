# Conflux Glossary

| Term | Meaning | Canonical owner |
|---|---|---|
| Principal | Authenticated identity; authority is supplied by policy | `domain.identity` |
| Principal Context | Conservative set of Principals influencing a decision | `domain.identity`, `ites.state` |
| Provenance | Origin and derivation, never a read ACL | `domain.provenance` |
| Artifact | Immutable value paired with provenance | `domain.artifacts` |
| Resource | Stable protected-object reference | `domain.resources` |
| Action | Declarative proposal that performs no side effect itself | `domain.actions` |
| Authorisation | Pointwise organisational policy decision | policy ports |
| Readability | Independent decision about observing an artifact | read policy port |
| Visibility | Decision about an action's observation channel | visibility policy port |
| Consent | Approval that can restrict but never grant authority | consent policy port |
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

Use "human user" only for an explicitly human interface actor. Otherwise use
Principal.
