# Deep Analysis of the Corpus Papers Most Similar to Conflux

**Date:** 2026-10-09
**Repository:** `/home/raya/projects/Conflux` at HEAD `7d6eb5e` (tree clean at session start)
**Scope:** read-only analysis of `research/reports/analysis/literature_corpus.json`, claim ledger
`docs/evidence/CLAIMS.md`, novelty audit `research/reports/analysis/2026-08-16-novelty-audit.md`,
and key-free metadata/abstract fetches (OpenAlex, Crossref, arXiv Atom) cached under
`.local/similar-papers-cache/` (untracked).
**Status:** research analysis; not a canonical specification; no existing tracked file was modified.

## 1. Scope, selection rule, and evidence depth

### 1.1 Selection rule (exactly as applied)

1. Start from `literature_corpus.json` (schema_version 2, 176 entries). Every entry has a non-empty
   `closest_relation`, so the filter `closest_relation != ""` keeps 176 entries.
2. Exclude Conflux's own entries (`stream == "Conflux"`: `confluxpreprint`, `confluxrepo`,
   `confluxreport`). They are the project's own documents, not similar external work, so they are
   not analysed as prior art; they are listed in the ranking table for completeness.
3. Order the remaining entries by:
   - `novelty_impact.risk_level` in {high, medium} first (high before medium); entries without a
     `novelty_impact` block are ranked after all classified entries;
   - then `adoption_priority` A, B, C, D;
   - then `reading_status == "read"` before `not_started`;
   - tie-break: newer `year` first.
4. Take the first 24 non-self entries (the task requires at least 20). This covers all 11 entries
   whose corpus `risk_level` is high or medium, all A-priority entries above the cut, and the first
   B-priority entries.

The resulting ranked list is in section 1.2. No paper was dropped after selection; every selected
paper has a section in section 2.

### 1.2 Ranked selection

| Rank | Key | risk_level | adoption_priority | reading_status | Year | Stream |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `lomac` | high | A | read | 2000 | Classical security |
| 2 | `myersliskov` | high | A | read | 2000 | Decentralized information-flow control |
| 3 | `biba1977` | high | A | read | 1977 | Integrity / information-flow control |
| 4 | `declassificationsurvey` | medium | A | read | 2009 | Classical security |
| 5 | `attackercontrol` | medium | A | read | 2007 | Classical security |
| 6 | `sabelfeld2003` | medium | A | read | 2003 | Classical security |
| 7 | `denning1976` | medium | A | read | 1976 | Information-flow control foundations |
| 8 | `camel` | medium | B | read | 2025 | System-level agent security |
| 9 | `forge` | medium | D | read | 2026 | Agent policy compiler / provenance |
| 10 | `pact` | medium | D | read | 2026 | Argument-level provenance / capabilities |
| 11 | `progent` | medium | D | read | 2025 | Agent privilege control |
| 12 | `agentdojo` | low | A | read | 2024 | Agent-security benchmark / prompt injection |
| 13 | `nonmalleableifc` | low | A | read | 2017 | Classical security |
| 14 | `robustdeclassification` | low | A | read | 2001 | Information-flow control / attacker influence |
| 15 | `designpatterns` | low | B | read | 2025 | Agent security architecture |
| 16 | `spotlighting` | none | B | read | 2024 | Model-level prompt-injection defence |
| 17 | `struq` | none | B | read | 2024 | Model-level prompt-injection defence |
| 18 | `confluxpreprint` (self, excluded) | none | D | read | 2026 | Conflux |
| 19 | `confluxrepo` (self, excluded) | none | D | read | 2026 | Conflux |
| 20 | `confluxreport` (self, excluded) | none | D | read | 2026 | Conflux |
| 21 | `agentguardian` | - | A | not_started | 2026 | Learned agent access control |
| 22 | `agentrfc` | - | A | not_started | 2026 | Agent protocol formal verification / conformance |
| 23 | `autoformpolicy` | - | A | not_started | 2026 | LLM autoformalization / policy-as-code |
| 24 | `contextualmanipulation` | - | A | not_started | 2026 | Contextual integrity / prompt injection |
| 25 | `solverpolicy` | - | A | not_started | 2026 | Agent policy formalization / SMT runtime checking |
| 26 | `symbolicguardrails` | - | A | not_started | 2026 | Agent symbolic guardrails / benchmark policy analysis |
| 27 | `cedarpaper` | - | A | not_started | 2024 | Authorization language |
| 28 | `flam` | - | A | not_started | 2014 | Authorization + information-flow control |
| 29 | `pbac` | - | A | not_started | 2012 | Provenance-based access control |
| 30 | `text2policy` | - | A | not_started | 2012 | Natural language policy extraction |
| 31 | `ciframework` | - | A | not_started | 2006 | Contextual integrity / formalization |
| 32 | `contextualintegrity` | - | A | not_started | 2004 | Contextual integrity / privacy |
| 33 | `executionhistory` | - | A | not_started | 2003 | History-based access control / privilege attenuation |
| 34 | `agentthread` | - | B | not_started | 2026 | Agent protocol composition / formal verification |
| 35 | `policybank` | - | B | not_started | 2026 | Policy interpretation / agent policy |
| 36 | `cillm` | - | B | not_started | 2025 | Contextual integrity / model alignment |
| 37 | `pinjectiondetect` | - | B | not_started | 2025 | Model-level detection critique |
| 38 | `nl2spec` | - | B | not_started | 2023 | LLM autoformalization / requirements |
| 39 | `fret` | - | B | not_started | 2020 | Controlled requirements / formalization |
| 40 | `abacsurvey` | - | B | not_started | 2017 | Access control / ABAC |

### 1.3 Conflux baseline used by every comparison

Facts below are taken from tracked repository documents (read-only): `docs/reference/SECURITY_MODEL.md`,
`docs/research/RELATED_WORK.md`, `docs/evidence/CLAIMS.md`, `docs/evidence/EVALUATION.md`,
`docs/decisions/025-authority-confinement-semantic-judgement-delegation.md` (ADR-025), and
`research/reports/analysis/2026-08-16-novelty-audit.md`.

- **Principal Context (PC).** ITES conservatively accumulates the authenticated principals whose
  information can influence an execution; PC never shrinks within an execution, alternative branches
  are isolated, and `PC(output) ⊇ PC(execution inputs)` for ordinary derived objects.
- **Authority rule.** An effectful action is permitted only if PC is known and non-empty and every
  principal in PC receives a pointwise allow from the organisation's effective authorisation state
  (`ACS_effective`, i.e. the external ACS plus scoped delegation grants). Intersecting permission sets
  is a meet in the powerset lattice.
- **Arguments.** Trusted operation schemas assign argument roles; authority-bearing selectors
  (destination, recipient, resource, credential reference) are checked pointwise per principal;
  missing roles or unconfigured argument policy deny.
- **Separation.** Provenance is an influence record, not a read ACL; read, visibility, consent,
  action and argument decisions stay independently visible.
- **Fail-closed.** Empty/unknown PC, policy errors, unsupported inputs, stale certificates,
  mismatched categories, provider failure and exhausted bounds deny.
- **Delegation.** Scoped, one-use delegation is modelled and SLED-checked but denied at runtime;
  activation needs independent Cedar parity evidence that does not yet exist.
- **Verification.** SLED is a bounded, finite-model checker over a shared transition kernel; it
  returns minimal counterexamples and has been used to check ITES and simplified abstractions of
  Dual-LLM, CaMeL, Progent, PACT-style defences. Horn 1 ("defence satisfies its own property Q")
  is bounded evidence; non-implication from Q to PE is shown by counterexample, not proved
  unbounded.
- **Confidentiality roadmap.** `docs/evidence/EVALUATION.md` defines Level 1 (read access,
  implemented), Level 2 (observer confinement, proposed) and Level 3 (controlled release /
  declassification, proposed). Only Level 1 is implemented.

### 1.4 Evidence depth legend

| Depth | Meaning |
| --- | --- |
| abstract-level | The fetched external abstract for the *claimed* paper was read in this session (OpenAlex, Crossref or arXiv Atom) and is the source of the external facts below. |
| corpus-level (external verification failed) | The corpus records an earlier reading, but no external source fetched today resolves to the claimed paper. External facts are marked UNVERIFIED and rest on the corpus entry plus local documents only. |

Every external fact below carries the fetch URL used for it. Where the corpus `doi`/`arxiv_id`
resolves to a *different* paper than the corpus title claims, the mismatch is reported and the
corrected identifier is **not** guessed.

### 1.5 Fetch log (recorded, not silently dropped)

- OpenAlex and Crossref DOI lookups were cached per paper under `.local/similar-papers-cache/`.
  404 on `10.1145/363516.363524` (`myersliskov`) from both OpenAlex and Crossref.
- `declassificationsurvey`: `10.3233/JCS-2009-0357` resolves to *Planning and verifying service
  composition* (same journal/year), not to Sabelfeld and Sands. The corpus itself notes this.
- `attackercontrol`: the corpus DOI `10.1109/CSF.2007.22` resolves to *Implementing STV securely in
  Pret a Voter*; the corpus `arXiv:1107.5594` is correct and resolves to *Attacker Control and Impact
  for Confidentiality and Integrity* (corrected DOI: `10.2168/LMCS-7(3:17)2011`). Corrected during
  writing — the first draft of this section wrongly called both identifiers wrong.
- `nonmalleableifc`: the corpus DOI `10.1145/3009837.3009843` resolves to *Cantor meets Scott:
  semantic foundations for probabilistic networks* (ProbNetKAT); the corpus `arXiv:1708.08596` is
  correct (*Nonmalleable Information Flow: Technical Report*) and carries the published DOI
  `10.1145/3133956.3134054` (CCS 2017). Corrected during writing, as above.
- OpenAlex title-search queries (to recover corrected identifiers) returned HTTP 429 for all five
  first-round queries; a Crossref bibliographic-search fallback was run and its outcome is recorded
  in section 1.6.
- arXiv Atom fetches: 16 of 16 first-round requests returned HTTP 200 with a single entry each;
  `agentrfc` was fetched separately from `arXiv:2603.23801` (the alphaxiv URL in the corpus)
  because the corpus `arxiv_id` field is empty.

### 1.6 Identifier defects found and corrected identifiers recovered (evidence-linked)

| Corpus key | Corpus identifier | Resolves today to | Corrected identifier (evidence) |
| --- | --- | --- | --- |
| `myersliskov` | DOI 10.1145/363516.363524 | HTTP 404 at OpenAlex and Crossref | 10.1145/363516.363526, TOSEM 9(4):410-442, 2000 (Crossref title search + DOI record) |
| `declassificationsurvey` | DOI 10.3233/JCS-2009-0357 | *Planning and verifying service composition*, Bartoletti et al., JCS 2009 | 10.3233/JCS-2009-0352, *Declassification: Dimensions and principles*, Sabelfeld & Sands, JCS 17(5):517-548 (Crossref title search + DOI record) |
| `attackercontrol` | DOI 10.1109/CSF.2007.22; arXiv 1107.5594 | the **DOI** resolves to *Implementing STV securely in Pret a Voter*; the **arXiv id is correct** (*Attacker Control and Impact for Confidentiality and Integrity*) | 10.2168/lmcs-7(3:17)2011, LMCS 7(3:17), 2011, Askarov & Myers (Crossref title search + DOI record; arXiv record confirms the same paper) |
| `nonmalleableifc` | DOI 10.1145/3009837.3009843; arXiv 1708.08596 | the **DOI** resolves to *Cantor meets Scott: semantic foundations for probabilistic networks* (ProbNetKAT); the **arXiv id is correct** (*Nonmalleable Information Flow: Technical Report*, v2) | 10.1145/3133956.3134054, CCS 2017:1875-1891, Cecchetti, Myers & Arden (Crossref title search + DOI record; the arXiv record carries the same DOI); only the corpus venue "POPL 2017" and the DOI are wrong |
| `robustdeclassification` | no identifier recorded | n/a | 10.1109/CSFW.2001.930133, CSFW 2001:15-23, Zdancewic & Myers (Crossref title search + DOI record) |
| `biba1977` | no identifier recorded | n/a | none recovered: DTIC ADA039107 page HTTP 403, ResearchGate HTTP 403 (recorded, not guessed) |

These defects do not change the novelty analysis (the mechanism descriptions in the corpus match the
corrected papers on the points used), but they must be fixed before any citation goes into the paper.
## 2.1 `lomac` - LOMAC (Low Water-Mark integrity in COTS kernels)

**Identity.** key `lomac`; DOI `10.1109/SECPRI.2000.848460`; IEEE Symposium on Security and Privacy 2000, pp. 230-245; author T. Fraser (Crossref). OpenAlex records the same DOI with publication year 2002; the venue/author/pages below come from the Crossref record. 
**Evidence depth: abstract-level.** Fetched 2026-10-09: OpenAlex `https://api.openalex.org/works/doi:10.1109/secpri.2000.848460` (abstract reconstructed from `abstract_inverted_index`) and Crossref `https://api.crossref.org/works/10.1109/secpri.2000.848460`. Cache: `openalex-lomac.json`, `crossref-lomac.json`. Mechanism facts outside the abstract (label creep as the primary concern, dynamic demotion discipline) come from the corpus entry `lomac` and are marked corpus-level.

