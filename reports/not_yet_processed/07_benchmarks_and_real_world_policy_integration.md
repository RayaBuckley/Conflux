# Benchmarks and Real-World Policy Integration

## What this direction is

This direction combines two sources of evidence:

1. application to existing benchmarks, especially agent-security benchmarks, and
2. one genuine integration with a real policy language or decision engine.

The point is to show that the project works both as a research evaluator and as something close to an organisational security layer.

## Why it matters

A defence that only exists in abstract or synthetic environments is harder to trust. A defence that works on a public benchmark but cannot interact with realistic policy machinery is also limited.

The project already has a good base for both:
- a benchmark-oriented evaluation path,
- and a policy abstraction with room for a real policy engine. The later review also argued that one policy integration should be pinned, differential, and evidence-driven rather than broad and approximate. fileciteturn0file1

## Analysis

### Benchmark integration

Use benchmarks to answer concrete questions:
- Does the defence preserve benign utility?
- Does it block attack classes the benchmark exercises?
- Does it still work when the model is stronger or weaker?
- Does the defence remain correct under the benchmark’s exact task and policy assumptions?

Do not let benchmarks become the only evidence. They are useful for comparison, not for proof.

### Real-world policy integration

One policy engine should be integrated end-to-end with:
- a typed request schema,
- explicit supported features,
- unsupported-feature rejection,
- differential tests,
- policy versioning,
- and traceable decisions.

Fine-grained policy over tool arguments is the natural bridge between the benchmark and the production story.

A realistic first target is a policy language or engine that already has a clear notion of principal, action, resource, and request context. The implementation should then map Conflux principal context and tool arguments into that engine rather than re-implementing the engine from scratch.

## Rationale

This direction matters because it produces external validity. It shows that Conflux is not only a theoretical kernel, but can also interact with actual policy concepts and public evaluation settings.

It also helps prevent overclaiming. The project can say exactly what it supports, what it does not support, and which policy features were tested.

## Constraints

This work should not:
- silently approximate unsupported policy features,
- hide benchmark-specific assumptions,
- conflate benchmark success with universal security,
- or treat a single integration as proof of general enterprise readiness.

## Open questions

- Which benchmark should be the first comparison target?
- Which policy engine is most faithful to the Conflux model?
- Should policy integration happen before or after delegation semantics are finalised?
- What is the smallest usable crosswalk between benchmark metadata and policy decision records?

## Suggested first increment

Pick one benchmark and one policy engine, pin exact versions, and produce one fully retained experiment with raw outputs, trace translation, and a comparison table.
