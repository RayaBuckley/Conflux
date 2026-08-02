# Fine-Grained Policy Languages for Tool Arguments

## What this direction is

This direction extends policy checking from whole actions to the semantic structure of tool arguments. Instead of asking only "may this principal call this tool?", the system asks questions like:

- may this principal choose this recipient,
- may this principal choose this file,
- may this principal choose this amount,
- may this principal choose this database row,
- may this principal choose this external endpoint?

That is materially different from checking the tool as a single opaque action.

## Why it matters

A tool call often bundles multiple kinds of authority into one interface. Some arguments are harmless content. Others are authority-bearing selectors. A policy that treats the whole call as one unit can be too coarse, because it either blocks too much or permits too much.

This is one of the most important improvements suggested by related work: the authority problem often lives inside the arguments, not only in the action name. The latest review also concluded that this should be absorbed into Conflux rather than treated as an optional flourish. fileciteturn0file2

## Analysis

A fine-grained policy language needs at least three levels of structure:

1. **Tool-level permission**  
   May the principal invoke the tool at all?

2. **Argument-level permission**  
   May the principal choose each argument value or class of values?

3. **Role-level permission**  
   Does the argument play a privileged role, such as recipient, target, destination, selector, or credential reference?

This suggests that policy objects should understand semantic roles, not only string patterns. For example, an email tool may have:
- `recipient` as an authority-bearing argument,
- `subject` as a lower-risk argument,
- `body` as content,
- `attachment` as a visibility-sensitive argument.

The policy language should therefore support predicates over:
- tool name,
- argument name,
- argument role,
- argument provenance,
- resource identity,
- request context,
- delegation state.

The likely design choice is to keep the base policy language small and deterministic, then attach role annotations at the schema layer. That keeps the evaluation tractable and makes the policy engine easier to review.

## Rationale

This direction strengthens realism. Real organisational policies rarely say only "allow tool X". They usually care about what is being acted on, where it is going, and which principal is binding which field.

It also improves security analysis. If the policy engine can see argument roles, then Conflux can distinguish:
- content that influences a decision,
- from selectors that determine authority-bearing side effects.

That distinction is critical for secure agent behaviour.

## Constraints

The policy language should avoid:
- hidden magic values,
- unconstrained string matching as the main mechanism,
- silent fallback to whole-action approval when role metadata is missing,
- policy evaluation that depends on model prose rather than schemas.

Unsupported roles should fail closed.

## Open questions

- How much of the role information should come from tool schemas versus policy configuration?
- Should roles be static, inferred, or both?
- Should policy composition differ for direct calls, delegated calls, and subagent calls?
- Should roles be machine-readable in traces so that explanations can be generated later?

## Suggested first increment

Implement one tool adapter whose schema explicitly distinguishes content arguments from authority-bearing arguments, then add a policy rule that allows the content but denies an unauthorised selector or recipient.
