# Repository-wide search and drift audit

Run this before and after edits. Inspect every hit; do not perform blind replacements.

## 1. Primary semantic search

```bash
git grep -n -i -E 'model[- ]level|model robustness|prompt injection defence|prompt injection defense|fully compromised|arbitrary model|untrusted for security|not trusted for security'

git grep -n -i -E 'only.*utility|utility.*model|security.*utility|model.*utility'

git grep -n -i -E 'authority versus harm|policy adequacy|correct ACS|existing ACS|current ACS|access-control system|access control system|P\(u, a\)|ACS\('

git grep -n -i -E 'delegat|authority transfer|authority-changing|permission transfer|grant model|DelegationNode'

git grep -n -i -E 'endorsement|trusted transformation|declassification|reduce influence|narrow Principal Context|remove.*provenance|drop.*provenance'

git grep -n -i -E 'planning|planner|trusted plan|required authority|authority minim|minimi.*authority'

git grep -n -i -E 'semantic|intent|human|employee|phishing|judgement|judgment|benign|malicious'
```

## 2. Exact risky phrases to locate

Search for wording equivalent to:

- "model-level defences only improve utility"
- "model behaviour affects utility but not security"
- "the LLM itself is not trusted for security"
- "the core question is not whether the model can detect malicious instructions"
- "fully compromised" without a property qualifier
- "correct ACS" without acknowledging the formal assumption / deployment granularity distinction
- "modify the ACS" as the only explanation for legitimate blocked tasks
- delegation as generic `ACS_t -> ACS_t+1` if execution-scoped effective policy is intended
- "trusted transformation" or "endorsement" as planned current Conflux work
- "planning" language that implies a plan grants authority
- "maximal utility" / "maximally permissive" without scope qualifiers

## 3. Search scope classification

For each hit, classify it as one of:

1. **Normative current** — must be consistent with ADR-025.
2. **Current research framing/publication** — update interpretation carefully.
3. **Historical archive** — do not edit; optionally add current cross-reference elsewhere.
4. **Related-work description** — preserve accurate description of other literature; do not rewrite history to match Conflux semantics.
5. **Code/test behavior** — only change if prose/comment is stale. If runtime behavior contradicts the new accepted semantics, open/report a separate implementation task rather than silently changing security code.
6. **Evidence artifact** — immutable; do not rewrite retained output.

## 4. Required post-edit consistency checks

Search again and verify:

- no current doc says model-level defences are merely utility;
- no current doc treats a model classification as authority/provenance evidence;
- `ACS_explicit` and `ACS_effective` are defined once and used consistently;
- delegation is never described as provenance removal;
- planner output is never described as authority by itself;
- no current direction proposes endorsement/trusted endorsement;
- classical endorsement mentions are explicitly literature-only;
- SLED scope remains system-level;
- maximality claims are scoped to PE + represented authority;
- runtime delegation status is still accurately "disabled" unless independent implementation work has actually landed.

## 5. Documentation ownership checks

Follow the repo's "one canonical owner" policy:

- ADR-025 owns the rationale/decision.
- `SECURITY_MODEL.md` owns normative security rules.
- `GLOSSARY.md` owns terminology.
- `STATUS.md` owns implementation status.
- `CLAIMS.md` owns claim strength.
- SLED docs own verification verdict semantics.
- research docs own positioning/open questions.
- current manuscript owns publication prose.

Do not paste the same multi-paragraph explanation into all of them.

## 6. Validation commands

Use the repository's current standard validation command. As of the audited snapshot the root README says:

```bash
python scripts/validate.py
```

Also run any documentation/audit-specific checks already wired into that script. If the local repo has changed, follow `AGENTS.md` and `docs/DEVELOPMENT.md` instead of this package's stale command.

If task registry/schema files change, run their deterministic/schema regeneration validation and inspect the diff for unrelated churn.
