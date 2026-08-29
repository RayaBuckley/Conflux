# FLMSec Final-Evening Revision Plan — Updated

## Objective

Revise the FLMSec submission so that a reviewer can quickly understand:

1. the broader ITES threat model;
2. the precise distinction from CaMeL and other system-level defences;
3. the principal-provenance + existing-ACS enforcement rule;
4. what is proved theoretically versus supported by bounded SLED evidence;
5. what newer Conflux work exists, without allowing it to obscure the workshop paper's core claim.

The main paper should be a focused argument. The appendix should preserve useful technical material that is cut for space and provide clearly labelled preliminary evidence from the newer repository.

## P0 — Verify the comparison literature

### 1. Identify the supervisor-mentioned CaMeL verification paper
- Search by title/author/citations to CaMeL.
- Record exact bibliographic metadata and URL/DOI/arXiv ID.
- Read the threat model, formal property, trusted computing base, and relationship to CaMeL.
- Add it only after verifying what it actually proves.
- If it verifies CaMeL's implementation/policy enforcement, explain that this strengthens CaMeL but does not automatically erase a threat-model distinction with ITES.
- If it changes a comparison claim, change the paper rather than defending the old wording.

### 2. Build a source-backed comparison matrix
For CaMeL and the most relevant system-level neighbours record:
- security objective;
- adversarial/influence model;
- trusted components;
- provenance/capability abstraction;
- source of policy/authority;
- treatment of data-dependent control flow;
- formal guarantee;
- empirical evaluation.

Do not use reconstructed implementations as the primary basis for theoretical claims.

## P0 — Refocus the main paper

### 3. Rewrite abstract/introduction around system-level neighbours
The main progression should be:
- system-level secure-by-design defences already avoid relying on model robustness;
- ITES asks a broader authority question: what if any processed information may arbitrarily influence the model?
- associate influence with authenticated principals;
- permit an action only when every influencing principal is authorised by the existing ACS;
- authority therefore monotonically decreases as influence accumulates;
- SLED provides bounded implementation evidence.

### 4. Replace the current CaMeL comparison table
Avoid claims such as simply saying CaMeL “depends on the planning model”.
Prefer rows for:
- threat/security objective;
- control-flow assumption;
- tracked security object;
- authority/policy source;
- arbitrary data-dependent action choice;
- trusted computing base;
- guarantee.

### 5. Add one differentiating workflow
Use a legitimate data-dependent task in which retrieved information determines which privileged action is appropriate. Explain how ITES permits arbitrary model proposals but restricts their resulting authority.

Do not overclaim that CaMeL cannot represent the workflow. State the narrower architectural/threat-model distinction.

### 6. Make threat model → PE → intersection the central derivation
Explicitly state:
- any supplied information may arbitrarily determine model proposals;
- therefore every originating principal is conservatively treated as potentially responsible;
- an action is safe under the paper's PE definition only if all influencers already possess its authority;
- adding influencers cannot increase effective authority.

### 7. Compress formalism
Retain:
- ACS;
- influence;
- PE definition;
- intersection rule;
- monotonicity;
- security result.

Move repetitive proof prose and secondary formal details to the appendix.

## P0 — Use the appendix aggressively but carefully

The appendix is the correct destination for material that improves credibility or reproducibility but is not required to understand the core paper.

### 8. Move cut original-paper material to appendix
Candidates:
- expanded SLED methodology;
- environment definitions;
- detailed result classifications;
- longer proof details;
- additional examples;
- secondary related-work discussion;
- reconstruction methodology/results if retained at all.

The main text must remain self-contained. Do not move a premise needed to understand the security claim into the appendix.

### 9. Add a clearly labelled “Post-original / preliminary extensions” appendix
Summarise newer ITES work only if it is implemented and checked in the current repository. Potential topics:
- delegation;
- consent;
- visibility/observer-aware confidentiality;
- finer-grained action/resource policies;
- decision/information provenance distinctions.

For each:
1. state that it is newer than the core submitted ITES result;
2. give the motivation;
3. give the semantic rule at a high level;
4. state implementation/evidence status;
5. avoid upgrading preliminary work into a main-paper claim.

This appendix should demonstrate that the framework generalises, not turn the submission into a fourth-year-project survey.

### 10. Add AgentDojo smoke-test appendix evidence
Include only reproducible facts from the current repository:
- exact adapter/test exercised;
- pinned scenario/configuration/model if applicable;
- what “smoke test” establishes;
- output/result;
- limitations.

A smoke test demonstrates integration plumbing, not comparative security or benchmark superiority. Label it accordingly.

### 11. Add preliminary SLED-V appendix
Explain:
- motivation: bounded trace enumeration does not itself provide an unbounded implementation proof;
- current verification IR/model-checking components;
- which backends/reductions currently work;
- exact preliminary properties checked;
- whether verdicts are bounded, finite-model, or unbounded;
- model-versus-implementation distinction;
- known limitations and unsupported features.

Prefer a compact table:
Property | Model | Backend | Verdict | Bound/assumptions | Repro command

