# Comparative Verification of Contemporary Agent Defences

## Status

Research design document. Claims about external defences must be validated against their papers and implementations before publication.

## 1. Motivation

Contemporary system-level defences often optimise for different security objectives:
- preventing indirect prompt injection;
- maintaining trusted control flow;
- enforcing developer-written policies;
- controlling information flow;
- constraining tool arguments;
- preserving provenance/capabilities.

Conflux instead defines a privilege-escalation property over influencing principals and an existing ACS.

A defence can therefore satisfy its own published property while violating the Conflux PE property. That is not necessarily a flaw in the defence; it demonstrates that the security objectives are non-equivalent.

## 2. Research question

For defence `D` and property `P`:

    Does every execution admitted by D satisfy P?

If not, return a minimal counterexample.

Where feasible, also encode the defence's intended property `Q` and establish:

    D satisfies Q
    but Q does not imply P.

This is stronger and fairer than beginning with an attack designed to "break" the defence.

## 3. Common verification interface

Each defence model should expose, directly or through an adapter:

    State
    InitialState
    EnabledProposals
    Transition
    ObservableEffects
    SecurityDecision
    Provenance/taint/capability state
    Policy state

The LLM remains adversarial/nondeterministic over well-typed proposals.

External implementations should eventually have a conformance/replay layer connecting concrete traces to the abstract model.

## 4. Candidate systems

### ITES / Conflux
Purpose:
- reference defence;
- expected to satisfy PE under assumptions;
- candidate maximally permissive controller.

### CaMeL
Model:
- trusted/planning path;
- data-processing/quarantined path;
- capabilities/data-flow restrictions;
- policy checks;
- replanning/error behaviour as specified.

Questions:
- does the faithfully modelled system satisfy its intended guarantees?
- does it satisfy Conflux PE?
- if not, which execution pattern distinguishes the properties?

Do not assume a PE counterexample exists before modelling.

### Dual-LLM pattern
Useful as a simpler architectural baseline:
- privileged planner;
- quarantined data processor;
- restricted communication/effects.

### PACT-like provenance system
Potentially useful for:
- argument-level provenance;
- cross-step/replanning provenance;
- contrasting provenance-to-authority semantics.

### Progent-like policy system
Potentially useful for:
- argument-sensitive tool policy;
- policy expansion/monotonicity;
- comparing ACS-derived authority with application-specific policies.

Only include systems whose semantics can be represented faithfully enough for defensible claims.

## 5. Property suite

### P1 — No privilege escalation

    Executed(a) ->
        for all p in Influencers(a), ACSAllows(p,a)

### P2 — No unauthorised read

    Read(p_context,d) ->
        every required principal is authorised under the chosen read semantics

The exact subject of the read check must be defined carefully.

### P3 — Provenance preservation

Influence required by the model is never silently discarded across transitions.

### P4 — No implicit authority transfer

Authority can increase only through explicit modelled ACS/delegation transitions.

### P5 — Defence-native property

Encode each defence's own intended property where practical.

### P6 — Goal reachability

Does at least one secure execution reach the task goal?

Later:
- strong/strategy-based completion;
- confidentiality/noninterference;
- visibility;
- consent.

## 6. Counterexample format

Every `UNSAFE` result should include:

    initial ACS
    initial provenance
    defence configuration
    sequence of LLM proposals
    policy/capability decisions
    state transitions
    executed effect
    violating principal/property
    shortest/minimality information

A human-readable rendering should accompany machine-readable JSON.

## 7. Scientific interpretation

Preferred wording:

    "Under the SLED-V formalisation and assumptions, defence D admits an
    execution violating property P."

If the defence's own property holds:

    "This does not contradict D's published guarantee; it demonstrates that
    D's property Q does not imply the Principal-Context PE property P."

Avoid:
- "CaMeL is insecure" from a mismatched property;
- claiming implementation vulnerabilities from specification-only models;
- comparing systems without aligning task/tool/policy semantics.

## 8. Experimental sequence

1. Verify ITES and defective ITES controls.
2. Encode a simple Dual-LLM baseline.
3. Encode one contemporary defence deeply, preferably CaMeL if semantics are sufficiently available.
4. Validate its native property on small instances.
5. Check PE.
6. Minimise any counterexample.
7. Replay against implementation where possible.
8. Only then add further defences.

Depth is more valuable than a broad but heuristic collection of adapters.
