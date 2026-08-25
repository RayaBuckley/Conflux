# Reproducing the Part B \~1.5M SLED Trace Evidence in Current Conflux

**Date:** 25 August 2026\
**Target:** current public `main` of `RayaBuckley/Conflux`\
**Purpose:** implementation specification for an AI coder to determine
whether current native SLED faithfully reproduces the original Part B
exhaustive enumeration, implement the missing reproduction path if
necessary, run it, and retain publication-grade evidence.

## Executive conclusion

Yes --- recreating the original approximately 1.5 million Part B SLED
traces with current Conflux appears feasible and is high-value for the
FLMSec paper.

However, **the repository does not currently reproduce the 1.5M
enumeration**. The existing `native-sled-reproduction-v1` bundle
explicitly records:

-   historical trace claim: `1,500,000`;
-   current transitions: `60`;
-   `classification: "enumeration_change"`;
-   `comparable: false`.

That bundle is useful mutation/conformance evidence, but it is not a
reproduction of the original exhaustive experiment.

Current Conflux now contains most of the semantic machinery needed for a
much stronger reproduction. `CombinatorialVerificationSystem` explicitly
auto-enumerates nested execution candidates from powersets of
environment data and supports the original distinction between
intermediate proposal sets and final primitive-only proposal sets.
Native SLED uses the canonical current ITES transition kernel. This
means a new experiment can test something more valuable than merely
rerunning archived code:

> **Can the current Conflux ITES/SLED implementation reproduce the
> original Part B exhaustive decision-path experiment when configured to
> use the same environments, proposal grammar, depth bound and
> classification rules?**

The correct implementation should **not replace native SLED's
canonical-state BFS with trace enumeration**. Canonical-state
deduplication is an optimization and intentionally changes the number of
explored objects. Instead, add a dedicated **legacy-enumeration
reproduction mode/experiment adapter** that drives the current canonical
ITES kernel through the exact original proposal/decision-path space
while separately counting: 1. raw legacy-equivalent decision traces; 2.
unique canonical states/transitions reached; 3. duplicate/subsumed
paths.

This produces both the historical comparison and a direct measurement of
how much the new state-based optimization compresses the old trace
space.

The expected historical totals from the archived paper are:

  Environment     Explored traces    Incomplete
  ------------- ----------------- -------------
  1                       422,535        40,040
  2                       996,451       159,112
  3                        43,621        19,755
  **Total**         **1,462,607**   **218,907**

The original action/task classifications should also be reproduced if
the archived fixtures and classifier semantics are recoverable exactly.

This should be attempted before the workshop submission because it
simultaneously provides: - historical-result reproduction; -
current-kernel regression/conformance evidence; - evidence that SLED's
later optimizations preserve the original security conclusions; - a
compelling "1.46M legacy traces collapse to X canonical
states/transitions" result if measured carefully.

------------------------------------------------------------------------

# 1. What current Conflux already supports

Current `docs/reference/SLED.md` states that native SLED: - explores
typed states breadth-first; - memoizes canonical future-relevant
state; - retains predecessor edges; - returns shortest
counterexamples; - reports unique states, transitions, duplicates and
truncation.

It also states that the combinatorial adapter: - supports nested
execution candidates generated from environment-data powersets; -
matches the original prototype's powerset-of-data exploration; -
supports depth-dependent option sets; - can restrict the final call to
primitive actions; - supports a separate final batch-size limit; -
exposes the union of all authors/readers in an environment.

The implementation confirms this.
`CombinatorialVerificationSystem.from_environment()` generates non-empty
subsets of environment artifacts as `NestedExecutionAction`s, combines
them with primitive actions, and `enabled()` enumerates proposal
batches. `max_model_calls`, `final_primitive_only`, and
`final_max_batch_size` correspond directly to the old depth-3
experiment.

The current explicit-state checker is deliberately **not** a legacy
trace enumerator. It deduplicates targets by `state_key`. This is why
the retained current reproduction has only tens of transitions rather
than 1.46M traces.

That distinction is important: a 60-transition state-space result is not
evidence that 1.46M old traces were rerun. It is evidence that a newer
abstraction/exploration strategy explored a much smaller set of
canonical states.

------------------------------------------------------------------------

# 2. What the existing reproduction does and does not establish

The retained bundle at
`research/output/runs/native-sled-reproduction-v1/` is deterministic and
checksummed. Its `result.json` explicitly says the historical comparison
is not comparable because enumeration changed.

