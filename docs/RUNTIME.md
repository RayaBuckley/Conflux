# Deterministic Runtime

## Scenario contract

`conflux.adapters.scenarios.load_scenario` reads UTF-8 YAML, validates the
version-1 scenario and proposal schemas, and constructs canonical immutable
domain values. Unknown fields, versions, Principals, input IDs, and action
kinds fail closed. Configuration cannot name Python callbacks or import code.

The scripted model returns checked proposal batches in declared order and
records the fingerprints of observed inputs. Exhaustion is an explicit failure
unless a fixture deliberately enables `repeat_last`.

## Providers

`InMemoryExecutor` is the deterministic test and demonstration boundary.
Results are idempotent by certificate ID; reuse with another action
fingerprint is rejected.

`ConfinedFilesystemExecutor` accepts only authorised primitive `write` actions
for the filesystem provider. It defaults to dry-run, confines resolved paths,
rejects traversal and symlinks, requires a precondition hash for live writes,
uses certificate-derived idempotency, and atomically replaces the target.

Provider failure remains separate from policy denial. Adapters cannot execute
during multi-branch exploration. `MediationService` reruns all policy dimensions
against the current environment and session immediately before each effect.
Revocation or certificate change blocks execution. Ordered plans stop at the
first action-time denial or provider failure.

## Rationale

| Runtime choice | Why |
|---|---|
| Strict versioned YAML | Fixtures stay portable without executable callbacks |
| Scripted model and memory executor | Contributors reproduce mediation without credentials |
| Dry-run filesystem default | A demonstration must not silently modify its host |
| Traversal and symlink rejection | Resolved paths must remain inside the declared capability root |
| Precondition hashes and atomic writes | Authority must apply to the state actually changed |
| Certificate-derived idempotency | Retries must not duplicate an effect |
| Failure distinct from denial | Infrastructure faults and successful defence mean different things |
