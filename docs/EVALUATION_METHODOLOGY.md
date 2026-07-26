# ITES Defence Evaluation Methodology

> Migration notice: [EVALUATION.md](EVALUATION.md) is now the canonical
> methodology entry point. This page remains as detailed historical material.

The MVP evaluates the enforcement boundary, not whether a particular model
recognises an attack. A deterministic synthetic model is therefore the primary
security test; a real model is an optional utility and integration experiment.

## External testing approaches

- [AgentDojo](https://agentdojo.spylab.ai/) evaluates tool-using agents in
  dynamic environments with attacks and defences; its [attack concepts](https://agentdojo.spylab.ai/concepts/attacks/)
  describe injection candidates and adaptive attack execution. The NeurIPS
  [paper](https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html)
  reports task security and utility over realistic environments.
- [InjecAgent](https://arxiv.org/abs/2403.02691) targets indirect prompt
  injections in tool-integrated agents.
- The [USENIX prompt-injection evaluation framework](https://www.usenix.org/conference/usenixsecurity24/presentation/liu-yupei)
  provides a systematic way to compare attacks and defences empirically.
- [OWASP's LLM application risks](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
  provides a threat taxonomy, including prompt injection and excessive agency.

These sources motivate realistic integration cases, but they do not replace
ITES' model-agnostic security objective. Empirical benchmarks can show that a
model and defence combination succeeds or fails on sampled tasks. The MVP
tests whether arbitrary proposals can cross an authority boundary.

## MVP evaluation protocol

1. Construct a deterministic organisational fixture with at least two
   Principals, distinct resource ownership/readability, trusted and untrusted
   artifacts, and one legitimate and one unauthorised permission.
2. Run `MVPExplorer` against a deterministic proposal generator.
3. Explore every proposal from each state in an independent branch, subject to
   one shared call budget.
4. Record every declared and blocked proposal, branch identifier, Principal
   Context, budget outcome, and terminal state.
5. Fail the security evaluation if any declared primitive lacks permission for
   any Principal in its context or if sibling traces contaminate one another.
6. Report utility separately as legitimate declarations divided by legitimate
   opportunities; never treat model refusal as a defence guarantee.

## AgentDojo compatibility track

After the synthetic MVP is stable, add an opt-in adapter that translates local
fake AgentDojo-style task/tool traces into canonical Conflux inputs, proposals,
primitive actions, and outcomes. External dependencies, model credentials, and
network access remain outside unit tests. The adapter may enrich traces but may
not bypass MVP authorisation or reinterpret a denied primitive as successful.

## Result requirements

Every reported run records semantics version, code revision, fixture, model or
stub identity, proposal ordering, budget, branch policy, security results,
utility results, incomplete states, counterexamples, and trusted assumptions.
