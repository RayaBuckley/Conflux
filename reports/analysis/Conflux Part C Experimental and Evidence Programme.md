# Conflux Part C Experimental and Evidence Programme

## Purpose

The objective for the remaining two months should not be to maximise the number of features in Conflux. It should be to maximise the amount of **credible evidence per unit of implementation effort** supporting a small number of important research claims.

This distinction matters because Conflux already has substantial engineering surface. The current repository describes a fail-closed ITES mediation kernel, bounded SLED verification, solver-facing models, deterministic adapters, authenticated dynamic plans, an offline CLI, policy integration and a pinned AgentDojo translation boundary. Its own development rules prioritise security-model correctness, organisational access-control fidelity and reproducibility ahead of extensibility and performance.

The current manuscript is appropriately cautious: AgentDojo, Cedar parity, planning and delegation claims are not supposed to become research claims until gated experiments produce retained, checksummed results. The experimental infrastructure likewise requires curated evidence bundles to contain manifests, raw traces, versioned results, summaries, checksums and a rerun command.

That is a strong foundation. The remaining risk is **evidence sparsity**: having a sophisticated system whose individual mechanisms have not been sufficiently isolated, compared, stressed, falsified and measured.

The proposed programme therefore treats the remaining roughly two months of AI-coder time as an experimental research campaign.

---

# 1. What the final project should demonstrate

A strong final dissertation should be able to defend six claims.

| Research question | Desired claim |
|---|---|
| RQ1: Correctness | Conflux implements its stated Principal Context semantics correctly. |
| RQ2: Necessity | Principal Context prevents failures that plausible weaker mechanisms do not. |
| RQ3: Utility | The security improvement does not come merely from rejecting everything. |
| RQ4: Robustness | The result survives different attacks, workflows, policies, models and numbers of principals. |
| RQ5: Scalability | The mechanism remains computationally practical as workflows become larger. |
| RQ6: Generality | The result transfers beyond hand-designed Conflux examples to recognised external benchmarks. |

There should also be a seventh, partly theoretical question:

**RQ7: Why does the mechanism work?**

The answer should not just be empirical. Ideally the dissertation establishes formal properties connecting provenance, Principal Context and action-time authorisation.

The final story becomes:

> Conflux identifies authority confusion as a distinct security problem in agentic systems; formalises a conservative Principal Context for addressing it; implements that semantics in a reference monitor; demonstrates the necessity of its components through ablation; evaluates security, utility and scalability; and compares the resulting architecture against contemporary agent-security mechanisms.

That is a substantially stronger research story than simply presenting a large software framework.

---

# 2. The most important change in strategy

From this point onward, every significant coding task should belong to one of four categories:

| Category | Purpose |
|---|---|
| Evidence-producing | Produces a result supporting/refuting a dissertation claim. |
| Evidence-enabling | Makes an important experiment possible. |
| Correctness-hardening | Increases confidence that existing results are genuine. |
| Reproducibility | Makes evidence independently rerunnable and auditable. |

A fifth category, "new functionality", should normally be rejected unless it is required by one of the above.

A useful rule for the AI coder is:

> **No feature without a research question; no experiment without an oracle; no result without raw evidence; no dissertation claim without a reproducible result.**

This is particularly appropriate given the repository's existing requirement that provenance not be silently discarded, Principal Context be evaluated at action time, authorisation/visibility/consent remain separate, and benchmark code not encode benchmark-specific shortcuts.

---

# 3. Establish a claim–evidence matrix first

Before implementing another experiment, the coding agent should construct or extend the existing canonical claim/task infrastructure rather than create another competing status document.

For every important dissertation claim, record:

| Field | Meaning |
|---|---|
| Claim ID | Stable identifier |
| Claim | Exact falsifiable statement |
| Type | theorem / implementation / experiment / benchmark / performance |
| Experiment IDs | Evidence supporting it |
| Negative tests | What could falsify it |
| Status | untested / partial / supported / contradicted |
| Raw evidence | Result artefacts |
| Figure/table | Dissertation presentation |
| Assumptions | Conditions under which claim holds |
| Limitations | Known counterexamples or scope limits |

This prevents the AI coder from producing large amounts of technically valid but academically low-value work.

The existing manuscript already uses a claim ledger and evidence gates, so this should extend that architecture rather than duplicate it.

---

# 4. Baseline hierarchy

Ablations should begin with a coherent hierarchy of increasingly strong systems.

| ID | System | Question answered |
|---|---|---|
| B0 | Unprotected agent | How vulnerable is the underlying agent? |
| B1 | Defensive system prompt | Can model instructions solve the problem? |
| B2 | Static tool allow-list | Is limiting tool availability sufficient? |
| B3 | Requester-only ACL | Is authenticating/authorising the initial user sufficient? |
| B4 | Static capability model | Is conventional least-privilege capability assignment sufficient? |
| B5 | Direct-source Principal Context | Is transitive provenance necessary? |
| B6 | Full Conflux Principal Context | Main treatment |
| B7 | Fides-style IFC | How does PC compare with contemporary information-flow enforcement? |
| B8 | CaMeL-style control/data separation | How does PC compare with another architectural prompt-injection defence? |

B0–B6 are much more important than adding another six sophisticated baselines.

Fides and CaMeL are particularly important related work now. Fides develops a formal IFC model and tracks confidentiality/integrity information through agent execution, while CaMeL separates trusted control flow from untrusted data and uses capabilities to restrict unauthorised information flow.

This means a future examiner can reasonably ask:

> Why Principal Context rather than information-flow control or capabilities?

The project should have an empirical and theoretical answer.

---

# 5. Core Principal Context ablations

These have the highest expected evidence value.

## A1. No security mediation

Disable Conflux mediation while keeping everything else as constant as possible.

Measure benign task success and attack success.

Purpose: establish that the benchmark actually contains exploitable situations.

## A2. Requester-only authority

The requester determines authority throughout execution.

Everything else remains unchanged.

This is probably the single most important ablation because it directly tests the motivating confused-deputy claim.

## A3. Union-of-authority

