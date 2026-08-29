# FLMSec Paper Revision Brief for AI Coder

**Basis:** Review of the current compiled FLMSec PDF (`main.pdf`) and supervisor feedback.  
**Purpose:** A targeted final revision pass. Prioritise reviewer comprehension and accuracy over adding further results.

## 1. Core objective

The paper should make one distinction unmistakable:

> ITES considers a broader influence/threat model than CaMeL: any information processed by the LLM, including the initiating user's input, may arbitrarily influence the resulting plan or action proposal. ITES therefore does not rely on model accuracy for security; it constrains the authority of whatever actions the model proposes using influencing-principal provenance and the existing access-control system (ACS).

The current paper is substantially improved, but this distinction should be made more concrete while avoiding unnecessary claims about comparative implementations.

## 2. Important correction: retain the CaMeL planning-model distinction

Do **not** remove the paper's observation that CaMeL relies on the LLM/planner behaving appropriately on the trusted user input.

The intended distinction is:

- CaMeL treats the user's query as trusted input and derives control flow/the execution plan from it.
- CaMeL's security architecture is designed to prevent *untrusted data* from changing that control flow.
- It does not treat prompt injection originating from the trusted user query as part of the same adversarial-input threat model.
- Consequently, accuracy/correctness of planning from the user query matters: an overly permissive or otherwise incorrect plan can expose a larger set of actions or flows than the user's actual intent required.
- ITES instead assumes that **all information supplied to an LLM execution may arbitrarily determine its proposals**, including the user's input.
- ITES does not require the resulting plan/action choice to be semantically correct for its PE guarantee. It permits an externally visible action only if every influencing principal is authorised for that action under the ACS.

Preserve this distinction, but phrase it precisely. Avoid the overly broad shorthand “CaMeL trusts the model for security” without explaining *what is trusted and why*. Prefer wording such as:

> CaMeL derives control flow from the trusted user query and prevents untrusted data from modifying that control flow. Its threat model therefore relies on the planner's interpretation of the trusted query to establish the intended execution structure. ITES instead treats information from every principal—including the initiating user—as potentially capable of arbitrarily determining model proposals, and constrains the authority of those proposals after influence has occurred.

Check the final wording directly against the CaMeL paper.

## 3. P0: add a concrete CaMeL–ITES example

The current Alice/Bob email example demonstrates ITES blocking PE but does not clearly demonstrate the architectural difference from CaMeL.

Add a short legitimate data-dependent workflow, preferably in the Introduction immediately after the CaMeL comparison.

Example structure:

> Alice asks the agent to inspect a report authored by Bob and perform whichever remediation action the report indicates. The report may therefore legitimately determine which action is proposed. ITES does not require this control-flow influence to be prevented: after the report is processed, both Alice and Bob are influencing principals, and the proposed action is permitted exactly when both are authorised for it.

Then explain the contrast:

- CaMeL seeks to derive control flow from the trusted query and prevent untrusted data from modifying it.
- ITES deliberately admits arbitrary data-dependent influence and instead restricts the authority available after that influence.
- ITES additionally applies the arbitrary-influence assumption to the user's own input rather than treating user-originated prompt injection as outside the adversarial-data model.

Do not claim that CaMeL can never express such a workflow. The point is the security boundary/threat model, not an absolute expressiveness impossibility.

## 4. P0: revise Table 1

The current table is useful but too compressed.

In particular, `Model trusted?` can hide the precise distinction above. Replace it with more explicit dimensions.

Suggested columns:

| System | Security objective | Influence/control-flow assumption | Authority/policy source | Security metadata |
|---|---|---|---|---|
| CaMeL | Policy/data-flow enforcement | Control flow derived from trusted user query; untrusted data constrained from changing it | Developer-defined policies | Capabilities / data-flow provenance |
| Progent | Privilege-policy enforcement | Verify against primary source | Symbolic/custom policy | Argument/tool metadata |
| PACT | Argument-sensitive enforcement | Verify against primary source | Contracts/policies | Argument provenance |
| FORGE | History-sensitive policy enforcement | Verify against primary source | Datalog policies | Causal/history information |
| ITES | PE prevention under arbitrary influence | Any principal's information may arbitrarily determine proposals | Existing organisational ACS | Influencing principals |

Only retain rows/cells that are directly supported by the cited papers.