It currently establishes: - three legacy/canonical fixture pairs; -
current canonical behavior; - five seeded defective monitors; -
five-of-five defect detection; - one-step witnesses; - deterministic
regeneration.

It does **not** establish: - exact enumeration of all Part B
model-output choices; - equality of the historical trace counts; -
equality of historical incomplete counts; - equality of the original
action/task classification totals; - that state deduplication preserves
every original task/utility classification; - runtime improvement over
the original evaluator.

Do not modify this existing bundle to pretend it provides those claims.
Create a new versioned experiment.

Recommended output:
`research/output/runs/native-sled-partb-reproduction-v1/`

------------------------------------------------------------------------

# 3. Important semantic mismatches to resolve before claiming exact reproduction

The coder must audit these explicitly.

## 3.1 Empty proposal batches

The Part B implementation generated proposal subsets with:

-   intermediate calls: subset sizes `0..2`;
-   final call: primitive subset sizes `0..3`.

Therefore the empty proposal set was a valid model output.

Current `conflux.evaluation.combinatorial._powerset()` explicitly
excludes the empty subset.

This is a concrete mismatch.

For exact historical enumeration, add an experiment-level/configurable
`include_empty_batch` behavior. Do not silently change normal native
SLED semantics if empty output is intentionally represented as
termination elsewhere.

The reproduction must count the empty-model-output branch exactly as the
old evaluator did.

## 3.2 Nested-input powerset size

The Part B implementation generated **all non-empty subsets of
environment data** for nested LLM calls.

Current `from_environment()` defaults `max_nested_inputs=3`.

For exact reproduction, set the bound to `len(environment.artifacts())`,
or provide an explicit `all_nested_input_subsets=True` reproduction
configuration.

Do not rely on the default.

## 3.3 Intermediate/final batch grammar

Original: - atoms = all primitive actions + every non-empty data-subset
nested action; - intermediate options = every proposal subset of size 0,
1 or 2; - final options = every primitive-action subset of size 0, 1, 2
or 3; - max LLM calls = 3.

Exact reproduction configuration should therefore be:

``` text
max_model_calls = 3
max_batch_size = 2
include_empty_batch = true
all nested input subsets = true
final_primitive_only = true
final_max_batch_size = 3
```

Verify whether the current kernel interprets a
`ProposalBatch.alternatives(...)` as the same semantics as the old
frozenset of proposals. If current "alternatives" means mutually
exclusive sibling branches while the old `MyLogic` iterated over every
proposal in a returned set, they are **not semantically identical**.
This must be audited.

If they differ, create a reproduction adapter representing an old LLM
output as one atomic **proposal set** whose contained proposals are all
processed according to the old semantics, while still using current ITES
authorization/read logic for each proposal.

Do not paper over this distinction.

## 3.4 Branch-local influence

The old evaluator saved/restored accumulated influence around nested
predefined logic. Current SLED specifies sibling branch isolation.

Verify that the reproduction adapter's branch restoration matches the
archived implementation exactly.

## 3.5 Read rule

The original `auth_read` required every current influencer to be a
reader of every proposed nested input.

Current canonical Conflux correctly separates provenance from read ACLs.
For this reproduction, configure the current read-policy adapter so that
it implements exactly the archived `R(d,u)` relation.

Do not regress production semantics to the old implementation.

## 3.6 Empty Principal Context

The original helper `auth()` vacuously returned true for an empty
influencer set. Current Conflux deliberately denies empty/unknown
Principal Context.

This may or may not affect the three original environments, because
their initial inputs appear to have authors. Determine empirically.

If no reachable historical branch has empty context, record
`semantic_difference_not_exercised`.

If it is exercised, exact count equality against the buggy historical
implementation and semantic fidelity to current ITES become
incompatible. In that case report **two modes**: - `historical_exact`:
emulates the old behavior only for reproduction; - `current_semantics`:
uses fail-closed current ITES.

Never reintroduce vacuous empty-context authorization into canonical
ITES.

## 3.7 Historical evaluator bugs

The archived Part B evaluator contains known fragile classification
logic. Exact count reproduction may require reproducing bugs rather than
intended semantics.

Separate: - **enumeration equivalence**; - **security-semantic
equivalence**; - **classification equivalence**.

If a historical classifier bug changes counts, retain: 1.
`historical_classifier` results; 2. `corrected_classifier` results; 3. a
documented delta.

The workshop paper should use corrected semantics for current claims,
while historical exact counts are reported as reproduction evidence.

------------------------------------------------------------------------

# 4. Recover the exact three historical environments

This is P0.

