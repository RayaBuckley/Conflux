# Results and Experiment Plan

## Immediate objective

Convert existing infrastructure into reproducible Part C evidence.

## A. Existing AgentDojo run

Before rerunning:
- locate all existing output/log files;
- identify exact Conflux commit;
- identify AgentDojo revision/version;
- identify model ID and local inference backend;
- record suite/tasks;
- record attack and defence configuration;
- record seed/sampling settings where applicable;
- record parser/tool-call failures separately;
- retain raw traces.

Create a manifest and summary. Do not publish aggregate numbers without raw evidence and configuration.

## B. Local-model smoke matrix

Cached/local models currently available should first be used for a small reproducible matrix.

Suggested dimensions:
- model: cached Qwen, cached Smol;
- mode: benign, attacked;
- defence: undefended/baseline, Conflux;
- tasks: 10–20 representative tasks initially.

Measure:
- benign task success;
- attacked task success;
- security violations;
- Conflux blocks;
- false blocks;
- parser failures;
- tool-call failures;
- latency;
- token/call counts if available.

Do not interpret security rates from a model with near-zero benign utility without qualification.

## C. Original SLED vs current state exploration

Recreate the Part B environments.

Record:
- original enumerated traces;
- unique canonical states;
- transitions;
- runtime;
- peak memory;
- shortest counterexample length for defective monitors;
- incomplete/bounded cases.

This should quantify the value of the state-based redesign.

## D. Verification baseline

For the smallest finite ITES model:
- run explicit-state checker;
- run Z3 bounded checker;
- run nuXmv/symbolic backend where supported;
- record exact property and assumptions;
- distinguish bounded from unbounded results.

Then run the same configuration against deliberately defective controllers.

## E. Reduction ablations

Baseline -> +COI -> +symmetry -> +POR -> +authority-aware subsumption, as implemented.

For each:
- states;
- transitions;
- runtime;
- memory;
- verdict;
- counterexample equivalence/minimality.

Do not add a reduction without a preservation argument.

## F. Controller synthesis

Small finite ACS instances:
1. expose arbitrary typed proposals;
2. specify PE as the forbidden property;
3. synthesise maximally permissive safe decisions;
4. compare synthesised decisions to ITES for every represented `(state, action)` pair.

Scale principals/actions/resources until the method becomes impractical; report the boundary.

## G. Comparative defence verification

After ITES is stable:
- model one alternative defence;
- validate its own semantics/property;
- check Conflux PE;
- retain counterexamples;
- distinguish specification-level from implementation-level findings.

## H. Provenance granularity ablation

Compare:
1. execution-level;
2. action-level;
3. argument-level;
4. visibility-aware argument-level.

Hold the PE property fixed.

Measure:
- secure tasks recovered;
- false blocks;
- required provenance metadata;
- verification state-space cost;
- real-model utility where available.

## Evidence layout suggestion

    experiments/
      <experiment-id>/
        manifest.json
        README.md
        raw/
        normalized/
        summary.json
        figures/

The exact path should be reconciled with the repository's existing conventions before adoption.
