---
document_id: conflux-literature-review-2026-07-27
project: Conflux
report_type: comprehensive_foundational_and_related_work_review
snapshot_date: 2026-07-27
primary_question: "How should Conflux position, formalise, evaluate, and extend principal-provenance-based security for LLM agents?"
primary_artifacts:
  - Preprint.pdf: "Influence Tracking for Secure LLM Agents: Preventing Privilege Escalation Under Worst-Case Model Behaviour"
  - Raya_Project_Report.pdf: "Securing LLM Assistants via Fine-Grained Provenance-Based Authority"
  - repository: "https://github.com/RayaBuckley/Conflux/"
intended_readers:
  - project_author
  - academic_reviewers
  - Codex and other repository agents
confidence_convention:
  high: "Directly supported by primary paper, supplied artifact, or formal derivation"
  medium: "Strong synthesis or comparison, but implementation details should be checked against the latest source"
  exploratory: "Research proposal requiring validation"
status_labels:
  KEEP: "Retain as a central contribution"
  QUALIFY: "Retain with narrower language and explicit assumptions"
  REFRAME: "Present under a more defensible conceptual framing"
  ADD: "Missing material that should be added"
  TEST: "Requires a new experiment or implementation check"
---

# Conflux: Comprehensive Review of Foundational and Related Work

## Executive assessment

Conflux has a strong central thesis: an LLM should not be treated as a trustworthy decision-maker with ambient authority. Instead, every externally visible effect should be mediated by a reference monitor whose decision is based on the principals that may have influenced the computation. The supplied project report developed this as **Influence Tracking and Extrapolated Security (ITES)** and introduced **SLED**, an exhaustive system-level evaluator. The preprint then sharpened the security objective from prompt-injection resistance to prevention of privilege escalation, formalised authority as the intersection of the permissions of all influencing principals, and presented bounded exhaustive results over approximately 1.46 million traces.

That thesis remains valuable, but the literature moved rapidly during 2025-2026. It is no longer defensible to position the work simply as the first system-level, provenance-based, privilege-escalation defence. FIDES, CaMeL, Progent, Conseca, FORGE, SEAgent, PACT, ARGUS, AgentArmor, and several newer systems now occupy adjacent territory. In particular:

- **SEAgent** independently frames LLM-agent attacks as privilege escalation and applies mandatory access control over an information-flow graph.
- **PACT** demonstrates that whole-execution or whole-tool-call provenance is too coarse for mixed-trust workflows and moves enforcement to individual action arguments.
- **FIDES** provides a direct information-flow-control formulation with confidentiality and integrity labels.
- **FORGE** provides an assume/guarantee observability contract, Datalog policy semantics, and reference-monitor enforcement across multi-agent histories.
- **ARGUS** and related work track causal provenance to justify individual action arguments against user intent and runtime evidence.

The strongest defensible novelty is therefore more specific:

1. **Principal-identity provenance as an authority label.** Conflux tracks *which principals* may have influenced a computation rather than assigning only binary trusted/untrusted or scalar integrity labels.
2. **Authority derived from an existing access-control system.** The effective action set is the meet/intersection of the action permissions of those principals, rather than a bespoke prompt-injection policy or a fixed trust hierarchy.
3. **A definition-relative maximality result.** Given the strict objective that every influencing principal must already be authorised for an action, the permission intersection is the unique maximal safe action set.
4. **Worst-case separation of model utility from enforcement security.** The model can behave arbitrarily; model behaviour changes which permitted action is proposed, but not whether an impermissible action is executed.
5. **SLED as a bounded explicit-state verifier for agent reference monitors.** This is more precise and defensible than calling SLED merely a benchmark.
6. **The emerging Principal Context abstraction.** The current repository separates authorization, visibility, consent, execution, policy, and provenance. Formalising this separation can become a larger contribution than the original ITES rule alone.

The most important technical conclusion is that the next version should not preserve a single flat `Influence(execution)` set as the final abstraction. It should generalise it into **role-sensitive Principal Context**:

- provenance is tracked per value and per action argument;
- arguments are classified by semantic role, such as target, command, selector, content, credential, or control;
- authorization, confidentiality/visibility, and consent are checked separately;
- authority may increase only through an explicit, scoped, attenuating delegation object;
- every adapter that introduces data or performs an effect must satisfy a formal provenance and mediation contract.

This change absorbs the central lesson of PACT while preserving Conflux's more distinctive use of real principals and existing organizational authorization. It also gives a coherent path from the original report to production software.

## 1. Scope, method, and evidence quality

### 1.1 Materials reviewed

This report synthesises four evidence classes:

1. The supplied 48-page project report, including the original implementation appendix and proposed extensions.
2. The supplied 15-page anonymous preprint, including its formal definitions, theorems, SLED model, and aggregate evaluation tables.
3. The public Conflux repository description and recent project context. The repository now describes a modular system with `core`, `execution`, `auth`, `policy`, `ites`, `providers`, `sled`, and `benchmarks` components, and distinguishes authorization, visibility, and consent.
4. Primary and recent literature available up to 27 July 2026, with priority given to original papers, official standards, and primary project pages.

The repository analysis in this report is architectural rather than a line-by-line code audit. The public README and recent project context were available, but a full remote checkout was not reliably retrievable in the research environment. Any claim about an exact class, interface, or test should therefore be validated against the current branch before Codex edits code.

### 1.2 Terminology used in this report

- **Principal**: an identity represented by the authorization system, including a human, service account, workload, external organization, or trusted infrastructure component.
- **Influence**: a conservative may-depend-on relation. If a value or action may depend on a principal's contribution, that principal is included.
- **Provenance**: structured evidence about entities, activities, sources, transformations, and responsible principals.
- **Authority**: the set of effects that a principal or execution is permitted to cause.
- **Principal Context**: the proposed generalized runtime security state containing provenance, authorization-relevant principals, observers, consent, delegations, and obligations.
- **System-level guarantee**: a guarantee enforced by trusted code outside the LLM, conditional on the stated trusted computing base and environmental assumptions.
- **Bounded exhaustive evaluation**: complete exploration of all states within a finite abstraction and declared bounds. It is not an unbounded proof of the implementation.

### 1.3 Evidence cautions

Many 2026 works are recent arXiv preprints. Their claims are useful for novelty analysis, but not all have completed peer review. Experimental numbers should be treated as reported results, not independently reproduced facts. For Conflux's paper, it is safer to compare mechanisms, threat models, trusted components, and formal objectives than to build an argument around small benchmark differences.

## 2. Evolution of the Conflux work

### 2.1 Project report: the original contribution package

The project report contains a broader design space than the current preprint. Its central model is:

\[
\mathrm{Influence}(d_s)=\bigcup_{d\in d_s}\{u\mid W(d,u)\},
\]

and an action is permitted iff:

\[
\forall u\in \mathrm{Influence}(e),\;P(u,a).
\]

The report also includes three extensions that should not be lost:

1. **Data as privileged instructions.** Marked data can act as an ephemeral delegation mechanism.
2. **Harmless-action exceptions.** Manually specified policies may allow selected actions even when the strict privilege-escalation rule would block them.
3. **Additional safety restrictions.** High-impact or irreversible actions may be rate-limited, approval-gated, or prohibited independently of authorization.

It further identifies a key problem that the preprint only briefly retains: legitimate workflows sometimes require controlled privilege transfer. The report proposes explicit delegation and recognizes that this changes the access-control state. It also notes possible leakage through allow/deny outcomes and the role of information bottlenecks.

Assessment:

- **KEEP** the strict core as a baseline policy.
- **ADD** delegation as a first-class formal object rather than an informal extension.
- **REFRAME** harmless-action exceptions as a separate safety/consent policy layer, not as a weakening of provenance semantics.
- **ADD** the access-control side-channel observation to the limitations and evaluation plan.

### 2.2 Preprint: stronger security framing and cleaner formal story

The preprint improves the work in several ways:

- It states that prompt injection is a mechanism, while privilege escalation is the system-level security objective.
- It gives a clearer influencing-principal definition and replaces the earlier attack-chain definition with a direct property over each executed action.
- It separates the access-control system, influence propagation, authorization rule, maximality theorem, monotonicity theorem, and corollary.
- It presents SLED as a worst-case nondeterministic model rather than an attack corpus.
- It distinguishes implementation validation from the formal result, although this distinction should be made even stronger.

The paper's best sentence-level idea is: **security should not depend on deciding whether an input is malicious; it should depend on whether every source allowed to control an effect possesses the necessary authority.** This should remain the organizing principle.

### 2.3 Current repository: from ITES to Principal Context

The current repository description broadens the architecture beyond the preprint. It treats ITES as a mediator around proposed actions, preserves provenance, derives a Principal Context, and applies distinct authorization, visibility, and consent checks. SLED is being generalized into environments, scenarios, attacks, benchmark adapters, trace recording, and reporting. Existing access-control systems and benchmark implementations are intended to be replaceable.

This is the right direction. The paper should be updated so that the repository is not presented as merely an implementation of the 15-page formalism. The repository is becoming a general agent security substrate in which ITES is one authorization policy over Principal Context.

A useful conceptual decomposition is:

```text
Untrusted and trusted inputs
        |
        v
Provenance acquisition and propagation
        |
        v
Principal Context construction
        |
        +--> Authorization: who may cause this effect?
        +--> Visibility: who may observe the derived information?
        +--> Consent: who requested or approved this effect?
        +--> Safety policy: is the effect permitted regardless of authority?
        +--> Delegation: is there a valid scoped transfer of authority?
        |
        v
Reference monitor / complete mediation
        |
        v
Tool or external effect
```

This decomposition maps much better to classical security and current related work than a single permission-intersection rule.

## 3. Foundational work and how it maps to Conflux

### 3.1 Reference monitors and secure design principles

The reference-monitor tradition is the most important missing foundation. Saltzer and Schroeder's principles explain why system-level enforcement is preferable to model obedience:

- **Complete mediation**: every security-relevant action must be checked. Conflux must intercept every effect path, including direct SDK calls, retries, background jobs, nested agents, and alternate tool transports.
- **Fail-safe defaults**: missing provenance, an unknown principal, an unknown action schema, or an unavailable policy decision point must deny or require approval.
- **Least privilege**: agent and tool credentials should be attenuated to the current task rather than exposing a user's full ambient authority.
- **Separation of privilege**: high-impact actions can require both authorization and explicit consent/approval.
- **Economy of mechanism**: the trusted computing base should be small, deterministic, and independently testable.
- **Psychological acceptability**: approvals and explanations must be usable enough that users do not blindly approve everything.

The preprint assumes correct enforcement but does not define complete mediation operationally. The production contribution should include an **effect boundary specification**: every adapter declares which operations are reads, writes, external observations, authority changes, or delegation events, and all such operations pass through one reference-monitor API.

### 3.2 Access matrices, RBAC, ABAC, and relationship-based authorization

The tuple `(A,U,D,P,W,R)` is an intentionally small access-control model. It is useful for proofs but should be related to established models:

- Lampson's access matrix represents rights of subjects over objects.
- RBAC assigns permissions through organizational roles and supports role hierarchies and separation-of-duty constraints.
- ABAC evaluates attributes of the subject, object, operation, and environment against policy.
- Relationship-based systems such as Zanzibar/OpenFGA derive permissions through graph relations.
- Policy engines such as Cedar and OPA/Rego evaluate parameterized requests with contextual attributes.

