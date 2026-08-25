# Workshop Review Pre-Mortem

Simulated reviewer objections for the FLMSec 2026 submission. Each objection is
mapped to the paper section that answers it, or to an acknowledged limitation.

## Reviewer A: Formal methods / security

### Objection 1: "This is bounded model checking, not proof."

**Answer**: The paper uses explicit bounded claim language throughout.
\textsc{SAFE} is reserved for exhausted finite state spaces;
\textsc{BOUNDED\_SAFE} is never promoted to proof. Section 4.1 states the
verdict semantics. Section 6 (Limitations) states that results are bounded to
finite models.

### Objection 2: "What exactly is the state machine?"

**Answer**: Section 2 defines the ACS tuple $(U, A, D, P, W, R)$ and the
execution model. Section 4.1 describes SLED's state-space exploration:
states contain the environment, ACS, data objects, accumulated influence,
pending executions, and possible actions. Section 4.2 describes the
serialisable verification IR with variables, transition rules, and invariants.

### Objection 3: "Why should I trust the abstraction?"

**Answer**: Section 4.2 acknowledges that the IR is a hand-written
abstraction of the runtime kernel and formal equivalence is not claimed.
Section 4.2 mentions differential conformance testing as a future direction.
The TCB box in Section 2.3 explicitly lists what is trusted and what is not
proved.

### Objection 4: "Biba already resembles this."

**Answer**: Section 3, paragraph after Theorem 2, explicitly states the
structural analogy to Biba's low-water-mark policy and the precise
distinction: Principal Context retains principal identities and derives
action-specific authority from an external ACS, rather than assigning a single
integrity label. The novelty is stated as the combination, not the integrity
mechanism itself.

### Objection 5: "Where is the implementation-refinement argument?"

**Answer**: Acknowledged in Section 6 (Limitations) and Section 4.2. The IR
shares canonical transition semantics with the runtime kernel, but formal
equivalence is not claimed. This is a known gap, not a hidden assumption.

## Reviewer B: LLM-agent security

### Objection 1: "How does this compare with CaMeL/Progent/PACT/FORGE?"

**Answer**: Section 6 (Related Work) discusses each system. Table 2 provides a
comparison along security property, provenance granularity, authority source,
model trust, policy language, and verification. Section 5.4 (RQ4) provides
comparative finite-model verification showing each satisfies its own property
while violating PE.

### Objection 2: "Does it work on realistic agents?"

**Answer**: The paper evaluates finite verification models, not live agent
deployments. AgentDojo integration is mentioned in Section 6 as pipeline
evidence only. The 1.5B model is too small for utility claims. This is
explicitly scoped.

### Objection 3: "Is Principal Context too conservative?"

**Answer**: Section 6 (Discussion) addresses the security-utility frontier:
the intersection rule is maximal under the PE objective. Recovering more
utility requires explicit delegation, trusted declassification, or a
different security objective. This is a fundamental trade-off, not an
implementation limitation.

### Objection 4: "Where is AgentDojo?"

**Answer**: Mentioned in Section 6 (Related Work) as complementary empirical
evaluation. The six-cell pipeline runs end-to-end, but the 1.5B model is too
small. This is integration evidence, not a headline result.

## Reviewer C: Agent evaluation

### Objection 1: "Why is this an agent verifier rather than ordinary software model checking?"

**Answer**: Section 4.1 states that SLED treats the language model as an
adversarial component producing arbitrary well-typed proposals. The transition
model includes nondeterministic model proposals, provenance propagation, and
security-property checking---not just software transitions. The verification
target is the defence's security semantics under arbitrary model behaviour.

### Objection 2: "Does it generalize beyond ITES?"

**Answer**: Section 5.4 (RQ4) demonstrates comparative verification of
Dual-LLM, CaMeL, Progent, and PACT defence abstractions, each encoded as
finite IR models. The IR/property interface is reusable: any system-level
defence that can be expressed as a transition system with security invariants
can be checked.

### Objection 3: "Where is the benchmark/evaluation contribution?"

**Answer**: The contribution is not a benchmark but a verification methodology:
SLED-V evaluates whether a defence satisfies its intended property under
arbitrary model behaviour, rather than testing robustness against a finite
collection of attacks. Sections 4 and 5 describe the method and evidence.

### Objection 4: "Does it provide actionable counterexamples?"

**Answer**: Yes. Every \textsc{UNSAFE} result includes a counterexample
(Section 4.3). Table 1 shows all 16 seeded defects are detected with one-step
witnesses. COI reduction preserves witnesses and lifts them to the original
model.

### Objection 5: "Is the evaluation reproducible?"

**Answer**: All tables are generated from versioned result JSON by
`scripts/generate_flmsec_tables.py`. Each generated `.tex` file includes a
SHA-256 provenance header. The NeurIPS checklist (Appendix A) documents that
all results are deterministic.
