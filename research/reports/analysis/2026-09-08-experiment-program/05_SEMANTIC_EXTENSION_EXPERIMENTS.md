# Semantic extension experiments

These are P1/P2 research tracks. Build formal/evaluation models before activating broad runtime features.

## Experiment S1 — Persistent-memory authority

### Research question

Can a low-authority principal's information acquire high authority merely because it is retrieved in a later high-authority session?

### Minimum memory state

Represent at least:

- memory ID/content hash;
- writer/producer provenance;
- write-session Principal Context;
- creation time/version;
- retrieval predicate;
- active/inactive state;
- validity/expiry;
- revocation/deletion status;
- whether content is authoritative vs ordinary information;
- activation history.

### Critical transition

Model `MemoryActivatedIntoContext`, not merely `MemoryExists`.

Activation must add conservative provenance to the current PC. A new session must not reset influence carried by activated persistent artefacts.

### Scenario matrix

1. low-authority writes memory -> high-authority session retrieves -> privileged action;
2. high-authority writes -> low-authority retrieves -> action authorised for both;
3. mixed-provenance summary stored -> later retrieval;
4. memory revoked before retrieval;
5. memory updated by a second low-authority principal;
6. irrelevant memory present but never retrieved;
7. two sessions with policy revocation between them;
8. attacker triggers retrieval predicate but cannot edit content.

### Properties

- no authority amplification from retrieval;
- provenance monotonicity across persistence;
- revocation semantics are respected;
- inactive memory does not contaminate PC merely by existing;
- observable confidentiality property where applicable.

### Deliverables

Start with finite SLED-V models and counterexamples. Add runtime integration only after the model is stable and covered by conformance tests.

---

## Experiment S2 — Rich argument/effect semantics

### Research question

Does modelling authority at operation-argument/effect granularity prevent cases that coarse action permissions miss, and what utility cost does it impose?

### Minimal typed operation set

Use a small interpretable set:

- `send(recipient, content_ref)`;
- `copy(source, destination)`;
- `delete(resource)`;
- `write(resource, content_ref)`;
- `query(resource, predicate)`.

### Trusted roles

Operation schemas, not model output, assign argument roles such as:

- authority-bearing resource selector;
- destination/recipient;
- content/data;
- credential reference;
- non-authority metadata.

### Scenario families

- both principals may send email but attacker selects an unauthorised recipient;
- both may write, but only one may write the selected resource;
- content provenance is low-authority while destination selector is high-authority;
- attacker controls only non-authority metadata;
- selector provenance unknown;
- mixed selectors derived from multiple principals.

### Metrics

- violations caught only by argument/effect layer;
- benign actions newly blocked;
- action-level vs argument-level decision disagreement;
- PC size by argument role;
- verification state-space growth.

### Acceptance criterion

The implementation must show at least one meaningful counterexample to coarse action-only authority and must not permit model-supplied role relabelling.

---

## Experiment S3 — Delegation activation gate

### Do not activate runtime delegation first.

Before runtime enablement, construct a verification and mutation suite covering:

- issuer authority to delegate;
- beneficiary;
- exact operation/resource/argument scope;
- expiry;
- use count;
- revocation;
- replay resistance;
- certificate binding;
- audience/visibility;
- nested/subplan behaviour;
- policy changes between grant and use;
- inability to redelegate unless explicitly allowed.

### Required result before activation

- canonical lifecycle model is safe under the stated delegation property;
- mutants for each omitted scope check are killed;
- implementation-to-IR conformance covers grant creation/use/revocation;
- evidence shows delegated authority is represented in `ACS_effective(e)` rather than by removing provenance or narrowing PC;
- `CreateDelegation` itself is independently authorised.

Only then make operational delegation configurable, initially opt-in and off by default.
