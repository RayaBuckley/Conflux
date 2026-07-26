# Conflux Evaluation

Purpose: describe how SLED evaluates ITES and comparison defences, including
metrics, benchmark boundaries, reproducibility, and evidence reporting.

Owner: evaluation maintainers. This is the source of truth for methodology;
implementation details belong in `conflux.sled` docstrings and results belong
in versioned evidence artifacts.

## Evaluation layers

- SLED environments and scenarios define controlled security conditions.
- Attacks transform scenarios without changing core authorisation semantics.
- Defences mediate proposals or expose comparison behavior.
- Evaluators explore one-shot or bounded exhaustive behavior.
- Traces preserve evidence for classification and reporting.
- Statistics separate security outcomes from legitimate utility.
- Benchmark adapters translate external systems at the boundary.

## Evidence requirements

Every reported run records the environment, attack, defence, model/configuration,
provider configuration, seed, trace, metrics, and limitations. A benchmark
must measure the defence rather than embed benchmark-specific permission logic
in `core` or `ites`.

## Tracks

- Native SLED: deterministic, offline, benchmark-independent reference runs.
- System-level benchmark: abstract attacks against complete execution flows.
- Model-level reference: compatibility comparison with prior model-focused work.
- External adapters: AgentDojo, CaMeL, and Dual-LLM command/trace translation.

The paper is an archived research reference. New repository functionality is
post-paper work and must be labelled as such in results and status records.

Provider-neutral inputs are `conflux.domain.environment.DataItem` values in an
`EnvironmentSnapshot`. The older SLED `Data` and `Environment` classes are
translation-era compatibility APIs, not the long-term provider contract.

The canonical trace boundary is `conflux.evaluation.TraceRecord`: immutable,
sequence-numbered, detached mappings with an explicit schema version.

## Results template

Use the claim/evidence matrix formerly maintained in `MVP_RESULTS.md` when
recording a result. Do not present an unexecuted template as a result.
# Evaluation

Purpose: define reproducible evaluation mechanics and evidence. Owner: the
evaluation maintainers. This is the source of truth for methodology and trace
formats; security semantics belong in `docs/ARCHITECTURE.md`.

The clean-slate trace boundary is `conflux.evaluation.TraceRecord`. Records
are immutable, sequence-numbered, detached mappings with an explicit schema
version. Benchmark adapters may add payload fields, but may not reinterpret
security decisions or omit provenance evidence.