**Mechanism (what it actually does).** A dynamically loadable extension to commercial off-the-shelf Linux kernels that implements Low Water-Mark access control: a kernel-resident integrity policy under which observing lower-integrity data lowers the subject's effective integrity, so that the subject can no longer write to higher-integrity objects. The paper classifies access-control models by their compatibility with COTS practice, argues that low-water-mark-like models are especially compatible, and reports practical strategies for the model's pathological cases, including a small extension of the model.

**Security property and threat model.** The enforced property is integrity of high-integrity objects against modification by lower-integrity processes or data, enforced by a kernel-resident reference monitor. The threat model is untrusted local code and untrusted data on a general-purpose operating system, including code that runs with the user's own account; there is no notion of an organisation's authorisation relation, and no per-action or per-argument authority.

**Assumptions and stated limits.** Scalar, system-wide integrity labels rather than principal identities; a global classification rather than action-specific permissions; enforcement only inside the OS mediation boundary; utility loss from label creep is an accepted engineering cost; the paper's own framing is compatibility-driven adoption rather than maximal assurance. No delegation, no consent, no argument-role semantics, no proof tooling, and no bounded verification of the monitor.

**How Conflux differs, concretely.** LOMAC demotes a process to a global low level; Conflux keeps a per-execution set of authenticated principals and intersects their permissions for each specific action and authority-bearing argument, so the same contaminated execution can still be permitted for action A and denied for action B. LOMAC needs kernel modification for a syscall-level mediation boundary; Conflux mediates at the tool/effect boundary and assumes authenticated provenance adapters and a correct ACS instead. LOMAC treats contamination as a property of a process; Conflux makes it a property of the data object, propagates it through nested model, plan, and tool execution without a silent reset, isolates alternative branches, denies on empty/unknown PC, and re-checks an exact decision certificate at execution time. Conflux also carries a bounded finite-model check (SLED) of its own monitor, which LOMAC argued for empirically by deployment experience.

**Novelty threat.** A1 ("authority decreases monotonically as influence accumulates") is the claim at risk: LOMAC already operationalises exactly that mechanism (demotion on observation, restricted future effects) in a commodity OS. A8 ("influence is never silently removed by nested execution") is also at risk as a novelty claim, because conservative, non-resetting contamination is standard low-water-mark behaviour. Conflux's distinguishable content is that the "level" is a set of authenticated principals whose *existing* ACS permissions are intersected per action and argument, and that PC survives nested LLM/plan/tool execution. **Verdict: conflict for A1 as an unqualified novelty claim; qualification needed for A1 as a theorem framing and for A8 as a contribution statement.**

**Cited external facts.** Kernel-resident LWM protection, kernel extension, compatibility classification, pathological-case extensions: Crossref abstract `https://api.crossref.org/works/10.1109/secpri.2000.848460` (also OpenAlex `https://api.openalex.org/works/doi:10.1109/secpri.2000.848460`). Author/venue/pages: Crossref. Label creep and dynamic-demotion engineering framing: corpus entry `lomac` (corpus-level, not verified against full text in this session).

## 2.2 `myersliskov` - Decentralized Label Model / Jif (Myers & Liskov)

**Identity.** key `myersliskov`; corrected DOI `10.1145/363516.363526`; ACM Transactions on Software Engineering and Methodology 9(4):410-442, 2000; authors Andrew C. Myers and Barbara Liskov (Crossref). The corpus DOI `10.1145/363516.363524` returns HTTP 404 at both OpenAlex and Crossref. 
**Evidence depth: abstract-level for the corrected DOI.** Fetched 2026-10-09: Crossref `https://api.crossref.org/works/10.1145/363516.363526` (abstract present); corrected identifier found by Crossref bibliographic title search. Cache: `crossref-fix-myersliskov.json`, `cr-search-myersliskov_fix.json`, and the two 404 error records `openalex-myersliskov.error.txt`, `crossref-myersliskov.error.txt`. Corpus-level additions from the corpus entry are marked as such.

**Mechanism (what it actually does).** The decentralized label model (DLM): an information-flow label is a set of owner-to-reader policies, so no central authority owns all labels and data owners can change readers of their own data ("decentralised declassification"). Programs are statically certified to permit only acceptable flows, which avoids most run-time checking; DLM is implemented in Jif, a Java extension providing static checking (as the fetched abstract states).

**Security property and threat model.** End-to-end confidentiality and integrity of data in systems with mutual distrust and decentralised authority, including programs containing untrusted code. The threat model is an untrusted or mutually distrusting program component that could otherwise leak or corrupt data; the property is enforced by static analysis of a typed program, not by a run-time reference monitor on effects, and not relative to an organisation's ACS.

**Assumptions and stated limits.** Requires typed or otherwise statically analysable programs with principal annotations, and a trusted type system/compiler; declassification is authorised by data owners and readers rather than by enterprise policy; no action or argument authority; no model of an opaque, probabilistically behaving component. The corpus entry adds that a direct port of DLM to LLM agents would either overtaint aggressively or need trusted semantic abstractions around model calls (corpus-level).

**How Conflux differs, concretely.** DLM proves a static property of a well-typed program; Conflux treats the language model as an opaque influence amplifier and mediates effects, and it derives authority dynamically from the organisation's existing ACS per action and per authority-bearing argument. DLM has no ACS, no action/argument granularity, and no notion of an execution certificate re-checked at effect time. Conflux never assumes the model's internal flows are typed or interpretable; DLM never assumes an external authorisation relation. The two mechanisms are therefore complementary in kind: DLM constrains the flow inside a program; Conflux bounds the authority of an execution whose proposal generator is untrusted.

**Novelty threat.** A2 ("provenance-based enforcement that derives effective authority from provenance and existing access-control policies") and A11 (the ITES-versus-IFC positioning claim). The *principal-sensitive* element of Conflux is not new: DLM already carries principal identities in labels and gives those principals decentralised declassification authority. What survives is the derivation of action authority from an existing ACS and the effect-level mediation argument. Any sentence that presents "retaining principal identities rather than scalar labels" as a Conflux innovation is in conflict with DLM; the claim is defensible only with the ACS-derivation qualifier. **Verdict: qualification needed (A2, A11).**

**Cited external facts.** DLM label structure, statically certified flows, Jif implementation, decentralised declassification: Crossref abstract `https://api.crossref.org/works/10.1145/363516.363526`. Title/venue/pages/authors: same record. Corpus DOI 404s: `https://api.openalex.org/works/doi:10.1145/363516.363524`, `https://api.crossref.org/works/10.1145/363516.363524` (both cached as error files).

## 2.3 `biba1977` - Biba integrity model (low-water-mark lineage)

**Identity.** key `biba1977`; no DOI or arXiv identifier in the corpus; venue recorded as MITRE Technical Report MTR-3153 (ESD-TR-76-372), 1977; corpus `source_url` is a ResearchGate landing page. 
**Evidence depth: corpus-level (no external source fetched).** External verification attempted 2026-10-09 and failed: DTIC citation page `https://apps.dtic.mil/sti/citations/ADA039107` returned HTTP 403, ResearchGate `https://www.researchgate.net/publication/235043659_Integrity_Considerations_for_Secure_Computer_Systems` returned HTTP 403. Cache: `fetch-log-biba.json`. The corpus entry itself records `verified.notes` = "Needs citation verification before publication". **Every mechanism statement below is UNVERIFIED externally** and is quoted from the corpus entry, `docs/research/RELATED_WORK.md`, and the novelty audit, all local documents.

**Mechanism (what it actually does).** (UNVERIFIED externally; as recorded locally.) A family of mandatory integrity policies, including low-water-mark variants: a subject that observes lower-integrity information has its effective integrity reduced and its future high-integrity effects restricted. Integrity is treated as the dual of multilevel confidentiality, with security levels over subjects and objects.

**Security property and threat model.** (UNVERIFIED externally; as recorded locally.) Protection of high-integrity objects from improper modification by lower-integrity subjects or data; the threat model is contamination of trusted state through untrusted inputs; no principal-specific organisational permissions.

**Assumptions and stated limits.** (UNVERIFIED externally; as recorded locally.) Coarse security levels over system subjects and objects; no principal identities; no action or argument granularity; no delegation, consent, or effect-level certificates; the corpus entry itself notes that Principal Context is more identity/permission-specific than a scalar integrity lattice but that "the contamination intuition is not new".

**How Conflux differs, concretely.** Conflux keeps the low-water-mark shape but replaces the global scalar level with a set of authenticated principals and the meet of their *actual permissions in the organisation's ACS*, evaluated separately for each action and authority-bearing argument. Conflux also states where the analogy stops: it does not claim a new monotonicity idea, and it has no endorsement/trusted-transformation mechanism (a Biba/managed-integrity-style upgrade is explicitly future work under ADR-025). Conversely, Biba is a mandatory policy over a fixed lattice and needs no authentication or provenance infrastructure; Conflux's guarantee is conditional on authenticated provenance and a correct ACS.

**Novelty threat.** A1 is the direct descendant of Biba low-water-mark contamination, and the novelty audit already classifies A1 as "partially anticipated". A2 and A8 inherit the same lineage at one remove. The actionable threat is not analytical but citation-level: the report cannot cite the MITRE report on the strength of this session, and the corpus flags it as unverified. The wording risk is a novelty statement such as "ITES introduces the idea that consuming untrusted information should reduce future authority", which the audit lists as unsafe. **Verdict: qualification needed (A1, A2, A8); additionally, citation verification is required before publication.**

**Cited external facts.** All Biba mechanism statements above are corpus/doc-level and UNVERIFIED externally in this session (`research/reports/analysis/literature_corpus.json` entry `biba1977`; `research/reports/analysis/2026-08-16-novelty-audit.md`, section A1; `docs/research/RELATED_WORK.md`). Failed fetches recorded in `.local/similar-papers-cache/fetch-log-biba.json`.

## 2.4 `declassificationsurvey` - Dimensions and Principles of Declassification (Sabelfeld & Sands)

**Identity.** key `declassificationsurvey`; corrected DOI `10.3233/JCS-2009-0352`; *Declassification: Dimensions and principles*, Journal of Computer Security 17(5):517-548, 2009; authors Andrei Sabelfeld and David Sands (Crossref). The corpus DOI `10.3233/JCS-2009-0357` resolves to a different article, *Planning and verifying service composition* (Bartoletti, Degano, Ferrari; JCS 2009, 799-837), and the corpus page range (609-655) also differs from the Crossref record. 
**Evidence depth: metadata-level (identity verified; Crossref carries no abstract for this DOI).** Fetched 2026-10-09: Crossref bibliographic title search `https://api.crossref.org/works?query.bibliographic=Dimensions+and+Principles+of+Declassification` and DOI record `https://api.crossref.org/works/10.3233/jcs-2009-0352`. Cache: `cr-search-declassificationsurvey_fix.json`, `crossref-fix-declassificationsurvey.json`. The mismatch of the corpus DOI is also visible in `openalex-declassificationsurvey.json` and `crossref-declassificationsurvey.json`. Content statements below rest on the corpus entry (corpus-level) because no abstract was fetched.

**Mechanism (what it actually does).** (Corpus-level.) A taxonomy and set of principles for declassification in information-flow systems: what information may be released, who may authorise the release, where in the system release may occur, and when it is permitted, together with security conditions such as noninterference modulo declassification and intransitive noninterference. The framework is conceptual: it classifies release mechanisms rather than embedding one in a system.

**Security property and threat model.** The property under study is a controlled, legitimate relaxation of confidentiality: a system that must release secret-derived information is secure only if the release is bounded by an explicit policy dimension; the threat model is an attacker who can observe releases, including through indirect channels, and the framework asks when a release can still be considered safe.

**Assumptions and stated limits.** A conceptual framework, not a mechanism for tool-using agents; no organisation ACS; no authenticated principal provenance; no treatment of attacker-influenced release decisions from untrusted content. Conflux has not implemented controlled release: `docs/evidence/EVALUATION.md` defines Level 3 (controlled release/declassification) as proposed, with Level 1 (read access) the only implemented level.

**How Conflux differs, concretely.** The dimensions map onto Conflux's visibility and disclosure design: "what" maps to field/event classes, "who" to the release authority, "where" to the disclosure point, and "when" to the policy state at effect time. Conflux adds an enforcement substrate (a monitor that decides the release per event class and projects records by audience) and an influence condition (which principals may influence the release decision), but it has implemented only Level 1. The taxonomy frames the design; it does not provide the agent-specific enforcement or the influence condition.

**Novelty threat.** A10 ("authorised reads do not establish noninterference") is described in the novelty audit as a non-claim that survives; this survey supports that framing rather than threatening it, because it is the standard source for the distinction between access safety and release policy. The real exposure is the opposite direction: the paper must not present visibility confinement or disclosure semantics as new, and the proposed Levels 2-3 must be described as instantiations of a classical declassification taxonomy with explicit release authority and robust-influence conditions. **Verdict: none for A10 (it is an explicit non-claim); qualification needed for the proposed visibility/disclosure roadmap.**

