# ADR-001: Documentation ownership and navigation

- Status: accepted
- Date: 2026-07-25

## Context

Conflux has several specialised documents and agent instructions. Without a
central index, contributors may miss the relevant contract or roadmap.

## Decision

`docs/README.md` is the canonical documentation hub. `README.md` remains the
concise public landing page. Specialised documents own their specific subject;
they should link to, rather than duplicate, adjacent guidance.

## Consequences

Documentation is easier to discover and update. New substantial guidance must
have a clear home and a link from the hub.