## 5. P0: reduce SLED-V prominence in the main paper

SLED-V is useful preliminary evidence but should not become a fourth principal contribution of this workshop paper.

Change:

- Remove detailed comparative SLED-V findings from the abstract.
- Remove SLED-V as a numbered principal contribution.
- Keep at most one concise main-text pointer to Appendix B.
- Keep substantive SLED-V evidence in the appendix.
- The conclusion may mention it briefly as preliminary follow-on work, but it should not compete with ITES/SLED for the paper's central narrative.

The desired main-paper story is:

**broader threat model -> ITES -> formal PE guarantee -> SLED implementation evidence.**

SLED-V is supplementary evidence/future direction.

## 6. P0/P1: treat comparative SLED-V results cautiously

The table showing finite abstractions of CaMeL, Progent, PACT, etc. satisfying their native property while admitting PE counterexamples is potentially interesting, but also the easiest result for a reviewer to dispute.

If retaining it:

1. Define exactly what each hand-written abstraction models.
2. Define the native property `Q` for each defence.
3. Explain how `Q` was derived from the cited paper.
4. Show or describe the PE witness.
5. State important omitted semantics.
6. Reiterate that these are finite **model-level abstractions**, not verification of the published implementations.
7. Do not use this table as the primary evidence that ITES differs from the other systems.

If this cannot be made rigorous and easily reviewable tonight, remove the comparative table. The theoretical comparison is more important and aligns with supervisor feedback.

## 7. P1: move Biba/delegation detail to the appendix

The Biba/LOMAC connection is valuable and should remain in the main paper, but the current detailed discussion of delegation as addressing low-water-mark limitations consumes too much space and mixes newer work into the original ITES contribution.

Main paper should retain approximately:

> ITES follows a low-water-mark intuition, but retains the identities of influencing principals and computes authority from parameterised ACS permissions rather than assigning a single integrity label.

Move detailed discussion of:

- irrevocable integrity degradation;
- scoped delegation;
- one-use/expiry/revocation semantics;
- argument-constrained grants;

to a clearly labelled preliminary ITES-extensions appendix.

## 8. P1: make extension status explicit

Use consistent labels throughout:

### Core ITES
The formal mechanism and guarantee presented by the paper.

### Preliminary ITES extensions
Newer implementation work such as:
- delegation;
- consent;
- visibility/observer-aware confidentiality;
- finer-grained parameter/resource authority;
- attribution/provenance refinements.

### Preliminary SLED-V
New formal-verification infrastructure and finite-model results.

Do not imply that the original theorem or 1.46M-trace evaluation automatically validates all newer extensions.

## 9. P1: tighten SLED wording

Avoid unqualified statements such as:

> “SLED exhaustively explored every execution trace…”

when the experiment has a recursive depth bound and excludes incomplete traces.

Prefer:

> “SLED exhaustively enumerated the execution traces admitted by each bounded experimental configuration.”

Keep the ~1.46M trace count, depth-three bound, and incomplete-trace fraction/count visible.

The theorem is the security argument. The SLED experiment provides implementation evidence within its bounded environments.

## 10. P1: qualify “maximal utility”

Replace generic claims of “maximal utility” with one of:

> “maximal utility under SLED's task model”

or, preferably:

> “all ACS-authorised tasks represented by SLED remained achievable.”

This avoids sounding like a general empirical usability result.

## 11. P1: qualify confidentiality claims

The read-access rule establishes an authorised-read/access-safety property under the stated model. It is not a proof of general observational noninterference.

Replace broad wording such as “provides a confidentiality guarantee” with:

> “provides a conservative authorised-read guarantee”

or:

> “enforces the paper's access-safety confidentiality condition.”

Keep the existing related-work acknowledgement that noninterference is stronger.

## 12. P1: use the appendix for cut and newer material

The supervisor explicitly indicated that material removed for the page limit can be preserved in the appendix.

Recommended appendix structure:

### A. Trusted Computing Base and assumptions
Keep current TCB material.

### B. Expanded theoretical details
- longer proofs if cut from main text;
- Biba/LOMAC comparison;
- detailed delegation discussion.

### C. Original SLED details
- environment definitions;
- detailed classification scheme;
- historical trace reproduction;
- additional result tables.

### D. Preliminary ITES extensions
- delegation;
- consent;
- visibility;
- finer-grained authority;
- status and tests for each.

