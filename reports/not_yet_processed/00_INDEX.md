# Conflux Fourth-Year Direction Package

This package is a review map for the current project directions discussed so far. Each file expands one direction into analysis, rationale, constraints, and a practical next step.

Source basis: the current project repository audit, the 3rd-year ITES/SLED report, the later literature review, and the current discussion about planning, delegation, policy semantics, visibility, attribution, and evaluation.

## Files

- `01_planning_optimisation.md` — How planning can improve utility without weakening authority checks; includes plan-space optimisation, authority-minimising planning, and controlled replanning.
- `02_delegation_and_consent.md` — Why delegation should be explicit and scoped, how it differs from consent, and how to model delegation as an auditable authority transfer.
- `03_fine_grained_policy_languages_tool_arguments.md` — Why policy checks should operate over tool arguments and semantic roles rather than just whole actions.
- `04_visibility_tracking_confidentiality.md` — How visibility tracking can support stronger confidentiality analysis than read-access checks alone.
- `05_attribution_tracking_reporting.md` — How attribution through LLMs can explain which principals influenced which actions and how to report that safely.
- `06_sled_optimisation_and_symbolic_verification.md` — How to reduce native SLED state explosion and how symbolic verification could be layered on top of a restricted transition model.
- `07_benchmarks_and_real_world_policy_integration.md` — How to turn the defence into real results using benchmarks and one policy-language integration.
- `08_repository_structure_and_agent_governance.md` — How to keep the codebase understandable, prevent AI-generated bloat, and make the project easier to supervise and extend.

## Recommended reading order

1. `01_planning_optimisation.md`
2. `02_delegation_and_consent.md`
3. `03_fine_grained_policy_languages_tool_arguments.md`
4. `04_visibility_tracking_confidentiality.md`
5. `05_attribution_tracking_reporting.md`
6. `06_sled_optimisation_and_symbolic_verification.md`
7. `07_benchmarks_and_real_world_policy_integration.md`
8. `08_repository_structure_and_agent_governance.md`

## Current synthesis

The strongest fourth-year shape is a single security story with four parts:

- authority-aware planning to improve utility,
- scoped delegation and consent to recover legitimate workflows,
- fine-grained policy and visibility/attribution semantics to improve realism and confidentiality analysis,
- stronger evaluation through reductions, symbolic verification, and one live benchmark or policy integration.

The core risk is breadth. The package therefore separates the project into independently reviewable directions so that each one can be accepted, rejected, or deferred on its own merits.