The current relation `P subseteq U x A` can encode parameterized actions only by treating every fully instantiated action as an atom. That is mathematically valid but operationally awkward. The production model should use:

\[
\mathrm{Authorize}(u, op, resource, args, env)\in\{allow,deny\}.
\]

Then the intersection rule becomes pointwise:

\[
\mathrm{ITESAllow}(ctx,a)\iff
\forall u\in\mathrm{AuthoritySources}(ctx,a),\;
\mathrm{Authorize}(u,a)=allow.
\]

This lets Conflux integrate with existing policy decision points without enumerating an infinite action universe. It also makes revocation, time, location, tenancy, resource ownership, and row-level permissions explicit.

### 3.3 Biba integrity and the low-water-mark analogy

ITES is closely related to the Biba integrity model and should cite it directly. A Biba low-water-mark policy lowers a subject's integrity after reading lower-integrity data, preventing that subject from later writing to higher-integrity objects. ITES similarly ensures that additional influence cannot increase authority.

The analogy is not identity:

- Biba usually uses a fixed integrity lattice or ordered levels.
- ITES uses a set of named principals and an action-sensitive interpretation through each principal's permission set.
- Two principals may have incomparable permissions; there need not be a single scalar trust ordering.
- The same influence set may permit one action and deny another.

A strong formal framing is to define each principal's authority as a subset of actions and use set inclusion as an authority lattice. The effective authority is the meet:

\[
\mathrm{EffAuth}(I)=\bigcap_{u\in I}\mathrm{Auth}(u).
\]

This makes the monotonicity theorem an instance of meet monotonicity. It clarifies that the novel element is not the abstract fact that taint lowers privilege, but the construction of the lattice from the organization's actual principal permissions.

### 3.4 Bell-LaPadula, confidentiality, and decentralized information-flow control

The paper's read rule is intended to prevent exfiltration, but confidentiality needs a more explicit observer model. Traditional confidentiality models ask whether information at one security label can flow to an observer at another label. Myers and Liskov's decentralized label model is particularly relevant because it expresses policies owned by multiple principals and supports controlled declassification.

Conflux should separate:

- **integrity/authority influence**: who may determine an effect;
- **confidentiality provenance**: which protected sources contribute to a value;
- **observers/recipients**: which principals can observe the effect;
- **declassification authority**: who is allowed to release that information to those observers.

The current condition that every influencing principal must be able to read every newly processed datum is conservative but difficult to interpret. A more direct confidentiality rule is:

\[
\forall d\in\mathrm{ConfSources}(payload),\;
\forall o\in\mathrm{Observers}(effect),\;
\mathrm{CanRead}(o,d)
\]

unless a valid declassification or disclosure delegation is present. This separates the principal who controls an action from the principal who receives information.

### 3.5 Noninterference and hyperproperties

Privilege escalation is a safety property over individual traces: once an unauthorized action occurs, a finite prefix witnesses the violation. Confidentiality is often stronger. Noninterference compares multiple traces that differ in secret inputs and asks whether a low observer can distinguish them. Clarkson and Schneider formalise such properties as hyperproperties.

Consequences for SLED:

- SLED can check privilege-escalation safety by exploring prefixes.
- A claim of information-exfiltration freedom based only on per-trace read checks is not equivalent to general noninterference.
- To support stronger confidentiality claims, SLED should add paired-run or self-composition analysis, observer projections, and explicit permitted leakage.
- Timing, termination, errors, approvals, and allow/deny results may themselves leak information.

The paper should either narrow the confidentiality claim to its exact access rule or extend the semantics accordingly.

### 3.6 Capabilities, confused deputies, and delegation

Hardy's confused-deputy problem is directly relevant: a more privileged component can be tricked into using ambient authority on behalf of a less privileged requester. LLM agents are unusually confusable deputies because natural-language data and instructions share the same processing path.

Capability systems address this by passing explicit, unforgeable, attenuable authority rather than relying on ambient identity. Macaroons demonstrate practical delegated credentials with contextual caveats such as purpose, time, target, and operation.

The project report's “data as privileged instructions” should be rebuilt as a capability mechanism. A delegation object should contain at least:

```text
issuer principal
beneficiary or bearer constraints
authorized operation and resource pattern
argument constraints
purpose/task identifier
validity interval and use count
transitivity/delegation depth
visibility/declassification scope
revocation handle
cryptographic or ACS-backed authenticity
```

Then authority remains monotonically non-increasing under ordinary influence, and can increase only through a separately audited `Delegate` transition. This is a stronger and cleaner theorem than silently discarding prior influence.

### 3.7 Provenance: authorship is not enough

Database provenance distinguishes why a result exists, where its values came from, and how it was derived. W3C PROV represents entities, activities, agents, generation, use, derivation, and attribution. These distinctions expose limitations in the current `W(d,u)` relation:

- A principal with write permission is not necessarily an actual contributor.
- A current author may be different from the principal that introduced a specific field.
- Tool transformations, merges, summaries, filtering, and retrieval need activity nodes.
- Shared accounts and compromised services can make principal attribution ambiguous.
- Provenance assertions themselves have provenance and trust requirements.

For the formal core, `W` can remain a conservative may-author relation. For production, Conflux should define a **Provenance Contract** with two modes:

1. **Sound conservative mode**: include every principal that could have contributed.
2. **Attested precise mode**: accept narrower provenance only from authenticated histories, signed tool responses, database audit logs, version-control commits, or verified transformation rules.

The key rule is that precision may improve utility, but unsound precision must never improve authority. Unknown provenance should widen the source set or introduce an `Unknown/External` principal with minimal permissions.

### 3.8 Dynamic taint tracking, implicit flows, and sanitization

Conflux is a form of dynamic taint tracking, but its taint is principal identity and its sink policy is authorization. Classic taint systems distinguish explicit data dependencies from implicit control dependencies. An LLM can encode influence through control decisions even when output text does not copy input tokens. Therefore token overlap or simple value matching is not a sound influence oracle.

The supplied work correctly adopts a conservative model in which all supplied inputs influence all outputs. This is sound but over-taints. Safe precision recovery requires a trusted mechanism, for example:

- a deterministic parser that extracts a field without consulting unrelated content;
- a typed tool that returns separately labelled fields;
- a verified transformation with a declared dependency footprint;
- an argument-level planner that proves which inputs bind which arguments;
- a trusted declassifier or endorsement step with scoped semantics.

An LLM assertion that “this output did not depend on source X” cannot be part of the security guarantee.

### 3.9 Model checking and formal verification

SLED is best understood through explicit-state model checking. It constructs a finite transition system, explores reachable states, and checks safety predicates. That framing provides established terminology and techniques:

- state hashing and canonicalization;
- partial-order reduction for independent actions;
- symmetry reduction across equivalent principals or resources;
- bounded model checking;
- abstraction and refinement;
- counterexample traces;
- mutation analysis;
- refinement checking between specification and implementation.

The phrase “exhaustively explores arbitrary model behaviour” should always be followed by “within the finite environment, proposal vocabulary, and depth bounds.” The paper's depth-three exploration and proposal-size restrictions make SLED a bounded verifier, not an unbounded proof engine.

A production-quality verification story should have three layers:

1. **Theorem**: the abstract policy prevents the defined violation under assumptions.
2. **Model checking**: a finite specification satisfies invariants across bounded environments.
3. **Implementation conformance**: tests, mutation testing, and possibly proof/refinement show that Python/Rust code implements the specification.

## 4. Related-work landscape

### 4.1 Taxonomy

The recent literature is easier to understand by identifying what is trusted and where enforcement occurs.

| Family | Representative work | Trusted component | Enforcement granularity | Main strength | Main limitation relative to Conflux |
|---|---|---|---|---|---|
| Model/prompt robustness | Spotlighting, StruQ, SecAlign, DefensiveTokens, DataSentinel | model training or detector | tokens/prompt | low deployment friction; preserves broad utility | probabilistic and adaptive-attack-sensitive |
| Isolation/planning | Dual LLM patterns, CaMeL, f-secure agents | privileged planner, interpreter, monitor | plan/tool call/data flow | strong structural separation | trusted-plan/control assumptions; data-dependent tasks can be difficult |
| IFC/taint | FIDES, RTBAS, AgentArmor | label propagation and sink checker | values, calls, traces | deterministic information-flow enforcement | labels/policies are usually bespoke and may be coarser than real principal authority |
| Contextual policy | Conseca, Progent, AgentSpec, FORGE | policy generator or author plus reference monitor | tool call/history | expressive organizational constraints | policy synthesis/authoring burden and policy correctness |
| Privilege-escalation/MAC | SEAgent | entity labels, graph, policy DB, memory logic | graph paths | explicit PE and multi-agent confused-deputy coverage | intent-derived least privilege and custom policies; default-allow risks |
| Argument-level provenance | PACT | contracts, provenance runtime, discharge procedures | individual arguments | solves mixed-trust granularity problem | automatic provenance and contract inference remain imperfect; uses trust classes rather than existing ACS principals |
| Causal evidence/intent | ARGUS, ProvenanceGuard, AgentSentry variants | causal inference, LLM judges, learned bounds | spans, arguments, trajectories | high utility on context-dependent tasks | model-based evidence decisions are not worst-case guarantees |
| Evaluation | AgentDojo, InjecAgent, AgentPI, AgentDyn, AutoDojo, LivePI, AgentSecBench, ART | benchmark oracle | task/trace/game | broader realism and adaptive attacks | no single benchmark proves a monitor correct |

### 4.2 Model-level defences

The preprint already cites representative prompt- and training-level work. The revised paper should keep this section short and use it to establish the threat-model boundary, not to survey every detector.

- **Spotlighting** marks or transforms untrusted content to help the model distinguish it from instructions.
- **StruQ** separates structured instructions and data and trains models to respect that structure.
- **SecAlign** uses preference optimization to align the model against prompt injection.
- **DefensiveTokens** introduces learned defensive token sequences.
- **DataSentinel** uses a game-theoretic detection formulation.
- Attack and audit work such as NeuralExec, Checkpoint-GCG, poisoning-based attacks, critical defence evaluations, and AutoDojo shows that robustness is distribution- and adversary-dependent.

Conflux's appropriate claim is not that model-level methods are useless. They reduce interference and improve utility. The claim is that they should not be the sole mechanism protecting privileged effects. A robust model can be composed with Conflux, but Conflux's authorization theorem must not rely on the model correctly identifying malicious text.

### 4.3 Dual-LLM patterns and CaMeL

**Core idea.** Dual-LLM architectures separate a privileged planner, which sees trusted instructions, from a quarantined model, which processes untrusted data. CaMeL turns a trusted user query into a structured program, executes it in a custom interpreter, tracks capabilities/data flows, and checks policies before effects. The reported CaMeL evaluation solves 67% of AgentDojo tasks with its stated provable-security configuration.

**Contribution.** CaMeL established that a protective system layer can give stronger security than prompt filtering and made capability/data-flow semantics central to agent execution.

**Comparison with Conflux.**

- CaMeL derives control flow from a trusted query and prevents untrusted data from changing that flow. Conflux permits arbitrary planning behaviour but restricts authority at effect time.
- CaMeL's capabilities and policies are application-specific. Conflux's baseline policy is derived from existing principal permissions.
- Conflux is naturally suited to tasks where retrieved data determines which authorized action is appropriate, but its current whole-execution taint can over-block mixed-trust actions.
- CaMeL's security and Conflux's security are defined differently. CaMeL focuses on prompt-injection/data-exfiltration properties under its execution architecture; Conflux focuses on whether any influencing principal lacks authority for the action.

