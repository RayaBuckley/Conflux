# Experiment 1: SLED to SLED-V Scaling

## Research question

How much do canonical state exploration, cone-of-influence reduction, and solver-backed bounded checking reduce the cost of worst-case verification compared with historical trace enumeration?

## Main claim supported

SLED-V is not merely a cleaner implementation of SLED. It removes large amounts of trace redundancy and enables deeper/wider finite verification while preserving verdicts and counterexamples on the supported model subset.

## Existing anchor

Retain and include the historical reproduction:

- raw historical traces: 1,462,607 total;
- canonical states: 31;
- depth bound: historical depth-three semantics;
- exact historical environment trace counts remain regression assertions.

Do not recast this as an unbounded proof.

## Implement as an extension of existing experiment infrastructure

Locate the current generators for:

- native SLED reproduction;
- COI scaling;
- Z3 agreement;
- verification IR fixture generation.

Add one shared parameterised fixture generator if this can be done without weakening the independently implemented reference/interpreter paths. Do not merge the reference checker and solver model into a single implementation that makes agreement circular.

## Synthetic environment parameters

Use structurally meaningful parameters rather than arbitrary noise only:

- principals P: 2, 4, 8, 16;
- data/resources D: 2, 4, 8, 16 where feasible;
- primitive action classes A: 2, 4, 8;
- nested depth K: 1, 2, 3, 4, then higher only where cheap;
- proposal branching B: 1, 2, 4;
- irrelevant/noise variables N: 0, 4, 8, 16, 32;
- policy-equivalence ratio: all distinct, half equivalent, mostly equivalent.

Do not run the full Cartesian product if unnecessary. Use a one-factor-at-a-time core plus a small stress grid.

### Minimum viable matrix

1. Historical anchor: 3 legacy environments.
2. Noise scaling: N = 0, 4, 8, 16, 32 on one safe and one unsafe fixture.
3. Principal scaling: P = 2, 4, 8, 16 at fixed D/A/B/K.
4. Branch/depth scaling: K = 1..5 at B = 2, plus B = 1,2,4 at K = 3.
5. One policy-equivalence experiment demonstrating state canonicalisation opportunity if the current canonicaliser supports it.

## Compared modes

At minimum:

- `trace_enum`: historical/legacy enumeration where available;
- `native_state`: canonical native SLED state exploration;
- `reference_coi`: reference interpreter on COI-reduced IR;
- `z3_bmc`: Z3 BMC on original IR;
- `z3_bmc_coi`: Z3 BMC on reduced IR.

If a mode is unsupported for a fixture, record `unavailable` rather than omitting the cell.

## Safe and unsafe fixtures

Every scale family must include both:

- a secure reference monitor expected to satisfy the checked property;
- a defective monitor or transition expected to violate it.

Unsafe fixtures must expose a short concrete witness. Verify witness replay/lifting when COI is used.

## Metrics

Per cell record:

- fixture ID;
- parameters P/D/A/K/B/N;
- expected verdict;
- actual verdict;
- trace count if trace enumeration is executed;
- unique state count;
- transition count;
- original IR variable count;
- reduced IR variable count;
- original rule count;
- reduced rule count;
- BMC depth;
- runtime wall seconds;
- peak resident memory if inexpensive to measure;
- witness length;
- witness replay/lift success;
- timeout flag and timeout threshold;
- backend identity/version;
- source commit.

## Correctness gates

1. All safe/unsafe verdicts agree semantically across every backend that supports the same fixture.
2. Every unsafe COI witness lifts to a valid witness in the original model.
3. Historical exact trace counts remain unchanged.
4. No optimisation may turn an unsafe model into a safe verdict.
5. Timeouts are data, not discarded cells.

## Expected paper outputs

### Figure S1

Log-scale explored objects vs scale, with trace enumeration and canonical-state exploration distinguished. Prefer number of traces/states on y-axis and environment scale on x-axis.

### Figure S2

Runtime vs irrelevant/noise variables for original Z3 and COI-reduced Z3.

### Table S1

Historical anchor:

- environment;
- legacy traces;
- canonical states;
- compression ratio;
- verdict;
- runtime if comparable.

### Table S2

Safe/unsafe backend agreement, including timeout/unavailable status.

## Claim boundary

Allowed claim: SLED-V drastically reduces redundancy and agrees with independent bounded/reference backends on the tested finite models.

Not allowed: SLED-V proves Conflux secure for arbitrary or unbounded deployments.
