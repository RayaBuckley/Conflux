# Experiment 6: Cheap Credibility Extensions

These tasks are P1. Do them only after the core deterministic and AgentDojo tracks are underway.

## A. Cedar differential parity

### Objective

Turn the existing Cedar 4.12.0 preflight from `evaluation ready` into retained differential evidence if the exact pinned binary can be run.

### Protocol

1. Confirm binary/version identity exactly matches the existing manifest expectation.
2. Run the full existing strict differential corpus.
3. For every cell retain:
   - canonical Conflux request;
   - translated Cedar request;
   - in-memory/oracle decision;
   - Cedar decision;
   - agreement yes/no;
   - unsupported/unavailable reason.
4. Do not silently approximate unsupported Cedar constructs.
5. If any disagreement occurs, retain it and diagnose before changing either evaluator.

### Output

A concise parity table:

- total corpus cells;
- matched decisions;
- mismatches;
- unavailable/unsupported;
- binary version and hash.

### Claim boundary

If all cells match: `The Conflux adapter agrees with Cedar 4.12.0 on the retained supported differential corpus.`

Do not claim general Cedar equivalence.

## B. Observational confidentiality fixture suite

### Objective

Expand current safe/unsafe self-composition evidence from a minimal pair to a small family of explicit leak channels.

### Add fixtures for

1. direct observable return-value leak;
2. action-argument leak;
3. branch-dependent observable action;
4. error-message leak;
5. correctly redacted result;
6. correctly hidden error detail;
7. same low-observation behaviour under secret changes;
8. explicit permitted/declassified observation if the current semantics represent this cleanly.

### Backends

Reference product-model interpretation and Z3 BMC with COI where supported.

### Metrics

- expected safe/unsafe;
- actual verdict;
- product-state size;
- reduced variable/rule counts;
- witness length for unsafe cases;
- witness readability/replay.

### Claim boundary

These remain finite self-composition results, not a general proof of noninterference.
