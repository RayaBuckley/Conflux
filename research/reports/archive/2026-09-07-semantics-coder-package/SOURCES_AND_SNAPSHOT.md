# Sources and inspected repository snapshot

This package synthesises user-confirmed semantic decisions from the 2026-09-06/07 discussion with a public-repository audit on 2026-09-07.

Key repository files inspected from public `main`:

- `README.md` — https://github.com/RayaBuckley/Conflux
- `docs/README.md` — https://github.com/RayaBuckley/Conflux/tree/main/docs
- `docs/OVERVIEW.md` — https://github.com/RayaBuckley/Conflux/blob/main/docs/OVERVIEW.md
- `docs/reference/SECURITY_MODEL.md` — https://github.com/RayaBuckley/Conflux/blob/main/docs/reference/SECURITY_MODEL.md
- `docs/reference/GLOSSARY.md` — https://github.com/RayaBuckley/Conflux/blob/main/docs/reference/GLOSSARY.md
- `docs/research/RESEARCH_OVERVIEW.md` — https://github.com/RayaBuckley/Conflux/blob/main/docs/research/RESEARCH_OVERVIEW.md
- `docs/research/RELATED_WORK.md` — https://github.com/RayaBuckley/Conflux/blob/main/docs/research/RELATED_WORK.md
- `docs/research/RESEARCH_QUESTIONS.md` — https://github.com/RayaBuckley/Conflux/blob/main/docs/research/RESEARCH_QUESTIONS.md
- `docs/decisions/015-open-ended-dynamic-planning.md`
- `docs/decisions/020-maximal-permissiveness-and-synthesis.md`
- `docs/decisions/024-external-provenance-and-authority-bounds.md`
- `docs/evidence/CLAIMS.md`
- `docs/evidence/STATUS.md`
- `docs/evidence/CHANGE_CATALOG.md`
- `docs/integrations/cedar.md`

Important observed current semantics/status:

- Root README describes one fail-closed ITES mediation kernel, bounded native SLED, authenticated dynamic plans, and pre-1.0 research status.
- Security model says models/planners/classifiers cannot grant authority or narrow Principal Context.
- Security model already distinguishes authority safety, intent/safety within authority, and policy adequacy.
- Delegation is modeled but runtime-disabled.
- Planning spec says planner output is untrusted and `ApprovalNode` manufactures no authority; `DelegationNode` remains blocked.
- Maximal-permissiveness spec fixes ACS for the base theorem and explicitly treats delegation as a separate extension.
- ADR-024 currently introduces a future trusted-transformation/endorsement direction; this package intentionally supersedes that forward-looking part.
- SLED/verification and empirical model/AgentDojo evidence are already treated as separate evidence surfaces in parts of the repo, but the new semantics should make the distinction explicit.

Historical conceptual basis also exists in the user's Part B report, where "data as privileged instructions" and secure delegation/ephemeral capability ideas were already discussed. Historical files should remain immutable per repo policy.

Because the repository changes rapidly, the coder must use the local checkout and `git grep` to discover any files added after this snapshot.
