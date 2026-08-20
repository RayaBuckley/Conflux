# Conflux

Conflux is a research framework for **Principal-aware security in AI agents**.
It derives authority from the Principals whose information influences an
action, evaluates organisational policy at action time, and preserves
provenance through execution and planning.

The repository currently provides one fail-closed ITES mediation kernel,
bounded native SLED verification, serialisable solver-facing models,
deterministic runtime adapters, authenticated dynamic plans, and an offline
CLI. It is pre-1.0 research software, not a production security product.

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
conflux demo --scenario examples/basic.yaml --output runs/demo
conflux plan demo --output runs/plan-demo
conflux sled run --suite examples/basic.yaml --output runs/sled
conflux report runs/demo/result.json
```

The commands write schema-checked JSON and human-readable evidence beneath
`runs/`, which is ignored except for curated fixtures. A securely blocked
proposal is a successful security outcome. Optional unavailable backends fail
explicitly instead of weakening the offline path.

Validate a checkout with `python scripts/validate.py`; PowerShell users may
also run `.\scripts\validate.ps1`.

## Find the right documentation

- [Plain-language overview](docs/OVERVIEW.md)
- [Documentation by task](docs/README.md)
- [Human contribution workflow](CONTRIBUTING.md)
- [AI-agent collaboration contract](docs/AI_AGENT_GUIDE.md)
- [Security model](docs/reference/SECURITY_MODEL.md)
- [Current capabilities and limitations](docs/evidence/STATUS.md)
- [Current fourth-year manuscript](manuscript/README.md)
- [Historical report sources and analysis](reports/README.md)

The previous paper under `paper/` and the original reports are integrity-
protected historical evidence. They do not define current behavior.