Permit an action if **any** influencing principal possesses the permission.

This deliberately represents an unsafe alternative and should produce clear counterexamples.

It demonstrates why "collect permissions from everyone involved" is not equivalent to conservative PC.

## A4. Full all-principal authority

Require every relevant influencing principal to satisfy the policy.

This is the primary treatment.

## A5. Direct provenance only

Include principals attached directly to the current value but discard transitive ancestors.

Construct attacks in which:

Alice → document → summary → plan → tool call.

If Alice disappears after summarisation, authority laundering becomes possible.

## A6. Bounded provenance

Keep only the most recent one, two, three, etc. provenance hops.

Plot attack success and false-denial rate against provenance depth.

This turns an implementation decision into a quantitative result.

## A7. No provenance

Preserve normal values but discard principal metadata.

This isolates the contribution of provenance itself.

## A8. Source trust labels instead of principals

Replace individual Principal Context with coarse trusted/untrusted labels.

This provides a useful bridge to prompt-injection defences.

Construct cases where two individually legitimate users have different permissions despite both being "trusted."

## A9. Requester + direct external source

A plausible intermediate architecture.

It tests whether the full transitive mechanism is really necessary.

## A10. Plan-time authority

Check authority when the plan is created but not immediately before execution.

## A11. Action-time authority

Canonical Conflux behaviour.

The paired A10/A11 experiment is especially valuable under permission revocation or policy updates.

---

# 6. TOCTOU and dynamic-policy experiments

Action-time authorisation is one of Conflux's stated invariants. It therefore deserves direct experimental evidence.

Construct workflows where the following changes after planning but before execution:

| Change | Expected canonical behaviour |
|---|---|
| User permission revoked | block |
| Resource ownership changes | re-evaluate |
| Group membership removed | block if authority depended on it |
| Consent withdrawn | block |
| Visibility tightened | block disclosure |
| Policy changes | use current policy |
| Principal disabled | block |
| Delegation expires | block |

Compare request-time, plan-time and action-time enforcement.

A particularly effective figure would show the proportion of stale-authority violations as the delay between planning and execution increases.

This experiment directly justifies **complete mediation at action time** rather than presenting it merely as an implementation detail.

---

# 7. Authorisation/visibility/consent ablations

The repository deliberately treats these as separate concepts. That architectural decision should be experimentally justified.

Run:

| Variant | Removed mechanism |
|---|---|
| Canonical | none |
| V1 | consent |
| V2 | visibility/audience constraints |
| V3 | read-access enforcement |
| V4 | authorisation |
| V5 | collapse consent into authorisation |
| V6 | collapse visibility into authorisation |

Create counterexamples where each collapsed design produces an incorrect decision.

The strongest outcome is not necessarily a huge benchmark. A small, exhaustive collection of carefully designed distinguishing examples can establish that these concepts are semantically non-equivalent.

---

# 8. Provenance-preservation experiments

This deserves a large dedicated suite.

Test provenance through:

| Transformation | Test |
|---|---|
| Copy | source retained |
| Concatenation | union of sources |
| Selection | relevant provenance retained |
| Filtering | retained values retain provenance |
| Summarisation | all influencing sources conservatively retained |
| Translation | provenance retained |
| Classification | source influences classification |
| Aggregation | participating sources retained |
| Sorting | source identity preserved |
| Join | provenance combines correctly |
| LLM generation | inputs influencing generation propagate |
| Tool call | argument provenance reaches action |
| Tool output | tool/resource principal introduced |
| Planning | context propagates into steps |
| Sub-plan | ancestry preserved |
| Memory | provenance survives persistence |
| Serialisation | exact round-trip |
| Deserialisation | cannot manufacture trusted provenance |

For each transformation test three things:

1. expected value;
2. expected provenance;
3. resulting policy decision.

The experiment suite should include chains of transformations, not just single operations.

---

# 9. Provenance laundering attacks

These are adversarial versions of the previous tests.

Try to make an unauthorised principal disappear through:

| Attack | Example |
|---|---|
| Summarisation laundering | malicious document → summary |
| Translation laundering | injected text → translated text |
| Encoding laundering | encoded content → decoder |
| Copy laundering | source → intermediate variable |
| Planning laundering | source → planner → action |
| Memory laundering | source stored then retrieved later |
| Tool laundering | source passed through apparently trusted tool |
| Agent laundering | source passed to sub-agent |
| Aggregation laundering | malicious source mixed with legitimate sources |
| Attribution spoofing | source claims another owner |
| Metadata injection | attacker supplies fake provenance metadata |
| Re-serialisation | labels removed/reconstructed |
| Cross-session laundering | provenance lost between runs |

These should become a named attack family in the dissertation.

---

# 10. Principal-count scaling experiment

This is one of the most distinctive experiments available to Conflux.

Generate equivalent scenarios with:

1, 2, 4, 8, 16, 32, 64, 128 and, for deterministic microbenchmarks, potentially hundreds or thousands of principals.

Measure:

- decision correctness;
- false-denial rate;
- mediation latency;
- memory;
- policy checks;
- provenance representation size.

Then separately vary the proportion of principals who possess the required permission.

This gives both systems and security results.

The important conceptual question is:

> What happens as an agent combines information belonging to increasingly many mutually independent authorities?

That question is much closer to Conflux's core novelty than generic prompt-injection benchmarking.

---

# 11. Provenance topology experiments

Principal count alone is insufficient. Keep principal count constant and vary graph structure.

| Topology | Purpose |
|---|---|
| Chain | provenance depth |
| Star | fan-in |
| Tree | hierarchical derivation |
| Diamond | deduplication |
| DAG | realistic mixed derivation |
| High fan-out | reuse of one source |
| Repeated principal | deduplication correctness |
| Cyclic planning graph | robustness to invalid structures |

Measure provenance size, evaluation time and correctness.

This produces a much stronger complexity analysis than a single latency number.

---

# 12. Permission-overlap experiment

For `n` principals, vary how similar their permissions are.

At one extreme all principals have identical authority.

