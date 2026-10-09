# Optional Verification and Model Backends

Conflux runs without any of these packages. Install them only when a
specific backend or benchmark is needed.

## z3-solver (formal verification)

```bash
pip install conflux[verification]
```

Provides `z3-solver>=4.13`, required by the SLED-V Z3 bounded checker
(`src/conflux/verification/z3_backend.py`). Without it, Z3-based
verification calls return a missing-backend result.

## Local model inference

```bash
pip install conflux[local-model]
```

Provides `transformers>=4.45`, `torch>=2.4`, and `accelerate>=1.0`,
used by the local model adapter
(`src/conflux/adapters/models/local_transformers.py`).

## AgentDojo benchmark

```bash
pip install conflux[agentdojo]
```

Pins `agentdojo==0.1.35`. Required by the AgentDojo adapter
(`src/conflux/adapters/benchmarks/agentdojo_v1.py`).

## OpenAI-compatible API

```bash
pip install conflux[openai-compatible]
```

Provides `httpx>=0.27`, used by the OpenAI-compatible planner adapter
(`src/conflux/adapters/models/openai_compatible_planner.py`).

## nuXmv (symbolic model checking)

nuXmv is a standalone binary, not a Python package.

1. Download from <https://nuxmv.fbk.eu/>.
2. Place the `nuXmv` binary on `PATH`, or set the
   `CONFLUX_NUXMV_PATH` environment variable to its absolute path.
3. The symbolic backend
   (`src/conflux/verification/nuxmv_backend.py`) will locate it
   automatically.

The environment is read on every call, so an export in the shell that
runs the verification is enough, and an explicit
`NuXmvBackend(binary=...)` wins over it. A `CONFLUX_NUXMV_PATH` that
is set but unusable fails closed: the backend returns the
`optional_binary_unavailable:nuXmv` unknown verdict instead of
reporting a property as safe.

Which runner runs the binary: a path that `PATH` or the override
resolves is executed directly as a subprocess. WSL
(`wsl -d <distribution> -- bash -ic 'which nuXmv'`) is the fallback for
a Windows host whose nuXmv lives inside a distribution, and it is
probed only when the binary cannot be resolved locally.
`NuXmvBackend().resolved_binary()` returns the binary and
`NuXmvBackend().selected_runner()` the runner that will be used.

Without nuXmv installed, symbolic model-checking calls return a
missing-backend result.