**What to reuse.**

- typed intermediate representations for tool plans;
- a small interpreter/reference monitor;
- capability-carrying values rather than raw strings;
- explicit modelling of tool return values and data-flow edges;
- benchmark ports for direct mechanism comparison.

**Paper positioning.** Avoid saying CaMeL's security “depends on the planning model producing a secure plan” without qualification. Its architecture deliberately limits what untrusted data can change. A fairer distinction is that plan generation and task utility rely on the privileged model and trusted-query assumption, while policy enforcement is system-level.

### 4.4 f-secure agents and the information-flow-control perspective

Wu, Cecchetti, and Xiao frame indirect prompt injection as information-flow contamination. Their system separates context, produces structured plans, and uses a security monitor to prevent untrusted information from affecting privileged control decisions.

This work is foundationally close to Conflux because both reject malicious-string detection and reason about flow. The distinction is:

- their central label is trusted/untrusted context and control/data separation;
- Conflux uses identities of possible influencers and derives action-specific authority from an ACS;
- their architecture constrains planning; Conflux's intended monitor can wrap arbitrary planners.

The revised paper should explicitly say that Conflux is an **identity- and authorization-sensitive refinement of information-flow integrity**, not a wholly separate category from IFC.

### 4.5 FIDES

**Core idea.** FIDES adapts information-flow control to LLM agents. Runtime values carry confidentiality and integrity labels; deterministic checks mediate sinks; explicit primitives support hiding, revealing, and controlled information release. The system separates model reasoning from label enforcement and evaluates on agent benchmarks.

**Contribution.** FIDES gives LLM agents a more conventional IFC semantics and shows that confidentiality and integrity need distinct labels.

**Comparison with Conflux.**

- FIDES's label lattice expresses confidentiality/integrity policy directly. Conflux's influence set can be interpreted as a richer integrity label whose meaning is derived per action from principal permissions.
- FIDES more explicitly handles declassification and information hiding. Conflux currently treats read access conservatively and needs a more complete observer/declassification model.
- Conflux may avoid a new policy language for baseline authorization, but only if adapters can faithfully map action arguments and resources into the existing ACS.
- FIDES is a direct precedent for monotonic taint propagation; the novelty is the principal-aware ACS meet, not monotonicity itself.

**What to reuse.** Separate integrity, confidentiality, and declassification semantics; typed labelled values; explicit sink classes; and evaluation of both security and over-tainting.

### 4.6 RTBAS

RTBAS adapts IFC to tool-using agents and combines label-based enforcement with model-based screening and selective user confirmation. Its design is useful because it treats confirmation as a controlled fallback when deterministic checks cannot establish safety.

For Conflux, the lesson is that `Ask` should be a formal enforcement result, not an ad hoc UI path. Approval must identify:

- which principal or source lacks authority;
- the exact operation and resource;
- whether approval grants a one-time delegation, declassification, or consent;
- how long the exception lasts;
- whether the approval is reusable or transitive.

### 4.7 Conseca

**Core idea.** Conseca generates a contextual security policy just in time from the user's task and trusted context, then enforces that policy deterministically. The policy generator is isolated from untrusted runtime content.

**Contribution.** It reduces static policy burden and recognizes that the same tool call can be legitimate or illegitimate depending on the task.

**Comparison.** Conflux's baseline does not try to infer task intent; it asks whether all influencers already possess authority. This yields a stronger worst-case authorization statement but does not prevent harmful or irrelevant actions that remain within those permissions. Conseca addresses task-specific intent but inherits policy-generation correctness risk.

**Composition opportunity.** Use Conseca-style generated policies as an optional **consent or task-alignment layer** above the ITES authorization floor. A generated policy may further restrict actions, but must not grant authority absent from the ACS or explicit delegation.

### 4.8 Progent

**Core idea.** Progent introduces a programmable privilege-control DSL, proxy enforcement around tool calls, and dynamic or LLM-assisted policy generation. It evaluates against AgentDojo, Agent Security Bench, and AgentPoison-style attacks, including adaptive attacks.

**Contribution.** Progent makes least-privilege constraints programmable and deployable without replacing the underlying agent.

**Comparison.**

- Progent expresses task- or tool-specific privilege policies; Conflux derives baseline authority from principal provenance and an ACS.
- Progent is more expressive for argument constraints, sequence constraints, quotas, and dynamic context.
- Conflux can reduce policy-writing burden for standard organizational authorization but still needs semantic action adapters.

**What to reuse.** A policy proxy, composable predicates, per-argument constraints, deny explanations, and explicit adaptive-attack evaluation.

### 4.9 AgentSpec

AgentSpec provides a DSL and runtime enforcement framework for constraining agent behaviour. It is relevant mainly as evidence that deterministic runtime policy languages are becoming a standard architecture. Conflux should not compete by inventing another general-purpose DSL unless necessary. A better design is:

- existing ACS for baseline authorization;
- a small, typed effect schema;
- optional pluggable policy backends for safety, consent, sequence, and quota constraints;
- compilation to established engines where possible.

### 4.10 FORGE: formal policy enforcement for real-world agentic systems

**Core idea.** FORGE treats policy enforcement as a cross-cutting concern. Policies are Datalog rules over abstract predicates. An observability service maintains those predicates under a formal assume/guarantee contract, and a reference monitor checks every policy-relevant action. Aspect-oriented instrumentation can retrofit agents without changing their internal reasoning. The case studies include prompt-injection information flow, multi-agent approval workflows, and customer-service policies.

**Contribution.** FORGE explicitly separates three things that Conflux currently combines informally:

1. the policy semantics;
2. the trusted observation/provenance contract;
3. the instrumentation that guarantees complete mediation.

**Comparison.**

- FORGE is policy-general; Conflux proposes a specific principal-intersection authorization semantics.
- FORGE needs policy rules; Conflux can generate baseline authorization facts from the ACS.
- FORGE handles causal history and multi-agent policy naturally through Datalog recursion.
- Conflux's Principal Context can serve as FORGE's observability facts, while ITES can be one compiled policy family.

**High-value direction.** Define Principal Context as a typed fact schema and provide a Datalog/Cedar/Rego compilation. This would turn the “no new policy language” claim into “no new policy language is required for baseline authorization, and existing engines can consume the same context for richer policy.”

### 4.11 SEAgent

**Core idea.** SEAgent defines privilege escalation as agent actions exceeding the least privilege required by the user's intended task. It maintains a directed System View graph of agents, tools, databases, and information flows; labels entities with attributes; matches policy path patterns; and produces `Allow`, `Deny`, or `Ask`. SEMemory resets raw context between rounds while selecting and reconstructing relevant prior graph edges. It explicitly evaluates indirect prompt injection, RAG poisoning, untrusted agents, and a multi-agent confused-deputy variant.

**Contribution.** SEAgent is the closest work to the paper's broad framing. It makes privilege escalation the unifying security lens and adds multi-agent graph paths and user-adaptive exceptions.

**Critical distinction.** The two definitions of privilege escalation are not the same:

- SEAgent: an action exceeds the least privilege necessary for the user's intended task.
- Conflux/ITES: an action is unauthorized for at least one influencing principal.

SEAgent's definition is intent-relative and can block an authorized but irrelevant action. Conflux's definition is provenance-relative and can permit an authorized but malicious or mistaken action. Conversely, Conflux may block benign workflows in which untrusted data is supposed to fill non-authority-bearing content.

**Security assumptions.** SEAgent relies on correct entity labels, policy paths, graph reconstruction, and in SEMemory a Memory LLM that selects relevant history. Its policy engine defaults to allow if no rule matches. Conflux's strict rule can fail closed under unknown provenance, giving a cleaner worst-case authorization guarantee, but less contextual utility.

**What Conflux should add.**

- a direct related-work subsection on SEAgent;
- multi-agent and confused-deputy examples;
- a comparison table separating source authorization, task alignment, confidentiality, and policy expressiveness;
- experiments that port SEAgent-like path policies into SLED;
- a statement that Conflux does not claim to be the first use of privilege escalation as the agent-security objective.

### 4.12 PACT: the most important direct challenge

**Core idea.** PACT argues that tool-call-level enforcement creates a granularity mismatch. In `send_email(recipient, body)`, an untrusted webpage may legitimately determine `body` but should not determine `recipient`. PACT assigns semantic roles to individual arguments, tracks value provenance across replanning, and checks role-specific contracts. Roles include target, command, credential, content, selector, and control. Contract precision progresses from opaque tool-level blocking to argument roles and certified routing. Under oracle provenance, PACT reports 100% utility and security on mixed-trust diagnostics; in AgentDojo deployments, automatic inference retains perfect security on the strongest tested models with 38.1-46.4% utility.

**Why it matters.** The current ITES rule attaches one influence set to the entire execution and therefore to every produced object/action. That is a flat monitor. It cannot distinguish content-bearing and authority-bearing arguments without extending the model.

**Where Conflux remains different.**

- PACT uses a trust lattice (`TRUSTED > USER > TOOL_OUTPUT > EXTERNAL`) and role-specific contracts.
- Conflux can use named principals and ask whether each source is actually authorized under the organization's ACS.
- PACT's certified discharge is conceptually close to Conflux's proposed delegation/declassification, but PACT scopes discharge by argument role.
- Conflux's visibility and consent layers can address harms inside content arguments that PACT explicitly leaves outside its structural guarantee.

**Required response.** The paper should not dismiss PACT as “requiring known prompt injections” or as depending entirely on LLM provenance. Its formal mechanism assumes oracle/conservative provenance and separately measures automatic inference. The correct critique is:

1. PACT proves enforcement conditional on correct contracts and provenance, just as ITES is conditional on correct principal provenance and ACS semantics.
2. Automatic role/provenance inference is an empirical bottleneck.
3. Its coarse trust classes do not directly encode organizational principal permissions.
4. Its argument-role insight is valid and should be incorporated.

**Recommended synthesis: role-sensitive Principal Context.** For each argument `arg_i`, track a principal provenance set `I_i` and a semantic role `r_i`. Define which roles are authority-bearing for operation `op`. Then:

\[
\mathrm{AllowAuth}(a,ctx)\iff
\forall i\in \mathrm{AuthorityArgs}(a),
\forall u\in I_i,
\mathrm{Authorize}(u,a,i)=allow.
\]

Content arguments are not exempt from all checks. They remain subject to confidentiality, integrity, safety, and recipient-visibility rules. This recovers benign mixed-trust utility without letting external data choose targets, commands, credentials, or control flags.

### 4.13 ARGUS

**Core idea.** ARGUS constructs an Influence-Provenance Graph from prompts, read-only actions, contexts, and state-changing actions. It segments context spans into benign or anomalous evidence, grounds each action argument in supporting spans, checks whether benign evidence entails the action, and verifies task invariants extracted from the user request. It reports an attack-success reduction from 28.8% to 3.8% on AgentLure while retaining 87.5% clean utility.

**Contribution.** ARGUS treats action justification as a causal-evidence problem and works at span and argument granularity.