Do not call a result “formal verification of ITES” unless the checked model and implementation-conformance story justify that wording.

## P0 — Page-budget strategy

### 12. Cut main text to the workshop limit
Cut in this order:
1. generic model-level discussion;
2. repeated motivation;
3. detailed SLED mechanics;
4. detailed result taxonomy;
5. long proof prose;
6. broad future-work catalogue;
7. reconstructed-defence evaluation discussion.

Protect:
- CaMeL/system-level comparison;
- threat model;
- PE definition;
- ITES rule;
- monotonicity/security theorem;
- one differentiating example;
- assumptions/limitations;
- compact SLED evidence.

Compile after every major cut. Target a small safety margin under the limit.

## P0 — Anonymous code artefact

### 13. Do not publish the full development repository as supplementary material
The full Conflux repository is broad, contains fourth-year work irrelevant to this submission, and creates avoidable deanonymisation and reviewer-overload risk.

Create a minimal anonymous artefact derived from a clean export, not by casually deleting files from the working repository.

Recommended contents:

anonymous-artifact/
  README.md
  LICENSE-or-licensing-note.md
  pyproject.toml / minimal dependency file
  src/
    <only modules needed for core ITES + SLED evidence>
  tests/
    <tests for those modules>
  experiments/
    <minimal reproduction entry points/manifests>
  results/
    <small machine-readable results needed by paper>
  APPENDIX_REPRODUCTION.md

Optionally include SLED-V source/tests only if the appendix discusses those preliminary results and they can be cleanly reproduced.

Optionally include the AgentDojo adapter/smoke-test code only if needed to reproduce the appendix smoke test. Avoid vendoring AgentDojo itself.

### 14. Decide source-code scope by dependency closure
Do not assume “src + tests” is automatically sufficient.

Start from the exact commands required to reproduce:
- core ITES tests;
- SLED headline evidence or a representative reproduction;
- SLED-V appendix results;
- AgentDojo smoke test.

Compute/copy the minimal internal dependency closure for those commands. Include configuration/fixtures/scripts they require. Exclude unrelated adapters, planning experiments, reports, literature notes, development docs, and unpublished fourth-year directions.

### 15. Anonymisation audit
Run automated and manual searches over every supplementary file for:
- author names;
- Oxford/Keble/department names;
- email addresses;
- GitHub username/repository URL;
- local filesystem usernames;
- git remotes;
- commit hashes if they can trivially identify the public repository;
- package metadata author fields;
- badges;
- DOI/Zenodo records identifying authors;
- comments/docstrings naming the project author;
- cached outputs containing absolute paths;
- notebook metadata;
- environment variables/API keys/secrets;
- acknowledgements;
- links to personal pages.

Also inspect:
- filenames;
- archive name;
- PDF metadata;
- source package metadata;
- test snapshots;
- generated HTML/coverage reports.

Do not include `.git/`.

### 16. Licence/provenance audit
Before redistributing extracted source:
- preserve any required licence/copyright notices;
- identify third-party copied/derived code;
- do not silently redistribute external benchmark code;
- document dependencies and their installation rather than vendoring them unless permitted.

### 17. Reproduction README
The anonymous README should state:
- this is an anonymised supplementary research artefact;
- which paper claims it supports;
- supported Python/platform versions;
- setup commands;
- exact test commands;
- exact reproduction commands;
- expected outputs;
- which results are preliminary;
- what is deliberately omitted.

Do not mention the public Conflux repository during double-blind review.

### 18. Fresh-environment validation
Unzip the final archive into a new directory/container and execute every documented command from scratch.

The artefact is not ready until:
- install succeeds;
- tests succeed;
- paper-facing reproduction succeeds;
- no command depends on the original checkout;
- no identifying paths appear in output.

## P1 — Final adversarial review

### 19. CaMeL-author pass
Search all uses of:
CaMeL, Dual LLM, trusted, untrusted, planning, policy, provenance, capability, guarantee, maximal, optimal, exhaustive.

Check every comparison against primary sources.

### 20. Claim/evidence pass
Classify each claim:
- theorem/definition consequence;
- bounded SLED evidence;
- new preliminary appendix evidence;
- external prior-work claim.

Do not allow language to blur these categories.

### 21. Double-blind pass
Check:
- manuscript author block;
- acknowledgements;
- self-citations;
- supplementary archive;
- anonymous hosting account/repository;
- URLs;
- file metadata.

## Definition of done

A reviewer reading the first two pages should be able to state:
- ITES's threat model;
- why it differs from CaMeL;
- the principal-context/ACS rule;
- the resulting monotonicity argument.

A reviewer opening the appendix should find:
- useful details cut for space;
- clearly labelled newer ITES extensions;
- reproducible AgentDojo smoke-test evidence;
- precise preliminary SLED-V evidence.

A reviewer opening the code artefact should find:
- a small, comprehensible implementation relevant to the paper;
- tests and reproduction commands;
- no unrelated repository material;
- no obvious identifying information.
