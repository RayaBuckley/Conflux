# Conflux Research Glossary

Purpose: define canonical research and implementation terminology. Owner:
repository maintainers. Use this page instead of duplicating definitions in
feature documents; detailed semantics remain in source docstrings and tests.

This glossary is the canonical vocabulary for the implementation and paper.

| Term | Conflux meaning | Code locations | Avoid |
|---|---|---|---|
| Principal | An entity that can contribute information, own resources, or receive authority. | `core/principals.py` | Using “user” for every principal |
| Principal Context | The principals whose information or authority is relevant to the current execution decision. | `core/provenance.py`, `ites/state.py` | “Current influence set” |
| Provenance | Causal origin and derivation information retained with data. | `core/provenance.py` | Treating provenance as merely metadata |
| Artifact | A value together with its provenance. | `core/artifacts.py` | Bare values when provenance matters |
| Resource | A protected object or capability operated on by an action. | `core/resources.py` | Confusing a resource with an artifact |
| Action | An explicit request to perform work. | `core/actions.py` | Authorising raw strings |
| Primitive action | An externally meaningful operation such as reading or writing a resource. | `core/actions.py` | Treating nested execution as primitive |
| Nested execution | Recursive agent/LLM execution represented as an explicit action. | `core/actions.py`, `ites/` | Implicit recursive calls |
| Delegation | A controlled transfer or use of authority by one Principal for another. | `core/consent.py`, `core/actions.py` | Silent permission broadening |
| Authorisation | A decision about whether an action may execute. | `auth/`, `policy/` | Equating authorisation with visibility |
| Visibility | A decision about which parties may observe an action or result. | `core/chat_policy.py` | Assuming permitted means Principal-visible |
| Consent | Voluntary approval that may constrain execution but never broadens authority. | `core/consent.py` | Treating consent as permission |
| Influence | The causal contribution of information or a Principal to a decision. | provenance and ITES state | Replacing Principal Context with a trust label |
| Execution trace | Immutable record of execution events and decisions. | `sled/trace.py`, `ites/state.py` | Recording only final outcomes |
| ITES | The provenance-aware defence architecture that mediates execution. | `ites/` | Treating ITES as a benchmark |
| SLED | The evaluation framework for attacks, defences, scenarios, and outcomes. | `sled/` | Putting benchmark-specific logic in ITES |
| Security outcome | Whether an execution respected the security policy. | `sled/task_classification.py` | Inferring security only from task success |
| Utility outcome | Whether legitimate task objectives were achieved. | `sled/task_classification.py` | Treating blocking as automatically useful |

“User” may be used only when specifically referring to a human user interface
actor. Otherwise use “Principal”.
