# Claim-to-Evidence Ledger

| Claim | Status | Evidence and limits |
|---|---|---|
| Empty/unknown context cannot authorise an effect | Implemented | policy and ITES tests; assumes mediation cannot be bypassed |
| Influence is never silently removed by nested execution | Implemented | immutable provenance and monotonic-context tests |
| Provenance is not a read ACL | Implemented | separate read port and reader/author inversion tests |
| Branches are isolated alternatives | Implemented | one transition kernel and branch-parent tests |
| Native SLED returns minimal counterexamples | Implemented within finite model | breadth-first checker tests |
| Dynamic effects are re-authorised at execution time | Implemented | planning runtime, revocation, certificate, and provider tests |
| Generated code cannot exceed the declared envelope | Implemented at adapter boundary | container arguments, mount/path checks, and fail-closed sandbox tests; host/container implementation remains in the TCB |
| Solver results match the supported runtime subset | Bounded evidence | serialisable IR, interpreter differential tests, optional Z3 backend |
| Conflux is secure for unbounded deployments | Not claimed | finite bounds and abstractions do not prove unbounded deployments |
| AgentDojo integration preserves upstream semantics | Implemented for translation | pinned 0.1.35 structures and raw fixture; Conflux annotations are additional assumptions |
| AgentDojo establishes Conflux utility or efficacy | Not yet evidenced | live comparative run is externally gated |
| Open-ended planning improves utility | Not yet evidenced | four-mode aggregator exists; matching live observations do not |
| Cloud policy behaviour matches a provider | Not claimed | current AWS adapter is an explicit fail-closed subset |
| The current evidence pipeline handles allow, block, and vulnerable-control cases | Bounded evidence | `runs/smoke/`, two scripted cases, one one-step negative-control witness |

The archived paper is historical evidence, not the status source of truth.
The M3 smoke result is pipeline-readiness evidence only; it is not promoted to
a deployment-security or external-utility claim.
