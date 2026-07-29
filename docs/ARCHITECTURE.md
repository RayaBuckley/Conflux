# Conflux Architecture

`conflux.domain` owns immutable security values. `conflux.ports` declares
provider, model, policy, executor, and tracing boundaries.
`conflux.application` composes decisions and use cases. `conflux.ites` owns the
only security transition kernel. `conflux.evaluation` owns SLED verification.
External systems exist only below `conflux.adapters`.

The model returns a `ProposalBatch`. Alternative actions are evaluated from the
same immutable parent in canonical order. Ordered-plan actions retain their
declared order, propagate branch state, stop at the first denial, and each
receives its own certificate. ITES derives the conservative Principal Context
from trusted provenance; a batch cannot grant authority to later steps.
Execution is a separate use case and revalidates the exact certificate.

Domain and ITES never import adapters or benchmarks. Evaluation observes the
kernel and cannot redefine its security decisions.

See [Security Model](SECURITY_MODEL.md), [SLED](SLED.md), and
[Reference](REFERENCE.md).
