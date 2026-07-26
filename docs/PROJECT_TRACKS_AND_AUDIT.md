# Conflux Project Tracks and Repository Audit

Date: 2026-07-25  
Scope: source tree, tests, documentation, paper source, and development tooling.

This report identifies the different tracks explored by Conflux, the unfinished
parts visible in the repository, and the changes most likely to improve research
accuracy and AI-assisted development.

## Executive assessment

Conflux already contains the main conceptual layers: immutable core models,
provenance-preserving execution, Principal Context authorisation, ITES
mediation, SLED evaluation, provider adapters, and benchmark adapters. The
highest-value next step is to turn these layers into a trustworthy research
instrument by tightening contracts and producing end-to-end evidence.

The main risk is not lack of code. It is semantic drift between the paper,
prototype APIs, benchmark adapters, and tests. Several APIs are deliberately
abstract, but the repository does not yet make the boundary between a complete
implementation, a reference implementation, and a placeholder sufficiently
visible.

## Project tracks

### 1. Security model and formal semantics

Purpose: define the security contribution independently of any model,
benchmark, or provider.

Current evidence:

- `core/` models Principals, resources, permissions, artifacts, provenance,
  actions, consent, sessions, and visibility.
- `auth/` implements the intersection-style Principal Context checks.
- The paper defines influence tracking, maximal secure authorisation, and
  authority monotonicity.
- Existing tests cover basic provenance and owner-policy behaviour.

Highest-value work:

- Specify the exact semantics of Principal Context derivation, especially when
  provenance contains resources, tags, derived artifacts, or empty principal
  sets.
- Add executable invariant tests for authority monotonicity, no authority
  escalation through derivation, and mixed-context behaviour.
- Reconcile implementation behaviour with the paper's formal definitions and
  record any intentional prototype simplifications.

### 2. ITES mediation and secure execution

Purpose: mediate proposed primitive actions, nested execution, messages,
consent, visibility, and delegation while retaining provenance.

Current evidence:

- `ites/mediator.py` contains the main reference algorithm.
- `ites/state.py` stores immutable execution state and trace steps.
- `ites/properties.py` defines executable security properties.
- Tests cover primitive/nested actions, call budgets, determinism, and state
  immutability.

Unfinished or risky areas:

- The public callback types are broad (`Any`, `FrozenSet`, and legacy proposal
  coercion), making it easy for an adapter to bypass the intended action
  contract.
- The mediator contains both compatibility behaviour and current semantics;
  this makes it difficult to tell which path is normative.
- Delegation, consent, visibility, and provider execution need end-to-end tests,
  not only isolated authorisation tests.
- Recursive execution has a call budget but no clearly documented execution
  identity, cycle policy, cancellation policy, or stable nested-call result.

Highest-value work: define a typed proposal/result protocol, isolate legacy
coercion behind an adapter, and add scenario tests for every action family.

### 3. Policy and organisational access control

Purpose: represent realistic authority rather than static prompt trust labels.

Current evidence:

- `policy/` contains policy interfaces, an owner policy, generic adapters, and
  an AWS-shaped adapter.
- `providers/` contains filesystem and Docker abstractions.

Unfinished or risky areas:

- The owner policy is intentionally minimal and does not model teams, roles,
  delegation, approval workflows, time bounds, or revocation.
- Provider interfaces are broad abstract contracts with many unimplemented
  operations.
- Adapter failure semantics, policy decision provenance, and resource identity
  rules are not yet documented as stable contracts.

Highest-value work: create a small organisational fixture model first—owners,
teams, delegated permissions, revocation, and mixed Principal Contexts—then use
it to drive policy and provider integration tests before adding external policy
engines.

### 4. SLED evaluation and benchmark methodology

Purpose: measure the defence and legitimate utility at the system level without
embedding benchmark-specific shortcuts in the security boundary.

Current evidence:

- `sled/` contains environments, scenarios, attacks, defences, state-space
  evaluation, traces, classifications, statistics, reporting, and runners.
- Native system-level and model-level benchmark builders exist.
- Native and external benchmark result schemas exist.

Unfinished or risky areas:

- Only a small portion of the evaluator, provider adapters, report generation,
  and external adapters is covered by tests.
- Incomplete, truncated, and failed executions have several representations;
  their relation to success, violation, and utility needs one canonical policy.
- Benchmark result serialisation and cross-run comparison need regression tests.
- There is no documented experiment manifest or committed example showing a
  complete run from scenario to report.

Highest-value work: add a deterministic end-to-end SLED fixture, canonicalise
outcome states, and test result round-tripping and comparison.

### 5. External integrations and deployment realism

Purpose: connect the abstract security model to real providers, policy engines,
agent runtimes, and external benchmarks.

Current evidence:

- AgentDojo, CAMEL, and dual-LLM external wrappers are present.
- AWS-shaped policy and Docker/filesystem provider adapters are present.

Unfinished or risky areas:

- These integrations are largely protocol shells and cannot yet establish
  strong compatibility evidence without fixture commands or recorded traces.
- External dependencies and credentials are not represented by a reproducible
  integration-test contract.

Highest-value work: define a fake external runner/provider contract, test all
translation boundaries locally, and reserve live integrations for opt-in
experiments.

### 6. Research, paper, and evidence synchronisation

Purpose: ensure implementation claims, experiments, and paper claims remain
consistent and reproducible.