**Cited external facts.** Corrected identity, venue, pages, authors: Crossref `https://api.crossref.org/works/10.3233/jcs-2009-0352` and the title search. Corpus DOI mismatch: `https://api.openalex.org/works/doi:10.3233/jcs-2009-0357`, `https://api.crossref.org/works/10.3233/jcs-2009-0357` (cache files `openalex-declassificationsurvey.json`, `crossref-declassificationsurvey.json`). Taxonomy content: corpus entry `declassificationsurvey` (corpus-level).

## 2.5 `attackercontrol` - Attacker Control and Impact for Confidentiality and Integrity (Askarov & Myers)

**Identity.** key `attackercontrol`; corrected DOI `10.2168/lmcs-7(3:17)2011`; Logical Methods in Computer Science 7(3:17), 2011 (journal extension of the CSF 2007 paper); authors Aslan Askarov and Andrew Myers (Crossref). The corpus **arXiv id `1107.5594` is correct** (it resolves to *Attacker Control and Impact for Confidentiality and Integrity*, the LMCS version of the paper); the corpus **DOI `10.1109/CSF.2007.22` is wrong** and resolves to *Implementing STV securely in Pret a Voter*.
**Evidence depth: abstract-level (corrected DOI record with abstract; arXiv record for the same paper).** Fetched 2026-10-09: Crossref `https://api.crossref.org/works/10.2168/lmcs-7(3:17)2011` (abstract present) after a bibliographic title search, arXiv Atom `http://export.arxiv.org/api/query?id_list=1107.5594`, and the mismatched corpus DOI record (`crossref-attackercontrol.json`). Cache: `crossref-fix-attackercontrol.json`, `cr-search-attackercontrol_fix.json`. Definitions beyond the abstract (attacker control as a set of similar attacks, robust declassification as release control within attacker control, checked endorsement) are corpus-level.

**Mechanism (what it actually does).** A semantic framework for specifying what security is guaranteed when a program uses declassification (relaxing confidentiality) and endorsement (relaxing integrity). Security is characterised by attacker influence: attacker control describes what the attacker can learn from a program's observable effects, and attacker impact describes the attacker's influence on trusted locations. The framework yields security conditions for checked endorsement and for robust integrity, recovers and improves on the notions of robustness and qualified robustness, and is soundly enforced by a security type system.

**Security property and threat model.** Security of programs that deliberately relax IFC policies: releases are safe only if the attacker cannot choose which release occurs, and integrity is robust only if the attacker cannot influence which trusted events occur. The threat model is an attacker who supplies or controls low-integrity code and observes low-level outputs, in a security-typed language.

**Assumptions and stated limits.** Program-level and type-system-level; scalar security levels rather than named principal identities; no organisation ACS; no LLM or prompt injection; no runtime mediation of tool effects. The corpus entry adds that checked endorsement is the closest classical analogue to scoped delegation, but it endorses variable values rather than principal authority (corpus-level).

**How Conflux differs, concretely.** Conflux's exceptions to monotonicity (delegation, disclosure, consent) are exactly the places where robustness conditions matter, and this framework supplies the classical vocabulary for them. But the objects differ: checked endorsement upgrades the trust of a value; Conflux delegation is bounded by the issuer actually holding the permission, by scope, ordering, expiry, revocation and one-use consumption, and is currently disabled at runtime. Conflux has no endorsement operation at all, so it currently has no attacker-controlled downgrade of PC. Where this paper proves type-system soundness for a language, Conflux only bounds a finite IR model (SLED) and assumes authenticated provenance plus a correct ACS.

**Novelty threat.** A1 and A8 (monotonic authority reduction and non-silent removal of influence): the framework formalises the strong version of "attacker influence must not decide what is released or upgraded", so any formulation of Conflux's exceptions (delegated grants and the proposed disclosure levels) as a new *idea* conflicts; the defensible formulation is that Conflux applies such influence conditions to principal authority derived from an existing ACS. A14 (delegation is not endorsement) is *supported*: endorsement changes the integrity status of information, delegation changes authority, and the paper's own treatment keeps them distinct. A10 (authorised reads do not establish noninterference) is reinforced by the robust-declassification line of work. **Verdict: qualification needed (A1, A8; A14 supported, A10 reinforced).**

**Cited external facts.** Two notions (attacker control/impact), conditions for checked endorsement and robust integrity, type-system enforcement, relation to robustness and qualified robustness: Crossref abstract `https://api.crossref.org/works/10.2168/lmcs-7(3:17)2011`. Identity/venue/authors: same record. Mismatched corpus identifiers: `https://api.crossref.org/works/10.1109/csf.2007.22`, `http://export.arxiv.org/api/query?id_list=1107.5594`. Detailed definitions: corpus entry `attackercontrol` (corpus-level).

## 2.6 `sabelfeld2003` - Language-Based Information-Flow Security (Sabelfeld & Myers survey)

**Identity.** key `sabelfeld2003`; DOI `10.1109/JSAC.2002.806121`; IEEE Journal on Selected Areas in Communications 21(1):5-19, 2003; authors A. Sabelfeld and A. C. Myers (Crossref). 
**Evidence depth: abstract-level.** Fetched 2026-10-09: Crossref `https://api.crossref.org/works/10.1109/JSAC.2002.806121` and OpenAlex `https://api.openalex.org/works/doi:10.1109/jsac.2002.806121`. Cache: `crossref-sabelfeld2003.json`, `openalex-sabelfeld2003.json`. The vocabulary mapping used below (explicit/implicit flows, overapproximation, security provenance vs exposure vs attribution) is the corpus entry's reading of the survey (corpus-level).

**Mechanism (what it actually does).** A survey of three decades of language-based information-flow security, focused on static program analysis for enforcing information-flow policies; it gives a structured view of the field, states that conventional access control and encryption do not directly enforce information-flow policies, and identifies open challenges.

**Security property and threat model.** End-to-end confidentiality: secret input data cannot be inferred by an attacker from observations of system output. The threat model is an attacker who observes the program's outputs (including covert and implicit channels) and tries to infer secrets; the enforcement target is the program's whole behaviour, not individual accesses.

**Assumptions and stated limits.** Language-based and mostly static; not a system-level mediator; no organisation ACS; no LLM or prompt injection; the survey is a taxonomy, not a mechanism. The corpus entry adds that a direct application to LLM agents would need a definition of "influence" that is deliberately conservative (corpus-level).

**How Conflux differs, concretely.** Conflux uses this survey's vocabulary rather than its enforcement technique. Conflux's Principal Context is an intentional overapproximation in the survey's sense: if information from a principal reaches an execution, that principal may influence the output. Unlike a type system, Conflux does not analyse the program (an LLM proposes it); it mediates effects and derives authority from the ACS. The project separates security provenance (the conservative enforcement input), exposure measurement (empirical), and attribution (best-effort) — a separation the survey's soundness/precision framing supports.

**Novelty threat.** A8 (provenance monotonicity / influence never silently removed): conservative label and flow propagation is the survey's standard practice, so the claim must be stated as an instantiation for nested agent execution, not as a new idea. A11: the survey is the canonical citation that "ITES is inspired by IFC" and therefore belongs in the positioning paragraph. A5 is unaffected: the survey's attacker model has no notion of a model that may be arbitrarily malicious while the enforcement layer stays sound. **Verdict: qualification needed (A8, A11).**

**Cited external facts.** Survey scope, three decades of research, static-analysis focus, access-control limitation: Crossref abstract `https://api.crossref.org/works/10.1109/JSAC.2002.806121` (also OpenAlex `https://api.openalex.org/works/doi:10.1109/jsac.2002.806121`). Vocabulary mapping: corpus entry `sabelfeld2003` (corpus-level).

## 2.7 `denning1976` - A Lattice Model of Secure Information Flow

**Identity.** key `denning1976`; DOI `10.1145/360051.360056`; Communications of the ACM 19(5):236-243, 1976; author Dorothy E. Denning (Crossref). 
**Evidence depth: abstract-level.** Fetched 2026-10-09: Crossref `https://api.crossref.org/works/10.1145/360051.360056` and OpenAlex `https://api.openalex.org/works/doi:10.1145/360051.360056`. Cache: `crossref-denning1976.json`, `openalex-denning1976.json`.

**Mechanism (what it actually does).** A mathematical framework for secure information flow in which security classes form a lattice derived from the semantics of information flow; the lattice properties give concise formulations of the security requirements of different systems, support classification of systems by objective, and lead to automatic program-certification mechanisms that verify secure flow.

**Security property and threat model.** Secure information flow relative to a flow relation permitted by the lattice partial order; the threat model is a system in which information can flow between classes in ways that violate the policy, and the model's contribution is a unifying algebra for those requirements plus certification of programs.

**Assumptions and stated limits.** Centralised, coarse security classes; no named principals, no organisational ACS, no action or argument permissions; certification is program-level; no run-time monitor for agent effects.

**How Conflux differs, concretely.** Conflux's authority meet over permission sets is the same algebra with different lattice elements: the elements are per-principal, per-action permission sets rather than data classes, and the order is set inclusion. Conflux must therefore not present monotone intersection as a new mathematical idea; its contribution is what the elements are and where the intersection is evaluated (an execution with authenticated principal provenance, mediated at effect time). Conversely, Denning gives no principal identity, no policy source, and no notion of a model proposing effects.

**Novelty threat.** A1 and, transitively, A2: the lattice/meet structure of authority reduction is classical. The specific unsafe wording the novelty audit already lists — "Conflux is the first generalisation of Biba to arbitrary permission sets" — remains unsafe on this evidence: the permission-set meet is the standard powerset-lattice operation, and this session did not find or exclude a prior system that computes it over named principals (see section 4, watchlist: FLAM, PBAC, execution-history access control). **Verdict: qualification needed (A1, A2); A15(2) stays a hypothesis, not an established contribution.**

**Cited external facts.** Lattice framework, certification mechanisms, classification of systems: Crossref abstract `https://api.crossref.org/works/10.1145/360051.360056` (also OpenAlex `https://api.openalex.org/works/doi:10.1145/360051.360056`). Authority-intersection framing: `docs/research/RELATED_WORK.md`, corpus entry `denning1976`.

## 2.8 `camel` - CaMeL: Defeating Prompt Injections by Design

**Identity.** key `camel`; arXiv `2503.18813` (v2); arXiv preprint, 2025; Google Research (fetched Atom metadata). 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2503.18813`. Cache: `arxiv-camel.xml`. Conflux-side comparison to the CaMeL abstraction rests on `research/output/runs/defence-models-v1/result.json` (local, read-only) and `docs/evidence/defence-model-fidelity.json`.

**Mechanism (what it actually does).** A protective system layer around an untrusted LLM: the system explicitly extracts control and data flows from the *trusted* user query, so untrusted retrieved data can never affect the program flow; a notion of capability prevents exfiltration of private data over unauthorised data flows by enforcing security policies when tools are called. Reported: 77% of AgentDojo tasks solved with "provable security" versus 84% for the undefended system.

**Security property and threat model.** Model-independent security of the agent architecture under the stated assumptions: untrusted data cannot steer control flow, and tool calls are checked against capability policies. The threat model is indirect prompt injection with a possibly fully attacker-controlled model; the LLM is untrusted, the planning/control extraction and the policy are trusted.

**Assumptions and stated limits.** Trusted control/data-flow extraction from the query, and trusted application policy, are inside the TCB; data-dependent planning can lose utility (the paper's 77% vs 84% gap); capability policies are application-defined, not derived from an organisation's existing ACS; policy completeness is external to the proof. Conflux's own bounded experiment on a CaMeL abstraction finds that its native property can hold while the PE property fails (`defence-models-v1`), but that result is a finite, unvalidated abstraction and must be reported as non-implication, not as a claim about the real system.

**How Conflux differs, concretely.** CaMeL keeps untrusted information out of control flow by construction and uses capability policies to block exfiltration; Conflux assumes untrusted content may be maximally influential, keeps no trusted planner, records which principals influenced the execution, and intersects their *existing ACS* permissions for each action and authority-bearing argument. CaMeL's trusted-query/control-extraction step has no Conflux analogue; Conflux's principal-sensitive ACS derivation has no CaMeL analogue. Both architectures are reference-monitor architectures around an untrusted model, so the architectural pattern is not a Conflux novelty.

**Novelty threat.** A4 (ITES prevents privilege escalation regardless of how influence was introduced): the claim survives as an instance of complete mediation but not as a new architecture; CaMeL already provides a model-independent guarantee under stronger assumptions about the trusted query. A13 (privilege escalation as the right system-level objective): defensible as a framing, but CaMeL and the capability literature already frame the failure as unauthorised data flow/tool use, so "first to reframe injection" would conflict. A9 is not threatened: CaMeL is a defence, SLED is a bounded checker; the Conflux-specific evidence is the non-implication experiment, not the checked property itself. **Verdict: qualification needed (A4, A13); none for A9.**

**Cited external facts.** Control/data-flow extraction, capabilities, provable security result, 77%/84% figures: arXiv abstract `https://arxiv.org/abs/2503.18813` (Atom fetch cached). Non-implication experiment: `research/output/runs/defence-models-v1/result.json` (bounded, finite IR, unvalidated abstraction; fidelity recorded in `docs/evidence/defence-model-fidelity.json`).

