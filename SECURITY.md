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
External model secrets are read from environment variables only and must not
be committed to manifests, logs, fixtures, or retained responses. Keep Docker,
model, solver, benchmark, and cluster workflows optional and credential-free
by default.

Supported security fixes target the current default branch. There is no stable
0.1 API compatibility promise yet.
