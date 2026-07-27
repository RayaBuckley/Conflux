# Codex-ready related-work rewrite for Conflux

This file is a paper-oriented condensation of the full research landscape. It is not a substitute for checking the source papers and bibliography keys before submission.

## Related work

### Model-level prompt-injection defences

Model-level defences attempt to make language models distinguish instructions from data or resist adversarial control through prompting, structured inputs, special tokens, detection, preference optimisation, fine-tuning, or re-execution. Representative approaches include Spotlighting, StruQ, SecAlign, DefensiveTokens, DataSentinel, and MELON. These methods can materially improve empirical robustness and therefore remain useful for utility: a model that resists an injection is less likely to abandon a benign task, propose blocked effects, or burden the user with approval requests. However, their security continues to depend on model behaviour and the evaluated attack distribution. Adaptive attacks and critical evaluations repeatedly show that benchmark robustness does not establish that a privileged effect can never be induced. Conflux therefore treats model-level methods as composable hardening, not as the authority-enforcement kernel.

### Architectural isolation and information-flow control

Dual-LLM architectures isolate a privileged planner from untrusted data processing. CaMeL extends this pattern with a custom interpreter, capabilities, and developer policies, obtaining deterministic enforcement for the instrumented execution while retaining dependence on trusted plan construction and application-specific policy specification. The system-level IFC line, including f-secure agents, FIDES, and RTBAS, treats the model as untrusted and propagates confidentiality/integrity or dependency labels through agent execution. These works are the closest foundations for Conflux's worst-case model assumption. Conflux differs in using authenticated principal identities as the integrity/authority label and querying the organisation's existing access-control system, rather than relying only on binary trust classes or a newly written security lattice. The two approaches are complementary: IFC provides mature confidentiality, declassification, and flow semantics that Conflux should adopt separately from authorization.

### Programmable privilege and runtime policy enforcement

Progent introduces a DSL for deterministic allow/forbid policies over tool names and typed arguments. An LLM may propose context-dependent policy updates, while an SMT solver distinguishes safe narrowings from privilege expansions; expansions require approval, yielding monotonic confinement. AgentSpec and AgentGuard similarly demonstrate programmable runtime enforcement. FORGE/PCAS expresses policies as Datalog over a causal dependency graph and instruments agent systems with a reference monitor. Its formal assume/guarantee contract makes explicit that enforcement correctness depends on the observability service supplying all policy-relevant events and predicates. Conseca generates contextual task policies, while authenticated-workflow and SecureClaw-style systems add approval and preview/commit boundaries.

Conflux should not claim to be the first privilege-control or deterministic agent-policy system. Its proposed distinction is the source of baseline authority: rather than synthesising the entire allowed effect set from a user task, Conflux derives authority from the identities of principals that causally control security-relevant values and from the existing ACS. Generated or developer policies may further restrict this baseline but cannot grant authority without an explicit delegation witness.

### Provenance granularity and action alignment

PACT identifies a granularity mismatch in whole-call and whole-execution defences. Untrusted information is dangerous when it determines an authority-bearing argument, such as a recipient, command, credential, selector, or transfer destination; it need not invalidate benign content arguments in the same call. PACT assigns semantic roles to arguments, propagates value provenance across replanning, and checks role-specific capability contracts. ARGUS, AuthGraph, ProvenanceGuard, NeuroTaint, AgentArmor, and Agent-Sentry variants likewise use influence graphs, evidence support, dual authority/execution graphs, semantic taint, program dependence, or execution provenance.

This work motivates a role-sensitive Principal Context. Every value should carry principal provenance, every effect argument should have a semantic role, and authorization should be checked only against the principals relevant to the corresponding authority decision. The current whole-execution ITES rule remains a conservative special case, but not the final state-of-the-art mechanism.

### Privilege escalation and delegated authority