Do not infer the environments from the published aggregate tables if
exact archived source exists.

Search the integrity-protected archive under
`research/publications/paper/`, archived reports, archived code, Git
history, and any preserved Part B `main.py`.

For each environment retain a normalized machine-readable fixture
containing: - principals and IDs; - each principal's exact action
permissions; - data IDs/tags; - authors; - readers; - initial input
set; - primitive action universe; - depth/proposal bounds.

Generate a fixture fingerprint/hash.

Then compare those fixtures against the existing three `legacy-*`
fixtures in `native-sled-reproduction-v1`.

The existing reproduction's fixture names are: -
`legacy-env-01-confidential-handoff`; - `legacy-env-02-cross-project`; -
`legacy-env-03-nested-assistance`.

Do **not** assume these are exact Part B environments merely because
there are three of them. The current bundle itself marks the historical
trace comparison non-comparable.

Produce a table:

  Field             Archived Part B   Existing legacy fixture   Exact?
  ----------------- ----------------- ------------------------- --------
  principals                                                    
  permissions                                                   
  data                                                          
  authors                                                       
  readers                                                       
  initial inputs                                                
  action universe                                               

If any mismatch exists, create exact `partb-env-01..03` fixtures rather
than modifying the existing mutation fixtures.

------------------------------------------------------------------------

# 5. Reproduction architecture

Implement a dedicated experiment driver, not a second security kernel.

Suggested conceptual interface:

``` python
PartBReproductionConfig(
    max_model_calls=3,
    intermediate_max_batch=2,
    final_max_batch=3,
    include_empty_batch=True,
    nested_inputs="all_nonempty_subsets",
    final_primitive_only=True,
)

PartBTraceEnumerator(
    kernel=current_transition_kernel,
    classifier=...,
    config=...,
)
```

The enumerator should enumerate **model decision paths**, not canonical
states.

For every model call: 1. construct the exact allowed output option list
for that depth; 2. process the selected proposal set; 3. recursively
enumerate any nested calls according to the old ordering/branch
semantics; 4. preserve sibling isolation; 5. classify the
completed/incomplete trace; 6. increment aggregate counters; 7.
optionally map every reached runtime state to its canonical `state_key`.

Do not retain 1.46M full Python trace objects in memory. Stream
aggregation.

Maintain: - total raw traces; - incomplete raw traces; - action-category
counts; - task-category counts; - unique canonical state keys; - unique
canonical transitions; - duplicate path hits; - maximum depth; -
runtime; - peak RSS if easy/reliable.

For counterexamples or mismatches, retain only a bounded sample/minimal
witness.

------------------------------------------------------------------------

# 6. Performance strategy

1.46M paths should be feasible on a laptop if the implementation streams
counts and avoids repeatedly constructing large immutable objects
unnecessarily.

The old implementation did roughly this scale in minutes despite
Python-level brute force.

Current optimization opportunities: - precompute the intermediate option
tuple once per environment; - precompute final options once; -
precompute nested action input/provenance/readability metadata; - cache
deterministic kernel transitions by
`(canonical_state_key, proposal_set_key, depth/config)`; - reuse
canonical immutable fixtures; - aggregate counts rather than retain
traces; - memoize classifier subresults where classification is a pure
function of compact trace summary; - avoid JSON serialization inside the
hot loop; - write evidence only after the run.

Important: transition caching is valid only if the cache key includes
**all future-relevant state**. Prefer current canonical `state_key` plus
exact proposal-set key and any reproduction-mode flags. Add a
differential test comparing cached and uncached enumeration on small
fixtures.

Do not use state deduplication to skip raw legacy paths when computing
the historical trace count. The point is to count all old paths.
Deduplication can be measured alongside it.

------------------------------------------------------------------------

# 7. Required comparison levels

Produce three increasingly strong comparisons.

## Level A --- exact enumeration count

Target:

``` text
env1 traces = 422535
env2 traces = 996451
env3 traces = 43621
total = 1462607
```

and incomplete:

``` text
40040
159112
19755
total = 218907
```

If exact equality fails, do not tune code until it matches blindly.
Produce the first divergent decision-path prefix and identify whether
the cause is: - fixture mismatch; - empty-batch mismatch; - option
ordering; - proposal-set semantics; - nested branch semantics; - read
rule; - current security repair; - historical classifier bug; - other.

## Level B --- original outcome taxonomy

From the Part B report, target action-level beneficial/non-beneficial
totals and task-level totals.

The archived paper reports action outcomes:

Environment 1: - secure goal: 176,352 - blocked PE: 352,704 - all
reported insecure/missing/irrelevant categories: 0

Environment 2: - secure goal: 381,328 - blocked PE: 878,096 - other
reported categories: 0

Environment 3: - secure goal: 45,488 - blocked PE: 28,852 - other
reported categories: 0

Task-level: - Env1 secure tasks: 2,118,454; blocked PE tasks: 75,648 -
Env2 secure tasks: 4,756,190; blocked PE tasks: 107,136 - Env3 secure
tasks: 141,342; blocked PE tasks: 0 - other reported task categories: 0.

Be careful: the older project report and later preprint use slightly
different labels. Store canonical machine-readable category IDs and map
both historical names in presentation.

## Level C --- current-kernel semantic reproduction

Run the same raw decision space through current canonical ITES.

Check: - zero unauthorized executed effects; - zero forbidden reads
under the configured historical read policy; - monotonic Principal
Context; - branch isolation; - current classification.

If Levels A/B match only under historical-bug compatibility but Level C
differs, report that transparently.

------------------------------------------------------------------------

# 8. New optimization result to collect

For each environment report both:

``` text
raw legacy-equivalent decision traces
unique canonical states
unique canonical transitions
duplicate/subsumed path count
compression ratio = raw_traces / unique_states
```

This is potentially more interesting for the workshop than merely saying
"we reran 1.46M traces."

It empirically demonstrates why native SLED moved from trace enumeration
to canonical-state model checking.

Do not compare `1,462,607` directly to the current retained bundle's
`60 transitions` unless both experiments use the same exact fixtures and
proposal grammar. The existing bundle does not.

------------------------------------------------------------------------

# 9. Evidence bundle

Create a new deterministic bundle:

``` text
research/output/runs/native-sled-partb-reproduction-v1/
    manifest.json
    protocol.json
    result.json
    historical-comparison.json
    table.md
    RERUN.txt
    CHECKSUMS.sha256
```

Optional: - `performance.json` (excluded from byte-deterministic
comparison if wall clock varies); - `mismatches.jsonl`; -
`counterexamples/`.

`protocol.json` must include: - source commit; - archived source
fingerprint; - fixture hashes; - exact option grammar; - exact bounds; -
classifier version; - compatibility flags; - cache enabled/disabled; -
Python version.

`result.json` should separate: - `historical_exact`; -
`current_semantics`; - `canonical_state_statistics`.

Never collapse them into one ambiguous "reproduced" field.

------------------------------------------------------------------------

# 10. Tests before the full run

Required tests:

1.  Empty proposal output exists in reproduction mode.
2.  Intermediate option counts match the archived formula.
3.  Final option counts match the archived formula.
4.  All non-empty nested input subsets are generated.
5.  A proposal set with two proposals has audited semantics matching the
    old implementation.
6.  Nested sibling influence is restored.
7.  Historical read rule matches `auth_read`.
8.  Cached vs uncached enumeration produces identical counts on small
    fixtures.
9.  Streamed aggregation equals retained-trace aggregation on a tiny
    fixture.
10. Current ITES negative control still produces a witness.
11. Reproduction mode cannot alter production/native SLED defaults.

Formula checks are useful.

If: - `P` = number of primitive actions; - `D` = number of data
objects; - `N = 2^D - 1` nested actions; - `A = P + N`;

then original intermediate option count is:

``` text
C(A,0) + C(A,1) + C(A,2)
```

and final option count:

``` text
C(P,0) + C(P,1) + C(P,2) + C(P,3).
```

Assert these counts against the recovered environments.

------------------------------------------------------------------------

# 11. Run protocol

After tests pass:

1.  Run each environment separately first.
2.  Record raw counts immediately.
3.  If Env1 differs, stop and diagnose before running Env2/3.
4.  Once Env1 exactly matches enumeration, run Env2 and Env3.
5.  Run once with transition cache disabled on at least a smaller
    validation slice.
6.  Run full cached reproduction.
7.  Regenerate evidence from a clean checkout.
8.  Verify checksums/deterministic files.
9.  Run relevant tests and repository validation.
10. Update `CLAIMS.md` and `STATUS.md` only after evidence exists.

Suggested claim states:

If exact counts + outcomes match: \> "Current Conflux reproduces the
archived Part B SLED decision-space counts and outcome taxonomy on all
three historical environments while using the current canonical ITES
kernel."

If counts match but corrected classifier differs: \> "Current Conflux
reproduces the archived decision-space enumeration; differences in
reported outcome counts are attributable to documented classifier
corrections."

