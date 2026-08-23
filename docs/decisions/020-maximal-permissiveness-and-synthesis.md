# Specification 020: Maximal permissiveness and controller synthesis

Type: specification
Status: accepted for implementation

## Objective

Formalise and empirically verify the claim that the ITES Principal
Intersection rule is the maximally permissive action-authorisation
controller that prevents privilege escalation (PE) under the stated ACS,
provenance, and arbitrary-LLM threat model (RQ1).

## Background

The research overview and `MAXIMAL_SECURITY_AND_SYNTHESIS.md` propose a
controller-synthesis experiment: encode a finite ACS, principal set,
action set, and provenance propagation as a transition system, give a
solver the PE bad-state predicate, and ask for the maximally permissive
safe controller. If the synthesised controller matches the ITES
intersection rule, this provides independent executable evidence for the
maximality theorem.

## Formal statement

### Definitions

Let:

- `U` be a finite set of principals.
- `A` be a finite set of effectful actions.
- `ACS(p, a)` mean principal `p` is authorised by the current ACS to
  perform action `a`.
- `PC(e)` be the conservative Principal Context influencing execution
  `e` — the set of principals whose information may have influenced it.
- `PE(a, PC)` iff `exists p in PC such that not ACS(p, a)`.
- `ITESAllow(a, PC) iff PC != empty and forall p in PC: ACS(p, a)`.

### Theorem (maximal permissiveness)

For a fixed ACS and Principal Context `PC`:

1. **ITES is safe**: if `ITESAllow(a, PC)` then `not PE(a, PC)`.
2. **ITES is maximal**: for any controller `C` such that `C(a, PC)`
   implies `not PE(a, PC)`, `C(a, PC)` implies `ITESAllow(a, PC)`.

### Proof sketch

**Safety**: If `ITESAllow(a, PC)` then `forall p in PC: ACS(p, a)`,
so `not exists p in PC: not ACS(p, a)`, hence `not PE(a, PC)`.

**Maximality**: Suppose `C` is safe (preserves PE) and `C(a, PC)` but
`not ITESAllow(a, PC)`. Then either `PC` is empty (and no effectful
action should be allowed) or `exists p in PC: not ACS(p, a)`. In the
latter case, `PE(a, PC)` holds, contradicting `C`'s safety. In the
former case, allowing an effect from an empty context is unsafe under
the non-vacuity condition. Hence `C(a, PC)` implies `ITESAllow(a, PC)`.

### Assumptions

- The ACS is fixed during the check (no authority-changing transitions
  in the base theorem; delegation is a separate extension).
- Principal Context is conservative: `actual_influence subseteq PC`.
- The controller can only allow or deny effectful transitions; it
  cannot alter ACS, provenance, or environment facts.
- Empty Principal Context denies all effectful actions (non-vacuity).

## Controller-synthesis experiment

### Approach

Rather than encoding ITES directly, the experiment constructs a finite
transition system with a PE bad-state predicate and uses Z3 to find, for
every reachable `(state, action)` pair, whether there exists a safe
allow decision that does not introduce PE. The maximally permissive safe
controller allows every action that does not create a PE violation.

### Negative controls

Each defective controller violates the PE invariant:

| Control | Defect |
|---|---|
| `ANY_AUTHORISED` | Allow if any single influencer is authorised |
| `REQUESTER_ONLY` | Check only the initiating principal |
| `DROP_PROVENANCE` | Reset PC after each transition |
| `TRUSTED_PLAN` | Ignore provenance introduced after planning |
| `EMPTY_IS_PRIVILEGED` | Allow effects from empty PC |
| `STALE_ACS` | Authorise against historical rather than current ACS |

### Evidence

Results are retained as schema-checked JSON under
`research/output/runs/controller-synthesis-v1/` with:

- the finite instance (principals, actions, ACS);
- the synthesised controller decisions;
- the ITES intersection rule decisions;
- equivalence check result;
- negative control verdicts and counterexamples.

## Scope

This specification covers the theorem, the synthesis experiment, and
negative controls. It does not claim:

- unbounded verification (the synthesis is finite);
- maximal permissiveness under delegation or consent;
- implementation conformance (that is RQ9);
- a formal proof assistant artefact (Z3 evidence is sufficient for the
  current research stage).
