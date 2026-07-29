# Deterministic Runtime

## Scenario contract

`conflux.adapters.scenarios.load_scenario` reads UTF-8 YAML, validates it
against the version-1 scenario and proposal schemas, then constructs only
canonical immutable domain values. Unknown fields, schema versions,
Principals, input IDs, and action kinds fail closed. YAML is configuration
only: it cannot name Python callbacks or import code.

The scripted model returns checked proposal batches in their declared order and
records the fingerprints of inputs observed at each call. Exhaustion is an
explicit failure unless a fixture deliberately enables `repeat_last`.

## Providers

`InMemoryExecutor` is the default deterministic execution boundary for tests
and demonstrations. Results are idempotent by certificate ID, and reuse of a
certificate with a different action fingerprint is rejected.

`ConfinedFilesystemExecutor` accepts only authorised primitive `write` actions
addressed to the `filesystem` provider. It:

- defaults to dry-run;
- confines relative paths to one resolved root and rejects traversal,
  symlinks, directories, and unsupported operations;
- derives its idempotency key from the decision certificate unless the
  resource names an explicit key;
- requires a `precondition_sha256` for live writes (`missing` is the
  new-file precondition);
- writes through a temporary file, flushes it, and atomically replaces the
  target.

Provider failure remains separate from policy denial. These adapters do not
grant authority and cannot execute during multi-branch exploration; execution
still enters through `MediationService` with the exact report certificate.
Immediately before each effect, the service reruns all policy dimensions
against the current environment and session. Revocation or any certificate
change blocks execution. Ordered plans execute one certificate-bound step at a
time and stop at the first action-time denial or provider failure.
