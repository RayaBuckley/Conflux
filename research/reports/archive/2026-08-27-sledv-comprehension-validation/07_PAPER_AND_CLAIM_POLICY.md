# Paper and Claim Policy During Verification Validation

## Objective

Keep the FLMSec/workshop paper defensible while SLED-V understanding and comparative-model validation mature.

## Claims safe to foreground now

Subject to retained evidence and exact repository status:

- Principal Context / ITES semantics and their stated assumptions.
- Historical SLED result reproduction.
- Native SLED's finite-state/counterexample machinery.
- Deliberately defective ITES variants detected by the verifier.
- Agreement between independent verification paths on explicitly supported finite fixtures.
- Solver-facing IR as an engineering/research mechanism.
- Boundedness and explicit `UNKNOWN` behaviour.

## Claims to qualify

### SLED-V
Preferred:
> “SLED-V extends SLED toward explicit finite-state and solver-backed verification. Current evidence validates the machinery on finite Conflux fixtures and negative controls.”

Avoid:
> “SLED-V formally proves Conflux secure.”

### External defences
Until validation:
> “We use preliminary finite abstractions inspired by contemporary defences as verifier-development fixtures; they are not yet implementation-conformance evidence.”

Do not put their PE verdicts in the abstract or headline results.

## Manuscript methodology addition

Add a subsection distinguishing:

1. **checker validity** — whether SLED-V correctly evaluates its input model;
2. **model fidelity** — whether that input model represents the intended defence;
3. **implementation conformance** — whether executable software follows the model.

Explain evidence used for each.

## Result hierarchy

Recommended order:

1. historical SLED reproduction / continuity;
2. native state-based checking and minimal witnesses;
3. mutation/negative-control validation;
4. independent backend agreement;
5. only validated external-defence comparison;
6. exploratory external abstractions in appendix if still unvalidated.

## Why this is stronger

A smaller set of claims with clear evidence boundaries is more credible than a broad table of formal-looking results whose model assumptions have not been independently checked.
