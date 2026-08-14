# Reviewer / Collaborator Meeting Checklist

Use this as preparation rather than canonical project documentation.

## Before the meeting

- Ensure the public/default branch passes validation.
- Ensure README points to a fast research-reviewer path.
- Confirm current claims/status documents are accurate.
- Have one command that demonstrates Conflux/SLED-V without network access if possible.
- Have one small `SAFE` example.
- Have one deliberately defective `UNSAFE` example with a short counterexample.
- Have the latest AgentDojo evidence available if validated.
- Prepare the core equation:

      Allow(a, PC) iff forall p in PC: ACSAllows(p,a)

- Prepare one concrete PE example.
- Prepare one example where a contemporary defence's objective may differ from PE.
- Know exactly which claims are theorem, model-checked, bounded, empirical, planned, or speculative.

## Questions worth asking formal-methods researchers

- Is maximal permissiveness best framed through supervisory control, safety games, or another formalism?
- Which backend is best suited to unbounded finite-state safety here: IC3/PDR, BDDs, k-induction, custom SMT?
- Can Principal-Context monotonicity justify an antichain/subsumption relation?
- What is required to prove a partial-order or symmetry reduction sound?
- How should implementation refinement/conformance be established?
- What is the cleanest route from PE safety to secure controller synthesis?

## Questions worth asking security/IFC researchers

- Is Principal Context best understood as an integrity label, provenance set, authority context, or a combination?
- Which Biba/LOMAC/declassification/endorsement results transfer cleanly?
- How should explicit delegation be formalised without undermining the base invariant?
- What observation model is needed for confidentiality/noninterference?
- Where does argument-level provenance materially change authority?
- Which assumptions about authenticated provenance are realistic?

## Questions worth asking LLM-agent security researchers

- Which contemporary defence has sufficiently precise semantics to model faithfully?
- Which AgentDojo tasks expose meaningful authority distinctions?
- Which real workflows distinguish PE prevention from prompt-injection prevention?
- What baseline would make a comparative result credible?
- Which model/tool parsing issues could confound utility/security measurements?

## Avoid spending the meeting on

- source-tree naming;
- broad productionisation;
- speculative cloud integrations;
- adding many benchmarks;
- minor documentation formatting.

The useful output is criticism of the threat model, theorem, formalisation, experimental design, and comparison methodology.
