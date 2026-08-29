# Anonymous Supplementary Code Artefact Specification

## Goal
Provide enough implementation and test material for a FLMSec reviewer to inspect and reproduce paper-facing claims without exposing the full Conflux development repository or obvious author identity.

## Recommended principle
Export by **claim dependency**, not by repository folder.

For every claim exposed in the paper/appendix, list:
1. claim;
2. command that reproduces/checks it;
3. entry-point file;
4. internal imports/fixtures/configuration required;
5. expected output.

Copy the union of those dependency closures into a new clean artefact.

## Suggested inclusion tiers

### Required
- canonical core types used by submitted ITES;
- submitted ITES implementation/security kernel;
- tests directly checking influence propagation, authorisation, read rules, nested execution and branch semantics;
- minimal SLED code needed to reproduce the reported paper result or a documented representative check;
- result fixtures/manifests actually cited by the paper;
- minimal packaging/dependency files;
- anonymous reproduction README.

### Include if appendix uses them
- ITES extension implementation + focused tests;
- SLED-V IR/checker/backend code + focused tests + result manifests;
- AgentDojo adapter and smoke-test harness + fixture/configuration.

### Exclude by default
- git history;
- AGENTS/AI-development instructions;
- supervisor/project planning reports;
- literature-review notes;
- unrelated provider/cloud adapters;
- unfinished planning work;
- unpublished experimental branches;
- personal scripts;
- full benchmark checkouts;
- local caches/results not cited;
- generated coverage/site files.

## Proposed tree
```
flmsec-anonymous-artifact/
├── README.md
├── REPRODUCIBILITY.md
├── THIRD_PARTY_NOTICES.md
├── pyproject.toml
├── src/
│   └── <anonymous package>/
│       ├── core/
│       ├── ites/
│       ├── evaluation/
│       └── verification/       # only if SLED-V appendix included
├── tests/
│   ├── test_ites_*.py
│   ├── test_sled_*.py
│   └── test_verification_*.py  # if included
├── experiments/
│   ├── reproduce_core.sh/.py
│   └── agentdojo_smoke.*       # if included
└── results/
    └── paper-facing machine-readable outputs
```

## Automated identity scan
Search recursively, including hidden text/configuration, for:
- Raya / Buckley;
- Oxford / Keble;
- known email domains/addresses;
- `RayaBuckley`;
- `Conflux` if the project name itself makes the public repository trivially discoverable;
- github.com URLs;
- absolute home paths;
- author/maintainer metadata.

Also inspect archive/PDF/package metadata manually.

## Important caution
Renaming identifiers purely to hide authorship can make the supplementary code diverge from the reviewed implementation. Prefer removing identifying metadata and hosting anonymously. If renaming the package/project is necessary, make the transformation mechanical and rerun all tests after export.

## Validation gate
The AI coder must produce an `ANONYMISATION_AUDIT.md` recording:
- files included/excluded;
- identity-search patterns;
- findings and fixes;
- third-party notices;
- clean-environment commands;
- test/reproduction outputs;
- final archive SHA-256.
