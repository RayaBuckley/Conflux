# Conflux

Conflux is a research framework for **principal-aware security in AI agents**.
It derives authority from the principals whose information influences an
action, checks organisation policy at action time, and preserves provenance
through execution and planning.

The repository contains one fail-closed ITES mediation kernel, bounded native
SLED verification, serialisable solver-facing models, deterministic runtime
adapters, authenticated dynamic plans, and an offline CLI. It is pre-1.0
research software, not a production security product.

## What this repository is

- A reference implementation of the ITES authority-confinement design.
- A testbed for explicit authority, provenance, delegation, and bounded
  verification.
- A reproducible evidence repository: generated results, claim ledgers, and
  paper sources live beside the code.

## What it is not

- Not a production security product.
- Not a model-level prompt-injection detector. Model defences are useful, but
  ITES does not rely on model judgement for the confinement decision.
- Not evidence that the full AgentDojo matrix has been run. Some retained runs
  are breadth and adapter-coverage pilots; one selected 30-cell matrix reports
  task utility on read-only tasks, so its security count is vacuous. Full tool
  coverage and effect-bearing comparisons remain pending.
- Not a claim that every authorised action is semantically appropriate.
  Authority confinement and semantic judgement are separate questions.

## Rationale

Model-level defences are useful, but they are empirical and probabilistic.
An effectful action needs a decision that does not depend on model judgement.
Conflux therefore separates causal influence from normative authority:
provenance supplies the principals whose information reached a proposal, policy
decides whether those principals permit the exact effect, and execution
revalidates the decision before the effect runs. The design is deliberately
conservative. Unknown influence is treated as present, and missing authority
denies the action.

## Quick start

Requirements: Python 3.12 or newer. No credentials, model endpoint, container,
or solver is needed for the deterministic path.

On Windows PowerShell:

```powershell
.\scripts\setup.ps1
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Then run:

```sh
conflux doctor
conflux demo --scenario examples/basic.yaml --output research/output/runs/demo
conflux plan demo --output research/output/runs/plan-demo
conflux sled run --suite examples/basic.yaml --output research/output/runs/sled
conflux report research/output/runs/demo/result.json
```

The commands write schema-checked JSON and human-readable evidence beneath
`research/output/runs/`, which is ignored except for curated fixtures. A
securely blocked proposal is a successful security outcome. Optional
unavailable backends fail explicitly instead of weakening the offline path.

Validate a checkout with:

```sh
python scripts/validate.py
```

PowerShell users may also run `.\scripts\validate.ps1`.

## Core concepts

- **Principal Context:** the conservative set of principals whose information
  may have influenced a proposal.
- **ITES:** the influence-tracking and extrapolated-security kernel. Every
  influencing principal must independently pass policy before an effectful
  action can execute.
- **Authority vs influence:** influence is causal; authority is normative.
  Additional influence can reduce effective authority, never increase it.
- **SLED:** bounded explicit-state verification over finite models. Its
  verdicts are scoped to the declared model and assumptions.
- **Decision certificate:** binds an action, principal context, branch, and
  policy versions so execution can revalidate the decision.

## Evidence status

The current evidence is deliberately bounded:

- The deterministic path and finite-model verification are the strongest
  retained evidence.
- AgentDojo currently provides translation, adapter-coverage, and bounded
  pipeline-execution evidence. It does not establish a general defence or
  utility result; the full effect-bearing matrix is pending.
- The arXiv paper distinguishes finite-IR verification from the
  authority-confinement theorem, which is supported by a proof sketch under its
  stated assumptions.

Read [Status](docs/evidence/STATUS.md) and [Claims](docs/evidence/CLAIMS.md)
before reusing a number from this repository.

## Repository map

| Directory | Purpose |
|---|---|
| `src/conflux/` | Python package source (domain, ITES, policy, planning, verification) |
| `tests/` | Unit, security, integration, and reproducibility tests |
| `docs/` | Architecture, specifications, evidence, and research documentation |
| `scripts/` | Validation, evidence-generation, and setup scripts |
| `schemas/` | Versioned JSON schemas for structured output |
| `research/experiments/` | Experiment manifests, suites, baselines, and pinned lock files |
| `research/output/` | Generated run output and curated fixtures |
| `research/publications/` | arXiv source, fourth-year report, and archived papers |
| `examples/` | Minimal runnable examples |

## Documentation

Start with the path that matches your task:

- [Plain-language overview](docs/OVERVIEW.md)
- [Documentation by task](docs/README.md)
- [Security model](docs/reference/SECURITY_MODEL.md)
- [Formal semantics](docs/reference/SEMANTICS.md)
- [Current capabilities and limitations](docs/evidence/STATUS.md)
- [Decision records](docs/decisions/README.md)
- [Current arXiv source](research/publications/arxiv/README.md)
- [AI-agent collaboration guide](docs/AI_AGENT_GUIDE.md)

The archived paper under `research/publications/paper/` and the original
reports are integrity-protected historical evidence. They do not define current
behaviour.

## License

MIT. See `pyproject.toml`.