At the other they have almost disjoint permissions.

Measure legitimate completion rate under Principal Context.

This exposes an important limitation:

**conservative authority intersection may become increasingly restrictive in heterogeneous multi-principal environments.**

That is worth measuring rather than hiding.

A negative result here would strengthen the dissertation if analysed properly.

---

# 13. Taint/principal flooding and denial of service

An attacker may not need to gain authority. They may deliberately influence an action so that their unauthorised principal enters PC, causing the action to be denied.

Construct adversaries whose goal is **availability loss rather than privilege escalation**.

Measure:

- induced false blocks;
- task completion degradation;
- number of malicious influences needed;
- whether provenance precision mitigates the attack.

This is an important security/utility limitation of conservative provenance mechanisms and closely parallels over-tainting problems in information-flow systems.

---

# 14. Attack-position experiment

Place malicious instructions at different points:

| Location |
|---|
| original user request |
| email body |
| document |
| web page |
| retrieved database field |
| tool response |
| calendar event |
| memory |
| intermediate LLM output |
| planner state |
| sub-agent response |
| structured metadata |
| tool description |

Compare attack success.

This tests whether security depends on where untrusted influence enters.

---

# 15. Attack-depth experiment

Nest malicious influence at increasing depth:

attacker → document → summariser → planner → tool

then:

attacker → document → RAG → summariser → planner → sub-agent → tool.

Plot attack success against provenance depth.

A provenance-based security architecture should ideally be much less sensitive to this depth than prompt-based defences.

---

# 16. Attack-encoding robustness

For the LLM-facing experiments, use semantically equivalent attacks represented as:

plain text, Markdown, HTML, JSON fields, XML, comments, quoted emails, Unicode variants, encoded text that the agent is expected to decode, code blocks and structured tool output.

The point is not to claim that Principal Context detects prompt injection. It should not need to.

The desired result is:

> Even when the model follows the injected instruction, enforcement still prevents an unauthorised action.

That distinction is fundamental.

---

# 17. Adaptive attacker experiment

Evaluate at least three attacker knowledge levels:

| Attacker | Knowledge |
|---|---|
| Black-box | knows only observable agent behaviour |
| Grey-box | knows Conflux uses provenance |
| White-box | knows PC semantics and policies |

The white-box attacker should deliberately attempt:

- provenance laundering;
- principal spoofing;
- policy confusion;
- delegation abuse;
- stale-plan execution;
- consent confusion;
- reader/recipient confusion;
- multi-step indirect effects.

A security architecture is substantially more convincing if the attacker knows the defence.

---

# 18. Colluding-principal experiments

Use multiple malicious principals.

Vary:

- one attacker among benign principals;
- multiple attackers;
- attackers with complementary permissions;
- attackers controlling different resources;
- attackers communicating through shared state.

An especially useful question is whether two principals can combine partial permissions into an authority neither possesses individually.

Canonical PC should prevent inappropriate authority union.

---

# 19. Delegation experiments

The current manuscript says scoped delegation exists in the model but runtime activation remains gated.

If delegation is activated, it deserves its own evaluation.

Test:

valid delegation, expired delegation, excessive scope, transitive delegation, revoked delegation, forged delegation, cyclic delegation, delegation to a principal already influencing the action, and attempts to use consent as delegation.

However, delegation should remain secondary unless it is necessary for the dissertation's central claim. Do not spend weeks turning it into another research project.

---

# 20. Dynamic-plan integrity experiments

Authenticated planning is already an implemented component. It needs adversarial tests.

Take a valid plan and mutate:

- action;
- arguments;
- principal context;
- provenance;
- resource ID;
- step ordering;
- step insertion;
- step deletion;
- recipient;
- permission;
- signature;
- plan identifier.

Also test replay of an old valid plan after policy changes.

Expected result: tampering is detected or reauthorisation prevents execution.

This gives authenticated planning an empirical justification.

---

# 21. Fail-closed experiments

The README explicitly claims unavailable optional backends fail rather than silently weakening the deterministic path. Test this systematically.

Inject:

policy timeout, policy exception, malformed response, unavailable solver, unavailable Cedar, invalid schema, corrupt provenance, missing principal, unknown action type, malformed tool call, unknown resource, deserialisation failure, invalid plan authentication and partially written state.

For every case, classify the result as:

secure deny / explicit error / insecure permit / crash.

There should be **zero insecure permits**.

This is high-value engineering evidence because it tests the security boundary rather than ordinary happy-path code.

---

# 22. Complete-mediation tests

Enumerate every way an agent can produce an externally meaningful effect.

Examples include tool calls, final responses containing protected information, file writes, network sends, database changes, plan execution and potentially logging/telemetry if these can expose sensitive values.

The coding agent should build a coverage table mapping:

`effect → mediation point → security test`.

Then try to create a side effect without passing through ITES.

This is essentially an adversarial architectural review of the reference monitor.

---

# 23. Action-taxonomy bypass testing

Conflux has an action taxonomy. Attack its boundaries.

Test:

- unknown action;
- generic action wrapping privileged action;
- tool alias;
- nested action;
- malformed action;
- argument-dependent privilege;
- read disguised as metadata lookup;
- write disguised as update;
- external send disguised as logging.

The principle should be fail-safe defaults: unclassified privileged behaviour must not accidentally inherit benign permissions.

---

# 24. Policy-engine differential testing

The current manuscript describes native policy handling and an optional pinned Cedar adapter, with Cedar parity still requiring gated evidence.

This is an excellent engineering experiment.

Generate large numbers of policy decisions and compare native and Cedar-backed outcomes on their common semantic subset.

Partition results into:

`agree-allow / agree-deny / expected semantic mismatch / unexpected mismatch / error`.

Randomised policy generation can greatly increase evidence density.

If 100,000 deterministic policy cases can be generated and checked cheaply, do it.

The important condition is that generated cases have an independent oracle or precisely defined common semantics.

---

# 25. Metamorphic security testing

This can produce enormous evidence density at low cost.

For any scenario, transformations should satisfy properties such as:

| Transformation | Expected relation |
|---|---|
| Add irrelevant non-influencing principal | decision unchanged |
| Add influencing authorised principal | existing allow remains allow |
| Add influencing unauthorised principal | allow may become deny, never the reverse |
| Tighten policy | deny cannot become allow |
| Revoke permission | cannot create allow |
| Withdraw consent | cannot create allow |
| Reduce visibility | cannot create disclosure permission |
| Reorder independent provenance unions | decision unchanged |
| Duplicate same principal | decision unchanged |
| Serialize/deserialize | decision unchanged |
| Change benign wording only | security oracle unchanged |

Generate thousands of these automatically.

This is more meaningful than simply reporting line coverage.

---

# 26. Property-based testing

Use generated principals, resources, policies, provenance DAGs, actions and plans.

The generator should deliberately emphasise boundary cases:

empty sets, singleton sets, maximum overlaps, contradictory policy, duplicate principals, missing metadata, deeply nested provenance and extreme argument values.

Check invariants rather than expected hand-written outputs.

This can expose implementation bugs while simultaneously supporting the formal semantics.

---

# 27. Mutation testing

Ordinary test coverage can be misleading.

Mutate security-critical implementation logic:

- `all` → `any`;
- allow → deny / deny → allow;
- remove provenance union;
- skip one authorisation check;
- ignore consent;
- ignore visibility;
- evaluate at plan time;
- accept unknown action;
- fail open on backend error;
- disable plan authentication.

The test/experiment suite should kill nearly every security-relevant mutant.

A strong dissertation result would be:

> The security regression suite detects X/Y deliberately introduced semantic faults.

That is excellent engineering evidence.

---

# 28. Exhaustive small-world verification

Generate all combinations for very small systems.

For example:

- 2–4 principals;
- 1–3 resources;
- a small permission alphabet;
- short traces;
- bounded plans.

Enumerate every state/transition allowed by the formal subset and check the core invariants.

This complements random testing because it gives complete coverage within a bounded universe.

The existing SLED and solver-facing infrastructure makes this particularly natural.

---

# 29. SLED depth/bound sensitivity

For each verification property, increase:

- trace depth;
- principal count;
- branching factor;
- action count;
- policy complexity.

Record:

- states explored;
- runtime;
- peak memory;
- counterexamples;
- timeout rate.

Plot state-space growth.

This transforms "we built a bounded verifier" into a measured result about what it can actually verify.

---

# 30. Counterexample quality

For deliberately broken variants, ask SLED to find violations.

Measure:

- whether a violation is found;
- minimum counterexample length;
- time to counterexample.

Examples:

requester-only authority, no provenance propagation, plan-time-only authorisation, fail-open policy handling.

A very strong presentation is:

> Remove invariant X → verifier automatically discovers counterexample Y.

That links theory, implementation and experimentation unusually well.

---

# 31. Native-versus-solver verification parity

Where native SLED and solver-facing semantics overlap, run identical bounded worlds through both.

Compare reachable violations and decisions.

Unexpected disagreement is either a bug or an important semantic discrepancy.

This is a strong form of differential testing because the two implementations can serve as partially independent checks on one another.

---

# 32. Formal properties worth proving

The remaining work should not be purely empirical.

At minimum, attempt precise statements and proofs of the following.

### Provenance composition

If a value is derived from values with provenance \(P_1,\ldots,P_n\), its conservative provenance includes their union.

Useful algebraic properties are associativity, commutativity and idempotence of provenance union.

### Principal-context monotonicity

Under all-principal authorisation, adding another influencing principal cannot create authority that was previously absent.

Informally:

\[
P \subseteq P' \land Allow(P') \Rightarrow Allow(P)
\]

Equivalently, enlarging Principal Context cannot turn a denied action into an allowed action merely by adding another principal.

### Authority-safety theorem

Under clearly stated assumptions:

1. provenance over-approximates all principals influencing an action;
2. all external actions undergo complete mediation;
3. policy decisions are evaluated correctly at action time;

then an action cannot execute unless every relevant influencing principal satisfies the required authority predicate.

This should be the central theorem if it can be formalised cleanly.

### Provenance soundness versus precision

If provenance is an over-approximation, security can remain sound while utility decreases through false denials.

This gives a formal explanation of the security/utility trade-off.

### Consent non-authority

Adding consent cannot make an otherwise unauthorised action authorised.

### Action-time revocation

If required authority is revoked before the mediation point, the action is denied even if a previously constructed plan was valid.

### Plan-integrity property

Unauthenticated modification of a protected plan component cannot result in execution as the original authenticated plan.

These do not all need machine-checked proofs. A precise mathematical model plus conventional proofs, backed by bounded model checking, would already add meaningful theoretical depth.

---

# 33. Theoretical comparison with Fides and CaMeL

This has become important because the related-work landscape is close to Conflux.

Fides explicitly applies information-flow control to agent security, with confidentiality/integrity labels, deterministic enforcement and selective information hiding. Its authors also develop a formal model and taxonomy of tasks.

CaMeL protects agent execution by extracting trusted control/data flows and using capabilities to prevent unauthorised exfiltration; its reported AgentDojo evaluation achieves 67% of tasks with provable security.

Do not argue merely that Conflux is "different."

Construct distinguishing examples.

The analysis should identify tasks:

- secured by both;
- naturally represented by PC but awkward under coarse IFC labels;
- naturally represented by IFC but potentially over-restricted by PC;
- requiring organisational ACL semantics;
- requiring confidentiality labels;
- involving several mutually authorised principals;
- involving a principal who is trusted but lacks a specific permission.

The outcome may be that PC and IFC are complementary rather than one subsuming the other.

That is an acceptable and potentially stronger conclusion.

---

# 34. Build a dedicated Principal Context benchmark

Conflux should have an internal benchmark specifically designed around its research question rather than relying entirely on generic prompt-injection suites.

The benchmark should be generated along several orthogonal dimensions:

| Dimension | Values |
|---|---|
| Principals | 1 → many |
| Provenance depth | shallow → deep |
| Fan-in | low → high |
| Permission overlap | complete → disjoint |
| Resource ownership | private/shared/public |
| Attack location | user/tool/document/memory/plan |
| Action sensitivity | read/write/send/delete/transfer |
| Consent | required/not required/withdrawn |
| Visibility | unrestricted/restricted |
| Policy dynamics | static/revoked/changed |
| Attacker knowledge | black/grey/white box |
| Workflow | linear/branching/multi-agent |

Every scenario should contain machine-readable ground truth for:

- expected influencing principals;
- expected authority decision;
- expected visibility;
- expected consent result;
- expected final execution decision.

Crucially, the oracle must not simply call the Conflux implementation under test.

---

# 35. Paired benign/adversarial scenarios

Every attack scenario should have a closely matched benign counterpart.

Example:

Benign:
Alice asks the agent to read Alice's document and email a summary.

Adversarial:
Alice asks the agent to read Bob's document; Bob-controlled content induces an unauthorised email action.

Paired designs control for task difficulty.

This lets the project distinguish:

**security improvement** from **general task degradation**.

---

# 36. Counterfactual scenarios

Create scenario pairs differing in exactly one variable:

- principal authorised ↔ unauthorised;
- provenance retained ↔ dropped;
- consent present ↔ absent;
- policy valid ↔ revoked;
- malicious source influential ↔ irrelevant;
- recipient permitted ↔ prohibited.

These provide unusually clean causal evidence about which part of the mechanism changes the result.

---

# 37. AgentDojo: primary external benchmark

AgentDojo should remain the highest-priority external benchmark.

It contains 97 realistic tasks and 629 security test cases spanning environments such as email, e-banking and travel, and was designed specifically for prompt-injection attacks and defences in tool-using agents.

The current Conflux manuscript already has a pinned AgentDojo translation boundary, making completion of this evaluation especially high-value.

Run, on the largest semantically valid common subset:

| Defence |
|---|
| no defence |
| defensive prompt |
| requester-only |
| Conflux |
| official/reproduced AgentDojo defence where feasible |
| CaMeL if practical |
| Fides if practical |

Report separately:

benign task success, attack success, secure task success, false-block rate, unsupported tasks and translation failures.

Never silently remove unsupported tasks from the denominator.

---

# 38. InjecAgent: attack-diversity benchmark

InjecAgent contains 1,054 test cases across 17 user tools and 62 attacker tools and focuses specifically on indirect prompt injection, including direct harm and private-data exfiltration.

It is useful for testing whether Conflux generalises across a wider variety of tool-mediated injections.

Priority: medium-high.

It is less important than AgentDojo because Conflux already has an AgentDojo boundary, but its attack diversity is valuable.

---

# 39. Agent Security Bench

ASB is broader: 10 scenarios, more than 400 tools, multiple prompt-injection attacks, memory poisoning, Plan-of-Thought backdoors, mixed attacks, 11 defences and 13 LLM backbones. It explicitly considers the security/utility trade-off.

Do not necessarily port the entire benchmark.

Select attack families that probe genuinely different Conflux assumptions:

- prompt injection;
- memory poisoning;
- mixed attacks;
- planning manipulation.

Priority: medium.

---

# 40. AgentHazard

The 2026 AgentHazard benchmark contains 2,653 instances designed around harmful behaviour emerging through sequences of individually plausible actions.

This is interesting for Conflux's pointwise/action-time reasoning because a globally problematic workflow may consist of locally ordinary actions.

However, its threat model is not identical to authority confusion.

Priority: stretch.

---

# 41. AgentHarm

AgentHarm focuses on explicitly malicious multi-step requests and jailbreaks, with 110 base tasks and 440 augmented tasks across 11 harm categories.

This tests model misuse/alignment more than Principal Context.

It is useful mainly as a negative conceptual comparison:

> Conflux enforces authority, not moral harmlessness.

Priority: low.

A properly authorised principal could request something dangerous under the organisational policy. Conversely, an innocuous-looking action could be unauthorised.

That distinction should be explicit in the dissertation.

---

# 42. Avoid benchmark tourism

Do not integrate benchmarks simply because they exist.

The benchmark priority should be:

| Priority | Benchmark/comparison | Reason |
|---|---|---|
| P0 | Internal PC benchmark | directly tests novelty |
| P0 | AgentDojo | external validity + existing adapter |
| P0 | requester-only baseline | isolates central contribution |
| P0 | Fides conceptual/direct comparison | closest current architecture |
| P1 | CaMeL | strong architectural baseline |
| P1 | InjecAgent | attack diversity |
| P1 | ASB subset | memory/planning/mixed attacks |
| P2 | AgentHazard | sequential safety |
| P3 | AgentHarm | different threat model |
| P3 | general agent benchmarks | limited security relevance |

Three deeply analysed benchmarks are better than eight superficial integrations.

---

# 43. Cross-model experiments

For end-to-end LLM experiments, use multiple model classes if budget permits.

The important comparison is not which LLM wins.

It is whether architectural security remains stable when the model changes.

Measure the same scenarios with:

- a strong frontier model;
- a cheaper/smaller model;
- an open-weight model where practical.

Prompt-based defences should be expected to vary with model behaviour. Architectural enforcement should ideally show much lower security variance.

This would support the claim that Conflux reduces reliance on model obedience.

---

# 44. Temperature and nondeterminism

For stochastic model experiments, repeat trials.

Record:

- model identifier/version;
- provider;
- date;
- temperature;
- system prompt hash;
- tool specification hash;
- scenario hash;
- Conflux commit;
- benchmark commit.

Do not report one successful run as a result.

For expensive tests, prioritise more independent scenarios over repeatedly sampling one scenario.

---

# 45. Security–utility frontier

Every defence should be evaluated on both axes.

Security metrics:

- attack success rate;
- unauthorised-action rate;
- data-exfiltration rate;
- policy-violation rate;
- severity-weighted violation rate.

Utility metrics:

- benign task completion;
- false-block rate;
- tool-task completion;
- legitimate plan completion.

System metrics:

- latency;
- policy-check count;
- memory;
- model calls/tokens;
- verification overhead.

The dissertation should contain a security–utility plot rather than reporting attack success in isolation.

---

# 46. Distinguish four outcomes

For every attempted action, classify:

| Ground truth | System | Outcome |
|---|---|---|
| authorised | permit | true allow |
| authorised | block | false deny |
| unauthorised | block | true deny |
| unauthorised | permit | false allow |

Security systems often hide poor utility behind high denial rates.

Conflux should report the complete confusion matrix.

---

# 47. Statistical methodology

Most comparisons will be paired because identical scenarios can run under different defences.

Prefer:

- raw counts;
- proportions;
- confidence intervals;
- paired effect sizes.

For binary paired outcomes, McNemar-style comparisons are appropriate.

For attack-success proportions, report confidence intervals rather than only percentages.

For performance distributions, report median and tail latency rather than only mean.

Bootstrap at the **scenario level**, not over repeated samples from the same scenario, where appropriate.

If many variants are compared statistically, control multiple-comparison inflation or explicitly label exploratory analysis.

Do not turn the dissertation into a collection of p-values. Effect size and failure analysis matter more.

---

# 48. Performance microbenchmarks

Benchmark security mechanisms independently of LLM latency.

Vary:

- number of principals;
- policy count;
- resource count;
- provenance nodes;
- provenance depth;
- action arguments;
- plan length.

Measure:

- PC construction time;
- policy evaluation time;
- provenance propagation;
- serialisation;
- plan verification;
- SLED verification;
- total mediation overhead.

Report p50/p95/p99 where repeated measurements are meaningful.

---

# 49. Macrobenchmarks

Then measure end-to-end workflows.

Examples:

email assistant, document summarisation/sharing, calendar workflow, travel booking, finance/procurement simulation and coding-agent workflow.

Measure total completion time with and without Conflux.

This separates:

> "security kernel adds 300 µs"

from:

> "end-to-end workflow becomes 4% slower."

Both are useful, but they answer different questions.

---

# 50. Complexity experiments

Empirically estimate scaling against:

\[
|PC|,\quad |Policy|,\quad |Plan|,\quad |ProvenanceGraph|.
\]

Fit simple expected complexity curves only where theoretically justified.

The dissertation should explain expected asymptotic behaviour and then show measured scaling.

That gives more theoretical substance than a benchmark table alone.

---

# 51. Verification state-space explosion

Bounded verification should be evaluated honestly.

Measure how SLED scales with:

principal count, trace length, branching factor and policy complexity.

Identify the practical boundary where exhaustive verification becomes infeasible.

A negative scaling result is valuable because it defines where runtime enforcement rather than exhaustive verification is required.

---

# 52. Availability and failure-mode benchmark

Security is not only confidentiality/authority.

Stress:

- policy server down;
- model unavailable;
- malformed model output;
- tool timeout;
- corrupted result;
- partial plan;
- repeated retries;
- invalid cache;
- unavailable optional solver.

Measure secure failures, crashes and recovery.

This is especially relevant because Conflux explicitly advertises fail-closed behaviour.

---

# 53. Determinism and replay

Run deterministic experiments repeatedly on:

- same machine;
- fresh process;
- clean checkout;
- Linux CI;
- another supported OS if practical.

The same inputs should produce semantically identical results.

Every counterexample should be replayable from its retained trace.

This turns reproducibility itself into measured engineering evidence.

---

# 54. Clean-machine reproduction

Before submission, perform a clean-room reproduction:

fresh clone → documented installation → validation → selected experiments → generated tables → manuscript.

Ideally a single documented command sequence should reproduce the central results.

The current repository is already oriented toward schema-checked results and retained evidence, so completing this path has unusually high value.

---

# 55. Test-suite evidence

Report more than test count.

Useful measures include:

- statement/branch coverage of security-critical modules;
- mutation score;
- number of property-based cases;
- exhaustive states explored;
- regression tests mapped to invariants;
- historical bugs now caught by tests.

The strongest metric is probably **security mutant kill rate**, not raw line coverage.

---

# 56. Fault injection

Deliberately introduce faults at boundaries:

policy backend, planner, serialiser, benchmark adapter, solver and runtime provider.

Verify that faults do not convert an unknown/error state into permit.

This is particularly well suited to automation by an AI coding agent.

---

# 57. Benchmark-adapter fidelity

External benchmark adapters are dangerous because translation bugs can produce apparently excellent results.

For each adapter:

1. select a manually audited sample;
2. compare source benchmark state with translated Conflux state;
3. compare actions/resources/recipients;
4. verify attack payload preservation;
5. verify ground-truth outcome;
6. verify no Conflux-specific information leaks into the agent.

Report adapter failures separately.

The repository already states that benchmark-specific behaviour must not enter the domain or ITES and that evaluation must not encode shortcuts.

Make that invariant empirically auditable.

---

# 58. Holdout challenge set

Do not develop exclusively against visible benchmark cases.

Create a small challenge set that is frozen before final tuning.

Ideally it includes manually designed adversarial cases not seen during implementation.

Run it only at milestones.

This provides some evidence against overfitting the implementation to the test suite.

---

# 59. Negative-results register

The AI coder should actively seek cases where Conflux performs badly.

Examples might include:

- excessive provenance causing false denial;
- attacker-induced principal flooding;
- policy complexity;
- unsupported delegation patterns;
- legitimate multi-principal collaboration becoming impossible;
- provenance ambiguity;
- expensive verification;
- tasks where Fides/CaMeL are more expressive.

Do not "fix" every negative result.

Some should become limitations.

A dissertation that accurately maps the mechanism's boundary is stronger than one that claims universal superiority.

---

# 60. Failure taxonomy

Every unsuccessful end-to-end task should be classified as:

`model failure / planner failure / policy denial / provenance overapproximation / benchmark translation / tool failure / authentication failure / unsupported semantics / timeout / genuine attack success`.

Without this taxonomy, a headline success rate is hard to interpret.

The coding agent should generate this automatically from structured traces wherever possible.

