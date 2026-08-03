# Security Policy

Conflux is pre-1.0 research software, not a production security product.
Report vulnerabilities privately to the repository owner rather than placing
credentials, exploit payloads, or confidential traces in a public issue.

The trusted computing base includes the canonical domain values, policy
implementations, ITES kernel, certificate-bound application service, selected
executor, scenario/model parsers, and integrity of the Python runtime and
dependencies. Bypassing mediation, lying policy adapters, compromised
providers, and incorrect provenance annotations are outside guarantees.

Provider and model adapters are research prototypes. Filesystem effects are
dry-run by default; live writes require confinement and a precondition hash.
Generated code is passed as data to a pinned container invocation with no host
shell interpolation, no network by default, read-only inputs/root filesystem,
explicit output mounts, and resource limits. Container-runtime compromise and
kernel escape remain outside the model.
External model secrets are read from environment variables only and must not
be committed to manifests, logs, fixtures, or retained responses. Keep Docker,
model, solver, benchmark, and cluster workflows optional and credential-free
by default.

Open-ended plan approval never grants authority. The authenticated catalogue
constrains operation identity and schema; every grounded effect is mediated and
re-authorised immediately before execution. Scoped delegation is modeled and
mutation-tested, but operational consumption remains unconditionally denied.
The optional Cedar adapter is not a production authority source until a pinned
live differential bundle exists; offline preflight is readiness evidence only.

Supported security fixes target the current default branch. There is no stable
0.1 API compatibility promise yet.

## Rationale

The trusted computing base is published because mediation cannot protect
effects that bypass it or inputs whose provenance is false. Fail-closed
optional integrations keep unavailable research infrastructure from weakening
the deterministic core. Dry-run defaults, environment-only secrets, bounded
capabilities, and action-time re-authorisation reduce configuration risk while
leaving residual host and provider trust explicit.
