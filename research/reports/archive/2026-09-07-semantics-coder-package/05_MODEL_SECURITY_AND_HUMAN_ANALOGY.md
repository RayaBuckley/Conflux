# Model-level security and the human analogy

## 1. Correct the old framing

The old simplifying story was approximately:

```text
model-level defences -> utility only
ITES -> security
```

This is no longer the intended project position.

Correct story:

```text
model-level/human semantic controls -> genuine risk reduction, empirical assurance
Conflux/ITES authority controls      -> deterministic/system-level confinement under stated assumptions
```

They defend different failure modes and should normally be combined.

## 2. Why model-level defences count as security

If a prompt-injection defence makes an AI less likely to follow a malicious email and thereby prevents an inappropriate authorised refund, disclosure, or destructive operation, it has improved security.

The absence of a formal guarantee does not make a control "not security". Organisations already rely on probabilistic controls:

- phishing training;
- employee judgement;
- fraud detection;
- behavioural monitoring;
- anomaly detection;
- human approval.

The relevant distinction is **assurance strength and property**, not "security versus non-security".

## 3. Humans expose the same semantic boundary

Suppose an employee can:

- read arbitrary customer email;
- refund orders;
- reset accounts;
- send internal messages.

The explicit access-control system often says the employee may perform these actions. It does not fully encode whether a particular email is legitimate, deceptive, exceptional, or policy-compliant. The employee's judgement resolves those conditions.

A phishing email can manipulate the human into misusing authority that the ACS genuinely grants. Training mitigates the risk but cannot guarantee prevention.

An AI agent in the same role faces the same structural issue. If the organisation wants the agent to inspect arbitrary untrusted semantic content and then make a privileged decision, some decision-maker must be trusted for semantic correctness. The model can fill that role with empirical defences, just as the human does.

## 4. What Conflux still guarantees

Conflux can make the consequences of a semantic failure smaller by limiting the available authority.

Example:

```text
Delegated choice set:
  refund order 17 up to £42
  resend order 17
  escalate order 17
```

A malicious email may still influence the model to choose `refund` incorrectly. ITES cannot prove that refund was the *right* choice if all choices are deliberately authorised. But Conflux can guarantee (under its assumptions) that the model cannot turn that influence into `delete_database` or refund a different order outside the scope.

This is a defence-in-depth story, not a competition between layers.

## 5. Machine-readable policy versus intended organisational policy

Avoid saying that humans "modify the ACS" whenever they interpret a request. Usually they do not.

Use:

> The explicit ACS captures machine-enforceable authority. Human/model semantic judgement resolves additional organisational conditions that may not be represented in that ACS.

For formal work, the theorem can continue to assume its represented authority source is correct for the property being proved. For deployment discussion, explain that the represented relation can be coarser than actual organisational intent.

## 6. Recommended wording bank

### Good

> Model-level prompt-injection defences are complementary security controls. They reduce the probability that malicious inputs cause inappropriate decisions, while Conflux bounds the machine-enforceable authority available to those decisions independently of model behaviour.

> Humans and models can both be semantic decision-makers. Neither role automatically carries a formal correctness guarantee.

> The LLM is not trusted to grant authority or narrow Principal Context, even when the deployment relies on it for semantic judgement within already authorised actions.

> ITES's worst-case model assumption is a proof technique/property boundary, not a claim that model robustness has zero operational security value.

### Bad

> Model-level defences only improve utility.

> The LLM is irrelevant to security.

> If the model is compromised, the system is secure.  
(Too broad; only the authority-confinement property is intended.)

> The ACS always captures exactly what the organisation intends.

> Every task blocked by ITES proves that the ACS is wrong.

> A classifier can mark an input benign and remove its author from Principal Context.