---

# 61. Case studies

Alongside aggregate statistics, retain approximately three detailed case studies.

A good set would be:

### Case study A: confused deputy

Requester possesses permission; malicious content owner does not.

Shows the core Principal Context idea.

### Case study B: dynamic revocation

Plan is initially legitimate; authority changes before execution.

Shows pointwise/action-time checking.

### Case study C: deep provenance

Malicious influence travels through several transformations/sub-agents before reaching an action.

Shows compositional provenance.

Each should include the provenance graph, policy state, attempted action and final decision.

---

# 62. Engineering contribution that is still worth adding

The highest-value engineering additions are now experiment infrastructure rather than user-facing features.

Useful additions include:

| Component | Value |
|---|---|
| unified experiment runner | very high |
| parameter-grid execution | high |
| checkpoint/resume | high |
| cost limits | high |
| deterministic replay | very high |
| automatic manifests | very high |
| automatic statistical summaries | high |
| automatic LaTeX tables | very high |
| automatic figures | high |
| benchmark adapters | high |
| property generators | very high |
| mutation-testing harness | high |
| failure classifier | high |
| clean-reproduction script | very high |

The principle should be that raw result → summary → dissertation table is automated.

Manual transcription of numbers should be eliminated.

---

# 63. Evidence lineage

Every number appearing in the dissertation should ideally have the chain:

\[
\text{paper claim}
\rightarrow
\text{figure/table}
\rightarrow
\text{generated summary}
\rightarrow
\text{result JSON}
\rightarrow
\text{raw trace}
\rightarrow
\text{manifest}
\rightarrow
\text{source commit}.
\]

The current repository is already close to this philosophy.

Completing it would be a meaningful engineering contribution in itself.

---

# 64. Recommended P0 experiment package

If only one group of experiments were completed, it should be this.

| Experiment | Variants |
|---|---|
| Core ablation | unprotected / prompt / requester-only / PC |
| Provenance | none / direct / transitive |
| Timing | request / plan / action |
| PC scaling | 1–128+ principals |
| Provenance topology | chain / star / DAG |
| Utility | paired benign/adversarial tasks |
| Formal | exhaustive small-world invariants |
| Verification | deliberately broken variants → counterexamples |
| External | AgentDojo |
| Related architecture | Fides/CaMeL analysis and at least one practical comparison |
| Engineering | mutation testing |
| Reproducibility | clean rerun |

If these are done well, the project has a coherent core evaluation.

---

# 65. Recommended P1 package

After P0:

| Experiment |
|---|
| consent/visibility/read ablations |
| policy revocation/TOCTOU |
| plan tampering |
| provenance laundering |
| adaptive white-box attacker |
| colluding principals |
| taint/principal flooding |
| Cedar/native differential testing |
| cross-model evaluation |
| InjecAgent |
| selected ASB attacks |
| detailed performance scaling |
| fault injection |

---

# 66. P2/stretch work

Only after the core evidence is secure:

| Work |
|---|
| AgentHazard |
| AgentHarm |
| broad multi-agent environments |
| sophisticated delegation |
| provenance compression schemes |
| formal proof mechanisation |
| OS/computer-use environments |
| additional provider integrations |
| entirely new policy languages |

These could consume large amounts of time while adding relatively little evidence to the central thesis.

---

# 67. Eight-week programme

Assuming roughly two hours of coding-agent access per day, there is enough time for a substantial campaign, but only if work is ordered by dependency.

| Week | Main objective | Expected output |
|---|---|---|
| 1 | Experimental infrastructure audit | claim matrix, metrics, runner, manifests, oracles |
| 2 | Internal benchmark + core ablations | first major security/utility tables |
| 3 | Provenance + PC scaling | topology, depth, principal-count results |
| 4 | Formal/verification programme | properties, exhaustive worlds, mutants, counterexamples |
| 5 | AgentDojo | recognised external result |
| 6 | Fides/CaMeL + secondary benchmark | related-work comparison |
| 7 | adaptive attacks + fault injection | robustness/limitations |
| 8 | reproduction and freeze | clean artefact, final figures, no new features |

Weeks should not be treated as rigid. The critical dependency is:

\[
\text{oracle}
\rightarrow
\text{runner}
\rightarrow
\text{internal experiments}
\rightarrow
\text{external experiments}
\rightarrow
\text{final analysis}.
\]

---

# 68. Daily AI-coder task format

Every coding session should receive a decision-complete task.

The prompt should specify:

**Research question:** What uncertainty are we reducing?

**Hypothesis:** What result is expected and why?

**Independent variables:** What changes?

**Dependent variables:** What gets measured?

**Controls:** What remains constant?

**Oracle:** How is correctness determined independently?

**Required implementation:** Smallest code change necessary.

**Required tests:** What must pass?

**Required artefacts:** Raw trace, result, manifest, summary.

**Acceptance criteria:** Exact definition of completion.

**Stop conditions:** Conditions under which the agent should stop rather than invent new architecture.

**Prohibited scope:** Explicitly state what not to refactor/add.

The repository already instructs AI contributors to inspect architecture, write a decision-complete specification, implement the smallest coherent change, validate, update canonical documentation and review the diff.

Use that discipline for experiments too.

---

# 69. AI-coder definition of done

A task is not complete because code was written.

For experimental work, "done" means:

`implementation + tests + validation + run + raw result + manifest + summary + interpretation hook`.

For theoretical work:

`definition + property + proof/counterexample + executable validation where possible`.

For benchmark work:

`adapter + fidelity tests + pinned version + run + exclusions + results`.

For performance work:

`benchmark + warmup/methodology + raw timings + statistical summary + plot`.

This prevents the coding agent from repeatedly leaving 90%-complete work.

---

# 70. Anti-scope-creep rules

For the remaining period:

Do not add a new subsystem because it is interesting.

Do not refactor stable code unless an experiment exposes a concrete problem.

Do not implement another policy backend unless it creates a meaningful comparison.

Do not integrate a benchmark without specifying which research question it answers.

Do not add a metric without explaining what construct it measures.

