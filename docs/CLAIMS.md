# Claim-to-Evidence Ledger

| Claim | Status | Evidence and limits |
|---|---|---|
| Empty/unknown context cannot authorise an effect | Implemented | policy and ITES tests; assumes mediation cannot be bypassed |
| Influence is never silently removed by nested execution | Implemented | immutable provenance and monotonic-context tests |
| Provenance is not a read ACL | Implemented | separate read port and reader/author inversion tests |
| Branches are isolated alternatives | Implemented | one transition kernel and branch-parent tests |
| Native SLED returns minimal counterexamples | Implemented within finite model | breadth-first checker tests |
| Conflux is secure for unbounded deployments | Not claimed | needs symbolic proof and implementation conformance |
| External benchmarks establish utility | Not yet evidenced | real integrations and result bundles are deferred |
| Cloud policy behaviour matches a provider | Not claimed | current AWS adapter is an explicit fail-closed subset |

The archived paper is historical evidence, not the status source of truth.