Current evidence:

- The LaTeX paper covers the threat model, ITES, SLED, results, and future work.
- Bibliography and diagrams are tracked.
- Documentation now includes status, roadmap, ADRs, reproducibility, and tests.

Unfinished or risky areas:

- There is no machine-readable mapping from paper claims to implementation
  modules, tests, and experiment outputs.
- The final PDF is tracked, but no documented paper build verification is
  available in the validation workflow.
- The bibliography is present, but literature review workflow is manual.

Highest-value work: add a claim/evidence matrix and an experiment manifest
format before expanding the paper or benchmark catalogue.

### 7. AI-agent development environment

Purpose: make repository work discoverable, bounded, reviewable, and repeatable
for AI agents.

Current evidence:

- Root and package-level `AGENTS.md` files exist.
- The documentation hub, feature specification, change checklist, roadmap,
  and ADRs now exist.
- Setup and validation scripts exist.

Unfinished or risky areas:

- The root instructions still contain placeholder sections such as “Describe
  every major directory and its purpose” rather than a fully maintained local
  contract.
- The setup script requires Python 3.12+ but the validation experience does not
  offer a clear diagnostic for interpreter discovery beyond failure.
- No CI workflow validates the documented commands.
- No automated documentation-link or terminology check exists.

Highest-value work: add CI, a lightweight docs consistency checker, and a
machine-readable project status/experiment manifest.

## Prioritised change queue

### P0 — establish trustworthy evidence

1. Add end-to-end SLED tests covering a legitimate action, a denied action, a
   mixed Principal Context, a nested execution, and a serialised report.
2. Add tests for consent, visibility, delegation, provider failures, incomplete
   traces, and benchmark result round-tripping.
3. Define and document canonical outcome states: success, security violation,
   blocked legitimate action, failed execution, and incomplete execution.
4. Create an experiment manifest containing code revision, scenario, attack,
   defence, model/provider configuration, seed, environment, and output paths.

### P1 — harden interfaces

1. Replace broad public `Any` callback contracts with typed protocol objects.
2. Separate legacy proposal coercion from the normative ITES action protocol.
3. Specify provider operation, resource identity, policy decision, and error
   contracts.
4. Add organisational fixtures for ownership, teams, delegation, revocation,
   and dynamic permissions.

### P2 — improve research operations

1. Add a claim/evidence matrix linking paper claims to code, tests, and results.
2. Add CI for setup, tests, coverage reporting, Ruff, mypy, and documentation
   consistency.
3. Add opt-in live integration workflows for external benchmarks and providers.
4. Expand scenario and attack coverage only after the evaluation contracts are
   stable.

## Zotero and literature workflow

Zotero would improve research accuracy and agent effectiveness, but it should be
introduced as a research-evidence integration, not as a runtime dependency.
Zotero's official Web API supports access to library items and collections, and
its documentation describes authenticated API access and standard BibTeX/RIS
import/export workflows ([Web API basics](https://www.zotero.org/support/dev/web_api/v3/basics),
[Web API overview](https://www.zotero.org/support/dev/web_api/),
[standardized import](https://www.zotero.org/support/kb/importing_standardized_formats)).

Recommended design:

- Keep `paper/iclr2026_conference.bib` as the reproducible, version-controlled
  citation snapshot used for builds.
- Add a future read-only Zotero export/synchronisation script that produces a
  deterministic BibTeX or CSL-JSON snapshot plus item keys, DOI, date, tags,
  and source collection metadata.
- Store credentials only in environment variables or a local secret store;
  never commit API keys or private library contents.
- Require explicit human review before changing the tracked bibliography.
- Use collection and tag conventions to separate threat-model papers, access
  control, prompt injection, agent benchmarks, and evaluation methodology.
- Link citations in the claim/evidence matrix to Zotero item keys and local
  bibliography keys.

This would improve literature recall, citation consistency, and provenance of
research decisions. It should not be used to automatically rewrite the paper
or inject unreviewed literature into implementation decisions. A first useful
milestone is a read-only export plus a bibliography-drift check in CI.

## Unfinished-part inventory

The following are intentional abstract methods rather than automatic defects,
but each needs an explicit status and contract:

- `sled/attack.py`: attack implementations must define metadata and scenario
  transformation semantics.
- `sled/task_suite.py`: task loading and stable ordering need a contract.
- `policy/base.py` and `policy/adapters.py`: policy evaluation and adaptation
  failure semantics need specification.
- `providers/base.py`: provider lifecycle, resource resolution, and execution
  errors need concrete local implementations and tests.
- `execution/operations.py`: operation composition and type compatibility need
  stronger interfaces.
- `ites/properties.py` and `ites/__init__.py`: property and ITES protocols need
  explicit versioning and result semantics.
- external benchmark wrappers: live command execution, credentials, timeouts,
  and trace translation need opt-in integration contracts.

These should not all be implemented immediately. The P0 evidence work should
decide which contracts are genuinely needed before the project expands its
surface area.

## Recommended next milestone

Build one complete, deterministic organisational SLED experiment: two or more
Principals, owned resources, one injected artifact, one nested execution, one
denied primitive action, one legitimate action, a complete immutable trace, a
canonical result file, and a test that reproduces the result. Then link its
implementation, tests, documentation, paper claim, and (when available)
literature rationale from a single evidence record.