## 2.9 `forge` - FORGE: formal policy enforcement for agentic systems

**Identity.** key `forge`; arXiv `2602.16708` (v3); the fetched title is *Formal Policy Enforcement for Real-World Agentic Systems*, while the corpus records the title *Policy Compiler for Secure Agentic Systems / FORGE* (version/title mismatch; corpus venue "FORGE/PCAS implementation"). 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2602.16708`. Cache: `arxiv-forge.xml`.

**Mechanism (what it actually does).** Policy enforcement for agentic systems treated as a cross-cutting concern, expressed with aspect-oriented programming: policies are written in Datalog over abstract predicates that describe the execution context, an observability service governed by a formal assume/guarantee contract maintains those predicates, and a reference monitor consults the policy at each action to produce an enforcement decision. When the environment contract holds, the enforced decisions coincide with the policy's intended semantics. The motivation is that system-prompt policy text admits no formal enforcement guarantee and cannot express history-dependent policies.

**Security property and threat model.** Conformance to a formally stated policy over execution history, enforced deterministically at each policy-relevant decision, conditional on the observability contract. The threat model is an agent (or multi-agent system) whose reasoning may violate the stated policy; the policy itself is an input, not a proved artefact.

**Assumptions and stated limits.** The guarantee is conditional on complete observability/instrumentation and on a correct extracted policy; policy intent stays external to the framework; predicates are only as good as the contract that maintains them; no authority relation derived from an organisation's existing ACS and no notion of authenticated influencing principals.

**How Conflux differs, concretely.** FORGE decides from Datalog facts about the execution; Conflux decides by intersecting the *actual ACS permissions* of every authenticated principal that influenced the execution, separately for the action and its authority-bearing arguments. FORGE's "policy" is a bespoke Datalog artefact whose correspondence to intent is assumed; Conflux's policy source is the organisation's existing authorisation relation. FORGE gives an assume/guarantee contract for observability; Conflux gives an authenticated-provenance assumption plus a bounded finite-model check of the monitor itself. Conversely, FORGE's expressiveness over causal history goes beyond what Conflux's current monitors encode.

**Novelty threat.** A4: history-sensitive, model-independent deterministic enforcement with a reference monitor is prior art, so ITES must be positioned as the principal-sensitive instantiation, not as a new enforcement architecture. A9: SLED's novelty cannot lie in "formally checking agent defence behaviour" in general — FORGE gives a formal enforcement guarantee and an observability contract; the defensible SLED contribution is the specific PE/defence semantics, the shared transition kernel, and the defence-model reductions. A15(2) (authority derived from the organisation's current ACS) is now the load-bearing distinction against FORGE and must be stated precisely in the related-work section. **Verdict: qualification needed (A4, A9); A15(2) remains a hypothesis that needs the explicit contrast.**

**Cited external facts.** Cross-cutting AOP enforcement, Datalog policies over abstract predicates, observability contract, reference monitor, coincidence with intended semantics: arXiv abstract `https://arxiv.org/abs/2602.16708` (Atom fetch cached).

## 2.10 `pact` - PACT: argument-level provenance and capability contracts

**Identity.** key `pact`; arXiv `2605.11039` (v1); title as fetched: *The Granularity Mismatch in Agent Security: Argument-Level Provenance Solves Enforcement and Isolates the LLM Reasoning Bottleneck*; 2026. Corpus venue is "PACT monitor". 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2605.11039`. Cache: `arxiv-pact.xml`.

**Mechanism (what it actually does).** A runtime monitor that assigns semantic roles to tool arguments, tracks value provenance across replanning steps, and checks whether each argument's origin satisfies its role-specific trust contract. The paper's premise is that injection becomes dangerous when untrusted content determines an authority-bearing argument rather than merely appearing in context. Reported: with oracle provenance, 100% utility and 100% security on mixed-trust diagnostic suites where flat invocation-level monitors incur false positives or false negatives; in AgentDojo across five models it reaches 100% security on the three strongest models.

**Security property and threat model.** Per-argument, role-specific trust enforcement with cross-step provenance: an argument may carry a value only if the value's origin satisfies the contract for that role. The threat model is indirect prompt injection steering argument values (destinations, commands, recipients) of tool calls while the model remains untrusted.

**Assumptions and stated limits.** Provenance inference, role/contract synthesis, and semantic ambiguity remain bottlenecks; not every harm is an argument-provenance harm; the strongest diagnostic result is stated under oracle provenance; utility/security on weaker models is lower; contracts are per-role policy artefacts rather than an organisation-wide authority relation.

**How Conflux differs, concretely.** PACT grades argument origins against role-specific trust contracts; Conflux requires the *conjunction of pointwise ACS allows for every influencing principal* on the action and on each authority-bearing argument, and denies when a role or argument policy is missing. PACT's "who may satisfy this argument" is local policy; Conflux's is the organisation's existing ACS. The shared idea — trusted roles for arguments, enforced deterministically — is now prior art; Conflux's distinct element is that argument values are bound to principal authority, not to a graded trust level, and that the same mechanism covers action, argument, read, visibility and consent decisions with one certificate.

**Novelty threat.** A6 ("authority-bearing action arguments cannot borrow authority from content or consent") is directly anticipated in its general form: PACT builds an enforcement mechanism precisely on argument-level provenance and role contracts. The surviving specificity is the pointwise Principal check against an existing ACS plus fail-closed semantics for missing roles/policies, which the corpus already lists as the implemented fourth-year contribution. A15(3) ("parameterised and argument-sensitive action authority" as a candidate distinction) should no longer be presented as a candidate novelty: it is now a contested space with a 2026 direct neighbour. **Verdict: qualification needed (A6); A15(3) downgraded from candidate distinction to contested prior art.**

**Cited external facts.** Semantic argument roles, cross-step provenance, role-specific trust contracts, oracle-provenance diagnostic results, AgentDojo five-model result: arXiv abstract `https://arxiv.org/abs/2605.11039` (Atom fetch cached).

## 2.11 `progent` - Progent: privilege control for LLM agents

**Identity.** key `progent`; arXiv `2504.11703` (v3); fetched title *Progent: Securing AI Agents with Privilege Control*; the corpus records *Progent: Programmable Privilege Control for LLM Agents* (version/title mismatch). 2025. 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2504.11703`. Cache: `arxiv-progent.xml`.

**Mechanism (what it actually does).** Privilege represented as a security policy of symbolic rules over tool names and arguments; every tool call is checked against the policy by a deterministic procedure, enforcing least privilege. An LLM generates the initial policy from the user's task and updates it during execution as new information arrives; an SMT solver classifies each proposed update as a narrowing (applied automatically) or an expansion (requiring explicit approval).

**Security property and threat model.** Task-scoped least privilege on tool invocations, enforced deterministically per call, with policy evolution controlled by solver-backed narrowing/expansion classification. The threat model is indirect prompt injection that triggers unauthorised or unnecessary tool calls; the policy text is generated by the untrusted-origin model, but enforcement is symbolic.

**Assumptions and stated limits.** The generated policy can be semantically wrong; allowed-but-harmful calls, free-form argument harms and natural-language harms remain possible; the policy source is the model plus the task text, not an organisational ACS; no authenticated principal provenance; no unbounded guarantee.

**How Conflux differs, concretely.** Progent derives "what is allowed" from a model-generated, SMT-classified policy; Conflux derives it from the organisation's persistent ACS and gives model proposals no authority effect. Progent auto-applies narrowing and requires approval for expansion; Conflux models expansion as delegation that is denied at runtime until independent policy-parity evidence exists, with issuer/beneficiary/scope/one-use gates. Progent has no principal set and no influence history; Conflux's decision is a function of which principals influenced the execution. Both check tool-call arguments deterministically, so that alone is not a Conflux novelty.

**Novelty threat.** A4 (ITES prevents privilege escalation) and A6 (arguments cannot borrow authority): deterministic, argument-sensitive privilege control for tool calls is prior art, and the audit already states that this "invalidates broad novelty claims around privilege control". A13: a wording such as "first to treat prompt injection as privilege escalation" conflicts with Progent's least-privilege framing; the defensible claim is about the *objective and its reference relation* (non-escalation relative to the organisation's ACS), not about the observation that injection ends in tool calls. **Verdict: qualification needed (A4, A6, A13).**

**Cited external facts.** Symbolic argument-sensitive rules, deterministic per-call checks, LLM-generated policy, SMT-classified narrowing vs expansion with approval: arXiv abstract `https://arxiv.org/abs/2504.11703` (Atom fetch cached).

## 2.12 `agentdojo` - AgentDojo: dynamic evaluation environment for prompt-injection attacks and defences

**Identity.** key `agentdojo`; arXiv `2406.13352` (v3); 2024; also a NeurIPS 2024 Datasets and Benchmarks paper (corpus `source_url`). 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2406.13352`. Cache: `arxiv-agentdojo.xml`. Conflux-side claims about annotated runs: `docs/evidence/CLAIMS.md` (rows on AgentDojo integration and utility) and `research/output/runs/agentdojo-7b-v5/`.

**Mechanism (what it actually does).** An extensible evaluation framework for agents that execute tools over untrusted data: 97 realistic tasks (email, e-banking, travel booking), 629 security test cases, and implementations of attack and defence paradigms from the literature; deliberately not a static test suite, so new tasks, defences and adaptive attacks can be added. The authors report that state-of-the-art LLMs fail many tasks even without attacks and that existing attacks break some security properties but not all.

**Security property and threat model.** Empirical measurement of agent utility and attack success; no formal property and no proof. The threat model is indirect prompt injection where tool-returned data hijacks the agent; the benchmark's security test cases define the concrete success/failure conditions.

**Assumptions and stated limits.** Finite tasks and attacks cannot prove universal security; results depend on task construction and on the specific attack implementations; Conflux's integration adds provenance/ACS annotations, which are additional assumptions rather than upstream semantics (`docs/evidence/CLAIMS.md`: "Conflux annotations are additional assumptions"), and the retained Conflux numbers (for example 24/30 utility and 30/30 security for Qwen2.5-7B-Instruct NF4 in `agentdojo-7b-v5`) are statistics under those assumptions.

**How Conflux differs, concretely.** AgentDojo measures outcomes; Conflux's PE is an authority invariant over a modelled execution. The two are complementary: AgentDojo provides ecological validity and a utility baseline, while SLED provides the bounded property check. AgentDojo cannot by itself test PE, because the PE check needs a known PC and a pointwise ACS decision that the upstream benchmark does not represent.

**Novelty threat.** A9: no novelty conflict — a benchmark is infrastructure, and using it strengthens the empirical section. The real risk is rhetorical: citing AgentDojo security rates as validation of PE, or citing the annotated integration as if it preserved upstream semantics. **Verdict: none (A9, benchmark/complement).**

**Cited external facts.** 97 tasks, 629 security test cases, extensibility, observed attack/defence results: arXiv abstract `https://arxiv.org/abs/2406.13352` (Atom fetch cached). Annotation caveat and retained numbers: `docs/evidence/CLAIMS.md` (local, read-only).

## 2.13 `nonmalleableifc` - Nonmalleable Information Flow Control

**Identity.** key `nonmalleableifc`; published version DOI `10.1145/3133956.3134054`; *Nonmalleable Information Flow Control*, Proceedings of the 2017 ACM SIGSAC Conference on Computer and Communications Security (CCS 2017), pp. 1875-1891; authors Ethan Cecchetti, Andrew C. Myers and Owen Arden (Crossref). The corpus **arXiv id `1708.08596` is correct** and is the technical report of the same paper (*Nonmalleable Information Flow: Technical Report*, v2; its Atom record carries DOI `10.1145/3133956.3134054`); the corpus **DOI `10.1145/3009837.3009843` resolves to a different paper** (*Cantor meets Scott: semantic foundations for probabilistic networks*, ProbNetKAT) and the corpus **venue "POPL 2017" is wrong** (the paper appeared at CCS 2017).
**Evidence depth: abstract-level (arXiv technical-report abstract, `arxiv-nonmalleableifc.xml`); identity verified from Crossref.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=1708.08596` and Crossref `https://api.crossref.org/works/10.1145/3133956.3134054` after a bibliographic title search; the mismatched corpus DOI was also fetched (`crossref-nonmalleableifc.json`). Cache: `arxiv-nonmalleableifc.xml`, `crossref-fix-nonmalleableifc.json`, `cr-search-nonmalleableifc_fix.json`.

**Mechanism (what it actually does).** A nonmalleability condition for information-flow control that generalises noninterference to permit coordinated downgrading of both confidentiality and integrity: robust declassification stops an attacker from exploiting a confidentiality downgrade, transparent endorsement downgrades integrity while resisting adversarial exploitation, and nonmalleable information flow subsumes both in a single property enforced by a static type system (implemented in the Flame GHC plugin).