Do not improve an attack after seeing results without retaining the original attack and recording the adaptation.

Do not silently change benchmark semantics.

Do not optimise performance until correctness measurements exist.

Do not write strong manuscript claims before the evidence gate passes.

This is where AI coding agents most often waste project time: locally reasonable improvements accumulate without increasing the strength of the dissertation.

---

# 71. What would constitute sufficient engineering depth?

There is no way to guarantee what an examiner will consider sufficient, and the previous 64% Part B result is a reason to avoid assuming that sheer implementation size will carry the project.

For Conflux, however, I would not treat "more application features" as the best route to greater engineering depth.

A stronger engineering package is:

\[
\text{reference monitor}
+
\text{policy integration}
+
\text{provenance runtime}
+
\text{authenticated planning}
+
\text{verification}
+
\text{benchmark adapters}
+
\text{experiment framework}
+
\text{reproducible artefacts}
+
\text{security testing}.
\]

The repository already contains much of the first half.

The remaining engineering should make the second half unusually rigorous.

---

# 72. What would constitute sufficient theoretical depth?

The best theoretical programme is not to invent more notation.

It is to connect the formal model directly to the implemented system.

Aim for:

1. precise definition of influence/provenance;
2. precise Principal Context semantics;
3. formal authorisation predicate;
4. authority-safety theorem;
5. monotonicity results;
6. provenance-composition properties;
7. action-time revocation result;
8. counterexamples for weaker semantics;
9. bounded automated verification;
10. explicit assumptions and limits.

The combination of theorem + executable model + implementation + ablation is much stronger than any one individually.

For example:

> Theorem says requester-only authority is unsound under multi-principal influence.

Then:

> SLED finds a minimal counterexample.

Then:

> the deterministic benchmark reproduces it.

Then:

> AgentDojo demonstrates the same class of issue in a realistic workflow.

That is extremely high evidence density.

---

# 73. The highest-value possible result

The strongest outcome would not be:

> Conflux blocked 100% of our attacks.

It would be something closer to:

> Across controlled multi-principal scenarios, requester-only and prompt-based architectures permitted authority-confusion attacks, while Principal Context prevented them under the stated provenance assumptions. Component ablations identify transitive provenance and action-time complete mediation as necessary mechanisms. The result persists across models and an external agent benchmark, while benign utility remains competitive. Exhaustive bounded verification independently establishes the core invariants for small systems, and performance experiments show that runtime enforcement remains practical over the tested range.

Every clause in that paragraph corresponds to an experiment or proof proposed above.

That is what the remaining work should build toward.

---

# 74. Minimum final figure/table set

The dissertation should ideally end up with approximately the following evidence surfaces:

| Figure/table | Content |
|---|---|
| Fig. 1 | architecture and security boundary |
| Fig. 2 | motivating authority-confusion trace |
| Table 1 | formal comparison with requester ACL / capabilities / CaMeL / Fides |
| Table 2 | core ablation results |
| Fig. 3 | security–utility frontier |
| Fig. 4 | attack success by provenance depth |
| Fig. 5 | principal-count scaling |
| Fig. 6 | runtime overhead scaling |
| Table 3 | AgentDojo results |
| Table 4 | provenance laundering/adaptive attacks |
| Table 5 | verification properties/counterexamples |
| Fig. 7 | SLED state-space scaling |
| Table 6 | mutation/fault-injection results |
| Table 7 | limitations/negative-result taxonomy |

The appendix can contain the much larger matrices.

The main dissertation should tell a story rather than dump experiments.

---

# 75. Priority score for AI-coder work

When choosing between tasks, score each approximately as:

\[
Priority =
\frac{
ClaimImportance
\times
UncertaintyReduction
\times
EvidenceQuality
}{
ImplementationTime
\times
FailureRisk
}.
\]

This naturally favours things such as requester-only ablation, metamorphic tests and AgentDojo completion over adding another provider integration.

A task that produces a publishable graph in four hours is generally more valuable now than a technically impressive subsystem requiring four days.

---

# 76. Immediate next actions

The first implementation sprint should be a **research-infrastructure sprint**, not another security feature.

The AI coding agent should first audit the current claim ledger, task registry, experiment definitions, result schemas and manuscript placeholders and produce a mapping from every current claim to existing evidence.

It should then identify claims that are currently implementation-only, historical-only or unsupported.

After that, implement the smallest unified configuration mechanism required to express the core ablations without maintaining forks of Conflux.

Next, construct the deterministic paired Principal Context benchmark and independent oracle.

Then run:

**unprotected → prompt-only → requester-only → direct provenance → canonical PC.**

Only once those results are trustworthy should the project branch into AgentDojo, Fides/CaMeL, cross-model experiments and broader attack suites.

---

# 77. Final recommendation

The remaining two months should be treated approximately as:

**35% core experiments and ablations**

**20% external benchmarks/comparisons**

**15% formal analysis and verification**

**10% adversarial/failure testing**

**10% reproducibility and experiment infrastructure**

**10% buffer, debugging and genuinely necessary implementation**

The central risk is no longer that Conflux contains too little code. The repository already has a fairly broad research-system architecture.

The larger risk is producing a dissertation in which an examiner sees substantial engineering but has to take too many claims on trust.

The best use of the remaining AI-coder budget is therefore to make Conflux **difficult to disbelieve**.

Every major design choice should acquire either a theorem, a distinguishing counterexample, an ablation, an external comparison, a stress test, or preferably several of these.

The most important sequence is:

**formalise the claim → construct the weakest plausible alternative → find a distinguishing case → automate a larger benchmark → measure security and utility → stress the assumptions → reproduce externally.**

If that programme is executed well, the final project will contain substantially more than "an AI-agent framework plus some benchmarks." It will contain a formal security proposal, an implementation, controlled causal evidence for its design decisions, adversarial evaluation, comparison with contemporary systems such as Fides and CaMeL, recognised external benchmarking, bounded verification, systems-performance analysis and a reproducible research artefact. That is the level of evidence density the remaining development effort should target.