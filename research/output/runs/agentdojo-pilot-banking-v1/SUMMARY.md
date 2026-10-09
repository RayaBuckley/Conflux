# banking stratified sweep (local, nf4, 0.5B)

- Suite and tag: `banking` v1.2.2
- Model: `Qwen/Qwen2.5-0.5B-Instruct` revision `7ae557604adf67be50417f59c2c2f167def9a775`, nf4,
  local RTX 4060, seed 0, temperature 0
- Protocol: 12 cells = 2 selected user tasks x 2 cases x 3 defences, `max_model_calls` 8,
  `max_steps` 16
- Source commit: `1127281`
- Result: 12 complete, 0 failed, utility 0/12, security 12/12
Rerun: see `RERUN.txt`; the sweep would build the four-task stratified protocol, not this one.
Repeated 2026-10-10 in this directory with the documented rerun command: all 12 cells agree on status,
utility, security, model calls and failures, and the protocol fingerprint is equal exactly; raw traces
differ only in `evaluation_timestamp` and `duration`.

Limits: 0.5B utility is zero by measurement at this scale (see `docs/evidence/VERIFICATION.md` §27),
so the security counts are vacuous: a model that completes no task cannot be shown to be protected.

Provenance: this bundle was produced before the frozen stratified selection existed, under the run
directory name `agentdojo-stratified-banking-v1`. It was renamed to `agentdojo-pilot-banking-v1` on
2026-10-10, when the four-task stratified run was retained beside it, so its recorded
`output_directory` still names the earlier path. See `docs/evidence/VERIFICATION.md` section 27.
