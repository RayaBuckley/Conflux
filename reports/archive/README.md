# Archived Report Evidence

Files below this directory are immutable historical inputs. Do not reformat,
correct, deduplicate, or update them. Add interpretation under
`reports/analysis/` instead.

## Package model

The archive uses five dated packages:

| Package | Historical role |
|---|---|
| `2026-07-27-engineering-and-sled` | Repository and SLED engineering diagnoses |
| `2026-07-27-literature-review-v1` | Initial literature synthesis and action manifest |
| `2026-07-27-research-landscape-v2` | Superseding research landscape and related-work materials |
| `2026-07-29-implementation-programme` | Canonical-migration and research delivery proposal |
| `2026-07-30-dynamic-planning-programme` | Progress assessment and dynamic-planning supplement |

`MANIFEST.json` records each original path, archive path, package, role, media
type, byte count, SHA-256 of the exact repository blob, and Git blob ID. It also
records duplicates, source limitations, and supersession links.

## Rationale

Repository blob identity is used because checkout line endings are not stable
evidence bytes. Known duplicates remain present and declared: deletion would
change the historical source package. Source-qualified task IDs are required
because unrelated report backlogs reuse identifiers such as `TRACE-001` and
`PLAN-001`.

Archive ingestion is append-only. A new report creates a new package and
manifest entries; it never changes an existing artefact.
