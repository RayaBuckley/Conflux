# NeurIPS 2026 Checklist Evidence

Maps each NeurIPS 2026 Paper Checklist question to a draft answer, supporting
paper section, and supporting artifact.

## 1. Claims

| Field | Value |
|---|---|
| Draft answer | Yes |
| Paper section | Abstract, Sections 1–5, Section 7 (Limitations) |
| Artifact | Formal proofs (Section 3), generated evidence tables (Tables 1–5), `research/output/runs/` result JSON |
| Remaining action | Verify every abstract sentence maps to a theorem, experiment, or source |

## 2. Limitations

| Field | Value |
|---|---|
| Draft answer | Yes |
| Paper section | Section 7 (Discussion, Limitations) |
| Artifact | N/A (in-paper text) |
| Remaining action | Ensure all limitations listed in Section 7 are visible, not only in the checklist |

Limitations that must appear:
- Provenance correctness (trusted assumption)
- ACS correctness (trusted assumption)
- Complete mediation (trusted assumption)
- Finite/bounded verification (not unbounded proof)
- IR abstraction gap (no formal refinement from Python)
- Conservative influence overapproximation
- No user-intent guarantee
- No general noninterference
- Comparative models are abstractions, not upstream implementation evaluations

## 3. Theory Assumptions and Proofs

| Field | Value |
|---|---|
| Draft answer | Yes |
| Paper section | Section 3 (Theorems 1–2, Corollary 1, with proofs) |
| Artifact | Formal proofs in `main.tex` |
| Remaining action | Ensure monotonicity theorem states "for a fixed ACS state" (DONE) |

## 4. Experiments

| Field | Value |
|---|---|
| Draft answer | Yes |
| Paper section | Section 5 (Evaluation) |
| Artifact | `research/output/runs/native-sled-reproduction-v1/`, `research/output/runs/sled-coi-reduction-v1/`, `research/output/runs/coi-scaling-v1/`, `research/output/runs/defence-models-v1/`, `research/output/runs/z3-agreement-v1/` |
| Remaining action | Document exact fixture definitions, bounds, and solver versions in supplementary material |

## 5. Reproducibility

| Field | Value |
|---|---|
| Draft answer | Yes (deterministic experiments) |
| Paper section | Section 5, Appendix A |
| Artifact | All result JSON is versioned and checksummed; `scripts/generate_*.py` provide deterministic regeneration with `--check` mode |
| Remaining action | Ensure fixture/model definitions and reproduction commands are in supplementary material |

## 6. Statistical Significance / Error Bars

| Field | Value |
|---|---|
| Draft answer | N/A |
| Paper section | Appendix A |
| Artifact | All results are deterministic verification outcomes (SAFE/UNSAFE/bounded_safe), not stochastic measurements |
| Remaining action | None |

## 7. Compute

| Field | Value |
|---|---|
| Draft answer | Yes |
| Paper section | Appendix A |
| Artifact | All experiments run on a laptop (CPU only); no GPU or cluster compute for headline results |
| Remaining action | Document exact CPU model, runtime, and solver version (Z3) |

## 8. Code / Data Availability

| Field | Value |
|---|---|
| Draft answer | Yes (anonymous supplementary artifact) |
| Paper section | Appendix A |
| Artifact | No identifying repository links during double-blind review |
| Remaining action | Prepare anonymous artifact if required by venue; otherwise state release-after-review |

## 9. Dataset Documentation

| Field | Value |
|---|---|
| Draft answer | N/A (synthetic formal fixtures, not a conventional dataset) |
| Paper section | Section 4 (SLED/SLED-V) |
| Artifact | `research/experiments/suites/sled-coi-v1/` fixture definitions |
| Remaining action | Explain construction/purpose of synthetic fixtures in supplementary material |

## 10. Human Subjects

| Field | Value |
|---|---|
| Draft answer | N/A |
| Paper section | N/A |
| Artifact | N/A |
| Remaining action | None |

## 11. Societal Impact

| Field | Value |
|---|---|
| Draft answer | Yes |
| Paper section | Appendix A |
| Artifact | N/A (in-paper text) |
| Remaining action | Ensure checklist notes: conditional guarantees may be overinterpreted as deployment security; bad provenance/ACS configuration invalidates guarantees; conservative enforcement can deny useful actions |

## 12. Licenses

| Field | Value |
|---|---|
| Draft answer | N/A (no external artifacts redistributed) |
| Paper section | N/A |
| Artifact | N/A |
| Remaining action | None |

## 13. Hyperparameter Search

| Field | Value |
|---|---|
| Draft answer | N/A |
| Paper section | N/A |
| Artifact | Model-checking bounds are configuration parameters, not hyperparameters |
| Remaining action | Document bounds/configuration separately from hyperparameter search |
