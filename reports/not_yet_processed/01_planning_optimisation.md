# Planning Optimisation

## What this direction is

Planning is the layer that decides which observations to request, which subgoals to pursue, which actions to defer, and when to ask for clarification or approval. In Conflux, planning is not merely a utility feature. It is the mechanism that determines how much of the environment becomes visible to the model, and therefore how much authority the execution accumulates.

The relevant question is not whether planning can make the system "smarter" in the abstract. The question is whether planning can improve task completion while keeping the authority footprint as small as possible.

## Why it matters

The current defence core is intentionally conservative. It blocks actions whenever the accumulated principal context does not justify them. That is good for safety, but it can reduce utility if the agent asks for too much information, observes the wrong thing at the wrong time, or retries in an inefficient order.

A planning layer can reduce this loss by:

- selecting only the information needed for the next step,
- delaying sensitive observations until they are strictly necessary,
- choosing between alternative tool routes,
- preferring low-authority paths first,
- stopping early when a task is provably impossible without delegation.

The 3rd-year report already pointed to planning as a future direction. The later repository review also identified planning optimisation as a natural place to recover utility without weakening the security kernel. fileciteturn0file3 fileciteturn0file0

## Analysis

A useful planning system for Conflux should be authority-aware rather than only cost-aware. Standard planners optimise for steps, latency, or success probability. Conflux needs an additional term: how much authority is introduced, exposed, or retained for how long.

This creates a lexicographic objective:

1. satisfy all security constraints,
2. maximise task completion,
3. minimise unnecessary visibility,
4. minimise principal-context growth,
5. minimise calls, tokens, latency, and irreversible effects.

That means planning should not be an untrusted free-form chain-of-thought artifact. It should be a typed structure with explicit preconditions, required reads, required permissions, possible outcomes, and safe abort paths.

The most valuable planning work is likely to be one of these two styles:

1. **Utility optimisation for secure workflows.**  
   Compare reactive execution, static planning, and dynamic replanning on tasks that are already secure under the current ACS.

2. **Authority-minimising planning.**  
   Show that a planner can reduce unnecessary exposure by choosing a narrower sequence of observations or tool calls.

The second is more distinctive. It is not merely better planning; it is planning that is aware of confidentiality and authority.

## Rationale

Planning is worth prioritising because it gives a direct answer to a practical complaint about conservative security systems: they can be secure but cumbersome. If Conflux can show that a planner recovers much of the lost utility while preserving the security invariant, the project becomes more compelling both scientifically and operationally.

It also fits the structure of the repository. The current architecture already separates the security kernel from higher-level orchestration. Planning can therefore be added as a layer above the kernel rather than as a modification to the core invariant.

## Constraints

Planning must not:

- infer authority from model confidence,
- bypass the security kernel,
- silently request more information than the task requires,
- erase provenance when it is convenient,
- convert a failed action into a security exception.

Planning failures should be represented as explicit outcomes such as no-plan, under-specified plan, or approval required.

## Open questions

- Should the planner be a separate trusted module, or a constrained proposal generator whose output is checked by a verifier?
- Should replanning be allowed freely, or only inside preverified envelopes?
- Which utility metric should dominate: task completion, number of actions, privacy exposure, or cost?
- Should plans be global, stepwise, or hierarchical?

## Suggested first increment

Implement one benchmarked comparison between:

- reactive execution,
- static plan-first execution,
- and one authority-aware planner.

Measure security-preserving utility, visibility exposure, and call count on a small set of secure tasks.
