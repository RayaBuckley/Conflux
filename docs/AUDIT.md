# Conflux Audit Ledger

Purpose: identify the required purpose, owner, evidence, and disposition of
every tracked file. This is the source of truth for file ownership and
consolidation decisions. The static audit script validates source docstrings,
links, and repository structure; reviewers validate the semantic fields below.

Disposition values: `canonical`, `compatibility`, `adapter`, `benchmark`,
`research artifact`, `tooling`, `deprecated`, or `remove`.

## Source and tests

| Path | Required purpose / owner | Evidence | Docs | Disposition | Risk |
|---|---|---|---|---|---|
| `src/conflux/__init__.py` | Package identity/version | imports | REFERENCE | canonical | version policy |
| `src/conflux/core/__init__.py` | Core public exports | package imports | REFERENCE | canonical | export drift |
| `src/conflux/core/principals.py` | Principal value and permissions | authorisation tests | ARCHITECTURE | canonical | policy semantics |
| `src/conflux/core/resources.py` | Protected resource value | policy/provenance tests | REFERENCE | canonical | provider metadata policy |
| `src/conflux/core/permissions.py` | Permission value normalization | policy tests | REFERENCE | canonical | provider mapping |
| `src/conflux/core/provenance.py` | Immutable causal metadata | provenance tests | ARCHITECTURE | canonical | resource/operation model |
| `src/conflux/core/artifacts.py` | Provenance-bearing values | artifact tests | ARCHITECTURE | canonical | compatibility methods |
| `src/conflux/core/actions.py` | Action taxonomy and proposals | ITES tests | REFERENCE | canonical | visibility semantics |
| `src/conflux/core/consent.py` | Consent decisions | ITES tests | ARCHITECTURE | canonical | policy integration |
| `src/conflux/core/chat_policy.py` | Visibility policy | ITES tests | ARCHITECTURE | canonical | terminology |
| `src/conflux/core/session.py` | Execution Principal Context/session | ITES state tests | ARCHITECTURE | canonical | state ownership |
| `src/conflux/execution/__init__.py` | Execution exports | imports | REFERENCE | canonical | narrow API |
| `src/conflux/execution/operations.py` | Provenance-preserving transforms | execution tests | REFERENCE | canonical | operation metadata |
| `src/conflux/auth/__init__.py` | Auth exports | imports | REFERENCE | canonical | export drift |
| `src/conflux/auth/authorisation.py` | Authority and action decisions | authorisation tests | ARCHITECTURE | canonical | mixed context rules |
| `src/conflux/policy/__init__.py` | Policy exports | imports | REFERENCE | canonical | export drift |
| `src/conflux/policy/base.py` | Policy request/decision contract | policy tests | REFERENCE | canonical | adapter contract |
| `src/conflux/policy/owner_policy.py` | Owner policy example | policy tests | EVALUATION | adapter | legacy owner shape |
| `src/conflux/policy/adapters.py` | Provider policy translation | imports | REFERENCE | adapter | incomplete providers |
| `src/conflux/policy/aws.py` | AWS-style policy adapter | imports | EVALUATION | adapter | external semantics |
| `src/conflux/ites/__init__.py` | Canonical ITES contract/exports | ITES tests | ARCHITECTURE | canonical | compatibility exports |
| `src/conflux/ites/mediator.py` | ITES mediation implementation | ITES/state tests | ARCHITECTURE | canonical | recursive branch evidence |
| `src/conflux/ites/state.py` | Immutable execution state | state tests | ARCHITECTURE | canonical | guarantee ownership |
| `src/conflux/ites/properties.py` | ITES property contracts | imports | ARCHITECTURE | canonical | abstract surface |
| `src/conflux/ites/mvp.py` | Historical MVP research harness | moved to research/mvp.py | EVALUATION | remove | relocated after zero-caller audit |
| `src/conflux/research/__init__.py` | Research namespace and artifact boundary | imports | EVALUATION | research artifact | not runtime API |
| `src/conflux/research/mvp.py` | Executable MVP research semantics | MVP tests | EVALUATION | research artifact | not canonical runtime |
| `src/conflux/ites/reference.py` | Historical reference ITES module | moved to compatibility/ites.py | REFERENCE | remove | relocated after zero-caller audit |
| `src/conflux/compatibility/ites.py` | Reference ITES compatibility implementation | compatibility tests | REFERENCE | compatibility | preserve research behavior |
| `src/conflux/providers/base.py` | Provider adapter contract | imports | ARCHITECTURE | adapter | SLED dependency |
| `src/conflux/providers/__init__.py` | Historical provider facade | moved to adapters/providers | ARCHITECTURE | remove | zero supported callers |
| `src/conflux/providers/filesystem.py` | Filesystem provider | imports | EVALUATION | adapter | host effects |
| `src/conflux/providers/docker.py` | Docker provider | imports | EVALUATION | adapter | optional runtime |
| `src/conflux/adapters/providers/base.py` | Provider capability and materialisation contracts | provider imports | ARCHITECTURE | adapter | legacy environment translation pending |
| `src/conflux/adapters/providers/filesystem.py` | Filesystem provider adapter | provider tests | EVALUATION | adapter | host effects |
| `src/conflux/adapters/providers/docker.py` | Docker provider adapter | provider tests | EVALUATION | adapter | optional runtime |
| `src/conflux/sled/__init__.py` | Historical SLED public exports | moved to evaluation | EVALUATION | remove | removed after graph move |
| `src/conflux/sled/environment.py` | Historical environment module | moved to evaluation/environment.py | EVALUATION | remove | removed after graph move |
| `src/conflux/sled/scenario.py` | Historical scenario module | moved to evaluation/scenario.py | EVALUATION | remove | removed after graph move |
| `src/conflux/sled/environment_suite.py` | Historical environment catalogue | moved to evaluation/environment_suite.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/task_suite.py` | Historical task suite contract | moved to evaluation/task_suite.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/task_sets.py` | Historical representative tasks | moved to evaluation/task_sets.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/attack.py` | Historical attack contract | moved to evaluation/attack.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/evaluator.py` | Historical evaluator module | moved to evaluation/evaluator.py | EVALUATION | remove | removed after graph move |
| `src/conflux/sled/benchmark_runner.py` | Historical suite orchestration | moved to evaluation/benchmark_runner.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/trace.py` | Historical execution traces | moved to evaluation/trace.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/counterexample.py` | Historical counterexample extraction | moved to evaluation/counterexample.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/task_classification.py` | Historical trace outcome labels | moved to evaluation/task_classification.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/task_result.py` | Historical task result normalization | moved to evaluation/task_result.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/statistics.py` | Historical outcome aggregation | moved to evaluation/statistics.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/reporting.py` | Historical reporting module | moved to evaluation/reporting.py | EVALUATION | remove | removed after graph move |
| `src/conflux/sled/evaluation.py` | Historical end-to-end evaluation driver | moved to evaluation/suite_evaluation.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/defence_evaluation.py` | Historical defence comparison workflow | moved to evaluation/defence_evaluation.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/model_benchmark.py` | Historical model benchmark | moved to evaluation/model_benchmark.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/system_benchmark.py` | Historical system benchmark | moved to evaluation/system_benchmark.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/defences/base.py` | Historical defence contract | moved to evaluation/defences/base.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/defences/__init__.py` | Historical defence package | moved to evaluation/defences | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/defences/no_defence.py` | Historical negative-control defence | moved to evaluation/defences/no_defence.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/defences/no_read_check.py` | Historical read-check negative control | moved to evaluation/defences/no_read_check.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/defences/union_permissions.py` | Historical union-authority negative control | moved to evaluation/defences/union_permissions.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/defences/latest_input_only.py` | Historical latest-input negative control | moved to evaluation/defences/latest_input_only.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/defences/initiator_only.py` | Historical initiator-only negative control | moved to evaluation/defences/initiator_only.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/sled/defences/ites_adapter.py` | Historical ITES evaluation adapter | moved to evaluation/defences/ites_adapter.py | EVALUATION | remove | relocated after graph move |
| `src/conflux/benchmarks/results.py` | Stable benchmark result schema | imports | EVALUATION | benchmark | schema versioning |
| `src/conflux/benchmarks/__init__.py` | Historical benchmark facade | moved to adapters/benchmarks | EVALUATION | remove | zero supported callers |
| `src/conflux/benchmarks/native.py` | Native benchmark adapter | imports | EVALUATION | benchmark | exhaustive coupling |
| `src/conflux/benchmarks/agentdojo.py` | AgentDojo adapter | imports | EVALUATION | adapter | optional dependency |
| `src/conflux/benchmarks/external/base.py` | External benchmark contract | imports | EVALUATION | adapter | command assumptions |
| `src/conflux/benchmarks/external/runner.py` | External command execution | imports | EVALUATION | tooling | process safety |
| `src/conflux/benchmarks/external/agentdojo.py` | External AgentDojo translation | imports | EVALUATION | adapter | external drift |
| `src/conflux/benchmarks/external/camel.py` | External CaMeL translation | imports | EVALUATION | adapter | external drift |
| `src/conflux/benchmarks/external/dual_llm.py` | External Dual-LLM translation | imports | EVALUATION | adapter | external drift |
| `src/conflux/adapters/benchmarks/native.py` | Native benchmark adapter | benchmark tests | EVALUATION | benchmark | legacy environment translation pending |
| `src/conflux/adapters/benchmarks/agentdojo.py` | AgentDojo benchmark adapter | benchmark tests | EVALUATION | adapter | optional dependency |
| `src/conflux/adapters/benchmarks/results.py` | Benchmark result schema | benchmark imports | EVALUATION | adapter | schema ownership |
| `src/conflux/adapters/benchmarks/external/base.py` | External benchmark adapter contract | imports | EVALUATION | adapter | optional dependency |
| `src/conflux/adapters/benchmarks/external/runner.py` | External command runner | imports | DEVELOPMENT | tooling | process assumptions |
| `src/conflux/adapters/benchmarks/external/agentdojo.py` | AgentDojo external translation | imports | EVALUATION | adapter | external drift |
| `src/conflux/adapters/benchmarks/external/camel.py` | CaMeL external translation | imports | EVALUATION | adapter | external drift |
| `src/conflux/adapters/benchmarks/external/dual_llm.py` | Dual-LLM external translation | imports | EVALUATION | adapter | external drift |
| `tests/AGENTS.md` | Local test rules | test guidance | DEVELOPMENT | tooling | keep concise |
| `tests/test_artifacts.py` | Artifact behavior tests | pytest | DEVELOPMENT | canonical | compatibility assertions |
| `tests/test_authorisation.py` | Authority invariant tests | pytest | DEVELOPMENT | canonical | legacy API assertions |
| `tests/test_benchmark_runner.py` | Runner integration tests | pytest | DEVELOPMENT | canonical | facade mismatch |
| `tests/test_execution.py` | Operation tests | pytest | DEVELOPMENT | canonical | operation metadata |
| `tests/test_ites.py` | Reference ITES tests | pytest | DEVELOPMENT | compatibility | legacy behavior |
| `tests/test_ites_mvp.py` | MVP semantics tests | pytest | EVALUATION | canonical | parallel semantics |
| `tests/test_ites_state.py` | State immutability tests | pytest | DEVELOPMENT | canonical | guarantee behavior |
| `tests/test_model_benchmark.py` | Model benchmark tests | pytest | EVALUATION | benchmark | reference-only |
| `tests/test_policy.py` | Policy contract tests | pytest | DEVELOPMENT | canonical | owner compatibility |
| `tests/test_provenance.py` | Provenance invariant tests | pytest | DEVELOPMENT | canonical | resource model |

## Tooling, documentation, and research artifacts

| Path | Required purpose / owner | Evidence | Docs | Disposition | Risk |
|---|---|---|---|---|---|
| `scripts/audit_repository.py` | Dependency-free structural audit | validation | DEVELOPMENT | tooling | ledger checks evolving |
| `scripts/setup.ps1` | Python environment setup | host validation | DEVELOPMENT | tooling | WindowsApps access |
| `scripts/validate.ps1` | Unified validation entry point | host validation | DEVELOPMENT | tooling | test failures |
| `pyproject.toml` | Build, dependency, tool configuration | package install | DEVELOPMENT | tooling | version drift |
| `.gitignore` | Exclude generated/local state | Git behavior | DEVELOPMENT | tooling | ignore drift |
| `README.md` | Project entry point | repository | docs/README | canonical | navigation drift |
| `AGENTS.md` | Repository-local AI rules | instructions | DEVELOPMENT | tooling | terminology consistency |
| `src/conflux/AGENTS.md` | Package-local rules | instructions | REFERENCE | tooling | overlap |
| `src/conflux/core/AGENTS.md` | Core security rules | instructions | ARCHITECTURE | tooling | overlap |
| `src/conflux/ites/AGENTS.md` | ITES security rules | instructions | ARCHITECTURE | tooling | overlap |
| `src/conflux/sled/AGENTS.md` | Historical SLED local rules | removed with obsolete package | EVALUATION | remove | root and evaluation rules supersede it |
| `paper/AGENTS.md` | Paper artifact rules | instructions | STATUS | research artifact | archive policy |
| `docs/README.md` | Documentation navigation | links | README | canonical | hierarchy migration |
| `docs/ARCHITECTURE.md` | System architecture | source/imports | ARCHITECTURE | canonical | API drift |
| `docs/REFERENCE.md` | Concepts/API ownership | source/imports | REFERENCE | canonical | export drift |
| `docs/DEVELOPMENT.md` | Development/testing workflow | scripts/tests | DEVELOPMENT | canonical | environment assumptions |
| `docs/EVALUATION.md` | Evaluation methodology | SLED modules | EVALUATION | canonical | result evidence |
| `docs/STATUS.md` | Evidence-backed status | tests/validation | STATUS | canonical | stale claims |
| `docs/AUDIT.md` | File-purpose ledger | inventory/imports | AUDIT | canonical | manual fields |
| `docs/GLOSSARY.md` | Terminology source | architecture | REFERENCE | canonical | duplicate terms |
| `docs/ITES_MVP_SEMANTICS.md` | Detailed MVP semantics reference | MVP tests | EVALUATION | compatibility | duplicate semantics |
| `docs/decisions/.gitkeep` | Preserve empty decisions directory | Git structure | ARCHITECTURE | tooling | unnecessary after ADRs |
| `docs/decisions/README.md` | ADR navigation | ADR files | ARCHITECTURE | tooling | decision drift |
| `docs/decisions/000-template.md` | ADR template | workflow | DEVELOPMENT | tooling | template maintenance |
| `docs/decisions/001-documentation-navigation.md` | Navigation decision | docs | AUDIT | tooling | superseded details |
| `docs/decisions/002-principal-context-terminology.md` | Terminology decision | glossary | REFERENCE | tooling | consistency |
| `docs/decisions/003-benchmark-independent-core.md` | Dependency decision | architecture | ARCHITECTURE | tooling | import drift |
| `docs/decisions/004-immutable-state-and-provenance.md` | Immutability decision | core/ITES | ARCHITECTURE | tooling | invariant drift |
| `docs/decisions/005-testing-and-validation.md` | Validation decision | scripts/tests | DEVELOPMENT | tooling | command drift |
| `docs/decisions/006-canonical-ites-contract.md` | ITES ownership decision | ITES modules | REFERENCE | tooling | compatibility drift |
| `docs/templates/FEATURE_SPEC.md` | Feature specification | workflow | DEVELOPMENT | tooling | required fields |
| `docs/templates/CHANGE_CHECKLIST.md` | Change completion checklist | workflow | DEVELOPMENT | tooling | checklist drift |
| `docs/AI_DEVELOPMENT_GUIDE.md` | Legacy workflow source | removed; migrated to DEVELOPMENT | DEVELOPMENT | deprecated | removed in cleanup commit |
| `docs/MODULE_GUIDE.md` | Legacy module map | removed; migrated to ARCHITECTURE/REFERENCE/AUDIT | REFERENCE | deprecated | removed in cleanup commit |
| `docs/TESTING.md` | Legacy test guide | removed; migrated to DEVELOPMENT | DEVELOPMENT | deprecated | removed in cleanup commit |
| `docs/REPRODUCIBILITY.md` | Legacy reproduction guide | removed; migrated to EVALUATION/DEVELOPMENT | EVALUATION | deprecated | removed in cleanup commit |
| `docs/EVALUATION_METHODOLOGY.md` | Legacy methodology | migrated to EVALUATION | EVALUATION | deprecated | consolidate |
| `docs/MVP_RESULTS.md` | Legacy results template | migrated to EVALUATION | EVALUATION | deprecated | evidence status |
| `docs/IMPLEMENTATION_STATUS.md` | Legacy status | removed; migrated to STATUS | STATUS | deprecated | removed in cleanup commit |
| `docs/ROADMAP.md` | Legacy roadmap | removed; migrated to STATUS | STATUS | deprecated | removed in cleanup commit |
| `docs/PROJECT_TRACKS_AND_AUDIT.md` | Legacy audit/tracks | removed; migrated to AUDIT/STATUS | AUDIT | deprecated | removed in cleanup commit |
| `paper/iclr2026_conference.tex` | Archived paper source | LaTeX artifact | STATUS | research artifact | claim synchronization |
| `paper/iclr2026_conference.pdf` | Archived paper output | PDF artifact | STATUS | research artifact | binary review |
| `paper/iclr2026_conference.sty` | Paper style dependency | LaTeX source | STATUS | research artifact | upstream provenance |
| `paper/iclr2026_conference.bst` | Paper bibliography style | LaTeX source | STATUS | research artifact | upstream provenance |
| `paper/natbib.sty` | Paper style dependency | LaTeX source | STATUS | research artifact | upstream provenance |
| `paper/fancyhdr.sty` | Paper style dependency | LaTeX source | STATUS | research artifact | upstream provenance |
| `paper/math_commands.tex` | Paper macros | LaTeX source | STATUS | research artifact | terminology |
| `paper/iclr2026_conference.bib` | Paper bibliography | LaTeX source | STATUS | research artifact | literature reproducibility |
| `paper/Branching.svg` | Paper diagram | LaTeX source | STATUS | research artifact | diagram drift |
| `paper/ITES_.svg` | Paper diagram | LaTeX source | STATUS | research artifact | diagram drift |
| `paper/ITES__.svg` | Paper diagram variant | LaTeX source | STATUS | research artifact | duplicate artifact |
| `paper/SLED.svg` | Paper diagram | LaTeX source | STATUS | research artifact | diagram drift |
| `paper/SLED__.svg` | Paper diagram variant | LaTeX source | STATUS | research artifact | duplicate artifact |

Rows marked deprecated remain as migration pointers until the canonical
documents have absorbed their unique evidence and all links are updated. No
 file is removed merely because it lacks a current import.

## Clean-slate migration additions

## Evaluation graph migration

The former `src/conflux/sled/` implementation graph now owns the canonical
evaluation modules under `src/conflux/evaluation/`. The old SLED package was a
facade-only compatibility boundary and has been removed after the source and
test import audit reached zero callers.

| Path | Required purpose / owner | Evidence | Docs | Disposition | Risk |
|---|---|---|---|---|---|
| `src/conflux/evaluation/environment.py` | Evaluation environment model | evaluation tests | EVALUATION | canonical | domain model convergence |
| `src/conflux/evaluation/evaluator.py` | One-shot and exhaustive evaluators | evaluator tests | EVALUATION | canonical | trace completeness |
| `src/conflux/evaluation/reporting.py` | Evaluation reports and summaries | reporting imports | EVALUATION | canonical | schema stability |
| `src/conflux/evaluation/trace.py` | Rich execution traces | external adapters | EVALUATION | canonical | evidence completeness |
| `src/conflux/evaluation/records.py` | Compact versioned trace records | trace tests | EVALUATION | canonical | schema evolution |
| `src/conflux/evaluation/defences/` | Comparison defence implementations | evaluation imports | EVALUATION | benchmark | adapter contracts |
| `src/conflux/evaluation/attack.py` | Attack contract | evaluation tests | EVALUATION | canonical | attack boundary |
| `src/conflux/evaluation/benchmark_runner.py` | Benchmark suite orchestration | benchmark tests | EVALUATION | canonical | evaluator contract |
| `src/conflux/evaluation/counterexample.py` | Counterexample extraction | evaluation imports | EVALUATION | canonical | trace assumptions |
| `src/conflux/evaluation/defence_evaluation.py` | Defence comparison workflow | evaluation imports | EVALUATION | canonical | metric overlap |
| `src/conflux/evaluation/environment_suite.py` | Environment catalogue | evaluation imports | EVALUATION | canonical | scenario scale |
| `src/conflux/evaluation/model_benchmark.py` | Model-level reference benchmark | model tests | EVALUATION | benchmark | post-paper scope |
| `src/conflux/evaluation/scenario.py` | Evaluation scenario | benchmark tests | EVALUATION | canonical | data model convergence |
| `src/conflux/evaluation/statistics.py` | Outcome aggregation | evaluation imports | EVALUATION | canonical | metric definitions |
| `src/conflux/evaluation/suite_evaluation.py` | End-to-end suite evaluation | evaluation imports | EVALUATION | canonical | orchestration overlap |
| `src/conflux/evaluation/system_benchmark.py` | System-level benchmark | evaluation imports | EVALUATION | benchmark | task coverage |
| `src/conflux/evaluation/task_classification.py` | Trace outcome labels | evaluation imports | EVALUATION | canonical | heuristic labels |
| `src/conflux/evaluation/task_result.py` | Task result normalization | evaluation imports | EVALUATION | canonical | utility/security split |
| `src/conflux/evaluation/task_sets.py` | Representative tasks | evaluation imports | EVALUATION | benchmark | intended behavior |
| `src/conflux/evaluation/task_suite.py` | Task suite contract | benchmark tests | EVALUATION | canonical | protocol compatibility |
| `src/conflux/evaluation/defences/__init__.py` | Defence package exports | evaluation imports | EVALUATION | canonical | export ownership |
| `src/conflux/evaluation/defences/base.py` | Comparison defence contract | evaluation imports | EVALUATION | canonical | decision schema |
| `src/conflux/evaluation/defences/initiator_only.py` | Initiator-only negative control | evaluation imports | EVALUATION | benchmark | security baseline |
| `src/conflux/evaluation/defences/ites_adapter.py` | ITES comparison adapter | evaluation imports | EVALUATION | adapter | mediation overlap |
| `src/conflux/evaluation/defences/latest_input_only.py` | Latest-input negative control | evaluation imports | EVALUATION | benchmark | security baseline |
| `src/conflux/evaluation/defences/no_defence.py` | Negative-control defence | evaluation imports | EVALUATION | benchmark | expected failures |
| `src/conflux/evaluation/defences/no_read_check.py` | Read-check negative control | evaluation imports | EVALUATION | benchmark | expected failures |
| `src/conflux/evaluation/defences/union_permissions.py` | Union-authority negative control | evaluation imports | EVALUATION | benchmark | security baseline |

| Path | Required purpose / owner | Evidence | Docs | Disposition | Risk |
|---|---|---|---|---|---|
| `src/conflux/domain/__init__.py` | Pure domain import surface | import test | ARCHITECTURE/REFERENCE | canonical | migration aliases remain |
| `src/conflux/domain/identity.py` | Explicit Principal Context | unit test | REFERENCE | canonical | Principal still comes from core |
| `src/conflux/domain/resources.py` | Provider-neutral resource identity | unit test | REFERENCE | canonical | adapters not migrated |
| `src/conflux/domain/provenance.py` | Typed derivation boundary | import test | REFERENCE | canonical | core provenance remains source |
| `src/conflux/domain/artifacts.py` | Domain artifact import | import test | REFERENCE | canonical | alias during migration |
| `src/conflux/domain/intents.py` | Declarative intent model | unit test | REFERENCE | canonical | not yet wired to ITES |
| `src/conflux/domain/decisions.py` | Independent decision values | unit test | REFERENCE | canonical | policy adapters not migrated |
| `src/conflux/ports/__init__.py` | Port export surface | import test | ARCHITECTURE | canonical | ports are initial contracts |
| `src/conflux/ports/model.py` | Model proposal Protocol | mypy | ARCHITECTURE | canonical | action generic migration pending |
| `src/conflux/ports/policy.py` | Policy decision Protocol | mypy | ARCHITECTURE | canonical | existing policy not adapted |
| `src/conflux/ports/resources.py` | Resource execution Protocol | mypy | ARCHITECTURE | canonical | provider boundary pending |
| `src/conflux/ports/tracing.py` | Append-only trace Protocol | mypy | EVALUATION | canonical | trace schema pending |
| `src/conflux/application/__init__.py` | Application use-case exports | import test | ARCHITECTURE | canonical | thin facade initially |
| `src/conflux/application/mediate.py` | Application mediation facade | integration test | ARCHITECTURE | canonical | delegates to current ITES |
| `src/conflux/adapters/__init__.py` | Adapter namespace | import test | ARCHITECTURE | canonical | implementations remain legacy paths |
| `src/conflux/adapters/providers/__init__.py` | Provider adapter namespace | import test | ARCHITECTURE | adapter | migration pending |
| `src/conflux/adapters/policy/__init__.py` | Policy adapter namespace | import test | ARCHITECTURE | adapter | migration pending |
| `src/conflux/adapters/models/__init__.py` | Model adapter namespace | import test | ARCHITECTURE | adapter | migration pending |
| `src/conflux/adapters/benchmarks/__init__.py` | Benchmark adapter namespace | import test | EVALUATION | benchmark | migration pending |
| `src/conflux/py.typed` | Type-checker package marker | package metadata | DEVELOPMENT | tooling | packaging validation pending |
| `tests/test_clean_architecture.py` | New boundary contract tests | pytest | DEVELOPMENT | canonical | expand into contract suites |
| `src/conflux/evaluation/__init__.py` | Evaluation contract exports | import test | EVALUATION | canonical | environment model convergence pending |
| `src/conflux/evaluation/trace.py` | Versioned immutable trace record | unit test | EVALUATION | canonical | JSON schema expansion pending |
| `src/conflux/domain/environment.py` | Provider-neutral data and snapshot values | pytest | ARCHITECTURE/EVALUATION | canonical | legacy SLED callers remain |
| `src/conflux/ports/environment.py` | Environment materialisation Protocol | mypy | ARCHITECTURE | canonical | provider implementations pending |
| `src/conflux/compatibility/__init__.py` | Explicit legacy/reference exports | import test | REFERENCE | compatibility | reference implementation remains |
| `src/conflux/compatibility/environment.py` | Deprecated SLED environment aliases | provider imports | EVALUATION | compatibility | migrate adapters to DataItem |
| `src/conflux/compatibility/proposals.py` | Legacy proposal translation boundary | no supported callers | REFERENCE | remove | removed after canonical ITES migration |
| `tests/test_environment_contract.py` | Environment boundary regression tests | pytest | EVALUATION | canonical | expand provider contracts |
| `src/conflux/application/policy.py` | Collective authorisation service | pytest | REFERENCE | canonical | visibility/consent composition pending |
| `src/conflux/evaluation/services.py` | Canonical evaluator exports | import test | EVALUATION | canonical | stable |
| `src/conflux/evaluation/reporting.py` | Canonical reporting exports | import test | EVALUATION | canonical | stable |
| `docs/decisions/007-legacy-code-mapping.md` | Archived implementation mapping decision | documentation review | ARCHITECTURE/REFERENCE | tooling | update as migration completes |
| `tests/test_policy_boundary.py` | Authorisation port behavior | pytest | REFERENCE | canonical | add visibility and consent cases |
| `tests/test_evaluation_contract.py` | Evaluator/result ownership tests | pytest | EVALUATION | canonical | add deterministic trace fixtures |
| `tests/test_evaluation_trace.py` | One-shot deterministic trace tests | pytest | EVALUATION | canonical | add exhaustive branch traces |
