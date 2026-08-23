# Conflux

Conflux is a research framework for **Principal-aware security in AI agents**.
It derives authority from the Principals whose information influences an
action, evaluates organisational policy at action time, and preserves
provenance through execution and planning.

The repository currently provides one fail-closed ITES mediation kernel,
bounded native SLED verification, serialisable solver-facing models,
deterministic runtime adapters, authenticated dynamic plans, and an offline
CLI. It is pre-1.0 research software, not a production security product.

## Repository map

| Directory | Purpose |
|---|---|
| `src/conflux/` | Python package source (domain, ITES, policy, planning, verification) |
| `tests/` | Unit, security, integration, and reproducibility tests |
| `docs/` | Architecture, specifications, evidence, and research documentation |
| `scripts/` | Validation, evidence-generation, and setup scripts |
| `schemas/` | Versioned JSON schemas for all structured output |
| `research/experiments/` | Experiment manifests, suites, baselines, and pinned lock files |
| `examples/` | Minimal runnable examples |
| `research/output/` | Generated run output and CI validation artifacts (curated fixtures tracked) |
| `research/publications/` | Current manuscript (`manuscript/`) and archived previous paper (`paper/`) |
| `research/reports/` | Historical report archive (`archive/`) and current analysis (`analysis/`) |
| `.github/` | CI workflows |

See also [AGENTS.md](AGENTS.md) for the AI-agent repository guide and
[docs/README.md](docs/README.md) for task-based documentation navigation.

## Why Principal Context?

An agent can combine instructions and data controlled by different people or
services. Treating the initial requester as the only authority lets an
untrusted contributor borrow permissions through the model. Conflux instead
uses a conservative **Principal Context**: every influencing Principal must be
authorised, while consent, visibility, and read access remain independent
restrictions.

## Run the offline system

Requirements: Python 3.12 or newer. No credentials, model endpoint, container,
or solver are needed for the deterministic path.

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
`research/output/runs/`, which is ignored except for curated fixtures. A securely blocked
proposal is a successful security outcome. Optional unavailable backends fail
explicitly instead of weakening the offline path.

Validate a checkout with `python scripts/validate.py`; PowerShell users may
also run `.\scripts\validate.ps1`.

## Find the right documentation

- [Plain-language overview](docs/OVERVIEW.md)
- [Documentation by task](docs/README.md)
- [Workflow](docs/AI_AGENT_GUIDE.md)
- [AI-agent collaboration contract](docs/AI_AGENT_GUIDE.md)
- [Security model](docs/reference/SECURITY_MODEL.md)
- [Current capabilities and limitations](docs/evidence/STATUS.md)
- [Current fourth-year manuscript](research/publications/manuscript/README.md)
- [Historical report sources and analysis](research/reports/README.md)

The previous paper under `research/publications/paper/` and the original reports are integrity-
protected historical evidence. They do not define current behavior.
