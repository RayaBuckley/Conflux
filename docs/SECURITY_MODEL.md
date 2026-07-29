# Security Model

## Trusted computing base

| Component | Trusted responsibility |
|---|---|
| Provenance adapters | Attach complete, authenticated origins; unknown input is labelled unknown |
| ITES kernel | Preserve context, isolate branches, compose decisions, and issue certificates |
| Policy ports | Return faithful pointwise authorisation, read, visibility, and consent decisions |
| Action schemas | Describe the exact operation and resource being decided |
| Executor | Execute only the action matching an authorising certificate |

The model and optional classifiers are not trusted to grant authority, assert
decision provenance, or narrow Principal Context.

## Normative rules

- Empty or unknown Principal Context denies observable, nested, delegation, and
  effectful actions.
- Every Principal in the context must receive a pointwise policy allow.
- Provenance describes influence. Read policy describes observation rights.
- Missing consent denies; internal stop and no-op are the only exceptions.
- Delegation is denied until an attenuating capability model is implemented.
- Policy exceptions, category mismatches, unsupported inputs, stale
  certificates, and provider errors fail closed.
- Rejected proposals are diagnostics, not executed security violations.

The current whole-action context is conservative. Role-sensitive argument
provenance is tracked as future work in [Change Catalogue](CHANGE_CATALOG.md).
