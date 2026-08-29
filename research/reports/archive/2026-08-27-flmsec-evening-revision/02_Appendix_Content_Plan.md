# Appendix Content Plan

## A. Expanded theoretical comparison
Use for details that support, but are not required for, the main CaMeL/ITES comparison:
- extended comparison matrix;
- additional system-level neighbours;
- longer discussion of trusted components and policy models;
- verified discussion of the new CaMeL-verification paper.

## B. Formal details
- expanded maximality/monotonicity proof details;
- additional definitions/assumptions;
- worked examples.

## C. SLED methodology and original evaluation
- state/execution model;
- exploration bounds;
- environment details;
- complete result taxonomy;
- incomplete-trace treatment;
- extra tables.

## D. Newer ITES extensions — preliminary
For each extension use the same template:
- Motivation
- Semantic change
- Why the original invariant is preserved/changed
- Implementation status
- Tests/evidence
- Limitations
- Status label: preliminary/post-original

Candidate extensions:
- explicit delegation;
- consent;
- action visibility / observer-aware confidentiality;
- finer-grained actions/resources;
- provenance/attribution refinements.

Do not imply these were part of the original 1.5M-trace result unless actually evaluated there.

## E. AgentDojo integration smoke test — preliminary
Report:
- exact upstream version/commit if known;
- exact scenario/configuration;
- adapter path;
- command;
- observed output;
- what was successfully exercised;
- what was not tested.

Interpretation must say that a smoke test validates integration plumbing, not comparative security.

## F. SLED-V preliminary verification
Report:
- verified model/IR version;
- property;
- backend;
- finite/bounded/unbounded status;
- assumptions;
- result;
- runtime/state counts if useful;
- command;
- implementation-conformance status.

Suggested table:
| Property | Model | Backend | Verdict | Scope/assumptions | Reproduce |
|---|---|---|---|---|---|

Explain the distinction:
- original SLED: bounded exhaustive behavioural evidence;
- SLED-V: formal checking of an explicit model/IR;
- implementation conformance: separate question unless established.

## G. Reproducibility
- anonymous artefact layout;
- setup;
- core tests;
- SLED reproduction;
- SLED-V reproduction;
- AgentDojo smoke test;
- expected outputs.