**Security property and threat model.** Nonmalleability: neither the decision to downgrade confidentiality nor the decision to upgrade integrity may be arbitrarily influenced by the attacker. The threat model is an attacker who supplies code that runs alongside trusted code and can attempt to exploit downgrade operations.

**Assumptions and stated limits.** Program-level IFC with scalar levels; no named principals, no organisation ACS, no agent or tool model. Conflux has not implemented any nonmalleability or endorsement check for its monotonicity exceptions (`docs/reference/SECURITY_MODEL.md`, ADR-025: any future exception needs a separately accepted semantics and proof obligation).

**How Conflux differs, concretely.** Conflux's delegation and disclosure designs are exactly coordinated downgrades of a principal-sensitive authority relation, so the nonmalleability question — who may influence the downgrade decision — transfers directly. Conflux does not yet answer it: delegation is denied at runtime, controlled release is Level 3 (proposed), and no nonmalleability condition is implemented. In the other direction, Conflux adds principal identities, an external ACS, and effect-time mediation, none of which this line of work has; and this line proves a static property for a language, where Conflux only bounds a finite model (SLED).

**Novelty threat.** A14 (delegation should not be called endorsement; delegation changes authority, endorsement changes integrity status) is *supported*: the classical literature keeps the two downgrades distinct and treats them as one family. The citation-level risk is significant: the corpus's **DOI** and **venue** for this entry are wrong (the arXiv technical-report id is right), and the report must not cite POPL 2017 or the ProbNetKAT DOI. Any future Conflux endorsement or trusted-transformation mechanism must be positioned against nonmalleability and transparent endorsement rather than presented as new. **Verdict: qualification needed (A14 supported; citation correction required; any future exception mechanism must cite this line).**

**Cited external facts.** Title/venue/pages/authors: Crossref `https://api.crossref.org/works/10.1145/3133956.3134054`. Abstract (noninterference generalisation, controlled downgrading of confidentiality and integrity, transparent endorsement, robust declassification comparison, type-system enforcement): arXiv `http://export.arxiv.org/api/query?id_list=1708.08596`. Mismatched corpus DOI: `https://api.crossref.org/works/10.1145/3009837.3009843`. The Flame implementation detail is corpus-level (`research/reports/analysis/literature_corpus.json`, entry `nonmalleableifc`). Conflux side: `docs/reference/SECURITY_MODEL.md`, ADR-025.

## 2.14 `robustdeclassification` - Robust Declassification (Zdancewic & Myers)

**Identity.** key `robustdeclassification`; corrected DOI `10.1109/CSFW.2001.930133`; *Robust declassification*, Proceedings of the 14th IEEE Computer Security Foundations Workshop, 2001, pp. 15-23; authors S. Zdancewic and A. C. Myers (Crossref). The corpus records no DOI or arXiv identifier for this entry. 
**Evidence depth: metadata-level for the corrected DOI (identity verified; no abstract in the Crossref record). Mechanism facts are corpus-level..** Fetched 2026-10-09: Crossref `https://api.crossref.org/works/10.1109/csfw.2001.930133` (authors, venue, pages) after a bibliographic title search. Cache: `crossref-fix-robustdeclassification.json`, `cr-search-robustdeclassification_fix.json`.

**Mechanism (what it actually does).** (Corpus-level; UNVERIFIED externally in this session.) Defines robust declassification: a declassification is robust when an attacker cannot influence what confidential information is released, i.e. the decision to release must itself be protected from attacker influence. This makes confidentiality release depend explicitly on the integrity/control of the release decision.

**Security property and threat model.** Confidentiality release that survives an attacker who can also influence the program; the threat model combines a confidentiality attacker (the observer) with an integrity attacker (the code that triggers releases).

**Assumptions and stated limits.** Targets declassification of information, not general tool or action authority, and not organisational permissions; no principal identities; agent effects that combine integrity, authority and confidentiality need more than one declassification condition (corpus-level).

**How Conflux differs, concretely.** Conflux's implemented level is read-access safety (Level 1); its Level 3 roadmap says controlled release must carry explicit release authority and robust-influence conditions — the property this paper defines. Conflux would instantiate it with principal provenance (which principals may influence the release decision) and with an ACS decision, but the mechanism is not implemented. In the other direction, Conflux covers authority for effects, which robust declassification does not address.

**Novelty threat.** A10 is an explicit non-claim ("authorised reads do not establish noninterference") and this paper supports it; there is no conflict. The exposure is the proposed visibility/disclosure design: a Level 3 disclosure mechanism without a robust-influence condition would repeat a solved problem, and the paper should cite this line rather than present influence-controlled release as new. **Verdict: none for A10; qualification needed for the Level 3 disclosure roadmap.**

**Cited external facts.** Corrected title/venue/pages/authors: Crossref `https://api.crossref.org/works/10.1109/csfw.2001.930133`. Definition and limits: corpus entry `robustdeclassification` (corpus-level) and `docs/evidence/EVALUATION.md` (Confidentiality hierarchy).

## 2.15 `designpatterns` - Design patterns for securing LLM agents against prompt injections

**Identity.** key `designpatterns`; arXiv `2506.08837` (v3); 2025. 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2506.08837`. Cache: `arxiv-designpatterns.xml`.

**Mechanism (what it actually does).** A set of principled architectural design patterns for building agents with "provable resistance" to prompt injection under stated assumptions, with a systematic discussion of utility/security trade-offs and case studies of real-world applicability.

**Security property and threat model.** Conditional resistance to prompt injection: each pattern has assumptions under which its guarantee holds; the threat model is prompt injection in agents with tool access and sensitive data.

**Assumptions and stated limits.** The guarantees depend on the pattern's assumptions and on correct implementation, and the policy origin is a separate problem (corpus-level addition); the paper is a taxonomy/design-pattern catalogue rather than a mechanism with a proof for a specific system.

**How Conflux differs, concretely.** Conflux is an instance of one pattern family (mediation by a trusted enforcement layer around an untrusted model), with the specific extra content that the enforcement relation is the influencing principals' existing ACS permissions. The pattern paper supplies the vocabulary for positioning Conflux among isolation/dual-model/plan-then-execute patterns; it does not supply principal provenance or an ACS-derived authority decision.

**Novelty threat.** A4: the reference-monitor-with-untrusted-model architecture is a named, catalogued pattern, so ITES must be positioned as an instantiation with principal-sensitive authority. A13 is unaffected: the pattern paper does not claim that privilege escalation is or is not the right objective. **Verdict: qualification needed (A4).**

**Cited external facts.** Design patterns with provable resistance under assumptions, trade-off analysis, case studies: arXiv abstract `https://arxiv.org/abs/2506.08837` (Atom fetch cached).

## 2.16 `spotlighting` - Spotlighting: marking untrusted content for the model

**Identity.** key `spotlighting`; arXiv `2403.14720` (v1); 2024. 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2403.14720`. Cache: `arxiv-spotlighting.xml`.

**Mechanism (what it actually does).** A family of prompt-engineering techniques that transform untrusted inputs (for example encoding or delimiting them) so the model receives a continuous signal of an input's provenance, improving its ability to distinguish user commands from data; evaluated as a defence against indirect prompt injection with minimal measured degradation on underlying NLP tasks.

**Security property and threat model.** Empirical reduction of indirect prompt-injection success by improving the model's source discrimination. The threat model is an attacker who embeds instructions in untrusted data; the defence acts entirely inside the model's input processing.

**Assumptions and stated limits.** Security remains empirical and model-dependent: an arbitrary or adversarially adapted model can ignore the cue; no system-level guarantee; the technique cannot constrain effects once the model proposes them (corpus-level addition).

**How Conflux differs, concretely.** Spotlighting tries to make the model behave; Conflux assumes the model may not, and removes authority from the model's reach: a spotlighted instruction still cannot cause an effect outside the influencing principals' ACS envelope. Conflux also needs no cooperation from the model. Reversely, spotlighting can reduce the false-positive pressure on system-level guards; the two layers are complementary, which is exactly the two-layer framing in `docs/reference/SECURITY_MODEL.md`.

**Novelty threat.** A5 ("security depends only on provenance, enforcement and the ACS; model behaviour affects utility but not security") is *supported*: this is a model-level control whose assurance is probabilistic, which the Security Model already states. No novelty conflict. **Verdict: none (supports A5; complementary baseline).**

**Cited external facts.** Spotlighting transforms inputs to signal provenance, empirical evaluation, minimal task degradation: arXiv abstract `https://arxiv.org/abs/2403.14720` (Atom fetch cached).

## 2.17 `struq` - StruQ: structured queries separating instructions and data

**Identity.** key `struq`; arXiv `2402.06363` (v2); to appear at USENIX Security Symposium 2025 (arXiv comment); 2024. 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2402.06363`. Cache: `arxiv-struq.xml`.

**Mechanism (what it actually does).** Structured queries: a secure front-end formats a prompt and user data into two separate channels, and a specially fine-tuned LLM is trained to follow only instructions in the instruction channel; the training strategy converts a base LLM into a structured instruction-tuned model.

**Security property and threat model.** Model-level resistance to prompt injection through channel separation: untrusted data cannot occupy the instruction channel. The threat model is an attacker embedding directives in data; the guarantee is empirical and depends on the trained model's behaviour.

**Assumptions and stated limits.** Depends on trained model behaviour and on fixed channel assumptions; data-dependent control remains difficult; no system-level enforcement of effects (corpus-level addition).

**How Conflux differs, concretely.** StruQ is a model-interface defence: it aims to make the model obey the channel discipline. Conflux assumes no such discipline and enforces authority at the effect boundary with principal provenance and ACS decisions. A structured-query model could be used inside a Conflux deployment without changing the PE property, because Conflux does not rely on the model to separate channels.

**Novelty threat.** A5 is supported: channel separation is a probabilistic model-level control, consistent with the Security Model's two-layer statement. No novelty conflict. **Verdict: none (supports A5; complementary baseline).**

**Cited external facts.** Structured queries, secure front-end plus fine-tuned model, instruction-only following: arXiv abstract `https://arxiv.org/abs/2402.06363` (Atom fetch cached; USENIX Security 2025 comment in the same Atom entry).

## 2.18 `agentguardian` - AgentGuardian: learned access-control policies for agents

**Identity.** key `agentguardian`; arXiv `2601.10440` (v1); 2026. 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2601.10440`. Cache: `arxiv-agentguardian.xml`.

**Mechanism (what it actually does).** A staging phase monitors execution traces of an agent application to learn legitimate behaviours and input patterns; from those traces the framework derives adaptive policies that regulate tool calls using real-time input context and the control-flow dependencies of multi-step actions. Evaluated on two real-world agent applications, reporting detection of malicious or misleading inputs while preserving normal functionality, and mitigation of hallucination-driven orchestration errors.

**Security property and threat model.** Conformance to learned, context-sensitive tool-call policies; empirical detection of malicious/misleading inputs. The threat model is malicious or misleading inputs plus orchestration malfunctions; the authority source is the learned policy, not an existing ACS.

**Assumptions and stated limits.** Coverage and generalisation of learned policies; rare benign behaviour can be blocked; free-form arguments are hard to constrain; poisoned or unrepresentative staging traces can corrupt the policy; no formal guarantee (corpus-level additions).

**How Conflux differs, concretely.** AgentGuardian learns what is legitimate from traces; Conflux takes what is authoritative from the organisation's existing ACS and gives model output no authority effect. Both regulate tool calls per context, but AgentGuardian's context is input plus control-flow dependence, while Conflux's is the set of authenticated influencing principals plus action/argument policy checks. AgentGuardian's assurance is empirical, which lands in Conflux's policy-adequacy and semantic-judgement categories (explicitly outside the core PE guarantee).

**Novelty threat.** No claim is undermined. The positioning requirement is that Conflux must not describe "policy learned from traces" or "context-aware tool-call governance" as novel; the defensible distinction is the authority source (existing ACS) and the model-independent guarantee. **Verdict: none (positioning note for A15(2); the A13 framing is unaffected).**

**Cited external facts.** Staging-phase learning, trace-derived adaptive policies, context and control-flow governance, two-application evaluation, hallucination mitigation: arXiv abstract `https://arxiv.org/abs/2601.10440` (Atom fetch cached).

## 2.19 `agentrfc` - AgentRFC / AgentConform: protocol security principles and conformance checking

