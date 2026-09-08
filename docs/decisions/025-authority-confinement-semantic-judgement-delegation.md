# ADR-025: Authority confinement, semantic judgement, and explicit scoped delegation

- Type: adr
- Status: accepted
- Date: 2026-09-07
- Owners: Conflux maintainers

## Context

Conflux has historically emphasised a worst-case model assumption: Principal Context and ITES should prevent privilege escalation even if model proposals are arbitrary. Earlier project framing sometimes treated model-level prompt-injection defences primarily as utility mechanisms because they cannot provide the same worst-case guarantee.

That framing is too strong. Real organisations routinely allow human employees to process untrusted information and then exercise privileged actions. The machine-readable access-control system often grants a coarse authority envelope, while the human resolves semantic conditions — for example whether an email is legitimate or a request satisfies policy — that are not fully represented in the ACS. Training employees to detect phishing improves security even though it does not prove that every decision is correct. Defended AI agents can occupy a similar semantic decision role.

The repository also needs clearer semantics for delegation. General authority transfer is unnecessarily broad for many agent workflows. A principal may instead explicitly delegate a bounded set of actions/effects for a particular execution. Planning can represent and minimise this set, but plan generation must not itself create authority.

Finally, prior documentation discussed endorsement/trusted transformations as a possible mechanism for reducing conservative influence. Endorsement is not part of the current intended Conflux design and should not remain a planned mechanism.

## Decision

### 1. Separate authority confinement from semantic judgement

Conflux distinguishes:

- **authority confinement**: whether an execution can perform a machine-enforceable effect outside the authority available to all influencing principals;
- **semantic judgement**: whether a choice inside available authority is appropriate for the actual task/context;
- **policy adequacy**: how completely the machine-readable policy captures the organisation's intended conditions.

ITES provides the first type of guarantee under its stated assumptions. It does not guarantee the second or solve the third completely.

### 2. Model-level defences are security-relevant but empirically assured

Model-level prompt-injection defences, classifiers, instruction hierarchy, fine-tuning and related controls may reduce the probability of malicious or inappropriate decisions. They are therefore security controls, not merely utility controls.

They remain outside the hard Conflux authority TCB: model/planner/classifier outputs cannot grant authority, assert trusted provenance, or narrow Principal Context.

A deployment may nevertheless rely on a model probabilistically for semantic judgement within already available authority.

### 3. Humans and AI may both be semantic decision-makers

Human judgement does not receive a formal privilege in the Conflux model merely because it is human. Organisations may choose a human, an AI with model-level defences, a combination of both, or refusal for semantic decisions that cannot be structurally encoded.

### 4. Distinguish explicit and effective machine authority

Let `ACS_explicit` denote the organisation's persistent machine-readable authority relation/PDP state.

Let `D_e` denote all valid explicit scoped delegation grants applicable to execution `e`.

Let `ACS_effective(e)` denote the machine authority relation ITES evaluates for `e` after combining `ACS_explicit` with `D_e`.

Conceptually:

```text
ACS_effective(e, p, a) = ACS_explicit(p, a) OR DelegatedAllow(D_e, p, a)
```

where delegation matching includes beneficiary, issuer, resource, argument, lifetime, use-count, revocation and any other configured constraints.

ITES continues to require a known non-empty Principal Context and pointwise authorisation for every influencing Principal under the applicable effective relation.

### 5. Delegation is explicit authority transfer, never provenance removal

A delegated principal remains in Principal Context. The action becomes authorised only because the effective authority relation contains a valid explicit grant.

Creating delegation is itself an authority-sensitive operation. Permission to perform an action does not automatically imply permission to delegate it.

The preferred unit is a finite or predicate-defined **delegated choice set** rather than broad ambient role transfer.

### 6. Planning is not an authority source

Planner output remains untrusted structured data.

Planning may represent/minimise a delegation already explicitly expressed by an authorised principal and may construct the exact scoped grant for authentication/confirmation. It may not create authority merely because a task or candidate plan requires it.

`RequiredAuthority(plan)` is diagnostic/planning information, not authorisation.

### 7. Authority envelope

The **authority envelope** of execution `e` is the set of machine-enforceable effects that can pass the Principal-Context authority checks under `ACS_effective(e)` and the trusted operation/argument authority schema.

Conflux guarantees confinement to this represented envelope under its assumptions. It does not guarantee that a human/model chooses the semantically best member of the envelope.

### 8. Endorsement is not a current Conflux mechanism

Current Conflux execution does not narrow Principal Context based on model/classifier judgement. The project does not currently plan an endorsement/trusted-endorsement mechanism.

Classical endorsement may remain discussed in related work. Any future mechanism that reduces conservative provenance/Principal Context requires a separate accepted design and proof obligation.

### 9. SLED/SLED-V scope

SLED/SLED-V remains a verifier/evaluator for system-level properties. Empirical prompt-injection resistance and semantic decision quality are evaluated through model/agent benchmarks and must be reported as a different evidence class.

## Consequences

- Existing statements that model-level defences only affect utility must be revised.
- "Arbitrary model behaviour" remains the threat model for the authority-confinement theorem, not a claim that model robustness has no operational security value.
- Documentation must distinguish `ACS_explicit` from `ACS_effective(e)` where delegation is discussed.
- Scoped delegation can support ephemeral agents/workflows without transferring ambient sponsor credentials or globally rewriting organisational policy.
- The maximal-permissiveness theorem remains relative to the stated PE definition and fixed represented authority relation.
- ADR-024's forward-looking endorsement/trusted-transformation direction is superseded by this ADR; its external-provenance, no-laundering, authority-vs-harm and authentication decisions remain active.
- Runtime delegation remains disabled until separately activated with implementation and evidence.

## Validation

- Repository-wide semantic grep finds no current statement that model-level defences are merely utility.
- Normative docs agree on `ACS_explicit`, `ACS_effective`, Principal Context and authority-envelope terms.
- Planning docs continue to state that planner output cannot grant authority.
- No current Conflux roadmap presents endorsement as a planned mechanism.
- Claims/status do not promote delegation activation.
- Current publications use the revised security-assurance distinction.
