# Conflux Status

The clean-architecture migration is complete: canonical values live in
`domain`, ITES has one transition kernel, SLED has a native bounded checker,
and legacy package surfaces have been removed.

Implemented evidence covers fail-closed Principal Context, independent policy
dimensions, provenance/read separation, deterministic branches, versioned
traces, decision certificates, bounded verification, minimal counterexamples,
and fail-closed experimental adapters. M0 archival integrity and a separate
current manuscript are complete. M1 now includes explicit alternative and
ordered-plan batches; ordered plans retain order, stop on denial, and preserve
per-step decision certificates.

M2 now supplies strict versioned YAML scenarios, deterministic trace/result
schemas, scripted and in-memory providers, a confined dry-run filesystem
executor, native `sled run`, and an installed `argparse` CLI. Commands whose
M4/M6/M7 backends do not yet exist fail closed with a documented unavailable
status.

M3 is complete for offline scripted evidence. Legacy-reproduction and
canonical suites are explicitly separated; five real negative-control engines
each yield a minimal witness while canonical ITES remains safe; and
`runs/smoke/` retains an authorised case, blocked attack, vulnerable control,
raw trace, result, generated table, manifest, rerun command, and checksums.

Production PDPs, complete mediation of real frameworks, real external
benchmarks, formal delegation, role-sensitive effects, persistent memory,
symbolic verification, and paper revision remain post-migration work.
