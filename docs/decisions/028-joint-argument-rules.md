# ADR-028: A joint argument rule for content origin and destination

- Type: adr
- Status: accepted
- Date: 2026-10-11
- Owners: Conflux maintainers

## Context

The harness demonstration sends a note out of the workspace and is blocked by
principal attribution, not by the content of the note
(`docs/integrations/harness-demo.md`). The question this record answers is
whether one shipped rule shape can constrain the origin of a value and its
destination together, or whether deployments must compose coarse rules.

A measured probe (the joint-rule decision note in the investigation workspace,
2026-10-11) recorded six facts.

1. `AUTHORITY_BEARING_ARGUMENT_ROLES` holds resource, recipient, destination and
   credential reference, but not content (`src/conflux/domain/actions.py:46`).
   `DecisionPipeline._authorise_arguments` therefore never judges a content
   argument (`src/conflux/application/policy.py:78`).
2. An argument grant pins one principal, one operation, one argument, one role
   and one value fingerprint (`src/conflux/policy/argument_policy.py`). It has
   no field for provenance and reads no other argument.
3. Consequence: a send of private content to a destination outside the
   workspace is authorised when the principal holds the destination grant. The
   injected call of the demonstration is refused because the injection principal
   holds no grant for the operation or the resource.
4. Consequence: the coarse compositions available today lose utility. Removing
   the destination grant refuses the injected call and the owner's legitimate
   call alike, so no composition of per-argument grants separates them.
5. A rule of the wanted shape installed on the content argument is never
   consulted: the decision and its evidence are unchanged from the arm without
   the rule.
6. The same shape installed on the judged destination argument does refuse, so
   the mechanism is not vacuous; the missing part is the ability of one
   argument's allowance to constrain another argument.

## Decision

1. An argument grant may carry requirements on other arguments of the same
   action. `ArgumentRequirement` names one sibling argument and holds when that
   argument's provenance sources are a subset of the permitted sources, or its
   value fingerprint equals the pinned one, or both.
2. The rule stays a condition on the allowance it is attached to: a matching
   grant authorises its argument only when every requirement of that grant
   holds. Grants remain additive allowances, so a rule is effective only when it
   is the only grant matching that argument; this is stated in the docstring and
   pinned by a test.
3. Requirements fail closed. An absent sibling argument, unknown provenance, an
   empty permitted-source list, or a different value all deny. The refusal
   reason is `argument_requirement_denied` and the evidence names each unmet
   requirement as `requires_failed:<argument>`.
4. A requirement is not a read decision. It constrains whether the effect may
   run, not which data a principal may read, so SEM-004 is unchanged.
5. The requirement is evaluated against the action's own arguments inside the
   argument-authorisation policy, so the decision stays the conjunction of
   independent dimensions of SEM-005 and no new policy dimension is introduced.
6. A grant with no requirements keeps its previous reason `argument_grant` and
   its five-element evidence, so every retained bundle stays valid.

## Consequences

- The joint rule is expressible in one place: the grant that allows the
  destination names the permitted origin of the body. No deployment needs a
  new dimension, a new port or a data-flow engine.
- The form usable with the current environment fixtures is the value pin,
  because a fixture artifact carries no data-item identity: `DataItem.to_artifact`
  builds provenance from the item's authors only
  (`src/conflux/domain/environment.py:35`), so `Provenance.sources` is empty for
  environment inputs. The provenance-source form fails closed there. Recording
  item identity in artifact provenance is a separate change, registered as task
  X19 in `open-tasks/clarity-programme-2026-10-10.md`.
- A deployment that wants the joint rule must not hold a second unconstrained
  grant for the same argument. That is a property of additive allowances, not a
  defect of the rule, and the test suite pins it.
- The rule is local to one action. It is not taint tracking across plan steps,
  and this record claims nothing about multi-step flows.

## Related

- `docs/reference/SEMANTICS.md` SEM-019 - the rule as a semantics entry.
- `src/conflux/policy/argument_policy.py` - the implementation.
- `tests/test_argument_policy_joint_rule.py` - unit tests and the demonstration gateway arm.
- `docs/integrations/harness-demo.md` - the demonstration whose gateway the new arm uses.
- `docs/decisions/024-external-provenance-and-authority-bounds.md`, `025-authority-confinement-semantic-judgement-delegation.md` - earlier work on argument-level authority.

## Update (2026-10-12)

Two changes since this record was accepted, both landed, so the context above reads as history:

- The provenance-source form is no longer unreachable with the environment fixtures: a data item
  now names itself in the provenance of the artifact it becomes
  ([SEM-020](../reference/SEMANTICS.md#sem-020-a-data-items-artifact-provenance-names-the-item),
  commit `5e4aa12`, task X19). The value-pin form remains the fallback.
- The harness demonstration installs this rule in its own envelope
  (`research/output/runs/harness-demo-v1/`, commit `d2a2f9c`, task X21): both addresses are inside
  the envelope for every influencing principal, each destination grant carries the requirement that
  the post's body come from the reviewed task item, and the retained run shows the rule refusing the
  injected call with `requires_failed:body` and allowing a body the task supplied at the same outside
  address. So the sentence in the Context, that the demonstration is blocked by principal
  attribution rather than by the content of the note, describes the state before that change, not
  the shipped demonstration.
