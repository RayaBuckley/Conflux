# Claim-to-Evidence Map

| Claim | Manuscript location | Evidence artifact | Allowed wording | Limitation |
| --- | --- | --- | --- | --- |
| PE prevention (mathematical) | Corollary 1, Sec 3 | Formal proof | "prevents PE under the stated threat model" | Conditional on correct provenance, ACS, enforcement |
| Maximality of intersection rule | Theorem 1, Sec 3 | Formal proof | "maximally permissive under the PE objective" | Fixed ACS, parameterised actions |
| Authority monotonicity | Theorem 2, Sec 3 | Formal proof | "monotonically non-increasing as influence accumulates" | Conservative provenance model |
| Biba/low-water-mark lineage | Sec 3, para after Thm 2 | docs/research/RELATED_WORK.md | "structurally analogous to Biba's low-water-mark" | Not a new integrity model; novelty in combination |
| Native SLED defect detection | Table 1, Sec 5 | research/output/runs/native-sled-reproduction-v1/result.json | "5/5 monitors detected, 1-step witnesses" | Finite fixtures, fixed bounds (depth 1, states 4) |
| Direction readiness mutations | Table 1, Sec 5 | research/output/runs/direction-readiness-v1/security-mutations.json | "11/11 mutants killed, 1-step witnesses" | Finite disclosure/delegation models, depth 1 |
| Checker agreement (ref + COI) | Table 2, Sec 5 | research/output/runs/sled-coi-reduction-v1/result.json | "reference and reduced agree on 2 fixtures" | Finite IR models; Z3 unavailable in environment |
| COI reduction preserves verdicts | Table 3, Sec 5 | research/output/runs/sled-coi-reduction-v1/result.json | "COI reduces variables/rules/states while preserving verdicts" | 2 fixtures only; unsafe witness lifts |
| Dual-LLM satisfies Q but violates PE | Table 4, Sec 5 | research/output/runs/defence-models-v1/result.json | "finite IR model comparison, not implementation evaluation" | Finite abstraction, not faithful to published system |
| CaMeL satisfies Q but violates PE | Table 4, Sec 5 | research/output/runs/defence-models-v1/result.json | "finite IR model comparison" | Finite abstraction |
| Progent satisfies Q but violates PE | Table 4, Sec 5 | research/output/runs/defence-models-v1/result.json | "finite IR model comparison" | Finite abstraction |
| PACT satisfies Q but violates PE | Table 4, Sec 5 | research/output/runs/defence-models-v1/result.json | "finite IR model comparison" | Finite abstraction |
| ITES preserves PE | Table 4, Sec 5 | research/output/runs/defence-models-v1/result.json | "bounded_safe within the stated finite model" | Finite IR model |
| Requester-only violates PE | Table 4, Sec 5 | research/output/runs/defence-models-v1/result.json | "UNSAFE with counterexample" | Finite IR model |
| AgentDojo pipeline executes | Sec 5 (related work) | research/output/runs/agentdojo-1b5-nf4-v1/result.json | "pipeline runs end-to-end" | 1.5B model too small for utility; not efficacy evidence |
| Observational confidentiality (bounded) | Sec 4.2 | docs/evidence/CLAIMS.md | "bounded evidence, not noninterference proof" | Finite product state spaces; Z3 BMC |
