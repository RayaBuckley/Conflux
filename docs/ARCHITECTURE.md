# Conflux Architecture

Purpose: define the system boundary, dependency direction, security invariants,
and extension points. Owner: repository maintainers. This is the architectural
source of truth; file ownership is recorded in [AUDIT.md](AUDIT.md) and public
API ownership in [REFERENCE.md](REFERENCE.md).

Conflux is organised around a provenance-aware security model for AI-agent
execution. ITES is the defence; SLED is the evaluation framework.

## System boundary

```text
agent/model proposals
          ↓
ITES mediation ← core domain, provenance, policies
          ↓
provider execution or nested execution
          ↓
immutable trace and SLED evaluation
```

The model, provider, and benchmark are adapters around the security boundary.
Benchmark-specific behaviour must not be embedded in core or ITES.

## Layers

### Core domain

`conflux.core` contains immutable values for Principals, resources,
permissions, artifacts, provenance, actions, consent, visibility, and sessions.
It must not depend on providers or benchmark implementations.

The clean-slate domain entry point is `conflux.domain`. It provides
provider-neutral `PrincipalContext`, `ResourceRef`, `Intent`, typed decisions,
and domain-level imports for artifacts and provenance. `conflux.core` remains
the behavioral compatibility source during migration; new domain code must
not import SLED, providers, or benchmarks.

`conflux.application` owns use cases such as mediation. `conflux.ports` owns
typed Protocol boundaries. `conflux.adapters` is reserved for outer
translations and has no authority to redefine domain semantics.

`conflux.evaluation` owns benchmark-independent, versioned trace values. It
records outcomes but does not decide whether an action is secure.

### Execution

`conflux.execution` transforms artifacts while preserving provenance. It is
the mechanism for representing derivation without silently losing causal data.

### Security

`conflux.auth` computes authority from the Principal Context. `conflux.policy`
defines policy decisions and adapters for external policy semantics.

### ITES

`conflux.ites` exposes the defence interface, mediates actions, tracks
immutable execution state, and evaluates security properties. ITES separates
authorisation, visibility, and consent.

### Evaluation

`conflux.sled` constructs environments and scenarios, applies attacks and
defences, explores execution, records traces, classifies security and utility
outcomes, and aggregates reports.

### Adapters

`conflux.providers` materialises filesystem and Docker environments.
`conflux.benchmarks` connects native and external benchmark systems. Adapters
translate external representations into Conflux models and must not weaken
provenance or authorisation checks.

## Public extension points

The principal interfaces are:

- `ITES`: runs a defence against an environment and input artifacts.
- `Policy`: evaluates a structured policy request.
- `PolicyAdapter`: translates provider policy context into a policy decision.
- `ProviderAdapter`: materialises, describes, resolves, and executes provider
  resources.
- `Attack`: transforms a scenario to model an attack.
- `TaskSuite`: supplies benchmark tasks.
- benchmark and external protocols: translate task inputs and execution traces.

The migration direction is:

```text
domain → ports → application → adapters
                 ↓
              evaluation
```

Compatibility modules may depend on canonical modules, but canonical domain
modules may not import compatibility, SLED, provider, or benchmark modules.

These interfaces require explicit technical contracts before new backends are
added. See `docs/MODULE_GUIDE.md` for the current module map.

## Security invariants

- Every security-relevant artifact retains provenance.
- The Principal Context is evaluated at action time.
- Mixed contexts use the intended intersection/collective-authorisation rule.
- Consent cannot manufacture or broaden authority.
- Visibility is independent from permission to execute.
- Execution state and traces are immutable from the caller's perspective.

## Repository structure

See `docs/MODULE_GUIDE.md` for file responsibilities. Architectural changes
should be recorded as decision records under `docs/decisions/` and synchronised
with the paper terminology and diagrams.
