# Finite IR model scope and fidelity

Read 2026-10-19T16:47:47Z at `bbc099a`. This file states what the verification IR factories in
`src/conflux/verification/defence_models.py` model and what they do not model.
It exists because a verifier verdict is only as strong as the model it was computed over.

## Bottom line

- All 19 factories are small finite abstractions. The largest has 9 boolean variables; three use a
  tiny finite set sort. None models a general principal set with per-principal permissions, an
  arbitrary action set, a policy language, a general provenance graph, nested execution,
  concurrency, or code-level mediation. The PACE native model contains a bounded two-edge cut
  fragment; it is not a general provenance graph.
- **None is implementation-conformance evidence for any system, including the Conflux ITES kernel.**
  The external candidate models are also not conformance evidence for their cited systems.
- The ITES reference IR is a **one-principal, one-action instance** of the intersection rule. It
  checks the block/allow partition and records a PE violation. It is not a model of the general
  ITES theorem and not a model of the implementation.
- `unbounded-checked` means an unbounded solver or exhaustive check over the declared finite IR.
  It is not `proved`, and it is not `implementation-conformant`.
- The rule-level theorem in the FLMSec and ICLR papers is a separate deductive result about the
  authorisation rule, conditional on correct influence tracking, provenance, ACS, and enforcement.
  It does not transfer to the IR or the code without a refinement proof.

## Inventory

| factory | bound | variables | rules | invariants | sorts | model shape | not represented |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `camel_ir` | 4 | 5 | 2 | 1 | boolean | 1 attacker-influenced planner, 1 capability-gated action | capability graph, data/control separation, multiple principals, action arguments |
| `camel_native_property_ir` | 3 | 4 | 4 | 1 | boolean | 1 untrusted flow, 1 capability record, 1 processor execution | capability semantics, multiple flows, principal set |
| `camelot_ir` | 5 | 6 | 4 | 1 | boolean | 1 plan precheck, 1 history fact, 1 action, 1 ticket | CTL liveness, tool trust lattice, multiple tickets/plans |
| `camelot_native_property_ir` | 4 | 5 | 4 | 1 | boolean | 1 recipient label, 1 send, 1 ticket | liveness, multiple recipients, tool trust lattice |
| `dual_llm_baseline_ir` | 4 | 5 | 2 | 1 | boolean | 1 planner, 1 processor, 1 action | principal set, per-principal ACS, arguments, planner/processor split |
| `dual_llm_native_property_ir` | 3 | 4 | 4 | 1 | boolean | 1 untrusted instruction, 1 planner sanction, 1 processor effect | multiple flows, actual quarantine boundary, principal set |
| `fides_ir` | 5 | 6 | 3 | 1 | boolean | 3 boolean integrity labels, 1 action | reader scope, full IFC lattice, multiple values/flows |
| `fides_native_property_ir` | 4 | 6 | 4 | 2 | boolean, set | 1 value, 1 call; `readers` and `released_readers` are sets | general reader lattice, multiple values/flows |
| `ites_defective_requester_only_ir` | 4 | 5 | 2 | 1 | boolean | 1 requester, 1 attacker, 1 action | general defective-policy family, multiple principals/actions |
| `ites_native_property_ir` | 5 | 5 | 5 | 1 | boolean | 1 attacker, 1 action | general ITES maximality theorem, multiple principals/actions, implementation |
| `ites_reference_ir` | 6 | 6 | 6 | 3 | boolean | 1 influencing principal (attacker), 1 action, 1 permission bit | arbitrary influence sets, arbitrary action sets, ACS policy language, provenance graph, nested execution, implementation |
| `ites_with_read_check_ir` | 5 | 5 | 3 | 1 | boolean, set | 1 attacker, 1 action; `pc` and `input_readers` are sets, with `input_readers={alice}` per assumptions | arbitrary principal sets, real read ACL, multiple actions |
| `pace_ir` | 5 | 7 | 4 | 1 | boolean | 1 request, 1 capability, 1 influence, 1 dispatch | episode graph, nine effect obligations, certificates, verifier |
| `pace_native_property_ir` | 5 | 4 | 5 | 1 | boolean, set | 1 graph, 2 cut edges, 1 dispatch, 1 effect | full graph, effect atoms, certificates, multiple effects |
| `pact_contract_role_gate_ir` | 4 | 9 | 8 | 2 | boolean | 1 argument value, 1 authority-role case, 1 safety/utility gate | full PACT policy, multiple roles/arguments, implementation |
| `pact_ir` | 4 | 5 | 2 | 1 | boolean | 1 argument provenance bit, 1 requester, 1 attacker, 1 action | argument tree, authority roles, per-argument ACS |
| `pact_native_property_ir` | 3 | 4 | 4 | 1 | boolean | 1 untrusted origin, 1 step, 1 provenance record | cross-step graph, multiple origins, implementation |
| `progent_ir` | 4 | 5 | 2 | 1 | boolean | 1 policy check, 1 action | policy language, per-principal authority, multiple calls |
| `progent_native_property_ir` | 3 | 4 | 4 | 1 | boolean | 1 pending call, 1 policy check, 1 execution | policy language, multi-call plans, multiple principals |

Counts and sorts were read from the live factories, not copied from prose. `bound` is the
declared numeric bound used by bounded backends; an unbounded backend ignores it for depth but
still reasons over the same finite state space.

## What a verdict does and does not mean

- A `safe` or `bounded_safe` result on one of these IRs means that no reachable state **in that IR**
  violates the named invariant. With IC3 or exact enumeration over a finite state space, no depth
  bound is involved; the result is `unbounded-checked` in the support vocabulary.
- It does **not** mean that the general rule is safe, that the external system is safe, or that the
  implementation refines the IR. Those are separate obligations.
- `proved` is reserved for a deductive argument over a stated model with named assumptions. A
  machine-checked proof counts only if the retained artifact shows the proof. A solver verdict over
  a hand-written abstraction is not a proof of the system.
- The register's fidelity axis records the model relation separately from the support strength:
  `unvalidated`, `declared-abstraction`, `theory-faithful`, `implementation-conformant`.

## External candidate models

`docs/evidence/defence-model-fidelity.json` covers seven external candidate models (Dual-LLM,
CaMeL, Progent, PACT, CaMeLoT, Fides, PACE). Every entry is `unvalidated`. The JSON has no entry
for the ITES reference model; this file is the scope statement for that model and for the other
Conflux IR factories. A candidate model can pass its own property Q while admitting a PE
counterexample; that is a property of the abstraction, not evidence about the external system.

## Future work: implementation conformance

Implementation conformance is not claimed today. It is tracked as hub task **X25** and requires:

1. a formal semantics for `TransitionKernel._transition`, `PrincipalContext.merge`, and the
   `DecisionEngine.decide` boundary;
2. a refinement relation from implementation states and traces to IR states;
3. a commuting-diagram argument for context merge, nested execution, branch isolation, ordered
   plans, certificates, and deny/unknown behaviour;
4. differential traces from retained runs, replayed through both the implementation and the IR;
5. an independent audit before any row may use `implementation-conformant`.

A refinement argument, differential traces, or a traceability record alone is not enough; all five
conditions are required. Until those exist, the strongest honest fidelity tag for these IRs is `declared-abstraction`
(when the omissions are stated) or `unvalidated` (when they are not).
