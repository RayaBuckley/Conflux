# Manifests

Each YAML or JSON manifest must validate against
`schemas/experiment-manifest.schema.json`. The `source_commit` is the exact
producer commit, not a moving branch name. The run copies the manifest to
`manifest.json`, stores its canonical SHA-256 in `result.json`, and emits the
tokenised rerun command as `RERUN.txt`.

`planning-laptop-smoke-v1.json` is a protocol plan, not a resolved live-run
manifest. It contains no invented weight or binary hashes. Use
`scripts/prepare_laptop_smoke.py` after the operator has acquired and reviewed
the local artifacts; resolved protocols belong under ignored
`experiments/local-runs/` unless their resulting evidence is deliberately
curated.
