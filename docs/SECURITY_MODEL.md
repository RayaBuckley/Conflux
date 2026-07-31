# Security Model

## Trusted computing base

| Component | Trusted responsibility |
|---|---|
| Authentication and provenance adapters | Attach complete origins; label uncertainty as unknown |
| ITES kernel | Preserve context, isolate branches, compose decisions, and issue certificates |
| Policy ports | Return faithful authorisation, read, visibility, and consent decisions |
| Action schemas | Identify the exact operation and protected resource |
| Application service and executor | Recheck and execute only the certificate-matching action |

Models, planners, optional classifiers, and benchmark data are not trusted to
grant authority, assert decision provenance, or narrow Principal Context.

## Decision pipeline

```text
authenticated inputs -> provenance -> conservative Principal Context
  -> read + authorisation + visibility + consent decisions
  -> exact decision certificate -> selected executor -> outcome evidence
```

The four policy decisions remain independently visible. Only their conjunction
can permit an observable or effectful action, and execution evaluates current
policy state again.

## Normative rules

- Empty or unknown Principal Context denies observable, nested, delegation,
  and effectful actions.
- Every Principal in the context must receive a pointwise policy allow.
- Provenance describes influence; read policy decides observation.
- Missing consent denies. Only internal stop and no-op can omit consent.
- Delegation is denied until scoped, attenuating capabilities are implemented.
- Policy errors, unsupported inputs, category mismatches, stale certificates,
  provider failures, and exhausted bounds remain explicit fail-closed outcomes.
- Rejected proposals are diagnostics, not executed security violations.
- Provenance and Principal Context accumulate monotonically through nesting;
  alternative siblings remain isolated.

The current whole-action context is conservative. Role-sensitive argument
effects remain future work in the [change catalogue](CHANGE_CATALOG.md).

## Rationale

| Rule | Why |
|---|---|
| Require a non-empty known context | Universal checks over an empty set otherwise grant vacuous authority |
| Require every influencing Principal to be allowed | One Principal cannot lend permissions to another |
| Separate provenance and read policy | Origin does not imply permission to observe |
| Keep consent restrictive only | Approval cannot substitute for organisational authority |
| Bind certificates to exact decisions | Stale or branch-mismatched approval cannot authorise another effect |
| Deny unsupported delegation | Safe delegation requires attenuation, scope, and revocation |
| Fail closed on errors | Infrastructure uncertainty is not evidence of permission |

These rules prevent authority amplification; they do not prove that every
authorised action matches subjective intent. Complete mediation and correct
authentication, provenance, policy, runtime, and provider isolation remain
assumptions. See [SECURITY.md](../SECURITY.md) for the operational boundary.