SEAgent directly studies multiple forms of privilege escalation in LLM-agent systems using a mandatory-access-control framework, including multi-agent and confused-deputy cases. Capability systems, macaroons, Biscuit tokens, and decentralized IFC provide the foundational model for safe delegation: authority is explicit, scoped, attenuable, and cannot be amplified by an intermediary. Progent's policy-update rule similarly separates automatic restriction from approved expansion. Conflux should therefore define privilege escalation relative to both the underlying ACS and a set of valid delegation witnesses. A scoped, revocable, purpose- and resource-bounded delegation is authorised authority transfer, not an attack.

### Persistent state, causal influence, and multi-agent execution

Persistent memory changes the threat model because malicious content can be planted in one session and influence a later privileged effect. TMA-NM argues that content-based trust and ordinary derivation lineage can be laundered through summarisation, trusted-tool echo, or manufactured corroboration; it binds a non-malleable authority ceiling to the original memory write. Bad Memory empirically studies cross-session injection in coding agents. Long-horizon and internal-channel benchmarks such as AgentLAB and AgentLeak further show that final-output auditing misses preparatory steps, memory writes, sub-agent communication, and delayed triggers.

Causality Laundering adds a distinct implicit channel: a denied action and its feedback can causally influence a later permitted effect. Consequently, Conflux's history must include denied actions, approval outcomes, timing/error observations, memory writes, and cross-agent messages, not only successful data-flow edges. FORGE's partially ordered dependency graph is a better multi-agent substrate than a single linear transcript.

### Foundations: access control, information flow, provenance, and capabilities

The Conflux design draws on the reference-monitor principles of complete mediation, tamper resistance, and verifiability; access-matrix, RBAC, ABAC, and ReBAC authorization; Biba-style monotone integrity; decentralized information-flow control; noninterference and hyperproperties; capability security; and database/whole-system provenance. These foundations also delimit the claims. An authorization theorem does not imply task alignment, consent, safety, or confidentiality. Provenance describes origin and derivation but does not itself establish read permission or factual correctness. Real policy adapters must query a pointwise decision procedure over principal, action, resource, arguments, and context, preserving provider-native deny and obligation semantics.

### Evaluation

AgentDojo, InjecAgent, Agent Security Bench, AgentPI, AgentDyn, LivePI, Agent-SafetyBench, and other suites provide useful empirical workloads, but fixed attack collections do not establish system-level correctness. Adaptive evaluations, public competitions, and automated attacks expose benchmark saturation and underspecification. SLED addresses a different question by treating model behaviour as nondeterministic and checking the enforcement transition system. The revised claim should be bounded explicit-state verification, not unqualified exhaustive security: bounds, omitted states, incomplete traces, model assumptions, and the relationship between generated tasks and checked properties must be explicit. SLED 2 should add visited-state canonicalisation, partial-order reduction, mutation testing, adapter conformance, minimal counterexamples, and relational checks for confidentiality.

## Contribution positioning

The paper can safely claim the following if implementation and evidence match:

1. a principal-identity authority label whose semantics are derived from an existing ACS;
2. a role-sensitive Principal Context that binds authority-bearing arguments to authorised origins;
3. a proof that authority cannot silently increase without an explicit delegation/approval witness, under a complete-mediation and provenance-soundness contract;
4. a compositional separation of authorization, visibility, consent, safety, and task alignment;
5. a bounded model-checking evaluator for system-level agent defences, with mutation and adapter-conformance evidence;
6. empirical integrations showing the mechanism in a real agent framework and policy engine.

Avoid claims of being the first system-level agent defence, the first privilege-control mechanism, the first provenance-based guardrail, or the first privilege-escalation framing.

## Suggested subsection order

1. Model robustness and its limits.
2. Architectural isolation and IFC.
3. Programmable runtime policy and privilege control.
4. Provenance, authority binding, and role-sensitive arguments.
5. Delegation, capabilities, and workflows.
6. Persistent memory, causal influence, and multi-agent systems.
7. Evaluation and verification.
8. Precise differentiation of Conflux.
