# Conflux Architecture

`conflux.domain` owns immutable security values. `conflux.ports` declares
provider, model, policy, executor, and tracing boundaries.
`conflux.application` composes decisions and use cases. `conflux.ites` owns the
only security transition kernel. `conflux.evaluation` owns SLED verification.
External systems exist only below `conflux.adapters`.

`conflux.planning` owns authenticated operation catalogues and immutable
open-ended plan programs. Planner text is never executable authority: argument
bindings are grounded from trusted runtime values, every effect returns through
ITES, and a fresh certificate is checked immediately before provider execution.
Explicit loop, continuation, model-call, value, and code bounds make incomplete
runs visible.

`conflux.verification` owns callback-free solver-facing IR and optional formal
backends. It does not replace native SLED in `conflux.evaluation`. Runtime-to-IR
conformance covers the documented finite subset; unsupported effects and tools
produce `UNKNOWN`.

The model returns a `ProposalBatch`. Alternative actions are evaluated from the
same immutable parent in canonical order. Ordered-plan actions retain their
declared order, propagate branch state, stop at the first denial, and each
receives its own certificate. ITES derives the conservative Principal Context
from trusted provenance; a batch cannot grant authority to later steps.
Execution is a separate use case and revalidates the exact certificate.

Domain and ITES never import adapters or benchmarks. Evaluation observes the
kernel and cannot redefine its security decisions.

Experiment code under `conflux.experiments` aggregates retained evidence and
materialises resumable jobs. It cannot redefine security decisions or infer
hardware. External benchmark translation is versioned beneath
`adapters.benchmarks`; it is not part of the public core API.

See [Security Model](SECURITY_MODEL.md), [SLED](SLED.md),
[Reference](REFERENCE.md), and the [dynamic-planning specification](specifications/010-open-ended-dynamic-planning.md).