### E. Preliminary SLED-V
- IR;
- checkers/backends;
- seeded defects;
- COI;
- exact verdict semantics;
- limitations;
- comparative finite abstractions only if sufficiently defensible.

### F. AgentDojo smoke test
Include only if there is a real reproducible run.

State:
- exact AgentDojo version/commit;
- scenario/configuration;
- command;
- observed result;
- what integration path was exercised;
- limitations.

Explicitly state that a smoke test validates integration plumbing, **not comparative security effectiveness**.

## 13. P1: improve Figure 1 if time permits

The current architecture/TCB figure is useful, but the supervisor's main concern is understanding the distinction from CaMeL.

If possible, adapt or supplement it with a tiny conceptual comparison:

### CaMeL
`trusted user query -> control-flow plan -> untrusted data constrained by capabilities/policies`

### ITES
`inputs from principals -> arbitrary model proposal -> influencing-principal set -> ACS intersection -> allow/block`

The visual should communicate that CaMeL constrains where adversarial influence can affect execution, whereas ITES permits arbitrary influence and attenuates the authority of its consequences.

## 14. P1: update NeurIPS checklist after final artefact decisions

There are likely inconsistencies if the supplementary artefact and AgentDojo appendix are included.

Recheck:

### Open access/code
If an anonymised code artefact is supplied, keep this as `Yes` and ensure exact reproduction commands exist.

### Existing assets
If AgentDojo is actually executed for the smoke test, it is no longer accurate to say that no external code/assets are used. Cite the exact version and licence as appropriate.

### New assets
An anonymised supplementary code/reproduction artefact may make `[N/A]` questionable. Answer according to the final NeurIPS interpretation and actual submission contents.

Do not let checklist answers describe an artefact that has not actually been packaged and tested.

## 15. Anonymous code artefact

Do not expose the complete Conflux development repository.

Build a clean supplementary archive from the dependency closure of the claims being reproduced.

Include:
- core ITES implementation;
- necessary domain/provenance/ACS types;
- focused ITES tests;
- SLED implementation/tests needed for paper results;
- result/reproduction scripts;
- SLED-V code/tests/fixtures if Appendix E reports them;
- AgentDojo smoke-test adapter/configuration only if Appendix F reports it;
- minimal packaging/dependency metadata;
- anonymous README and reproduction instructions.

Exclude by default:
- `.git`;
- public repository URL;
- author names/emails;
- Oxford/Keble metadata;
- AI-agent development instructions;
- project-planning reports;
- literature notes;
- unrelated fourth-year experiments;
- unused adapters/providers;
- personal filesystem paths;
- generated caches/coverage output.

Run identity/secret scans and execute all documented commands from a fresh unpacked copy before submission.

## 16. Final execution order

1. Preserve but precisely rewrite the CaMeL trusted-user-query/planning distinction.
2. Add the concrete data-dependent CaMeL-vs-ITES example.
3. Simplify and source-check Table 1.
4. Remove SLED-V comparative results from the abstract and numbered contributions.
5. Move detailed Biba/delegation material to the appendix.
6. Qualify SLED exhaustiveness, utility, and confidentiality wording.
7. Decide whether comparative SLED-V Table 7 is rigorous enough to retain.
8. Add clearly labelled preliminary ITES extensions to the appendix.
9. Add AgentDojo smoke-test appendix only if reproducible evidence exists.
10. Build/test the minimal anonymous code artefact.
11. Recompile and verify the main paper remains within the eight-page limit.
12. Re-audit every checklist answer against the final PDF and artefact.
13. Perform a final CaMeL-author review: every statement about CaMeL must be defensible from the primary paper.

## Definition of done

A reviewer should be able to read the first two pages and correctly explain:

1. **Threat model:** any principal's information, including the initiating user's input, may arbitrarily determine model proposals.
2. **CaMeL distinction:** CaMeL derives control flow from a trusted user query and constrains untrusted-data influence; ITES permits arbitrary influence and constrains the resulting authority.
3. **ITES mechanism:** track influencing principals and intersect their existing ACS permissions.
4. **Guarantee:** an action cannot execute if any influencing principal lacks authority for it.
5. **Evidence:** SLED provides bounded implementation evidence; SLED-V is preliminary supplementary verification work.

If those five points are immediately clear, prioritise submission correctness and anonymisation over adding further technical results.