**Identity.** key `agentrfc`; arXiv `2603.23801` (v1); 2026; corpus `source_url` is the alphaxiv page for the same identifier and the corpus `arxiv_id` field is empty (fetched from the URL, not guessed). 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2603.23801` (second-round fetch). Cache: `arxiv-agentrfc.xml`, `fetch-log-arxiv-round2.json`.

**Mechanism (what it actually does).** Three parts: (1) the Agent Protocol Stack, a six-layer architectural model defining what a complete agent protocol must specify at each layer; (2) the Agent-Agnostic Security Model, eleven security principles formalised as TLA+ invariants, each tagged with a taxonomy that distinguishes protocol non-conformance from framework-imposed hardening; (3) AgentConform, a two-phase conformance checker that extracts normative clauses from protocol specifications into a typed Protocol IR with explicit Protocol/Environment/Adversary action separation, compiles the IR to TLA+ and model-checks it against the invariants, then replays counterexample traces against live SDK implementations. It also introduces a Composition Safety principle, demonstrated with models of five protocol composition patterns, and reports recurrent gaps in credential lifecycle, consent enforcement, audit completeness and composition safety.

**Security property and threat model.** Protocol conformance and the eleven stated security invariants (including composition safety) for agent protocols; the threat model includes adversarial protocol peers and composition through shared infrastructure; the guarantees are relative to the extracted normative clauses and to the models compiled from them.

**Assumptions and stated limits.** Targets protocol specifications rather than agent authorisation semantics; correctness depends on clause extraction/modelling (an LLM-assisted extraction boundary); preliminary application, with full evaluation deferred to a complete version; some findings under coordinated disclosure.

**How Conflux differs, concretely.** AgentConform and SLED share the binding idea: a formal model plus replay of counterexamples against an implementation. Conflux's differences must therefore be substantive: SLED checks defence semantics (ITS/PE-style properties of monitors such as ITES, Dual-LLM, CaMeL, Progent, PACT abstractions) over a shared finite transition kernel with minimal-counterexample witnesses, whereas AgentConform checks protocol-level invariants extracted from specifications against SDK behaviour. Conflux also adds principal provenance and ACS-derived authority, which are not protocol-clause properties; conversely, Conflux has no protocol-composition or credential-lifecycle analysis.

**Novelty threat.** A9 (SLED evaluates defences independently of model behaviour) and A15(4) ("verifying the security layer under arbitrary model proposals" as a candidate distinction): the workflow "model-check a formalisation, then replay witnesses against the implementation" is now prior art in the agent space, so SLED's novelty must be located in the property semantics (PE and non-implication), the shared kernel and the defence-model reductions, not in the general verification workflow. AgentRFC also independently names consent enforcement and credential lifecycle as recurrent gap areas, which strengthens (rather than threatens) the Conflux emphasis on consent and delegation gates. **Verdict: qualification needed (A9; A15(4) remains a hypothesis).**

**Cited external facts.** Agent Protocol Stack, 11 TLA+ principles with property taxonomy, AgentConform two-phase checker with Protocol IR and counterexample replay, Composition Safety with five patterns, gap findings: arXiv abstract `https://arxiv.org/abs/2603.23801` (Atom fetch cached).

## 2.20 `autoformpolicy` - Autoformalization of agent instructions into Cedar policy-as-code

**Identity.** key `autoformpolicy`; arXiv `2606.26649` (v1); 2026; accepted at the Second Workshop on Agents in the Wild (AIWILD), ICML 2026 (arXiv comment). 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2606.26649`. Cache: `arxiv-autoformpolicy.xml`.

**Mechanism (what it actually does).** An autoformalization pipeline that translates agent prompts, MCP tool descriptions and natural-language policy documents into formally verified Cedar policies using an LLM-based generator-critic loop; evaluated on MedAgentBench, where the autoformalized policies cover substantially more of the source natural-language specification than hand-coded symbolic enforcement in prior work.

**Security property and threat model.** The generated artefact is an analyzable Cedar policy set; the paper's claim is coverage of the source specification and formal usability, not semantic equivalence between prose and Cedar (the corpus entry records the same limit: hard checks prove properties of generated Cedar, not equivalence to the prose).

**Assumptions and stated limits.** The translation boundary remains model-dependent; Cedar analysis proves properties of the generated policies, not of the intended prose policy; coverage metrics on one benchmark; a generated policy is only as authoritative as its review process.

**How Conflux differs, concretely.** Conflux consumes an authorisation relation and derives execution-authority decisions from it; this work addresses how such an ACS could be populated from prose. If Conflux's ACS is autoformalised, the translation itself becomes a trust assumption (policy adequacy), which the Security Model places outside the core guarantee. In the other direction, Conflux adds the enforcement invariant and influence provenance that Cedar policies alone cannot express, since Cedar decisions are point-in-time and have no notion of which principals influenced an execution.

**Novelty threat.** No core claim is undermined. The exposure is a boundary statement for A15(2) ("deriving effective authority from the organisation's current ACS"): Conflux must say who is trusted to have produced the policy facts, because an LLM-generated Cedar policy set is exactly the kind of ACS input that a reviewer will question. Absent that sentence, the claim invites the objection that the hard guarantee rests on a probabilistic translation step. **Verdict: qualification needed (A15(2) boundary statement); otherwise none.**

**Cited external facts.** Generator-critic pipeline, Cedar output, MedAgentBench coverage comparison: arXiv abstract `https://arxiv.org/abs/2606.26649` (Atom fetch cached).

## 2.21 `contextualmanipulation` - AI Agents May Always Fall for Prompt Injections (contextual manipulation)

**Identity.** key `contextualmanipulation`; arXiv `2605.17634` (v1); 2026. 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2605.17634`. Cache: `arxiv-contextualmanipulation.xml`.

**Mechanism (what it actually does).** Recasts prompt injection through Contextual Integrity: it argues that the prevailing data-instruction separation paradigm fails to detect attacks that work through contextual manipulation and also degrades contextually appropriate behaviour; builds benign and attack scenarios that violate norms by misrepresenting the flow, manipulating norms, or mixing multiple flows; derives an impossibility-style trade-off in which an adversary can construct a context that makes a blocked flow look legitimate, and a defender who tightens norms blocks genuinely legitimate flows.

**Security property and threat model.** Contextual Integrity norm compliance (appropriateness of information flows with respect to contextual norms), not a machine-checkable authorisation invariant; the result is a negative/impossibility-style argument about defending norm compliance in general.

**Assumptions and stated limits.** Does not provide deterministic enforcement of arbitrary contextual norms; the framework is evaluative; scope differs from a narrowly defined authorisation invariant (corpus-level addition).

**How Conflux differs, concretely.** Conflux does not try to enforce contextual appropriateness. Its hard invariant is narrower: no execution may exceed the authority available to every influencing principal. Contextual appropriateness stays in the semantic-judgement/policy-adequacy layer, where assurance is empirical (ADR-025). This paper strengthens the argument for that split by showing that "correct context" is not decidable by a channel-separation defence, and it warns against promising a hard guarantee over norms.

**Novelty threat.** A13 (privilege escalation rather than prompt injection as the appropriate system-level security objective) is *supported*: the impossibility result argues that a general defence against manipulative contexts is not achievable as a hard property, which is exactly why Conflux confines itself to an authority invariant. The qualification is presentational: the paper must say explicitly that authority confinement does not imply contextual appropriateness (already the ADR-025 and Security Model position). **Verdict: none for A13 (supporting evidence); qualification sentence recommended at the semantic-judgement boundary.**

**Cited external facts.** Contextual Integrity recasting, failure of data-instruction separation, three attack families, impossibility-style trade-off: arXiv abstract `https://arxiv.org/abs/2605.17634` (Atom fetch cached).

## 2.22 `solverpolicy` - Solver-aided verification of policy compliance in tool-augmented LLM agents

**Identity.** key `solverpolicy`; arXiv `2603.20449` (v1); 2026. 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2603.20449`. Cache: `arxiv-solverpolicy.xml`.

**Mechanism (what it actually does).** An LLM-assisted, human-guided translation of natural-language tool-use policies into SMT-LIB constraints over agent-observable state and tool arguments; at runtime, planned tool calls are intercepted and checked against the constraints with the Z3 solver as a precondition to the call, and violating calls are blocked. Evaluated on TauBench, reporting fewer policy violations while maintaining task accuracy.

**Security property and threat model.** Compliance of tool calls with formalised policy constraints, checked deterministically before execution. The threat model is policy-violating tool use, including injection-driven deviations; the guarantee is relative to the encoded constraints and the modelled observable state.

**Assumptions and stated limits.** Formal guarantees apply to the encoded constraints and modelled state, not to the fidelity of the prose-to-SMT translation; incomplete state observability or omitted tool effects can make correct constraints insufficient; evaluation remains benchmark-based (corpus-level additions).

**How Conflux differs, concretely.** Solver-aided precondition checking of arguments and state is prior art for the enforcement technique Conflux uses in its argument layer. Conflux's differences are (a) the authority relation is the organisation's existing ACS rather than a bespoke SMT encoding, (b) the decision is parameterised by the set of influencing principals, and (c) the guarantee is about non-escalation, which no state-only precondition can express because it is a relation between influence history and permissions. Conversely, this paper handles richer state predicates than Conflux's current schemas.

**Novelty threat.** A9 (SLED) and A15(2)/(3): a 2026 paper already combines autoformalisation, argument-level checks and deterministic runtime enforcement, so Conflux's novelty statement must drop the enforcement technique and rest on the ACS-derived authority invariant plus the bounded verification of defence semantics. A6 is also weakened as a novelty claim: deterministic argument preconditions are standard. **Verdict: qualification needed (A6, A9, A15(2)/(3) boundary statements).**

**Cited external facts.** SMT-LIB constraints over observable state and arguments, Z3 preconditions, interception and blocking, TauBench results: arXiv abstract `https://arxiv.org/abs/2603.20449` (Atom fetch cached).

## 2.23 `symbolicguardrails` - Symbolic guardrails for domain-specific agents (benchmark policy enforceability)

**Identity.** key `symbolicguardrails`; arXiv `2604.15579` (v2); the fetched title is *Don't Make Models Guess Security and Safety: Symbolic Guardrails for Domain-Specific AI Agents*, while the corpus records *Symbolic Guardrails for Domain-Specific Agents: Stronger Safety and Security Guarantees Without Sacrificing Utility* (version/title mismatch); 2026. 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2604.15579`. Cache: `arxiv-symbolicguardrails.xml`.

**Mechanism (what it actually does).** Three studies: a systematic review of 80 agent security and safety benchmarks finding that 85% do not state verifiable requirements (61% none, 24% high-level goals only); an applicability analysis on tau-squared-Bench, CAR-bench and MedAgentBench finding that 74% of requirements are symbolically enforceable and 95% of those need only simple low-cost checks; and an empirical evaluation showing symbolic guardrails improve security and safety without sacrificing utility, often improving it.

**Security property and threat model.** Deductive (symbolic) enforcement of exactly the requirements that can be stated as verifiable conditions over observable state and arguments; the paper is explicit that this class is a subset of what benchmarks ask for.

**Assumptions and stated limits.** Only specified and observable policies are amenable; many benchmarks lack concrete policies; the remaining requirements need model judgement, human review or richer state semantics and must not be conflated with hard guarantees (corpus-level addition).

**How Conflux differs, concretely.** Conflux's PE property belongs to the symbolically enforceable subset identified here; Conflux's own documentation already separates the hard authority invariant from semantic judgement and policy adequacy, which is the same split this study quantifies. The study supplies external, benchmark-scale evidence for scoping Conflux claims: claims about "agent security policy" in general cannot be met by any symbolic layer.

**Novelty threat.** No claim is undermined. It does threaten over-broad scope wording: any sentence that presents ITES as enforcing organisational policy in general (rather than the machine-readable authority relation) invites the 26%-of-requirements objection recorded here. **Verdict: none (scoping evidence; wording constraint on policy-coverage statements).**

**Cited external facts.** 80-benchmark review with 85%/61%/24% figures, 74%/95% enforceability figures, three-benchmark evaluation: arXiv abstract `https://arxiv.org/abs/2604.15579` (Atom fetch cached).

## 2.24 `cedarpaper` - Cedar: authorization policy language and evaluator

**Identity.** key `cedarpaper`; arXiv `2403.04651` (v2, extended version); 2024. 
**Evidence depth: abstract-level.** Fetched 2026-10-09: arXiv Atom `http://export.arxiv.org/api/query?id_list=2403.04651`. Cache: `arxiv-cedarpaper.xml`.

**Mechanism (what it actually does).** Cedar is an authorization policy language with readable syntax that supports role-, attribute- and relation-based access-control use cases; requests are decided quickly by an evaluation engine; an optional-type validator helps policy authors; the design admits a sound and complete logical encoding so policies can be analysed precisely (for example to check that refactoring preserves authorised permissions). The paper reports a Lean model with machine-checked design properties and a Rust implementation, benchmarked against OpenFGA and Rego.

**Security property and threat model.** Correct and analysable evaluation of authorization decisions over request/entity facts; the threat model includes policy authoring and refactoring mistakes, not influence history or agent behaviour. Cedar decisions are functions of the current request and entity state.

**Assumptions and stated limits.** Engine correctness does not prove policy completeness or fidelity to organisational intent; history-dependent conditions require explicit external state (corpus-level addition, consistent with the decision-function design in the fetched abstract).

