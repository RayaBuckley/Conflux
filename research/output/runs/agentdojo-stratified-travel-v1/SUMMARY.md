# travel stratified sweep (local, nf4, 0.5B)

- Suite and tag: `travel` v1.2.0
- Model: `Qwen/Qwen2.5-0.5B-Instruct` revision `7ae557604adf67be50417f59c2c2f167def9a775`, nf4,
  local RTX 4060, seed 0, temperature 0
- Protocol: 60 cells = 10 selected user tasks x 2 cases x 3 defences, `max_model_calls` 8,
  `max_steps` 16
- Source commit: `1127281`
- Result: 60 complete, 0 failed, utility 0/60, security 60/60

The protocol counted 42 policy-caused utility failures across the cells; with utility zero
at this scale that says nothing about defence efficacy.

Rerun: `python scripts/run_agentdojo_sweep.py --suite travel --model-config <run>/transformers.json`.

Limits: 0.5B utility is zero by measurement at this scale (see `docs/evidence/VERIFICATION.md` §27),
so the security counts are vacuous: a model that completes no task cannot be shown to be protected.
