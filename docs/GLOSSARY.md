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

Use “human user” only for an explicitly human interface actor. Otherwise use
Principal.
