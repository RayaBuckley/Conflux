# Manifests

Each YAML or JSON manifest must validate against
`schemas/experiment-manifest.schema.json`. The `source_commit` is the exact
producer commit, not a moving branch name. The run copies the manifest to
`manifest.json`, stores its canonical SHA-256 in `result.json`, and emits the
tokenised rerun command as `RERUN.txt`.