**How Conflux differs, concretely.** Conflux consumes Cedar-style decisions as `ACS_explicit`; it does not replace the PDP and does not inherit Cedar's analysability for the Conflux layer. Conflux's decision is additionally parameterised by the influencing principals and the argument roles, which are not Cedar inputs; and Conflux's Cedar integration is currently a preflight without a completed differential run (`docs/evidence/CLAIMS.md`: "Cedar decisions match the in-memory oracle — not yet evidenced"), so no parity claim can be made.

**Novelty threat.** No novelty threat to A1-A15. The exposure is internal-claim hygiene: citing Cedar must not imply that the Conflux monitor has been shown to agree with a real Cedar engine, because that evidence does not exist yet (the pinned differential matrix has not run). A15(2) is unaffected but should cite Cedar as the concrete ACS substrate. **Verdict: none (ACS substrate citation; no claim conflict).**

**Cited external facts.** Language design, validator, sound-and-complete encoding, Lean-checked properties, Rust implementation and performance comparison: arXiv abstract `https://arxiv.org/abs/2403.04651` (Atom fetch cached). Cedar preflight status: `docs/evidence/CLAIMS.md` (local).

## 4. What this changes for the paper

The novelty audit states claims A1-A15 with verdicts taken from the local audit text; this section converts the 24 paper-level findings above into concrete edits. Verdicts below refer to the *claim wording*, not to the underlying work. Notation: **A15(n)** means the n-th candidate distinction listed under audit item A15 - (1) retaining authenticated principal identities, (2) deriving effective authority from the organisation's current ACS, (3) parameterised and argument-sensitive action authority, (4) verifying the security layer under arbitrary model proposals.

### 4.1 Claims that must be re-quoted before reuse

| Claim | Why the wording fails as written | Replacement direction |
|---|---|---|
| **A1** ("authority decreases monotonically as influence accumulates") | Low-water-mark contamination already does this: Biba 1977 (UNVERIFIED externally, see 2.3) and LOMAC (Fraser, IEEE S&P 2000, DOI `10.1109/SECPRI.2000.848460`, Crossref record `crossref-lomac.json`) both reduce a subject's effective level after it observes lower-integrity data and restrict its future higher-integrity effects; the audit itself calls the monotonic authorisation intersection a standard meet in the powerset lattice, and its stated search question (does any prior system take the meet over permission sets derived from *authenticated principal identities*?) is answered for the accreditation side by FLAM and PBAC (§3). No sentence may present "consuming untrusted information should reduce future authority" as new. Note: the fetched LOMAC abstract states low-water-mark integrity protection, the COTS kernel extension and the compatibility classification; the meet-over-influencers reading is the standard lattice reading of low-water-mark, not a quotation from that abstract. | Keep the construction, replace the novelty claim: "the effective authority is the pointwise intersection of the ACS permissions of every *authenticated information principal* that influenced the execution, with fail-closed arity policy checks and a policy certificate; the intersection-over-influencers structure is classical (LOMAC, Biba) and the Conflux-specific content is the principal-level, ACS-based, fail-closed construction." |
| **A13** (prompt injection as privilege escalation, if phrased as a first) | Progent frames injection as a least-privilege/violation-of-privilege problem and enforces privilege control per tool call; PACT enforces argument-level contracts; AgentGuardian governs tool calls from learned policies. Any wording of the form "first to treat ... as privilege escalation" conflicts. | Drop firstness; use "we treat prompt injection as an *authority* problem and define the system-level objective as non-escalation relative to the organisation's existing ACS", and cite the refusal to make contextual appropriateness a hard objective (A13-supporting impossibility-style result in `contextualmanipulation`). |
| **"First formal enforcement / reference monitor for agentic policies"** (if such a sentence exists anywhere in the paper or related work) | FORGE (arXiv `2602.16708`, fetched) gives Datalog policies over execution facts, a reference monitor and an assume/guarantee observability contract with a formal coincidence guarantee. | Cite FORGE as contemporaneous prior art for formal enforcement architecture and position ITES as the principal-sensitive, ACS-derived instance. |
| **"We introduce formal verification of agent defences"** (if present) | AgentRFC (arXiv `2603.23801`, fetched) already model-checks TLA+ invariants and replays counterexample traces against live SDKs; solverpolicy uses Z3 preconditions; autoformpolicy generates Cedar policies that are then analysed. | Position SLED by its *property semantics*: a shared finite transition kernel over defence abstractions, PE/ITS-style defence properties, non-implication results between those properties, and minimal counterexamples — not by the model-check-plus-replay workflow. |

### 4.2 Claims to qualify (claim keeps its substance, wording gains a boundary)

| Claim | Required qualification | Nearest evidence in this analysis |
|---|---|---|
| **A2** ("ITES derives effective authority from information provenance and existing access-control policies") | The provenance step has deep prior art: PBAC (PST 2012) makes provenance and dependency paths first-class inputs to access decisions, execution-history access control ties rights to the origins of everything that has run, FLAM integrates authorization with information flow, and taint/label systems already union sources before a policy step (the audit says the same). State the Conflux-specific content as the combination: *authenticated information principals* (not scalar labels or generic taint), the *organisation's existing ACS* as the only authority source (no new policy language for authority), the pointwise meet over the PC for each action and argument, and fail-closed behaviour when a PC or policy is missing. | §3.2, §3.1, §3.3, §2.1, §2.2, §2.7 |
| **A6** (authority-bearing arguments cannot borrow authority from content or consent) | The general idea is prior art: PACT tracks argument provenance against role-specific trust contracts; Progent and solverpolicy check tool names and arguments with symbolic/SMT preconditions. The surviving specificity is the *pointwise Principal check against the existing ACS* plus fail-closed semantics when a role or policy is missing, recorded in the certificate. | §2.10, §2.11, §2.22 |
| **A8** ("influence is never silently removed by nested execution") | Conservative label/flow propagation is standard practice (Biba, LOMAC, taint tracking, and the language-based IFC survey), so A8 must be stated as the instantiation for nested agent execution: provenance is authenticated, immutable across model/plan/tool nesting, never reset by a nested call, and subject to exactly one named exception (trusted argument roles). Add the explicit non-claims: provenance is not a confidentiality level, and the Myers-Liskov ROA-style rollback/endorsement move is not available in Conflux. | §2.1, §2.3, §2.6, §2.2 |
| **A9** (SLED evaluates defences independently of model behaviour) | Narrow to the kernel and property semantics (see 4.1, last row), and state explicitly which parts are inherited: formal enforcement architectures (FORGE), conformance checking and counterexample replay (AgentRFC), solver preconditions (solverpolicy), policy analysis (Cedar). | §2.9, §2.19, §2.22, §2.20, §2.24 |
| **A11** ("ITES uses provenance to derive effective authority under an existing access-control system rather than preventing information flows") | The audit notes that the distinction may not be sharp, because decentralized IFC systems also derive decisions from organisational structures (acts-for relations, principal hierarchies) — Myers & Liskov and Jif are the concrete comparison points, and nonmalleable IFC shows the same line handling authority-like downgrades. Keep the distinction but make it about the *enforcement objective and evidence* rather than the absence of a label language: Conflux produces a per-execution authority decision with a certificate, mediated at effect time, and it does not require a new label/flow language from the deployer. | §2.2, §2.13, §2.6 |
| **A13** (the system-level objective) | Say plainly that the hard objective is a narrow authority invariant; authority confinement does not imply contextual appropriateness. | §2.21, §2.15 |
| **A14** (delegation is not endorsement) | The distinction is *supported* by the classical literature (coordinated downgrades: robust declassification, transparent endorsement, nonmalleability), so keep the distinction and cite these works for it; what must not be claimed is that Conflux invented the separation. | §2.13, §2.14 |
| **A15** (candidate distinctions, currently hypotheses) | (1) "authority from provenance" is heavily constrained by FLAM, PBAC and execution-history access control — cite all three; (2) "authority derived from the organisation's current ACS" survives but needs a policy-source boundary sentence, since an ACS may itself be trace-learned (AgentGuardian) or LLM-generated (Progent, autoformpolicy); (3) argument-sensitive authority is contested prior art and should leave the candidate list; (4) "verifying the security layer under arbitrary model proposals" must be restated as defence-property semantics, not as the verification workflow (AgentRFC). | §2.10, §2.9, §2.20, §2.18, §3 |

## 3. Watchlist: closest neighbours outside the ranked 24

These three corpus entries are not in the top 24 by the objective ordering, but they constrain claims A15(1)/(2) so directly that they belong in the related-work section regardless of adoption priority.

### 3.1 `flam` - Flow-Limited Authorization (FLAM)

- **Identity (verified).** Corrected venue: *Flow-Limited Authorization*, 2015 IEEE 28th Computer Security Foundations Symposium (CSF 2015), pp. 569-583, DOI `10.1109/CSF.2015.42` (Crossref record `crossref-watch-flam.json`). The corpus entry records year 2014, no DOI and no venue — a citation defect. Related records located in the same Crossref search: `10.1109/CSF.2016.17` (A Calculus for Flow-Limited Authorization, CSF 2016) and `10.1109/EuroSP.2019.00015` (Programming with Flow-Limited Authorization: Coarser is Better).
- **Why it matters.** The corpus already records this as the boundary entry for the integration of authorization and information-flow: FLAM defines *robust authorization*, so that attackers cannot improperly influence authorization decisions or learn confidential trust relationships. A15(1) (retaining authenticated principal identities) and A2 (deriving effective authority from provenance plus an existing access-control system) must cite FLAM and PBAC as theoretical predecessors.
- **Evidence depth.** metadata-level only (Crossref gives authors/venue/pages; the record carries no abstract). Mechanism and limits facts are corpus-level, marked UNVERIFIED.

### 3.2 `pbac` - A Provenance-Based Access Control Model

- **Identity (verified).** *A provenance-based access control model*, 2012 Tenth Annual International Conference on Privacy, Security and Trust (PST 2012), pp. 137-144, DOI `10.1109/PST.2012.6297930` (Crossref record `crossref-watch-pbac.json`). The corpus entry records no DOI. Related records: `10.1109/PST.2013.6596060` (provenance-based access control for dynamic separation of duties) and `10.1109/SAI.2015.7237321` (delegation-enabled provenance-based access control).
- **Why it matters.** Direct prior art that data provenance and dependency paths are first-class inputs to access decisions. The corpus's own note is the right framing: provenance-based access control predates LLM agents, so Conflux must specify its novel provenance semantics (authenticated information principals whose influence set is auditable) and its authority rule (pointwise ACS intersection), not the fact that provenance participates.
- **Evidence depth.** metadata-level only (no abstract in the Crossref record). The 2015 delegation-enabled follow-up is especially relevant to A14 and to the delegation gates.

### 3.3 `executionhistory` - Access control based on execution history

- **Identity (partially resolved).** The corpus entry has no DOI, no venue and year 2003. Crossref bibliographic search (`cr-search-executionhistory.json`) returns as its closest record *Access control by tracking shallow execution history*, IEEE Symposium on Security and Privacy 2004, pp. 43-55, DOI `10.1109/SECPRI.2004.1301314` — the same idea (rights determined from the origins of code that has executed, tracked to a shallow depth) at a named venue. The corpus's 2003 item itself (typically cited as an NDSS 2003 paper) was **not** resolved to an identifier in this session; its citation must be checked before it is used.
- **Why it matters.** This is the historical analogue of "authority is a function of accumulated origins", which is precisely the structure A15(1) and the principal-context invariant generalise. It must be cited, and no paper sentence may imply that history-dependent authority is new.
- **Evidence depth.** metadata-level for the related record; corpus-level for the 2003 item itself.

### 4.3 Claims that survive unchanged

| Claim | Status after this analysis |
|---|---|
| **A3** ("ITES is the maximally permissive authorisation preserving PE safety") | Unaffected: the audit classes it as a correctness proof about a specific construction, not a novelty claim, and no fetched paper addresses maximality relative to a PE definition. Two presentation requirements from the audit and this analysis: state maximality relative to the PE definition (not as general optimality), and cite the classical meet/lattice lineage (Denning, LOMAC) for the intersection structure so the resemblance is acknowledged rather than discovered by a reviewer. |
| **A5** (security depends only on provenance tracking, enforcement and the ACS; model behaviour affects utility, not security) | Unaffected and externally supported: `spotlighting` and `struq` are model-level defences with empirical assurance, `designpatterns` catalogues the architecture, `symbolicguardrails` shows that only 74% of benchmark requirements are symbolically enforceable, and `agentdojo` supplies the utility/security measurement protocol. |
| **A10** (authorised reads do not establish noninterference — an explicit non-claim) | Unaffected and reinforced by `robustdeclassification`, `declassificationsurvey` and `attackercontrol`: the classical line separates access safety from noninterference, and the Conflux Level 1/2/3 hierarchy already reflects that. |
| **A15(2)** in its narrow reading (the ACS is the authority source, not the model) | Survives, with the boundary sentence from 4.2 (who produced the ACS facts). |

### 4.4 Suggested replacement sentences (short, quotable)