**Comparison.** ARGUS's evidence classification, entailment, and invariant extraction are model-dependent. Conflux's authorization result can remain deterministic even if the model is fully compromised. However, ARGUS addresses a property Conflux does not: whether an action is supported by the user's task and benign evidence.

**Composition opportunity.** Treat ARGUS-like evidence as an optional `consent/task_alignment` signal. It may restrict or request confirmation, but it should not create authority. The deterministic Principal Context monitor remains the final floor.

### 4.14 ProvenanceGuard, NeuroTaint, and causal provenance systems

- **ProvenanceGuard** compares tool calls with provenance support for user intent and is relevant to the repository's consent layer.
- **NeuroTaint/TaintBench** reconstructs semantic and cross-session provenance and provides benchmark scenarios across agent frameworks. It is useful for auditing and provenance-quality evaluation, but offline or learned inference should not be assumed sound enough to remove conservative taint.
- **AgentWatcher** and counterfactual/causal monitors identify influential context segments. These can help explain decisions and locate attacks, but their causal estimates remain empirical.
- **AgentSentry** uses counterfactual re-execution and context purification to continue after detecting takeover; another Agent-Sentry system learns behavioural bounds from execution traces. Both improve utility, but neither replaces a deterministic authorization monitor.

Conflux should distinguish **provenance capture** from **provenance inference**:

- captured provenance is supplied by trusted adapters and execution semantics;
- inferred provenance is a best-effort optimization that must fail closed or be evaluated separately.

### 4.15 AgentArmor

AgentArmor treats runtime traces as programs, constructs control-flow, data-flow, and program-dependence graphs, and applies a type system and property registry. This is highly relevant to both Conflux and SLED.

Useful components:

- a graph IR for traces;
- independently typed tool/data metadata;
- static or incremental analysis over the IR;
- explicit control-dependence edges;
- policy checking separate from the model.

A Conflux trace IR could become the common format for runtime enforcement, SLED exploration, audit logs, and external benchmark adapters.

### 4.16 SecureClaw and dual-boundary designs

SecureClaw separates two boundaries: effect-sink authorization and read-boundary plaintext confinement. Sensitive reads return opaque handles or bounded summaries rather than exposing raw plaintext to the model.

This addresses a weakness in the current read rule. Even if later actions are blocked, exposing a secret to a compromised model/runtime can be risky through logs, memory, side channels, or future bugs. Conflux should consider:

- opaque data handles;
- trusted transformations over handles;
- model-visible summaries as explicit declassification;
- sink authorization for all external effects.

### 4.17 Silent Egress and covert channels

Silent Egress and related work show that network egress and multimodal channels can bypass application-level action checks. An agent may exfiltrate through URLs, image pixels, DNS-like requests, previews, chunked outputs, or apparently benign content.

Conflux should state clearly that ACS authorization does not by itself provide channel-capacity bounds. A production system needs:

- an egress proxy/reference monitor;
- destination allowlists and policy-aware routing;
- content-size and encoding restrictions;
- rate limits;
- audit correlation across multiple low-volume actions;
- optional multimodal covert-channel defenses.

### 4.18 Authenticated workflows and cryptographic provenance

Authenticated-workflow proposals use cryptographic attestations across prompts, tools, data, and context, with runtime policy enforcement. Even where individual claims require independent validation, the architectural lesson is important: provenance should not be an unauthenticated dictionary attached by cooperative application code.

Conflux should define a signed envelope or equivalent authenticated record for cross-process and cross-agent boundaries. At minimum it should bind:

- source principal/workload identity;
- data or action identifier and hash;
- transformation/activity identifier;
- parent provenance references;
- declared dependency set;
- timestamp, nonce, and policy version;
- adapter identity and verification result.

## 5. Evaluation and benchmark landscape

### 5.1 AgentDojo

AgentDojo provides dynamic tool environments, benign tasks, attacks, and security/utility metrics. It remains the most important common comparison point because CaMeL, PACT, Progent, FIDES-related work, MELON, and many other defences report on it.

For Conflux, AgentDojo should not replace SLED. It should answer different questions:

- Can a real model complete useful tasks under Conflux?
- How much utility is lost from provenance granularity and policy checks?
- Does a concrete attack reach the reference monitor with an unauthorized proposal?
- How often does the monitor block, ask, or allow?

SLED answers whether the monitor's stated policy can be violated in its abstract model.

### 5.2 InjecAgent and Agent Security Bench

These benchmarks broaden tool domains and attack cases. They are useful for external validity and for comparing action-level defenses, but they usually lack the exact principal, writer, reader, and delegation metadata Conflux requires. A high-value contribution is to publish **ACS/provenance annotation layers** for existing benchmarks rather than creating only bespoke synthetic environments.

### 5.3 AgentPI

AgentPI was introduced with a 2026 systematization of prompt-injection threats. Its key motivation is context-dependent tasks, where external observations are legitimately needed to determine the action. This directly tests Conflux's weakest utility regime and should be a priority integration.

### 5.4 AgentDyn

AgentDyn contains 60 open-ended tasks and 560 injection cases across shopping, GitHub, and daily-life domains. It emphasizes dynamic planning, helpful third-party instructions, and realistic under-specification. The authors report that many existing defences either remain insecure or over-defend.

This is a natural test for role-sensitive Principal Context and explicit delegation. Flat ITES is expected to over-taint some helpful-instruction tasks; the revised mechanism should quantify how much argument-level provenance recovers.

### 5.5 AutoDojo and adaptive evaluation

AutoDojo adapts attacks to the defence and finds that black-box optimization can recover substantial attack success against filters that appear secure on static injections. It also identifies “action-open” tasks, where the user intentionally delegates action selection to external content, as a structural problem.

Deterministic authorization should be invariant to payload wording if provenance is correct. Therefore AutoDojo should be used to attack:

- provenance-inference heuristics;
- contract/role synthesis;
- adapter metadata;
- approval wording;
- delegation issuance;
- missing mediation paths.

This is more meaningful than merely checking whether an injection causes the LLM to propose a blocked action.

### 5.6 LivePI and production-like testbeds

LivePI evaluates real VM-integrated surfaces such as email, chat, web, files, repositories, and wallet operations. Such environments are useful for proving that complete mediation holds across actual framework integrations, not just simulated tools.

A Conflux production evaluation should include at least one live-but-test-controlled environment with real network, filesystem, email, and repository adapters.

### 5.7 AgentSecBench and formal security games

AgentSecBench proposes formal games for instruction integrity, retrieval confidentiality, and capability integrity, including an intent-to-execution noninterference perspective. This work can help SLED move from bespoke counters to property definitions with explicit adversaries, observations, and permitted leakage.

### 5.8 ART/public competitions and real-world prevalence

Large public competitions and studies of indirect prompt injection in the wild show that attack corpora are diverse, adaptive, and frequently concealed. They reinforce the need for structural monitors and recurring benchmark updates. They do not, by themselves, validate a formal authorization policy.

### 5.9 Recommended evaluation stack

Conflux should report four distinct layers:

| Layer | Question | Method | Example output |
|---|---|---|---|
| Policy proof | Does the abstract rule imply the security property? | theorem/proof assistant | soundness, maximality, delegation theorem |
| Monitor verification | Does the finite monitor model satisfy invariants? | SLED/model checking | counterexamples, state coverage, bounds |
| Implementation conformance | Does code implement the monitor? | mutation, property-based, differential tests | killed mutants, spec/code equivalence cases |
| Real-agent performance | Is it useful and robust in practice? | AgentDojo/AgentPI/AgentDyn/LivePI | task success, ASR, block/ask rate, latency |

## 6. Contribution and novelty audit

### 6.1 Claim matrix

| Candidate claim | Status | Defensible version | Main competing work |
|---|---|---|---|
| Privilege escalation is the correct objective | QUALIFY | Privilege escalation is a useful system-level authorization objective distinct from prompt-injection detection; Conflux proposes an influencer-relative definition | SEAgent; formal contextual-security frameworks |
| First provenance-based system-level defence | REMOVE | Conflux provides a principal-identity and existing-ACS interpretation of provenance | FIDES, CaMeL, f-secure, PACT, ARGUS |
| No model-behaviour assumptions | QUALIFY | The authorization decision is independent of model correctness, conditional on complete mediation, sound provenance, correct action schemas, and ACS correctness | CaMeL, FIDES, FORGE, PACT have related conditional guarantees |
| No new policy language | QUALIFY | Baseline authorization can be derived from an existing ACS without a bespoke prompt-injection policy language | Progent, Conseca, FORGE, SEAgent; real adapters still require semantics |
| Authority monotonicity | KEEP/REFRAME | Principal influence joins monotonically and effective authority is the meet of principal permissions | Biba low-water mark, IFC lattice theory |
| Maximal secure authorization | KEEP/QUALIFY | Under the strict influencer-authorization definition, permission intersection is the unique maximal set of actions that does not violate that definition | mathematically immediate; novelty is application and construction |
| Prevents prompt injection | REMOVE as broad claim | Prevents prompt injection from causing actions outside the effective authority; does not prevent task disruption or harmful authorized actions | all execution-level defences |
| Prevents information exfiltration | QUALIFY | Enforces the stated conservative read/visibility rule; general noninterference and covert-channel freedom are not shown | FIDES, SecureClaw, Silent Egress |
| SLED exhaustively proves implementation security | REMOVE | SLED exhaustively explores a bounded finite abstraction and validates monitor behaviour within those bounds | model checking foundations; AgentSecBench |
| SLED is a novel evaluator | KEEP/QUALIFY | SLED is a bounded explicit-state evaluator designed for worst-case model choices and system-level policy invariants | dynamic/adaptive benchmarks evaluate different properties |
| Maximal utility | QUALIFY | The rule permits every action that satisfies the strict per-influencer authorization predicate in the SLED task model | does not imply maximum human task completion; PACT exposes over-tainting |
| Principal Context is novel | PROMISING | A unified, typed runtime context that separates source authority, visibility, consent, delegation, and evidence, grounded in existing ACS identities | pieces exist separately; integration/formal algebra may be novel |

### 6.2 Strongest core contribution

The strongest core statement is:

> Conflux represents the integrity/authority state of an agent execution as a set of organizational principals that may have influenced each security-relevant value. It interprets this set through the organization's existing authorization decision procedure, so ordinary information flow can only attenuate executable authority. Under complete mediation and sound provenance, arbitrary LLM behaviour cannot cause an effect for which an authority-bearing source lacks permission.

This statement is narrower than “secure agents” but more technically meaningful.

### 6.3 Why the maximality theorem is useful but not enough

The theorem is correct under the paper's definition, but a reviewer may view it as tautological:

1. Privilege escalation is defined as any action unauthorized for any influencer.
2. Therefore the safe actions are exactly those authorized for every influencer.

The theorem should be retained as a characterization lemma, not marketed as the main theoretical breakthrough. The stronger theory should address questions that are not true by definition:

- compositional propagation across nested executions and tools;
- role-sensitive arguments;
- dynamic authorization and revocation;
- explicit delegation and its attenuation constraints;
- confidentiality observer semantics;
- multi-agent handoff;
- equivalence between the abstract monitor and implementation;
- completeness or optimality under a formal utility preorder.

### 6.4 Distinctiveness of principal identity sets

A principal set has several advantages over binary trust:

- permissions can be incomparable;
- authorization is action- and resource-specific;
- no universal ordering of trusted sources is required;
- the monitor can explain exactly which source blocks an effect;
- organizational revocation is reflected by the existing ACS;
- policy is reusable across agent applications.

However, this representation is not automatically more precise than IFC labels. Decentralized labels can encode principal-owned policies, and ABAC can encode arbitrary source attributes. The novelty claim should be architectural and operational: **Conflux obtains labels directly from real provenance identities and interprets them through an existing policy decision point.**

### 6.5 SLED's genuine novelty opportunity

SLED can become a substantial independent contribution if it develops from a bespoke enumerator into a defense-agnostic verification framework with:

- a formal transition-system semantics;
- a property specification language;
- independent monitor and oracle implementations;
- automatic minimal counterexamples;
- state hashing, symmetry reduction, and partial-order reduction;
- mutation testing against deliberately broken defences;
- hyperproperty or paired-run support;
- adapters from real benchmark traces and ACS snapshots;
- reproducible coverage metrics and bounds.

Without these, a reviewer may interpret the 1.46 million traces as extensive testing of a policy whose correctness already follows directly from its checker.

## 7. Technical issues in the current formalisation

### 7.1 The initial-authority and empty-influence problem

The intersection over an empty set is mathematically the universe of actions. If an execution can have no influencing principal, it may accidentally receive maximum authority. The model must define one of:

- every execution includes an authenticated initiating principal;
- an `Unknown` principal with minimal permissions is always present;
- empty provenance denies all effects;
- a trusted system principal is explicitly included with tightly scoped rights.

Recommended rule: `Influence(e)` is never empty for an effectful execution; otherwise `deny`.

### 7.2 Potential writers versus actual contributors

Using all principals with write permission is sound but may make shared documents unusable. Using only recorded authors improves utility but can be unsound if histories are incomplete or mutable.

Define provenance precision levels:

```text
P0 UNKNOWN: include UnknownExternal; fail closed
P1 ACL-CONSERVATIVE: include every current/potential writer
P2 HISTORY-ATTESTED: include authenticated contributors to the current version
P3 FIELD/ARGUMENT-ATTESTED: include contributors to the specific value or field
P4 VERIFIED-TRANSFORM: narrow dependencies using a trusted deterministic transform
```

Evaluation should report utility by provenance precision level.

### 7.3 Whole-execution over-tainting

The rule “every object produced by an execution inherits the complete execution influence set” is safe but coarse. It makes all output fields depend on all inputs, even when only one field is used for a privileged target.

Required extension:

- values and arguments carry separate provenance;
- the LLM output parser returns a structured action with per-field labels;
- any narrowing of provenance must be supplied by trusted execution structure, not the LLM's unsupported claim;
- if provenance cannot be resolved, fields inherit the full execution context.

### 7.4 What counts as influence

The phrase “information contributes, directly or indirectly” is intuitive but not operational. The paper should distinguish:

- semantic dependence in the true model computation;
- conservative supplied-input dependence used by the monitor;
- captured data-flow edges from tools and deterministic code;
- inferred causal influence used only for optimization/audit.

The security theorem should use the monitor's conservative relation, not an unobservable metaphysical notion of influence.

### 7.5 Trusted tools and source principals

The preprint says a trusted tool may produce data associated with a trusted system principal, while an outsourced tool may inherit the invoking principal. This can be dangerous. A tool's code identity, data owner, operator, caller, and returned-data author may all differ.

Use separate fields:

```text
producer_workload
caller_principal
data_owners
data_contributors
external_origin
attestation_issuer
transform_semantics
```

A trusted parser can be trusted to report provenance accurately without being treated as the author of all parsed content.

### 7.6 Dynamic ACS semantics

The preprint evaluates permissions at action time, which naturally handles revocation. But several edge cases need definitions:

- What if a contributor account is deleted?
- Does revocation retroactively reduce authority of existing derived objects?
- Can a newly granted permission make old untrusted content able to trigger a new action?
- Which policy version is used in audit/replay?
- How are long-running transactions handled if policy changes between check and effect?

Recommended approach:

- action-time authorization for safety;
- immutable principal identifiers and explicit tombstones;
- policy version recorded in every decision;
- atomic check-and-use or short-lived authorization tokens bound to the exact effect;
- optional historical replay against the policy version used at execution.

### 7.7 Authorization versus intent, consent, and safety

Conflux intentionally does not guarantee that an action serves the user's goal. The current repository's separation of authorization, visibility, and consent is therefore essential.

A complete decision should be a product rather than one Boolean:

```text
AuthorizationDecision = Allow | Deny
VisibilityDecision    = Allow | Redact | Deny
ConsentDecision       = Satisfied | Ask(principals, scope) | Deny
SafetyDecision        = Allow | Ask | Deny
DelegationDecision    = None | Valid(scope) | Invalid(reason)
FinalDecision         = deterministic composition of the above
```

This prevents vague claims that authorization alone solves agent alignment.

### 7.8 Confidentiality and observations

The current paper does not define what an attacker observes. It should identify:

- tool outputs;
- final messages;
- action success/failure;
- timing and retries;
- approval prompts;
- logs and traces;
- network metadata;
- state changes visible through later reads.

Without an observation model, “no information exfiltration” is underspecified.

### 7.9 Multi-step and aggregate effects

Individual actions may be authorized while their sequence is harmful: repeated small transfers, gradual data release, or a read-then-write pattern. Add history-sensitive policy support for:

- quotas and budgets;
- temporal ordering;
- transaction boundaries;
- cumulative disclosure;
- rate limits;
- separation of duty;
- approval reuse.

This is where FORGE/Datalog or a temporal-policy module is more appropriate than the core meet rule.

### 7.10 Side channels and policy-oracle leakage

Allow/deny outcomes reveal information about permissions and provenance. Repeated probes may infer organizational structure. Mitigations include:

- generic user-facing errors;
- rate limiting;
- permission-query access control;
- constant-shape responses where feasible;
- aggregation of audit information;
- explicit policy-oracle leakage in the threat model.

## 8. Evaluation critique of the current SLED results

### 8.1 What the existing results do establish

Within the implemented finite environments and depth/proposal bounds, no explored completed trace produced the counted privilege-escalation or exfiltration outcomes, and every task classified as secure under the evaluator's model remained achievable. This is useful evidence that the prototype checker follows its intended rule across many combinations.

### 8.2 What they do not establish

The results do not independently establish:

- unbounded security;
- correctness outside the three synthetic environments;
- sound provenance acquisition;
- complete mediation in real agent frameworks;
- confidentiality noninterference;
- utility with imperfect benign models;
- robustness of automatic argument provenance;
- safe delegation;
- protection from sequences, concurrency, side channels, or direct infrastructure compromise.

### 8.3 Incomplete traces

Approximately 15% of traces in the preprint reach the depth bound and are excluded. For safety properties, an already observed violation in a prefix should never be discarded merely because the rest of the task is incomplete. Report separately:

- explored prefixes;
- completed traces;
- bound-truncated states;
- safety violations observed before truncation;
- task-utility metrics only for traces where completion is meaningfully decidable.

### 8.4 Circularity risk

If SLED classifies an action as secure using the same `auth` predicate that ITES uses to allow it, zero violations can become nearly tautological. The oracle should be independently specified and ideally implemented separately. Recommended methods:

- declarative property specification distinct from monitor code;
- deliberately mutated monitors that omit one influencer, skip one read, use union instead of intersection, or mishandle nested calls;
- confirm that SLED finds minimal counterexamples for every mutant;
- differential testing against a small executable formal specification.

### 8.5 State-space reporting

Raw trace counts can be misleading because many traces may differ only in irrelevant ordering. Add:

- number of unique states;
- number of transitions;
- branching-factor distribution;
- reduction ratios;
- state-equivalence definition;
- depth and proposal bounds;
- wall-clock time, memory, CPU, and hardware;
- coverage by action/tool/principal/policy class;
- reproducible seeds or proof that enumeration is deterministic.

### 8.6 Real-model evaluation

Worst-case nondeterminism is correct for the security proof but cannot measure practical task completion. Add a separate real-model evaluation and keep claims distinct:

- **security of enforcement**: model-independent under assumptions;
- **proposal quality and utility**: empirical by model, task, and provenance precision;
- **attack interference**: empirical reduction from model-level defences;
- **monitor overhead**: deterministic runtime cost.

## 9. Prioritized research agenda

### P0.1 Role-sensitive Principal Context

**Problem.** Flat execution-level influence causes avoidable over-blocking and is directly challenged by PACT.

**Design.**

```text
PrincipalContext:
  execution_sources: set[Principal]
  values: map[ValueId, ProvenanceLabel]
  arguments: map[ArgumentPath, ProvenanceLabel]
  observers: set[Principal]
  consents: set[ConsentGrant]
  delegations: set[DelegationCapability]
  obligations: set[PolicyObligation]
  policy_version: PolicyVersion
```

Each `ProvenanceLabel` should include source principals, source entities, activity chain, precision class, and attestation status.

**Theorem target.** If every authority-bearing action argument is authorized for every principal in its sound provenance label, and all effects are mediated, then no principal can influence an authority-bearing choice beyond its direct or delegated authority.

**Evaluation.** Mixed-trust email, calendar, file, payment, shell, database, and API cases; PACT-style oracle diagnostics; AgentPI and AgentDyn.

### P0.2 Explicit scoped delegation

**Problem.** Strict monotonicity blocks legitimate authority transfer; informal “privileged instructions” are difficult to audit.

**Design.** A delegation is an authenticated capability with attenuation and caveats. It must not allow the delegatee to widen operation, target, duration, argument, observer, or delegation depth.

**Theorem target.** Ordinary flow never increases authority. A delegation transition increases authority only within the issuer's authority and the capability's scope; downstream delegation can only attenuate it.

**Evaluation.** One-time approvals, scheduled payments, assistant-to-assistant handoff, document-authored workflows, revocation, expired capabilities, replay, and confused-deputy attacks.

### P0.3 Provenance and observability contract

**Problem.** All guarantees currently rely on correct provenance without specifying how adapters earn trust.

**Design.** Define an adapter interface with formal obligations:

- identify all effectful operations;
- attach sound source provenance to every returned field;
- propagate parent provenance through transformations;
- never narrow provenance without an approved trusted transform;
- identify all observers and external sinks;
- bind decisions to exact effect parameters;
- emit tamper-evident audit records.

**Evaluation.** Adversarial adapter tests, forged labels, missing fields, shared accounts, stale histories, retries, and alternate execution paths.

### P0.4 SLED 2 as a model checker

**Problem.** Current SLED is bounded enumeration with bespoke classifications.

**Design.**

- formal state and transition schema;
- property language for safety and observer properties;
- state canonicalization;
- counterexample minimization;
- mutation framework;
- partial-order and symmetry reductions;
- benchmark trace import/export;
- independent reference specification.

**Evaluation.** Demonstrate that SLED catches a curated suite of flawed monitors, including subtle nested-execution and delegation bugs.

### P1.1 Multi-agent Principal Context

Propagate context across agent-to-agent messages without ambient service authority. Every handoff should carry authenticated provenance and an attenuated capability. Add confused-deputy and untrusted-agent scenarios from SEAgent.

### P1.2 Real ACS adapters

Priority integrations:

1. Cedar or a Cedar-like policy decision point for parameterized authorization.
2. OpenFGA/relationship-based authorization.
3. OPA/Rego for general organizational policy.
4. Cloud IAM simulator/adapters for AWS/Azure/GCP-style actions.
5. Filesystem, Git, email/calendar, and database provenance providers.

Report adapter policy burden and semantic gaps rather than claiming all ACSs fit the minimal tuple without work.

### P1.3 Separate visibility, consent, and safety algebras

Formalise each as its own policy domain. Authorization should be necessary but not sufficient. This is likely the best use of the repository's current modular architecture.

### P1.4 Benchmark annotation and cross-defence ports

Publish principal/provenance overlays for AgentDojo, AgentPI, AgentDyn, InjecAgent, and at least one live environment. Port simplified CaMeL, FIDES, PACT, Progent, and SEAgent policy baselines into a common action IR where licensing and fidelity permit.

### P1.5 Adaptive attacks against the trusted boundary

Attack the system-level assumptions, not only the LLM:

- spoof provenance;
- exploit missing interceptors;
- cause role misclassification;
- manipulate action serialization;
- exploit TOCTOU;
- induce approval fatigue;
- replay delegation tokens;
- split harmful effects across individually allowed calls.

### P2.1 Formal implementation assurance

Use TLA+/PlusCal or Alloy for the protocol and state transitions; use a proof assistant or verification-aware language for core lemmas if feasible; use property-based testing and refinement tests for the implementation. Maintain a verification-status table that distinguishes proved, model-checked, tested, and assumed properties.

### P2.2 Confidentiality hyperproperties and egress

Add paired-run checks, observer projections, permitted leakage, cumulative disclosure budgets, and a network/egress monitor. Keep this separate from the core privilege-escalation theorem.

### P2.3 Provenance precision as an optimization problem

Study the tradeoff among:

- soundness;
- precision;
- utility;
- adapter cost;
- runtime overhead;
- auditability.

A useful metric is **authority loss from over-tainting**: the difference between actions allowed under ideal field-level provenance and actions allowed under the deployed provenance precision.

### P2.4 Planning for maximal permitted utility

Given a task, available data, and an ACS, plan an execution that avoids unnecessary low-authority inputs before privileged actions. This is analogous to query planning under security labels. The planner may be heuristic, but SLED can verify the resulting effect sequence.

## 10. Recommended paper restructuring

### 10.1 Proposed title and claim focus

The current title is clear, but the paper will be stronger if it emphasizes the distinctive mechanism rather than a broad first-principles claim. Candidate formulations:

- **Principal Context for Secure LLM Agents: Authority Attenuation under Arbitrary Model Behaviour**
- **Conflux: Deriving LLM-Agent Authority from Principal Provenance and Existing Access Control**
- **Principal-Provenance Authorization for LLM Agents under Worst-Case Model Behaviour**

The existing subtitle “Preventing Privilege Escalation under Worst-Case Model Behaviour” remains useful.

### 10.2 New introduction structure

1. Agents combine multiple principals' information with privileged effects.
2. Prompt-injection detection cannot be the only security boundary.
3. Existing system-level work uses isolation, IFC labels, or bespoke policies.
4. Missing problem: connecting fine-grained provenance to existing organizational principal authority, while supporting data-dependent workflows.
5. Introduce Principal Context and the strict ITES authorization policy.
6. State exact assumptions and non-goals.
7. Present contributions narrowly.

### 10.3 Revised contribution list

Suggested wording:

1. **Principal-context authorization model.** We model each security-relevant value and execution with a conservative set of influencing organizational principals and derive authorization by querying the existing ACS for every authority-bearing component of an effect.
2. **Authority-attenuation result.** We show that ordinary provenance propagation is monotone and that the induced authority is the meet of the influencing principals' permissions; under complete mediation and sound provenance, no action can exceed the direct or explicitly delegated authority of an influencing principal.
3. **Bounded system-level verification.** We introduce SLED, an explicit-state evaluator that treats model outputs as nondeterministic and checks reference-monitor invariants independently of attack-string distributions within declared finite bounds.
4. **Implementation and empirical study.** We evaluate security, authorized utility, provenance precision, and policy burden on synthetic environments and annotated real-agent benchmarks.

Do not claim “first” unless a final search immediately before submission supports a precisely scoped first claim.

### 10.4 Related-work section outline

```text
2.1 Prompt-injection robustness and adaptive attacks
2.2 Isolation and control/data separation: Dual LLM, CaMeL, f-secure
2.3 Information-flow and taint enforcement: FIDES, RTBAS, AgentArmor
2.4 Policy and privilege control: Conseca, Progent, FORGE, SEAgent
2.5 Provenance and argument-level enforcement: PACT, ARGUS, related systems
2.6 Evaluation: AgentDojo, AgentPI, AgentDyn, AutoDojo, AgentSecBench
2.7 Classical foundations: reference monitors, Biba/DLM, capabilities, provenance, model checking
```

A comparison table should include: threat objective, label/provenance granularity, policy source, trusted components, data-dependent task support, multi-agent support, formal guarantee, and evaluation type.

### 10.5 Threat-model rewrite

Add a dedicated trusted-computing-base table:

| Component | Trusted for | Failure consequence |
|---|---|---|
| Reference monitor | complete mediation and correct decision composition | arbitrary security failure |
| Provenance adapters | sound source/observer labels | omitted principal may gain authority |
| Action schema | correct operation, resource, and argument roles | authority-bearing data may be treated as content |
| ACS/PDP | correct organizational authorization | policy-authorized harm is allowed |
| Delegation verifier | authenticity, attenuation, expiry, replay protection | unauthorized authority increase |
| LLM | not trusted for security | may reduce utility or propose harmful-but-blocked actions |
| Optional intent/provenance classifiers | not trusted to grant authority | may only restrict or trigger conservative fallback |

### 10.6 Formal section rewrite

Recommended definitions:

```text
Principal, Entity, Activity, Value, Action, ArgumentPath, Observer
ProvenanceLabel(value)
Role(argument)
AuthoritySources(action, argument)
ConfidentialitySources(payload)
DelegationCapability
PrincipalContext
AuthorizationDecision
```

Then prove:

1. Provenance join monotonicity.
2. Authority meet monotonicity.
3. Argument-level non-escalation.
4. Delegation attenuation.
5. Compositionality across nested/multi-agent execution.
6. Fail-closed behavior under unknown provenance.

### 10.7 Evaluation section rewrite

Replace the single large count narrative with:

- environment and abstraction table;
- bounds and coverage table;
- mutant/counterexample table;
- security invariant results;
- utility by provenance granularity;
- real-model benchmark results;
- runtime and policy burden;
- limitations and external-validity discussion.

Use percentages and confidence intervals where sampling occurs. For exhaustive finite runs, report exact counts and coverage rather than statistical language.

### 10.8 Claims to remove or narrow

Remove or revise phrases equivalent to:

- “prevents prompt injection” -> “prevents prompt injection from increasing effective authority.”
- “maximal utility” -> “maximal permitted action set under the strict authorization objective and model.”
- “exhaustively evaluates arbitrary behaviour” -> “exhaustively explores the declared finite abstraction and bounds.”
- “information exfiltration is impossible” -> exact observer/read-rule statement unless noninterference is added.
- “no new policy language” -> “reuses existing ACS decisions for baseline authorization.”
- “security depends only on provenance and ACS” -> include complete mediation, action semantics, delegation verification, and decision composition.

## 11. Concrete architecture proposal for Conflux

### 11.1 Core data model

```python
PrincipalId = str
EntityId = str
ActivityId = str
ValueId = str

@dataclass(frozen=True)
class ProvenanceLabel:
    principals: frozenset[PrincipalId]
    entities: frozenset[EntityId]
    activities: tuple[ActivityId, ...]
    precision: ProvenancePrecision
    attestation: AttestationStatus
    obligations: frozenset[Obligation]

@dataclass(frozen=True)
class ActionArgument:
    path: str
    value: object
    role: ArgumentRole
    provenance: ProvenanceLabel

@dataclass(frozen=True)
class Effect:
    operation: str
    resource: ResourceRef
    arguments: tuple[ActionArgument, ...]
    observers: frozenset[PrincipalId]
    effect_class: EffectClass

@dataclass(frozen=True)
class PrincipalContext:
    initiator: PrincipalId
    execution_provenance: ProvenanceLabel
    delegations: tuple[DelegationCapability, ...]
    consents: tuple[ConsentGrant, ...]
    policy_version: str
```

### 11.2 Decision pipeline

```text
1. Normalize proposed tool call into a typed Effect.
2. Validate schema and argument roles; unknown schema fails closed.
3. Verify provenance labels and attestations.
4. Compute authority-bearing source principals per argument.
5. Query ACS/PDP for each required principal-effect relation.
6. Apply valid scoped delegation capabilities.
7. Check confidentiality against observers and payload sources.
8. Check consent/approval obligations.
9. Apply independent safety, quota, and sequence policies.
10. Produce Allow, Deny, or Ask with a machine-readable proof/explanation.
11. Bind decision to exact serialized effect and execute atomically.
12. Emit a tamper-evident trace record and provenance for outputs.
```

### 11.3 Decision certificate

Every allowed effect should emit a certificate containing:

```text
effect hash
principal-context hash
policy version
authorization queries and results
delegations consumed
visibility result
consent result
safety-policy result
monitor version
timestamp and nonce
```

This supports audit, reproducibility, SLED replay, and conformance testing.

## 12. Codex-oriented action plan

The following tasks are intentionally written as repository-edit instructions. Exact filenames should be resolved against the current tree before modification.

### RW-001 - Rebuild the related-work taxonomy

- **Priority:** P0
- **Paper areas:** related work, introduction comparison table, bibliography
- **Action:** Replace the three-category survey with the taxonomy in Section 10.4.
- **Required additions:** FIDES, Progent, Conseca, FORGE, SEAgent, PACT, ARGUS, AgentArmor, AgentPI, AgentDyn, AutoDojo, AgentSecBench.
- **Acceptance criteria:** Every closest work has a mechanism summary, trusted-component statement, and precise difference from Conflux. No unsupported first claim remains.

### FM-001 - Make the trusted computing base explicit

- **Priority:** P0
- **Paper areas:** threat model, limitations, security theorem
- **Code areas:** core monitor interfaces, provider/adapter contracts
- **Action:** Add the TCB table from Section 10.5 and make theorem assumptions refer to named interfaces.
- **Acceptance criteria:** Missing provenance, unknown actions, monitor bypass, and ACS errors have defined semantics.

### FM-002 - Replace atomic actions with parameterized effects

- **Priority:** P0
- **Paper areas:** ACS formalism, authorization definition
- **Code areas:** `core`, `auth`, `policy`, tool/action models
- **Action:** Define operation, resource, arguments, environment, and observers.
- **Acceptance criteria:** Email recipient/body, file path/content, shell command/arguments, and database query/parameters can be distinguished.

### FM-003 - Add role-sensitive argument provenance

- **Priority:** P0
- **Paper areas:** ITES algorithm and theorems
- **Code areas:** `core`, `execution`, `ites`, provider adapters
- **Action:** Add argument roles and per-argument provenance with full-execution fallback.
- **Acceptance criteria:** The monitor allows a webpage-derived email body to an independently authorized recipient while blocking a webpage-derived recipient; no LLM assertion can narrow provenance without trusted evidence.

### FM-004 - Formalize delegation