If counts differ because current semantics intentionally changed: \>
"Current Conflux replays the historical proposal space, but exact
historical counts are not comparable because \[specific semantic
repair\]."

Never call a near match an exact reproduction.

------------------------------------------------------------------------

# 12. Paper implications

If successful, this deserves a compact FLMSec result.

A strong formulation would be:

> We reconstructed the original bounded SLED experiment using the
> current Conflux transition kernel and the archived proposal grammar.
> Across the three historical environments, the reproduction enumerated
> 1,462,607 model-decision traces \[if exact\], recovering the original
> security/utility classifications \[if exact\]. Native canonical-state
> exploration additionally maps these paths onto substantially fewer
> future-relevant states, illustrating the benefit of state memoization
> without changing the checked security result.

Then separately report current SLED-V evidence.

This creates a useful evidence chain:

``` text
Part B archived implementation/results
          |
          v
exact legacy decision-space reproduction
using current kernel
          |
          v
canonical-state SLED result
          |
          v
SLED-V independent/solver-backed checks
```

That is much stronger implementation-faithfulness evidence than the
current three tiny canonical fixtures alone.

------------------------------------------------------------------------

# 13. Priority for the AI coder

## P0 --- audit before coding

-   locate exact archived Part B source and all three environments;
-   compare with current `legacy-*` fixtures;
-   audit empty proposal batches;
-   audit multi-proposal batch semantics;
-   audit nested branch restoration;
-   audit historical classifier.

Write a short `PARTB_REPRODUCTION_AUDIT.md` before implementing if any
ambiguity remains.

## P0 --- implement exact raw enumerator

Use current kernel; enumerate historical decision paths; stream counts;
no state skipping for raw count.

## P0 --- run Environment 1

Do not proceed blindly if it fails exact comparison.

## P1 --- full three-environment run

Once Env1 semantics are validated.

## P1 --- canonical-state/compression metrics

Measure unique state/transition mapping alongside raw paths.

## P1 --- retain evidence and update claims

Only after successful rerun.

## P2 --- optimization benchmark

Compare: - archived reported runtime if trustworthy; - current
uncached; - current cached; - canonical-state BFS.

This is optional for the workshop. Correct reproduction is more
important than speed.

------------------------------------------------------------------------

# 14. Explicit non-goals

Do not: - modify the canonical ITES security semantics to match
historical bugs; - replace native SLED BFS with raw trace enumeration; -
count only unique states and call them historical traces; - alter
existing `native-sled-reproduction-v1`; - hard-code the expected totals
into the enumerator; - suppress mismatches; - add unrelated SLED-V
features; - spend time on model-backed experiments before this
deterministic reproduction is resolved.

------------------------------------------------------------------------

# 15. Acceptance criteria

The implementation is complete when:

-   [ ] exact archived Part B environments are fingerprinted;
-   [ ] original proposal grammar is represented exactly;
-   [ ] empty model outputs are represented;
-   [ ] all non-empty nested input subsets are represented;
-   [ ] multi-proposal semantics have been audited;
-   [ ] current canonical ITES kernel is used for `current_semantics`;
-   [ ] raw paths are counted without canonical-state pruning;
-   [ ] canonical-state statistics are collected separately;
-   [ ] Env1/2/3 trace totals are compared against 422,535 / 996,451 /
    43,621;
-   [ ] incomplete totals are compared against 40,040 / 159,112 /
    19,755;
-   [ ] original action/task taxonomy is compared where recoverable;
-   [ ] any mismatch has a machine-readable reason/witness;
-   [ ] runtime is practical;
-   [ ] deterministic evidence bundle is retained;
-   [ ] rerun command is documented;
-   [ ] tests demonstrate caching/optimization does not alter counts;
-   [ ] claims/status are updated conservatively;
-   [ ] no production security behavior is weakened for compatibility.

## Bottom line

Current Conflux is close to being able to do this, but the existing
"native reproduction" is deliberately a **different experiment** and
says so. The missing piece is a raw legacy-equivalent decision-path
enumerator/configuration layered over the current kernel.

Because the current combinatorial adapter already contains explicit
support for the old powerset-of-data and depth-dependent proposal
grammar, this should be a relatively contained implementation rather
than a reconstruction of SLED from scratch.

The first thing to test is not performance. It is **semantic equivalence
of the option grammar**, especially empty outputs and the meaning of
multi-proposal batches. Once those match, 1.46M streamed paths should be
computationally modest, and the resulting evidence would be particularly
valuable for the workshop paper.
