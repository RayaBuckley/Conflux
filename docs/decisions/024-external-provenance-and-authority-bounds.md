# ADR-024: External Provenance Non-Escalation and Authority Bounds

- Type: adr
- Status: accepted
- Date: 2026-09-03
- Owners: Conflux maintainers

## Context

Supervisor feedback (2026-09-02 feedback package) identified a critical
provenance modelling defect in earlier manuscript wording: tool outputs were
associated with "the principal on whose behalf the tool was invoked." This
conflates the source of an output with the principal who requested the
operation, enabling authority transfer to attacker-controlled content.

The feedback also identified three related gaps:

1. **No-laundering closure**: the repository enforces monotonic provenance but
   lacked an explicit formal statement that persistent artefacts, scheduled
   executions, and new assistant sessions cannot reset Principal Context.
2. **Authority versus harm**: ITES prevents authority amplification but does not
   prevent misuse of already-authorised actions; this distinction was not
   explicit in the security model.
3. **Authentication and utility**: authentication makes provenance sound but
   does not grant authority; two distinct problems (provenance uncertainty vs
   genuine low-authority influence) were not separated.

## Decision

1. **External-provenance non-escalation**: an externally fetched object retains
   the authenticated provenance of its actual source(s). It does not inherit the
   requesting user's organisational authority merely because the request was
   made on the user's behalf. Every object must distinguish producer/author,
   execution/agency, transport/tool identity, and provenance.

2. **No-laundering closure**: for ordinary derived objects,
   `PC(output) ⊇ PC(execution inputs)`. For scheduled executions,
   `PC(scheduled) includes PC(scheduling context)`. New assistant calls or
   sessions cannot reset Principal Context. Only an explicitly trusted,
   separately modelled transformation may reduce influence.

3. **Authority versus harm**: ITES prevents authority amplification relative to
   ACS granularity. It does not guarantee that authorised actions are safe,
   intended, or optimally parameterised. Three questions are distinguished:
   authority safety (ITES), intent within authority (not guaranteed), and
   policy adequacy (assumption).

4. **Authentication and utility**: authentication is in the TCB and establishes
   provenance soundness. It does not grant organisational authority.
   "Authentication makes the security decision accurate; it does not make the
   decision permissive."

5. **Trusted transformation model**: a trusted transformation is modelled as an
   explicit state transition with a trusted transformer identity, input
   provenance, output provenance, policy justification, and transformation
   certificate. Ordinary model-generated plans and object creation cannot
   perform this operation. Runtime endorsement remains unactivated.

## Consequences

- Provenance attachment for external sources must distinguish source identity
  from requesting identity.
- Persistent artefacts and scheduled executions must inherit Principal Context.
- The authority-vs-harm distinction is an explicit limitation in all papers and
  documentation, not just an implicit property.
- Future trusted-transformation work must specify and verify the transformation
  semantics before activation.
- The FLMSec paper, fourth-year manuscript, security model, related work,
  evidence ledger, and analysis documents must be updated to reflect these
  rules.

## Validation

- Security model documentation (`docs/reference/SECURITY_MODEL.md`) now
  includes the external-provenance, no-laundering, authority-vs-harm, and
  authentication-utility rules.
- FLMSec paper (`research/publications/flmsec_2026/main.tex`) tool-output
  provenance wording corrected.
- Claim ledger (`docs/evidence/CLAIMS.md`) records the new claims.
- Existing provenance monotonicity and branch isolation tests cover the
  no-laundering invariant. Additional regression tests for external-source
  provenance are planned as a separate phase.
- Source: `research/reports/archive/2026-09-02-supervisor-feedback-coder-package/`

Security impact: strengthens the provenance invariant by preventing authority
transfer via tool-output attribution; makes the authority-vs-harm boundary
explicit; closes the laundering hole for persistent and scheduled artefacts.
