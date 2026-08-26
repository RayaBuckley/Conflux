# Conflux FLMSec Morning Work Plan --- 26 August 2026

**Repository reviewed:** public `main`, 335 commits\
**Target:** FLMSec 2026\
**Purpose:** prioritized AI-coder work before the next human review.

## Executive assessment

The latest changes have moved the submission from manuscript
construction to evidence-integrity and submission-hardening. Preserve
the current focused Principal Context/ITES framing, TCB table, bounded
SLED/SLED-V claims, and four-RQ evaluation structure.

The morning should prioritize reviewer trust over adding features.

The main issues found are:

1.  The manuscript claims comparative finite-model results for Dual-LLM,
    CaMeL, Progent and PACT, while the canonical claim ledger visibly
    records comparative evidence only for Dual-LLM and the
    requester-only negative control. Audit or narrow this claim.
2.  The Biba paragraph says the contribution moves "from a total order
    on integrity labels"; this is unnecessarily strong and should be
    replaced by a more careful structural comparison.
3.  The motivating example appears logically inconsistent: Bob is said
    to lack permission, yet the requester-only controller is then said
    to permit the action. Use a high-authority requester plus a
    low-authority influencing document author instead.
4.  `STATUS.md` contradicts itself: its opening says live-model evidence
    remains future work/no model results are retained, while later
    sections and `CLAIMS.md` document completed Qwen planning and
    AgentDojo runs.
5.  The paper has still not been compiled/page-counted with the official
    template according to the current handoff.
6.  The Part B 1,462,607-trace reproduction does not yet appear as
    retained evidence and is now a high-value deterministic experiment.

## P0 --- compile and establish the real submission state

Obtain the official NeurIPS 2026/FLMSec template from the official venue
source. Record its provenance/checksum internally. Build
`research/publications/flmsec_2026/main.tex`.

Record: - exact build command; - warnings/errors; - total pages; -
main-text pages before references; - bibliography pages; -
appendix/checklist pages.

Fail submission validation if main text exceeds eight pages. Run
anonymity and placeholder checks against both source and generated PDF.

Do not make speculative cuts until the actual page count is known.

## P0 --- audit comparative-defence evidence

Current paper text says the finite abstractions of Dual-LLM, CaMeL,
Progent and PACT satisfy native properties while violating PE. Current
`CLAIMS.md` visibly records only the Dual-LLM comparative result and
requester-only negative control.

For every system claimed experimentally, require a retained record
containing: - model ID and source paper; - exact abstraction scope; -
native security property and its formalization; - PE formalization; -
state variables/rules/bounds; - generated native-property verdict; -
generated PE verdict; - counterexample where unsafe; - source commit.

A system stays in the empirical table only if its abstraction exists,
its native-property interpretation is justified from the primary paper,
both verdicts are generated, and evidence is retained/ledgered.

If this cannot be established quickly, remove CaMeL/Progent/PACT from
the empirical claim. Keep them in Related Work. A smaller fair
comparison is stronger than a questionable large table.

Always write "our finite abstraction of X", not an unqualified "X
violates PE".

If only Dual-LLM remains, narrow the abstract to:

> comparative finite-model verification demonstrates that satisfying a
> defence-native property need not imply PE safety.

## P0 --- correct Biba/Denning wording

Replace the current "total order" sentence with a conservative
structural comparison, approximately:

> The similarity is structural rather than an equivalence of policy
> models. Low-water-mark integrity lowers a subject's effective
> integrity after consuming lower-integrity information. Principal
> Context instead retains the identities of all conservatively
> influencing principals and computes permitted parameterized actions
> from the intersection of their current ACS permissions. Thus
> attenuation is induced by organizational authority rather than by
> assigning a single integrity label to the execution.

Optionally add:

> When permission sets are ordered by inclusion, intersection is their
> meet.

Verify the primary Biba citation, LOMAC authors/venue, Denning metadata,
PACT/FORGE metadata, and remove/fix the uncertain Myers/Liskov entry if
applicable.