- **Priority:** P0
- **Paper areas:** new delegation section, theorem, threat model
- **Code areas:** `auth`, `policy`, `core`, audit
- **Action:** Implement scoped attenuating delegation capabilities with expiry, use count, target, operation, argument, observer, and transitivity caveats.
- **Acceptance criteria:** Delegation can never exceed issuer authority; replay, widening, expiry, and revocation tests exist.

### EV-001 - Recast SLED as bounded explicit-state verification

- **Priority:** P0
- **Paper areas:** SLED design and claims
- **Code areas:** `sled`
- **Action:** Document state schema, transitions, bounds, state equivalence, and property semantics.
- **Acceptance criteria:** Report unique states/transitions, truncation, coverage, and minimal counterexamples; eliminate unqualified “exhaustive” wording.

### EV-002 - Add mutation testing for defences

- **Priority:** P0
- **Code areas:** `sled`, tests
- **Action:** Create flawed monitors: omitted influencer, union-of-permissions, stale ACS, skipped nested propagation, unknown-provenance allow, missing observer check, replayable delegation.
- **Acceptance criteria:** SLED finds a counterexample for each mutant and the correct monitor passes within the same bounds.

### EV-003 - Separate security and utility evaluation

- **Priority:** P0
- **Paper areas:** results
- **Code areas:** benchmark reporting
- **Action:** Keep worst-case nondeterminism for invariant checking and add real-model runs for task utility.
- **Acceptance criteria:** No metric called security depends on the model refusing an attack; no utility claim is inferred from abstract authorization alone.

### EV-004 - Add benchmark provenance overlays

- **Priority:** P1
- **Code areas:** `benchmarks`
- **Action:** Annotate AgentDojo first, then AgentPI/AgentDyn, with principals, resources, read/write relationships, argument roles, and intended observers.
- **Acceptance criteria:** At least one mixed-trust task differentiates flat ITES from role-sensitive Principal Context.

### SW-001 - Define a provenance adapter contract

- **Priority:** P0
- **Code areas:** `providers`, `core`
- **Action:** Specify soundness, field labels, activities, attestations, unknown fallback, and output propagation.
- **Acceptance criteria:** An adversarial provider test suite detects omitted or forged provenance and fails closed.

### SW-002 - Add complete-mediation tests

- **Priority:** P0
- **Code areas:** execution and provider integrations
- **Action:** Enumerate every effect path and test that bypassing the reference monitor is impossible through alternate methods, nested calls, retries, or background tasks.
- **Acceptance criteria:** A documented effect-boundary inventory maps each external side effect to one monitor entry point.

### SW-003 - Integrate a real policy decision point

- **Priority:** P1
- **Code areas:** `auth`, adapters
- **Action:** Implement one parameterized adapter, preferably Cedar or OpenFGA, while retaining the in-memory ACS for formal tests.
- **Acceptance criteria:** Resource- and argument-sensitive authorization, revocation, and policy-version recording work end to end.

### SW-004 - Make authorization, visibility, consent, and safety independent

- **Priority:** P1
- **Code areas:** `auth`, `policy`, `ites`, reporting
- **Action:** Replace a single Boolean checker with typed component decisions and deterministic composition.
- **Acceptance criteria:** Tests show cases that are authorized but lack consent, authorized but violate visibility, and unauthorized despite being safe.

### DOC-001 - Add a claim-to-evidence ledger

- **Priority:** P1
- **Paper/docs areas:** `paper`, `docs`
- **Action:** For every major claim, record formal assumption, proof/test/benchmark evidence, known counterexamples, and source references.
- **Acceptance criteria:** Codex can locate the evidence supporting each abstract/conclusion claim without inferring it from prose.

## 13. Research hypotheses capable of producing a state-of-the-art contribution

### H1 - Existing-ACS argument provenance dominates trust-tier contracts in heterogeneous organizations

**Hypothesis.** For workflows with principals that have incomparable permissions, principal-specific authorization will allow more legitimate actions and block more unauthorized actions than a fixed trusted/user/tool/external hierarchy.

**Experiment.** Construct tasks where two external services have different resource permissions, not a total trust order. Compare PACT-style trust thresholds, binary IFC labels, and Conflux principal-aware checks at the same argument granularity.

**Novelty value.** High. This directly tests the distinctive reason to use named principals rather than trust classes.

### H2 - Delegation capabilities recover action-open utility without weakening worst-case authorization

**Hypothesis.** A scoped capability with role- and argument-level caveats can support tasks where external content legitimately chooses among approved actions, while retaining a formal attenuation guarantee.

**Experiment.** Use AutoDojo action-open tasks and AgentDyn helpful-instruction tasks. Compare flat blocking, user confirmation, broad allowlisting, and caveated delegation.

**Novelty value.** High. Existing work discusses user approval and certified discharge, but an ACS-grounded, multi-principal attenuation theorem and implementation would be distinctive.

### H3 - Provenance precision can be optimized independently from policy semantics

**Hypothesis.** A fixed authorization policy exhibits a measurable frontier between provenance soundness, utility, and capture cost. Field-level attested provenance recovers most utility without relying on model-level source inference.

**Experiment.** Evaluate P0-P4 provenance precision levels from Section 7.2 across mixed-trust benchmarks. Report authority loss from over-tainting and security failures from deliberately unsound narrowing.

**Novelty value.** Medium-high. PACT isolates provenance inference as a bottleneck; Conflux can provide a systems-oriented precision ladder and attestation design.

### H4 - SLED mutation completeness predicts real integration bugs

**Hypothesis.** A verifier that kills a comprehensive monitor-mutant suite is more likely to detect real framework bypasses than a large raw-trace count.

**Experiment.** Seed bugs in adapters and monitor code, generate minimal counterexamples, then compare with integration tests over AgentDojo/LivePI-like environments.

**Novelty value.** High for evaluation methodology.

### H5 - Principal Context is a reusable security effect system

**Hypothesis.** Authorization, visibility, consent, delegation, and audit obligations can be represented as a compositional effect attached to values and actions, enabling static checks for deterministic code and dynamic checks around LLM calls.

**Experiment.** Define algebraic join/meet operations and a typed Python IR. Show composition across nested tools and multi-agent handoff, with runtime fallback for opaque LLM transformations.

**Novelty value.** High if formalised and implemented cleanly. This could broaden the project beyond one policy.

### H6 - Security-preserving planning reduces over-tainting

**Hypothesis.** Planning that delays low-authority reads until after privileged decisions, or separates independent subcomputations, completes more authorized tasks without changing the monitor.

**Experiment.** Compare naïve full-context prompting, dependency-aware task decomposition, and label-aware planning under the same Principal Context policy.

**Novelty value.** Medium-high; connects system security to agent planning rather than policy relaxation.

## 14. Recommended sequence for the next project year

### Phase 1 - Stabilise claims and specification

1. Rewrite threat model and related work.
2. Define parameterized effects, argument roles, and Principal Context.
3. Formalise the TCB and fail-closed semantics.
4. Recast current ITES as the flat baseline policy.
5. Add SEAgent, PACT, FIDES, FORGE, and ARGUS comparisons.

### Phase 2 - Implement the strongest mechanism extension

1. Per-argument provenance with conservative fallback.
2. Separate authorization/visibility/consent decisions.
3. One real ACS adapter.
4. Mixed-trust benchmark cases.
5. Delegation capability prototype.

### Phase 3 - Turn SLED into verification infrastructure

1. Independent property specification.
2. State canonicalization and minimal counterexamples.
3. Monitor mutation suite.
4. Explicit bounds and coverage reports.
5. Import/export trace IR.

### Phase 4 - Empirical comparison

1. AgentDojo annotated overlay.
2. AgentPI or AgentDyn context-dependent tasks.
3. AutoDojo attacks against inference/adapter boundaries.
4. At least one real-model and one live integration.
5. CaMeL/FIDES/PACT/SEAgent-inspired baselines at matched granularity where faithful comparison is possible.

### Phase 5 - Formal assurance and paper consolidation

1. Model-check the monitor/delegation protocol.
2. Add proof or mechanised lemmas for attenuation.
3. Publish a claim-evidence ledger and reproducibility bundle.
4. Rewrite the paper around Principal Context rather than only ITES.

## 15. Source inventory and suggested citations

The list below is intentionally machine-readable. `relevance` indicates how the source should be used, not an endorsement of every claim.

### 15.1 Primary Conflux artifacts

- **CONFLUX-REPORT-2026**. Raya Buckley. *Securing LLM Assistants via Fine-Grained Provenance-Based Authority*. Oxford MCompSci Part B project report, Trinity 2026. `relevance: original ITES/SLED design; extensions; prototype`.
- **CONFLUX-PREPRINT-2026**. Anonymous. *Influence Tracking for Secure LLM Agents: Preventing Privilege Escalation Under Worst-Case Model Behaviour*. June 2026 preprint. `relevance: current formal claims and evaluation`.
- **CONFLUX-REPO-2026**. RayaBuckley/Conflux. https://github.com/RayaBuckley/Conflux/ `relevance: current Principal Context architecture and implementation roadmap`.

### 15.2 Closest system-level and provenance work

- **CAMEL-2025**. Edoardo Debenedetti et al. *Defeating Prompt Injections by Design*. arXiv:2503.18813. https://arxiv.org/abs/2503.18813
- **DESIGN-PATTERNS-2025**. Luca Beurer-Kellner et al. *Design Patterns for Securing LLM Agents against Prompt Injections*. arXiv:2506.08837. https://arxiv.org/abs/2506.08837
- **FSECURE-2024**. Fangzhou Wu, Ethan Cecchetti, Chaowei Xiao. *System-Level Defense against Indirect Prompt Injection Attacks: An Information Flow Control Perspective*. arXiv:2409.19091. https://arxiv.org/abs/2409.19091
- **FIDES-2025**. Luca Costa et al. *Securing AI Agents with Information-Flow Control*. arXiv:2505.23643. https://arxiv.org/abs/2505.23643
- **RTBAS-2025**. *RTBAS: Defending LLM Agents Against Prompt Injection and Privacy Leakage*. arXiv:2502.08966. https://arxiv.org/abs/2502.08966
- **CONSECA-2025**. Tsai and Bagdasarian. *Contextual Agent Security: A Policy for Every Purpose*. arXiv:2501.17070. https://arxiv.org/abs/2501.17070
- **PROGENT-2025**. *Progent: Programmable Privilege Control for LLM Agents*. arXiv:2504.11703. https://arxiv.org/abs/2504.11703
- **AGENTSPEC-2025**. *AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents*. arXiv:2503.18666. https://arxiv.org/abs/2503.18666
- **AGENTARMOR-2025**. Peiran Wang et al. *AgentArmor: Enforcing Program Analysis on Agent Runtime Trace to Defend Against Prompt Injection*. arXiv:2508.01249. https://arxiv.org/abs/2508.01249
- **FORGE-2026**. Nils Palumbo et al. *Formal Policy Enforcement for Real-World Agentic Systems*. arXiv:2602.16708. https://arxiv.org/abs/2602.16708
- **SEAGENT-2026**. Zimo Ji et al. *Taming Various Privilege Escalation in LLM-Based Agent Systems: A Mandatory Access Control Framework*. arXiv:2601.11893. https://arxiv.org/abs/2601.11893
- **PACT-2026**. Linfeng Fan et al. *The Granularity Mismatch in Agent Security: Argument-Level Provenance Solves Enforcement and Isolates the LLM Reasoning Bottleneck*. arXiv:2605.11039. https://arxiv.org/abs/2605.11039
- **ARGUS-2026**. *ARGUS: Defending LLM Agents Against Context-Aware Prompt Injection*. arXiv:2605.03378. https://arxiv.org/abs/2605.03378
- **PROVENANCEGUARD-2026**. *Safeguarding LLM Agents from Misalignment through Provenance Analysis*. arXiv:2607.01236. https://arxiv.org/abs/2607.01236
- **NEUROTAINT-2026**. *Ghost in the Agent: Redefining Information Flow Tracking for LLM Agents*. arXiv:2604.23374. https://arxiv.org/abs/2604.23374
- **AGENT-SENTRY-BOUNDING-2026**. Rohan Sequeira et al. *Agent-Sentry: Bounding LLM Agents via Execution Provenance*. arXiv:2603.22868. https://arxiv.org/abs/2603.22868
- **AGENTSENTRY-CAUSAL-2026**. Tian Zhang et al. *AgentSentry: Mitigating Indirect Prompt Injection in LLM Agents via Temporal Causal Diagnostics and Context Purification*. arXiv:2602.22724. https://arxiv.org/abs/2602.22724
- **SECURECLAW-2026**. Yuhan Ma and Stefan Schmid. *SecureClaw: Clawing Back Control of LLM Agents*. arXiv:2606.09549. https://arxiv.org/abs/2606.09549
- **AUTH-WORKFLOWS-2026**. Mohan Rajagopalan and Vinay Rao. *Authenticated Workflows: A Systems Approach to Protecting Agentic AI*. arXiv:2602.10465. https://arxiv.org/abs/2602.10465
- **SILENT-EGRESS-2026**. *Silent Egress*. arXiv:2602.22450. https://arxiv.org/abs/2602.22450

