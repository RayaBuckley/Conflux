# Cedar integration

Conflux has an optional, local Cedar policy adapter pinned to version `4.12.0`
and commit `fdcbaed32bdb8c8d13e4eaf2b58db5555e9fb8c5`. Core installation and CI do not
download or invoke Cedar.

## Offline preflight

```text
conflux policy cedar preflight \
  --bundle experiments/manifests/cedar-policy-bundle-v1.json \
  --corpus experiments/suites/cedar-differential-v1.json \
  --output output/runs/cedar-preflight
```

This validates the configured version, commit, checksum shape, supported
features, policy bundle, entities, differential cases, bounds, and translated
pointwise PARC requests. With `--binary PATH`, it also hashes the candidate
binary and compares the bytes with the bundle. It does not execute a policy
request. `conflux doctor --cedar-bundle BUNDLE --cedar-binary PATH --json`
performs the same identity check.

## Live gate

A future operator-gated parity run must execute every corpus case with the
exact pinned binary and retain its responses and hashes. Mixed Principal
decisions, explicit forbids, missing entities or attributes, malformed output,
timeouts, unsupported features, and identity drift deny. The adapter never
approximates an unsupported Cedar construct.

## Rationale

The in-memory oracle makes expected decisions inspectable, while Cedar supplies
an independent policy decision point. Keeping preflight separate from live
parity prevents successful request translation—or a plausible expected
answer—from being mislabeled as evidence that the real PDP agrees. A local,
pinned binary also avoids turning a hosted service or mutable release into an
unrecorded part of the trusted computing base.
