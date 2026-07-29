# Conflux Architecture

`conflux.domain` owns immutable security values. `conflux.ports` declares
provider, model, policy, executor, and tracing boundaries.
`conflux.application` composes decisions and use cases. `conflux.ites` owns the
only security transition kernel. `conflux.evaluation` owns SLED verification.
External systems exist only below `conflux.adapters`.

The model proposes declarative alternatives. ITES derives the conservative
Principal Context from trusted provenance and evaluates every alternative from
the same immutable parent. An authorised action receives a certificate bound to
the action, context, branch, and policy versions. Execution is a separate use
case and requires that certificate.

Domain and ITES never import adapters or benchmarks. Evaluation observes the
kernel and cannot redefine its security decisions.

See [Security Model](SECURITY_MODEL.md), [SLED](SLED.md), and
[Reference](REFERENCE.md).