### 15.3 Evaluation, attacks, and systematization

- **AGENTDOJO-2024**. Edoardo Debenedetti et al. *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents*. arXiv:2406.13352. https://arxiv.org/abs/2406.13352
- **INJECAGENT-2024**. *InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents*. arXiv:2403.02691. https://arxiv.org/abs/2403.02691
- **AGENTPI-SOK-2026**. Peiran Wang et al. *The Landscape of Prompt Injection Threats in LLM Agents: From Taxonomy to Analysis*. arXiv:2602.10453. https://arxiv.org/abs/2602.10453
- **AGENTDYN-2026**. Hao Li et al. *AgentDyn: A Dynamic Open-Ended Benchmark for Evaluating Prompt Injection Attacks of Real-World Agent Security System*. arXiv:2602.03117. https://arxiv.org/abs/2602.03117
- **AUTODOJO-2026**. Xinhang Ma et al. *AutoDojo: Adaptive Attacks Expose Superficial Defenses and User-Underspecification Limits in LLM Agents*. arXiv:2606.15057. https://arxiv.org/abs/2606.15057
- **LIVEPI-2026**. Lei Zhao, Abhay Bhaskar, Edgar Dobriban. *LivePI: More Realistic Benchmarking of Agents Against Indirect Prompt Injection*. arXiv:2605.17986. https://arxiv.org/abs/2605.17986
- **AGENTSECBENCH-2026**. *AgentSecBench*. arXiv:2605.26269. https://arxiv.org/abs/2605.26269
- **ADAPTIVE-EVAL-2026**. *Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection in LLM Agents*. arXiv:2606.26479. https://arxiv.org/abs/2606.26479
- **AUTOMATED-ATTACKS-2026**. David Hofer, Edoardo Debenedetti, Florian Tramèr. *Assessing Automated Prompt Injection Attacks in Agentic Environments*. arXiv:2606.10525. https://arxiv.org/abs/2606.10525
- **PUBLIC-COMPETITION-2026**. Mateusz Dziemian et al. *How Vulnerable Are AI Agents to Indirect Prompt Injections? Insights from a Large-Scale Public Competition*. arXiv:2603.15714. https://arxiv.org/abs/2603.15714
- **ART-2025**. *Security Challenges in AI Agent Deployment: Insights from a Large Scale Public Competition*. arXiv:2507.20526. https://arxiv.org/abs/2507.20526
- **FORMAL-AGENT-SECURITY-2026**. Vincent Siu et al. *A Framework for Formalizing LLM Agent Security*. arXiv:2603.19469. https://arxiv.org/abs/2603.19469
- **ARCHITECTING-2026**. *Architecting Secure AI Agents: Perspectives on System-Level Defenses Against Indirect Prompt Injection Attacks*. arXiv:2603.30016. https://arxiv.org/abs/2603.30016

### 15.4 Model-level defence and attack references already relevant to the paper

- **STRUQ-2024**. Sizhe Chen et al. *StruQ: Defending Against Prompt Injection with Structured Queries*. arXiv:2402.06363.
- **SPOTLIGHTING-2024**. Keegan Hines et al. *Defending Against Indirect Prompt Injection Attacks with Spotlighting*. arXiv:2403.14720.
- **DEFENSIVETOKENS-2025**. Sizhe Chen et al. *Defending Against Prompt Injection with a Few DefensiveTokens*. arXiv:2507.07974.
- **SECALIGN-2025**. Sizhe Chen et al. *SecAlign: Defending Against Prompt Injection with Preference Optimization*. ACM CCS 2025. DOI:10.1145/3719027.3744836.
- **DATASENTINEL-2025**. Yupei Liu et al. *DataSentinel: A Game-Theoretic Detection of Prompt Injection Attacks*. arXiv:2504.11358.
- **NEURALEXEC-2024**. Dario Pasquini et al. *Neural Exec: Learning (and Learning from) Execution Triggers for Prompt Injection Attacks*. arXiv:2403.03792.
- **CHECKPOINT-GCG-2025**. Xiaoxue Yang et al. *Checkpoint-GCG: Auditing and Attacking Fine-Tuning-Based Prompt Injection Defenses*. arXiv:2505.15738.
- **CRITICAL-EVAL-2025**. Yuqi Jia et al. *A Critical Evaluation of Defenses Against Prompt Injection Attacks*. arXiv:2505.18333.
- **MELON-2025**. Kaijie Zhu et al. *MELON: Indirect Prompt Injection Defense via Masked Re-execution and Tool Comparison*. arXiv:2502.05174.

### 15.5 Classical foundations

- **SALTZER-SCHROEDER-1975**. Jerome H. Saltzer and Michael D. Schroeder. *The Protection of Information in Computer Systems*. Proceedings of the IEEE 63(9), 1278-1308. DOI:10.1109/PROC.1975.9939.
- **ANDERSON-1972**. James P. Anderson. *Computer Security Technology Planning Study*. ESD-TR-73-51, 1972. `relevance: reference monitor`.
- **LAMpson-1971**. Butler Lampson. *Protection*. Fifth Princeton Symposium on Information Sciences and Systems, 1971. `relevance: access matrix and protection domains`.
- **BIBA-1977**. Kenneth J. Biba. *Integrity Considerations for Secure Computer Systems*. MITRE ESD-TR-76-372, 1977.
- **BELL-LAPADULA-1973**. D. Elliott Bell and Leonard J. LaPadula. *Secure Computer Systems: Mathematical Foundations*. MITRE, 1973.
- **GOGUEN-MESEGUER-1982**. Joseph Goguen and José Meseguer. *Security Policies and Security Models*. IEEE Symposium on Security and Privacy, 1982. DOI:10.1109/SP.1982.10014.
- **CLARKSON-SCHNEIDER-2010**. Michael R. Clarkson and Fred B. Schneider. *Hyperproperties*. Journal of Computer Security 18(6), 1157-1210. DOI:10.3233/JCS-2009-0393.
- **MYERS-LISKOV-1997**. Andrew C. Myers and Barbara Liskov. *A Decentralized Model for Information Flow Control*. SOSP 1997. DOI:10.1145/268998.266669.
- **MYERS-LISKOV-1998**. Andrew C. Myers and Barbara Liskov. *Complete, Safe Information Flow with Decentralized Labels*. IEEE Symposium on Security and Privacy, 1998.
- **HARDY-1988**. Norm Hardy. *The Confused Deputy (or Why Capabilities Might Have Been Invented)*. ACM SIGOPS Operating Systems Review 22(4), 36-38. DOI:10.1145/54289.871709.
- **MACAROONS-2014**. Arnar Birgisson et al. *Macaroons: Cookies with Contextual Caveats for Decentralized Authorization in the Cloud*. NDSS 2014.
- **RBAC-1996**. Ravi Sandhu, Edward Coyne, Hal Feinstein, Charles Youman. *Role-Based Access Control Models*. IEEE Computer 29(2), 38-47, 1996.
- **NIST-ABAC-2019**. Vincent C. Hu et al. *Guide to Attribute Based Access Control (ABAC) Definition and Considerations*. NIST SP 800-162. DOI:10.6028/NIST.SP.800-162.
- **BUNEMAN-2001**. Peter Buneman, Sanjeev Khanna, Wang-Chiew Tan. *Why and Where: A Characterization of Data Provenance*. ICDT 2001. DOI:10.1007/3-540-44503-X_20.
- **GREEN-2007**. Todd J. Green, Grigoris Karvounarakis, Val Tannen. *Provenance Semirings*. PODS 2007. `relevance: how-provenance algebra`.
- **W3C-PROV-2013**. W3C. *PROV Family of Documents*. W3C Recommendations, 30 April 2013. https://www.w3.org/TR/prov-overview/
- **SERVOS-OSBORN-2017**. Daniel Servos and Sylvia L. Osborn. *Current Research and Open Problems in Attribute-Based Access Control*. ACM Computing Surveys 49(4). DOI:10.1145/3007204.
- **PROVOS-2003**. Niels Provos, Markus Friedl, Peter Honeyman. *Preventing Privilege Escalation*. USENIX Security 2003.
- **CLARKE-EMERSON-1981**. Edmund M. Clarke and E. Allen Emerson. *Design and Synthesis of Synchronization Skeletons Using Branching-Time Temporal Logic*. `relevance: model checking`.
- **QUEILLE-SIFAKIS-1982**. Jean-Pierre Queille and Joseph Sifakis. *Specification and Verification of Concurrent Systems in CESAR*. `relevance: model checking`.
- **COUSOT-COUSOT-1977**. Patrick Cousot and Radhia Cousot. *Abstract Interpretation: A Unified Lattice Model for Static Analysis*. POPL 1977.

## 16. Final assessment

The original project made a correct strategic move: it stopped asking an untrusted model to be the final security authority. The next stage should preserve that principle while acknowledging that provenance-based agent security is now a crowded and fast-moving area.

The project can still make a substantial contribution by becoming the system that connects four layers that existing papers usually address separately:

1. **real organizational identities and access-control decisions**;
2. **fine-grained, attested provenance at value and argument level**;
3. **explicit, attenuating delegation and consent**;
4. **bounded formal verification plus real-agent benchmark evaluation**.

The clearest paper-level thesis is no longer “intersection is all you need.” It is:

> **Principal Context is the system-level security interface between probabilistic reasoning and deterministic authority.**

ITES then becomes the strict baseline authorization rule over that interface, SLED becomes the verifier for reference-monitor implementations, and Conflux becomes the production framework that integrates both with real policies, tools, agents, and provenance sources.
