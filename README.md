# Conflux

Conflux is a research framework for principal-aware security in AI agents. It
implements and evaluates the hypothesis that an agent should be modelled as
being influenced by multiple principals, with permissions determined by its
current **Principal Context** rather than by static prompt trust labels.

## Research system

Conflux has two complementary contributions:

- **ITES** is the provenance-aware defence architecture. It mediates proposed
  actions, preserves provenance through execution, derives the Principal
  Context, and applies authorisation, visibility, and consent checks.
- **SLED** is the evaluation framework. It constructs environments and
  scenarios, generates attacks, executes benchmark tasks, records traces, and
  reports security and utility outcomes.

The security model treats prompt injection as an influence attack. Information
from prompts, documents, tools, and generated artefacts retains provenance as
it flows through recursive execution. A primitive action is permitted only
when the relevant principals in its Principal Context are collectively
authorised for that action.

## Architecture

```text
core domain model
        ↓
execution and provenance-preserving operations
        ↓
authorisation and policy adapters
        ↓
ITES mediation
        ↓
providers and benchmark integrations
        ↓
SLED evaluation, traces, metrics, and reports
```

The core defence is independent of a particular model, agent framework,
provider, or benchmark. Adapters materialise realistic environments and
translate external traces without changing the security model.

## Repository structure

```text
src/conflux/core/          Immutable domain objects and action taxonomy
src/conflux/execution/     Provenance-preserving operations
src/conflux/auth/          Principal-aware authorisation functions
src/conflux/policy/        Policy interfaces and policy-provider adapters
src/conflux/ites/          ITES interfaces, mediation, and execution state
src/conflux/providers/     Filesystem and Docker environment adapters
src/conflux/sled/          Synthetic evaluation framework and defences
src/conflux/benchmarks/    Native and external benchmark integrations
tests/                     Unit and integration-oriented tests
docs/                      Architecture, terminology, and development guides
paper/                     Tracked LaTeX source, diagrams, and final PDF
```

## Design commitments

- Provenance is never silently discarded.
- Security decisions use the Principal Context, not static trust labels.
- Authorisation, visibility, and consent remain distinct decisions.
- Domain models are explicit, immutable where practical, and benchmark
  independent.
- Providers, policies, runtimes, and benchmarks are replaceable adapters.
- Evaluation measures both defence and legitimate utility.

## Documentation

Use the [documentation hub](docs/README.md) as the canonical index for
architecture, terminology, testing, reproducibility, agent development,
implementation status, roadmap, and architecture decisions.

## Development

The project targets Python 3.12 or newer. Create or refresh the local virtual
environment and install the development extras with:

```powershell
.\scripts\setup.ps1
```

Run the complete validation workflow with:

```powershell
.\scripts\validate.ps1
```

The environment is stored in `.venv/`, is ignored by Git, and should not be
committed. See [Testing](docs/TESTING.md) and [Reproducibility](docs/REPRODUCIBILITY.md)
for direct fallback commands and paper instructions. Detailed interface
contracts are maintained as the architecture is refined; the current public
extension points are described in the module guide.
