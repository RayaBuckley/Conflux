# Maximal Security and Controller Synthesis for ITES

## Status

Research proposal / supporting analysis. This is not a proof artefact and should not replace the canonical security specification.

## 1. Objective

Formalise the claim that, under the Conflux privilege-escalation definition, ITES is not merely safe but **maximally permissive**.

The key idea is to separate:
- mathematical maximality of the authorisation rule;
- model checking of an executable transition system;
- synthesis of a maximally permissive controller;
- conformance of implementation to verified semantics.

## 2. Basic setting

Let:
- `U` be principals;
- `A` be externally visible/effectful actions;
- `P(p,a)` mean principal `p` is authorised by the current ACS to perform action `a`;
- `PC(e)` be the conservative Principal Context influencing execution/effect `e`.

Define privilege escalation for an executed action `a` as:

    PE(a, PC) iff exists p in PC such that not P(p,a).

The ITES authorisation predicate is:

    ITESAllow(a, PC) iff for all p in PC, P(p,a).

Equivalently:

    Allowed(PC) = intersection over p in PC of Permissions(p).

Empty-context semantics must be explicitly defined rather than inherited from vacuous truth.

## 3. Mathematical maximality

This result is an optimality characterisation of the policy choice, not a
technically difficult theorem. It establishes that the intersection is not
merely arbitrary conservative policy.

For fixed `PC`, ITES permits exactly the complement of PE actions.

Suppose another authorisation rule permits a strict superset of `Allowed(PC)`.
Then it permits some `a` not in `Allowed(PC)`.
Therefore there exists `p in PC` with `not P(p,a)`.
Executing `a` satisfies the PE definition.

Hence no rule can permit a strict superset while preserving the same PE property.

This is the conceptual maximality theorem. Formalisation should specify:
- fixed/current ACS semantics;
- parameterised actions/resources;
- empty Principal Context;
- authority-changing ACS transitions;
- which transitions are controllable by the mediator.

## 4. Transition-system formulation

Represent the uncontrolled agent environment as:

    M = (S, T, S0)

where transitions include arbitrary well-typed LLM proposals and modelled environment/provider outcomes.

Define:

    Bad(s) := an unauthorised effect has occurred

or transition-locally:

    BadTransition(s, action, s')
        iff action is effectful
        and exists p in PrincipalContext(action,s)
        such that not ACSAllows(s,p,action).

The ITES controller disables precisely the bad controllable effect transitions.

Safety target:

    Reach(M_ITES) intersection Bad = empty.

## 5. Maximal-permissive controller claim

Let `C` range over controllers that may disable controllable effect transitions but cannot alter the ACS/provenance facts arbitrarily.

Desired theorem:

    For every safe controller C,
    Enabled_C(s) subseteq Enabled_ITES(s)

for all relevant reachable states `s`, modulo transitions that are outside the authorisation problem.

This needs care when:
- reads are treated as effects;
- consent adds restrictions;
- visibility adds confidentiality constraints;
- provider failures add nondeterminism;
- delegation changes the ACS;
- controllers may modify future state rather than simply allow/deny the current effect.

The cleanest initial theorem should cover primitive action authorisation under a fixed ACS and correct Principal Context.

## 6. Controller-synthesis experiment

Do not encode the ITES allow rule into the synthesiser.

Give the synthesiser:
- finite ACS;
- finite principal/resource/action domains;
- provenance/PC propagation semantics;
- arbitrary typed LLM proposals;
- controllable allow/deny decisions;
- PE bad-state predicate.

Ask for the maximally permissive safety controller.

Then compare the synthesised controller with ITES.

Expected result:

    SynthAllow(a,PC) == all(ACSAllows(p,a) for p in PC)

for every represented state/action.

This provides:
- independent validation of the theorem/formalisation;
- an executable demonstration of why Principal Intersection emerges;
- a foundation for synthesising controllers under richer properties.

## 7. Negative controls

Create deliberately defective controllers:

1. `ANY_AUTHORISED`: permit if any influencer has permission.
2. `REQUESTER_ONLY`: check only initiating user.
3. `DROP_PROVENANCE`: reset PC after nested execution.
4. `TRUSTED_PLAN`: ignore provenance introduced after planning.
5. `EMPTY_IS_PRIVILEGED`: permit effects from empty PC.
6. `STALE_ACS`: authorise against historical rather than current permissions.

SLED-V should generate minimal PE counterexamples for each.

## 8. Extensions

### Delegation

Model delegation as an explicit state transition changing the ACS/capability state.

A theorem can then say:
- the delegation transition itself must be authorised;
- subsequent effects are checked normally against the resulting authority state.

This is preferable to weakening the intersection predicate.

### Confidentiality

Maximality for PE alone does not establish maximality for confidentiality.
A separate property is required for reads/observations.

### Authority versus harm

ITES prevents authority amplification relative to the granularity of the ACS.
It does not by itself guarantee that authorised actions are safe, intended, or
optimally parameterised. If both influencing principals can perform an
operation, an attacker-controlled input may still influence which recipient,
amount, or attachment is selected. Fine-grained argument policies can reduce
harm within authorised action classes without weakening the PE invariant.

### Consent

Consent is an additional restriction, so a consent-aware controller can be less permissive than the maximally PE-safe controller without contradicting the theorem.

### Planning

Once the transition model is available, synthesis can ask a second question:

    Among PE-safe behaviours, does a strategy exist that reaches the task goal?

This separates security from utility.

## 9. Candidate outputs for the thesis

- formal theorem and proof;
- finite controller-synthesis implementation;
- equivalence check between synthesised controller and ITES;
- symbolic/unbounded verification of the transition semantics;
- defective-controller counterexamples;
- scaling results as principals/actions/resources increase;
- extension analysis showing exactly where the simple maximality theorem stops applying.
