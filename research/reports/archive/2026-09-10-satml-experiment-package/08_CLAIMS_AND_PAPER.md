# Claims, Interpretation, and Paper Mapping

## Central SaTML story

Recommended structure:

1. Principal Context / ITES provides a model-independent authority-confinement boundary derived from authenticated provenance and existing organisational authorisation.
2. SLED-V verifies finite models of such system-level security semantics much more efficiently than historical trace enumeration and produces counterexamples for seeded defects.
3. Provenance precision and authenticated planning can recover legitimate utility without changing the authority boundary.
4. Real-model AgentDojo results demonstrate the distinction between an attack influencing model behaviour and an attack obtaining an unauthorised external effect.

## Exact claim discipline

### Strongly supported existing claims

- canonical ITES implementation enforces action-time Principal Context authority within its implemented semantics;
- provenance and reader permissions are separate;
- historical bounded trace counts are reproducible;
- current native SLED uses finite state exploration and shortest counterexamples;
- Z3/COI paths agree on retained finite fixtures;
- AgentDojo and planning pipelines run end-to-end.

### Claims these new experiments should support

#### C-SCALE

`Across the evaluated finite models, canonical-state SLED-V reduces substantial trace redundancy and enables scalable bounded verification while preserving backend verdicts and unsafe witnesses.`

Evidence: Experiment 1.

#### C-MUT

`Across a declared mutation suite spanning Principal Context, provenance, read/disclosure, argument authority, planning/certificates, and delegation, SLED/SLED-V detects the retained seeded defects and returns concrete witnesses.`

Evidence: Experiment 2.

#### C-PROV

`Authenticated contributor-level provenance recovers utility relative to conservative may-have-written provenance without changing ITES's all-influencers authorisation rule.`

Evidence: Experiment 3.

#### C-ADOJO

`On the selected AgentDojo tasks/models/attacks, Conflux mediates malicious proposals at the authority boundary and prevents the measured unauthorised effects, with the reported utility cost.`

Evidence: Experiment 4.

#### C-PLAN

`On the declared planning suite, planning improves task completion and/or reduces authority exposure while every effect remains subject to the same ITES action-time authorisation.`

Evidence: Experiment 5.

#### C-CEDAR

`The Conflux Cedar adapter agrees with pinned Cedar 4.12.0 on the retained supported differential corpus.`

Only claim if Experiment 6 actually produces complete agreement.

## Claims that must remain prohibited

- `Conflux is secure for all deployments.`
- `SLED-V proves the Python implementation correct in general.`
- `No prompt injection can affect the model.`
- `AgentDojo proves universal prompt-injection security.`
- `Cedar parity on a finite corpus proves full Cedar semantics.`
- `The candidate CaMeL/Progent/PACT/Dual-LLM finite abstractions faithfully represent those published systems.`
- `The Principal Context permission intersection is mathematically unprecedented.`
- `Authorised reads imply noninterference.`
- `Planning gives security by itself.`

## Manuscript integration

Every results subsection should begin by saying what is being tested, then give the numerical result, then state the limitation.

Suggested results order:

1. Historical SLED reproduction and SLED-V compression.
2. Verification scaling and backend agreement.
3. Security mutation benchmark.
4. Provenance precision / utility trade-off.
5. AgentDojo real-model evaluation.
6. Planning utility recovery.
7. Optional Cedar/confidentiality supplementary results.

## Evidence index

Create `research/publications/manuscript/generated/evidence_index.json` or the repository's equivalent with one entry per numerical statement:

- claim ID;
- manuscript label/table/figure;
- exact source run path;
- source file and JSON key;
- manifest hash;
- generator commit;
- aggregation script/version.

Add a test that all generated manuscript result references resolve to existing retained files.