## P0 --- fix the motivating example

The current example says Alice authors confidential data, Bob requests
an email, Bob lacks permission, but then says a requester-only
controller would permit the action. That is inconsistent if Bob is the
requester.

Use: - Alice = high-authority requester, permitted to perform action
`a`; - Mallory/Bob = author of influencing document/content, not
permitted to perform `a`; - requester-only controller checks Alice and
permits; - Principal Context includes Alice + Mallory/Bob and blocks; -
SLED-V finds the requester-only counterexample.

Use the same example consistently in introduction, theorem intuition,
and evaluation.

## P0 --- fix evidence-status contradiction

Update stale opening text in `docs/evidence/STATUS.md`.

It should reflect that limited laptop evidence now exists for Qwen
planning and AgentDojo, while explicitly saying it does not establish
strong utility/efficacy and larger-model evaluation remains future work.

Do not alter the actual bounded claims.

## P1 --- promote the Part B 1.46M reproduction

The existing handoff calls this P2. Promote it after the P0
paper-integrity work.

It is valuable because it is deterministic, requires no LLM, tests
continuity from Part B to the current kernel, and can quantify how
canonical-state SLED compresses the old trace space.

### Audit first

Recover the exact archived Part B source and three environments.
Verify: - empty model-output batches; - all non-empty nested data
subsets; - intermediate batch sizes 0--2; - final primitive-only batches
0--3; - max model calls = 3; - semantics of multi-proposal outputs; -
branch-local influence restoration; - historical read rule; -
empty-context semantic difference; - known historical classifier
defects.

If exact fixtures cannot be recovered, stop and document that rather
than approximating.

### Implementation rule

Do not replace native SLED BFS. Add/use a reproduction experiment
adapter that enumerates the historical raw model-decision paths through
the current canonical ITES kernel while separately mapping reached
states to current canonical state keys.

Stream aggregates rather than retaining 1.46M trace objects.

Collect: - raw traces; - incomplete traces; - original action/task
categories; - unique canonical states; - unique canonical transitions; -
duplicate path hits; - runtime.

### Exact historical targets

  Environment            Traces    Incomplete
  ------------- --------------- -------------
  1                     422,535        40,040
  2                     996,451       159,112
  3                      43,621        19,755
  **Total**       **1,462,607**   **218,907**

Run Env1 first. If it differs, stop and identify the first divergence
rather than repeatedly running the full experiment.

Classify the outcome as exactly one of: - exact reproduction; -
enumeration reproduction with corrected classifier/current semantics; -
non-comparable replay with documented reason.

Never tune blindly to expected totals.

If successful, retain a versioned checksummed evidence bundle before
adding the result to the paper.

Potential paper result:

> We replay the archived Part B proposal space through the current ITES
> kernel, recovering 1,462,607 bounded model-decision traces across the
> three historical environments \[only if exact\]. Current SLED maps
> these paths onto X canonical future-relevant states, providing a
> regression bridge from the original evaluator to the optimized
> state-based implementation.

## P1 --- repair RQ2 / regenerate Z3 evidence

The manuscript's RQ2 is "Independent Checker Agreement", but its current
prose mainly describes original-vs-COI-reduced reference agreement.
Those are different questions.

Check/regenerate: - `verify-coi-safe`; - `verify-coi-unsafe`; -
`verify-coi-original-safe`; - `verify-coi-original-unsafe`.

If retained Z3 artifacts exist, generate a table containing: - reference
verdict; - Z3 verdict; - BMC bound; - original/reduced verdict; -
witness/lifting status.

If artifacts cannot be regenerated, narrow RQ2 so the manuscript does
not imply unavailable independent-backend evidence.

## P1 --- correct SLED trace wording

Current text says the state-transition graph "contains every execution
trace". Since native SLED memoizes canonical states, use more precise
wording:

> SLED explores the reachable finite transition system induced by every
> enabled well-typed proposal under the configured model; predecessor
> edges retain counterexample paths.

This also makes the distinction from the proposed raw Part B trace
enumerator explicit.

## P1 --- soften universal "fundamental" wording

Prefer:

> We study PE as a fundamental system-level security objective.

or:

> We propose PE as the system-level objective considered in this work.

Avoid implying all confidentiality, integrity, intent, and availability
problems reduce to PE.

## Page-pressure policy

Only after compilation.

If over eight pages, cut in this order: 1. compress duplicate
comparison-table prose; 2. merge motivating example into
introduction/evaluation; 3. shorten nonessential SLED implementation
details; 4. move observational-confidentiality implementation detail to
appendix if it has no headline result; 5. move secondary related-work
detail to appendix; 6. remove/compress architecture figure if redundant.

Do not cut: - PE definition; - TCB; - maximality theorem; - monotonicity
theorem; - Biba relationship; - boundedness limitations; - core
evaluation evidence.

## P2 --- only after the above

Possible later tasks: - runtime↔IR differential conformance; - COI
scaling family; - anonymous evidence/code artifact.

Do not activate delegation, add providers/benchmarks, redesign planning,
or add solver backends before submission.

## Suggested morning order

### 0--30 min

-   obtain official style;
-   compile;
-   record page count;
-   fix build failures;
-   run anonymity/placeholder audits;
-   correct motivating example.

### 30--60 min

-   audit comparative models/evidence;
-   remove unsupported comparative claims immediately if needed;
-   correct Biba wording/citations;
-   fix stale `STATUS.md`.

### 60--120 min

-   recover exact Part B fixtures/source;
-   audit proposal semantics;
-   implement only missing reproduction adapter/configuration;
-   validate option counts;
-   run Env1;
-   if exact, run Env2/Env3 and retain evidence;
-   if not exact, retain first-divergence diagnosis.

### 120--150 min

-   regenerate/check Z3 evidence;
-   generate a correct RQ2 table;
-   add Part B result table only if evidence exists.

### Final 15--30 min

-   regenerate paper tables;
-   rebuild PDF;
-   verify page limit;
-   run paper/relevant repo validation;
-   update claim/evidence map;
-   update `NEXT_REVIEW_2026-08-26.md`.

The handoff must state: - exact commit; - page count; - build status; -
which comparative systems survived evidence audit; - Biba sources
checked; - Part B reproduction result/blocker; - Z3 status; - remaining
decisions.

## Noon-review acceptance gate

Before the next review, aim for:

-   [ ] official-template PDF builds;
-   [ ] exact main-text page count known;
-   [ ] anonymity passes;
-   [ ] motivating example is logically correct;
-   [ ] Biba framing is conservative and citations verified;
-   [ ] every comparative empirical claim has retained evidence,
    otherwise removed;
-   [ ] `STATUS.md` is internally consistent;
-   [ ] RQ2 distinguishes independent backend agreement from COI
    preservation;
-   [ ] Part B reproduction has evidence or a precise documented
    blocker;
-   [ ] no broad new subsystem added;
-   [ ] \<=8 pages or a concrete cut plan;
-   [ ] claim/evidence map matches manuscript;
-   [ ] handoff contains only remaining research/editorial decisions.

## Priority ranking

1.  No unsupported comparative claims.
2.  Compiled, page-counted, anonymous submission.
3.  Correct Biba lineage and motivating example.
4.  Exact or diagnostically useful Part B reproduction.
5.  Clean Z3/reference agreement evidence.
6.  Only then scaling/conformance additions.

The coder should optimize for reviewer trust rather than the number of
features or tables. The strongest plausible morning outcome is a
technically conservative manuscript plus a successful historical
reproduction showing that the current ITES kernel recovers the original
1,462,607 bounded decision traces and that optimized native SLED
represents the same behavior through a much smaller canonical state
space.
