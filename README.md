# Conflux

Conflux is a research framework for Principal-aware security in AI agents. It
models authority from the current **Principal Context** and organisational
policy decisions, while preserving the provenance of information that can
influence an action.

- **ITES** is the sole mediation transition kernel.
- **SLED** performs bounded explicit-state verification of that kernel.

The canonical dependency direction is:

```text
domain -> ports -> application -> adapters
             \-> ITES -> evaluation
```

Principals are identities, not permission containers. Authorisation,
readability, visibility, and consent are independent injected decisions.
Provenance never acts as a read ACL, missing context and consent fail closed,
and multiple model proposals are isolated alternatives.

Start with [the documentation hub](docs/README.md). Set up Python 3.12+ with
`.\scripts\setup.ps1`, then run `.\scripts\validate.ps1`.

The work-in-progress fourth-year paper lives in
[`manuscript/`](manuscript/README.md). The previous-year `paper/` tree is a
checksum-protected archive and is not evidence for the current implementation.
