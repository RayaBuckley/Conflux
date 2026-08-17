# Test guidance

Tests must cover security invariants, not only happy paths. For security
changes include allowed, denied, mixed-Principal Context, provenance, nested
execution, immutability, and regression cases where applicable. Keep tests
independent of external services unless explicitly marked integration tests.

## Mandatory security test categories

Every security-relevant change must include tests from each applicable
category:

| Category | What to test | Example |
|---|---|---|
| Empty context | Actions denied when `is_authority_bearing` is false | `test_empty_context_denies_effect` |
| Mixed Principal | Every Principal in context must independently allow | `test_mixed_context_requires_every_principal` |
| Provenance accumulation | Merging never drops Principals; unknown propagates | `test_provenance_merge_never_drops_principals` |
| Decision independence | Consent/visibility cannot override authorisation | `test_missing_consent_denies_effect` |
| Immutability | Domain values cannot be mutated after construction | `test_domain_values_are_immutable` |
| Nesting | Nested execution merges input provenance into context | `test_nested_execution_accumulates_provenance` |
| Revocation | Policy change between decision and execution blocks | `test_execution_reauthorises_and_observes_policy_revocation` |
| Failure distinct from denial | Provider failure is not a policy denial | `test_provider_failure_is_recorded_separately` |
| Fail-closed | Errors, unknowns, missing, and unavailable deny | `test_delegation_is_unsupported` |

## Semantics testing

The formal semantics are in [docs/SEMANTICS.md](../docs/SEMANTICS.md). Each
SEM-* property has a corresponding test. When adding a new property, add a
test that:

1. Exercises the property on the canonical implementation.
2. Constructs a mutant that violates the property.
3. Verifies that SLED or the direct test kills the mutant.

### Semantic corpus (`tests/semantics/test_corpus.py`)

Corpus entries verify that direct `DecisionPipeline.decide` and
`TransitionKernel.expand_batch` produce conforming results for representative
scenarios. Add corpus entries when adding new decision paths or action types.

### Mutation killing (`tests/semantics/test_mutation_killing.py`)

Each mutant in `tests/semantics/mutants.py` violates exactly one security
property. When adding a new security property, add a corresponding mutant and
a test that SLED or a direct assertion kills it with a minimal witness.

### Algebraic laws (`tests/semantics/test_algebraic_laws.py`)

Tests for commutativity, associativity, idempotence, and monotonicity of
domain merge operations. These are referenced from SEM-001 and SEM-003.

## Test file organisation

| Directory | Scope |
|---|---|
| `tests/` (root) | Unit and integration tests per module |
| `tests/semantics/` | Algebraic laws, corpus, and mutation killing |
| `tests/planning/` | Dynamic planning, sandbox, and SLED planning |
| `tests/integration/` | Cross-boundary and negative-control integration |

## Fixture conventions

Shared fixtures live in `conftest.py`. Security tests should use `alice`,
`bob`, and `mallory` principals. The `pipeline` fixture provides a standard
decision pipeline with alice and bob grants. For adversarial or combinatorial
cases, construct fixtures locally rather than modifying shared ones.
