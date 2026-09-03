# Coder Package: [title]

> Template for dated task packages produced by external AI sessions and archived
> under `research/reports/archive/YYYY-MM-DD-name/`. Replace all bracketed
> placeholders. Delete sections that are not applicable.

Date: [YYYY-MM-DD]
Source: [supervisor meeting / literature review / self-directed / ChatGPT session]
Context: [Paste the contents of `docs/templates/REPOSITORY_CONTEXT_BRIEF.md`
here, or link to it if the coder already has repository access.]

## Summary

[2-3 sentences: what this package asks the coder to do and why.]

## Tasks

### T1: [title]

- **Security impact:** [none / specific invariant affected]
- **Files:** [expected file set — list each file]
- **Acceptance criteria:**
  - [ ] [testable condition 1]
  - [ ] [testable condition 2]
- **Evidence required:** [if applicable — what evidence to generate or update;
  otherwise delete this line]
- **Notes:** [implementation guidance, constraints, or links to ADRs]

### T2: [title]

- **Security impact:** [none / specific invariant]
- **Files:** [file set]
- **Acceptance criteria:**
  - [ ] [condition]
- **Evidence required:** [if applicable]

## Priority order

1. T1 — [reason]
2. T2 — [reason]

## Non-goals

- [Explicit list of what NOT to do — prevents scope creep]
- [e.g. "Do not activate delegation runtime; model only."]

## Human review points

- [When to stop and surface for human decision]
- [e.g. "Before generating evidence, confirm the fixture bounds with the
  supervisor."]

## Findings (optional)

If this package was produced from a review or analysis, list structured
findings using the repository's finding classification:

| Finding | Classification | Evidence | Suggested action |
|---|---|---|---|
| [description] | confirmed_defect / research_gap / design_hypothesis / documentation_drift / cleanup / rejected | [link or reference] | [T1 / T2 / defer] |