- **A1:** "For each execution, effective authority is the pointwise intersection of the ACS permissions of every authenticated information principal that influenced the execution inputs; the intersection-over-influencers structure is classical (LOMAC, Biba), and Conflux adds the principal-level, ACS-based, fail-closed construction and its certificate."
- **A6:** "Authority-bearing arguments are bound to the influencing principals' ACS permissions rather than to a trust grade or to model context; argument-level enforcement is prior art (PACT, Progent), and the Conflux-specific content is the pointwise ACS conjunction with fail-closed missing-policy behaviour."
- **A9:** "SLED checks PE/ITS-style defence properties for abstract defence models on one shared finite transition kernel, proves non-implication between those properties, and returns minimal counterexamples; the model-check-then-replay workflow itself follows FORGE and AgentRFC."
- **A13:** "Conflux treats prompt injection as an authority problem and defines the system-level objective as non-escalation relative to the organisation's existing ACS; it does not claim that authority confinement implies contextual appropriateness."

### 4.5 Related-work additions the analysis forces

- Classical lattice and integrity line: Denning 1976 (`10.1145/360051.360056`), Biba 1977 (no verified identifier, see 2.3), LOMAC (Fraser, IEEE S&P 2000, `10.1109/SECPRI.2000.848460`), Myers & Liskov 2000 (`10.1145/363516.363526`), robust declassification (CSFW 2001), nonmalleable IFC (CCS 2017), attacker-controlled mechanisms (LMCS 2011), declassification survey (JCS 2009).
- Provenance/authorization line: FLAM (CSF 2015), PBAC (PST 2012), execution-history access control (2003/2004).
- Agent-security line 2024-2026: AgentDojo, Spotlighting, StruQ, design patterns, CaMeL, PACT, Progent, FORGE, AgentGuardian, AgentRFC, autoformalization of Cedar policies, solver-aided policy checks, symbolic guardrails, contextual manipulation, Cedar.
- Internal artefacts to cite for the Conflux side: `docs/reference/SECURITY_MODEL.md`, `docs/evidence/CLAIMS.md`, `docs/evidence/EVALUATION.md`, `research/reports/analysis/2026-08-16-novelty-audit.md`, `docs/research/RELATED_WORK.md`.

## 5. Evidence depth, fetch outcomes and residual uncertainty

### 5.1 Evidence depth per selected paper

| # | key | evidence depth |
|---:|---|---|
| 1 | `lomac` | abstract-level |
| 2 | `myersliskov` | abstract-level |
| 3 | `biba1977` | corpus-level (no external source fetched; both external pages HTTP 403) |
| 4 | `declassificationsurvey` | metadata-level (identity verified; no abstract in the Crossref record) |
| 5 | `attackercontrol` | abstract-level |
| 6 | `sabelfeld2003` | abstract-level |
| 7 | `denning1976` | abstract-level |
| 8 | `camel` | abstract-level |
| 9 | `forge` | abstract-level |
| 10 | `pact` | abstract-level |
| 11 | `progent` | abstract-level |
| 12 | `agentdojo` | abstract-level |
| 13 | `nonmalleableifc` | abstract-level (arXiv technical-report abstract; published version = CCS 2017) |
| 14 | `robustdeclassification` | metadata-level (identity verified; no abstract in the Crossref record) |
| 15 | `designpatterns` | abstract-level |
| 16 | `spotlighting` | abstract-level |
| 17 | `struq` | abstract-level |
| 18 | `agentguardian` | abstract-level |
| 19 | `agentrfc` | abstract-level |
| 20 | `autoformpolicy` | abstract-level |
| 21 | `contextualmanipulation` | abstract-level |
| 22 | `solverpolicy` | abstract-level |
| 23 | `symbolicguardrails` | abstract-level |
| 24 | `cedarpaper` | abstract-level |

Counts: **abstract-level 21**, **metadata-only 2** (`declassificationsurvey`, `robustdeclassification`), **corpus-level 1** (`biba1977`). Watchlist entries (3.1-3.3) are metadata-level for identity with corpus-level mechanism facts.

### 5.2 Fetch outcomes (2026-10-09, all key-free)

- **Succeeded.** OpenAlex DOI lookups for the classical entries; Crossref DOI records and bibliographic searches; arXiv Atom queries for 16+1+15 identifiers of the modern entries (all cached under `.local/similar-papers-cache/`).
- **HTTP 404 (corpus identifier wrong).** `myersliskov` corpus DOI `10.1145/363516.363524`; corrected to `10.1145/363516.363526` via Crossref bibliographic search. Both OpenAlex and Crossref returned 404 for the corpus DOI.
- **Identifier resolves to a different paper (corpus defect).** `declassificationsurvey` corpus DOI `10.3233/JCS-2009-0357` resolves to Bartoletti et al., not to the Sabelfeld & Sands survey (corrected: `10.3233/JCS-2009-0352`); `attackercontrol` corpus DOI `10.1109/CSF.2007.22` resolves to the STV / Pret a Voter paper while its corpus arXiv id `1107.5594` is correct (corrected DOI: `10.2168/LMCS-7(3:17)2011`); `nonmalleableifc` corpus DOI `10.1145/3009837.3009843` resolves to ProbNetKAT while its corpus arXiv id `1708.08596` is correct, and the corpus venue "POPL 2017" plus the corpus pages 257-270 are wrong (corrected: CCS 2017, `10.1145/3133956.3134054`, pp. 1875-1891); `declassificationsurvey` corpus venue JCS 17(5), 609-655 belongs to the wrong article (corrected record: JCS 17(5), 517-548).
- **HTTP 403 (unfetchable, recorded not guessed).** `biba1977`: DTIC and ResearchGate both returned 403; no DOI or arXiv identifier exists in the corpus, so the entry stays corpus-level. The 1977 integrity report must be verified from a library copy before it is cited.
- **HTTP 429 (rate limits).** OpenAlex title searches (first and second round, including an 8-second-spaced retry) were rate limited and are recorded as failures; Crossref bibliographic search supplied the corrections instead.
- **Version/title mismatches in the corpus** (fetched title vs corpus title): `forge` (arXiv title *Formal Policy Enforcement for Real-World Agentic Systems*), `progent` (*Progent: Securing AI Agents with Privilege Control*), `symbolicguardrails` (*Don't Make Models Guess Security and Safety: ...*), `cedarpaper` (has an "(Extended Version)" suffix). These are version differences rather than wrong papers, but the bibliography must use the fetched titles and venue/version facts.
- **Missing corpus identifiers recovered or noted:** `agentrfc` had an empty `arxiv_id` field (identifier taken from the corpus `source_url`, then confirmed by an arXiv Atom fetch); `flam`, `pbac`, `executionhistory`, `robustdeclassification` and `declassificationsurvey` had no DOI, and corrected/related DOIs were located for all except the 2003 execution-history item.

### 5.3 Residual uncertainty (must stay marked in the paper)

- Mechanism and limit statements for `biba1977` are corpus-level and UNVERIFIED; the entry also needs a citation fix.
- Mechanism statements for `declassificationsurvey`, `robustdeclassification` and `nonmalleableifc` are corpus-level; only their identity (title, authors, venue, pages, year) is externally verified.
- All fetched abstracts are abstracts: for `pact`, `progent`, `solverpolicy`, `agentguardian`, `agentrfc` and `autoformpolicy` there is no full-text verification in this session, so quantitative claims quoted from them (percentages, benchmark names) are as-reported by the authors.
- The corpus-level "closest relation" fields are the corpus's own wording, not this analysis's judgement; the updates JSON keeps them separate from the evidence-based `key_findings`/`limitations` values.
- **Errata applied during writing (2026-10-09).** Claim ids in section 4 were re-checked against the exact texts in `research/reports/analysis/2026-08-16-novelty-audit.md`; the first draft paraphrased A2 and A11 incorrectly (A2 is the provenance-derived-authority claim, A11 the IFC-versus-provenance positioning claim), and those rows, the `attackercontrol` verdict (§2.5), the `agentguardian` verdict (§2.18) and the `nonmalleableifc` note (§2.13) were corrected. Two identifiers written from memory in section 4 were also wrong and are fixed here: LOMAC is IEEE S&P 2000, DOI `10.1109/SECPRI.2000.848460` (no arXiv identifier), and Denning 1976 is DOI `10.1145/360051.360056`. The all-identifier audit in section 5.2 remains the reference for identities.

## 6. Summary: top novelty threats and claim rewrite list

### 6.1 Top five novelty threats

| Rank | Paper | Claim(s) | Verdict | One-line reason |
|---:|---|---|---|---|
| 1 | `lomac` (§2.1) | **A1** | **conflict** (wording cannot stand) | Low-water-mark contamination (Biba 1977 lineage, LOMAC 2000) already reduces authority when lower-integrity information is observed and restricts later higher-integrity effects; the audit calls the monotonic intersection a standard lattice meet, and FLAM/PBAC (§3) cover the accreditation side. |
| 2 | `pact` (§2.10) | **A6**, **A15(3)** | qualification needed; A15(3) leaves the candidate list | Argument-level provenance with role-specific trust contracts and cross-step tracking is a 2026 direct precedent for the argument-authority idea. |
| 3 | `forge` (§2.9) | **A4**, **A9** | qualification needed | Datalog policies over execution facts, a reference monitor and an assume/guarantee observability contract with a formal coincidence guarantee occupy the "formal agent policy enforcement" position. |
| 4 | `progent` (§2.11) | **A4**, **A6**, **A13** | qualification needed | Deterministic per-call privilege control with symbolic tool-name/argument rules and SMT-classified policy narrowing/expansion; frames injection as least-privilege violation. |
| 5 | `agentrfc` (§2.19) | **A9**, **A15(4)** | qualification needed | Eleven TLA+ security principles, a two-phase conformance checker with Protocol/Environment/Adversary separation, and counterexample replay against live SDKs; also names consent and credential-lifecycle gaps independently. |

Runners-up that constrain wording but not the core contributions: `solverpolicy` (§2.22, SMT preconditions on tool arguments), `myersliskov`/`meyers` (A2/A11 influence-robustness), `nonmalleableifc` (§2.13), `flam`/`pbac`/`executionhistory` (§3), and `symbolicguardrails` (§2.23, scope of "policy" claims).

### 6.2 Owner claims to rewrite

- **Rewrite (wording change required):** **A1** (re-quote as the principal-level, ACS-based, fail-closed construction and cite LOMAC/Biba), **A13** (remove any firstness claim; state the objective as non-escalation relative to the existing ACS), **A15(3)** (drop argument-sensitive authority from the candidate distinction list).
- **Qualify (add a boundary sentence or narrow the property):** **A2** (provenance-derived authority: cite PBAC/FLAM/execution-history; state the specific combination as authenticated principals + existing ACS + pointwise meet + fail-closed), **A6** (pointwise ACS conjunction and fail-closed semantics, not argument-level enforcement), **A9** (SLED = shared kernel, defence-property semantics, non-implication, minimal counterexamples), **A11** (compare against decentralized IFC/Jif acts-for hierarchies, and put the distinction on the enforcement objective and evidence rather than on the absence of a label language), **A14** (keep the delegation/endorsement distinction, cite nonmalleable IFC and robust declassification), **A15(2)** (policy-source boundary), **A15(4)** (property semantics rather than verification workflow).
- **Keep as stated:** **A3** (with a LOMAC citation for the meet structure), **A5**, **A10**.
- **Bibliographic fixes required before submission:** venue/DOI/title corrections listed in §1.6 and §5.2, and delete any sentence of the form "first formal policy enforcement/reference monitor for agentic systems".

### 6.3 Companion updates file and proposed risk-level changes

The proposed corpus updates are written to `research/reports/analysis/2026-10-09-similar-paper-corpus-updates.json` (24 entries; each update carries its evidence URL, fetch date and cache filename; the file does not modify the corpus). The `updates` payloads were validated in memory against `schemas/literature-corpus.schema.json` (`closest_relation`, `novelty_impact`, `relevance`; no schema violations).

| key | corpus risk | proposed risk | reason |
|---|---|---|---|
| `pact` | medium | **high** | direct 2026 argument-level precedent on A6; removes A15(3) from the candidate list |
| `agentrfc` | (absent) | **medium** | A9/A15(4): model-check-then-replay workflow with SDK counterexample replay |
| `solverpolicy` | (absent) | **medium** | A6/A9: SMT preconditions on tool arguments plus runtime enforcement |
| `agentguardian` | (absent) | low | A15(2): learned policies are the contrast case for the authority-source distinction |
| `autoformpolicy` | (absent) | low | A15(2): policy-source boundary (LLM-generated ACS facts) |
| `contextualmanipulation` | (absent) | low | supports A13 and marks the limit of the hard guarantee |
| `symbolicguardrails` | (absent) | low | scope constraint on policy-coverage wording (74% of requirements enforceable) |
| `cedarpaper` | (absent) | none | ACS substrate citation; only internal claim-hygiene exposure |

All other selected entries keep their corpus risk level. Claims touched across the 24 entries: A1 (4 entries), A2 (3), A4 (5), A5 (3), A6 (3), A8 (4), A9 (5), A10 (2), A11 (2), A13 (3), A14 (2), A15 (6).

