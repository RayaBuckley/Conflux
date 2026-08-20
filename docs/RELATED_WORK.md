# Related-work Positioning

The report corpus organises relevant work by mechanism: model robustness,
architectural isolation and information-flow control, runtime policy,
provenance granularity, delegation, persistent state, and verification.

Conflux's defensible distinction is Principal identity provenance interpreted
through an organisation's access-control decisions. This is narrower than
being the first system-level defence, provenance guardrail, or privilege
control mechanism. Whole-action ITES is presently a conservative special case;
trusted selector roles and pointwise argument authorisation are implemented;
richer operation-specific argument-effect semantics remain proposed work.

The [current report analysis](../reports/analysis/PROJECT_ANALYSIS.md) explains
how the detailed archived taxonomy and literature matrix relate to the current
repository. The [comparative defence verification
analysis](../reports/analysis/COMPARATIVE_DEFENCE_VERIFICATION.md) proposes a
research design for verifying contemporary agent defences against the Conflux
PE property. The [foundational security literature
analysis](../reports/analysis/2026-08-13-foundational-security-literature.md)
identifies the classical integrity and IFC lineage underlying Principal
Context and ITES. Very recent preprints, titles, author lists, and reported
numbers must be checked against primary sources before publication. This
document does not revise the archived paper.

## Foundational security lineage

The core ITES mechanism does not arise without classical precedent. The
principal-sensitive authority intersection rule is structurally analogous to
low-water-mark contamination from Biba's integrity models, operationalised in
systems such as LOMAC. The fourth-year framing should acknowledge this lineage
explicitly.

### Integrity and low-water-mark policies

Biba (1977) defines multiple integrity policies, including low-water-mark
variants where consuming lower-integrity information reduces a subject's
effective integrity and restricts its future high-integrity effects. This is
the direct structural ancestor of ITES: adding an influencing principal to
Principal Context can preserve or reduce effective authority but cannot
increase it. Conflux enriches this pattern by retaining authenticated principal
identities and deriving action-specific authority from the organisation's
existing authorisation relation rather than requiring a single integrity
classification.

LOMAC operationalises low-water-mark integrity in commodity operating
systems. It confronts the same engineering tension as Conflux: conservative
contamination tracking preserves security but can destroy utility through
label creep. LOMAC's experience with process contamination directly informs
Conflux's planning research, where avoiding unnecessary observations
minimises authority loss.

### Information-flow control and noninterference

Denning (1976) provides the lattice model for secure information flow:
security classes combine via a lattice, and flows must respect the partial
order. Conflux's authority intersection over permission sets is a meet in
the powerset lattice over actions; the dissertation should not claim this
structure is non-lattice.

Noninterference (Goguen and Meseguer) establishes that varying secret
information should not alter observations available to unauthorised
observers. This is strictly stronger than Conflux's current read-access
safety. Authorised reads do not establish noninterference: a system can obey
local ACL checks and still leak information through outputs, control flow,
success/failure behaviour, or timing. SLED-V should distinguish access
safety from observational confidentiality.

### Language-based IFC and influence

Sabelfeld and Myers (2003) provide vocabulary for explicit and implicit
flows, static and dynamic enforcement, noninterference, and precision versus
soundness. This vocabulary clarifies what Conflux means by "influence":
Principal Context conservatively assumes that if information from a principal
reaches an execution, that principal may influence its output. This is an
intentional overapproximation, not a claim of exact causal dependence.

The project retains three distinct concepts: **security provenance**
(conservative overapproximation for enforcement), **exposure measurement**
(empirical measure of information supplied), and **attribution**
(best-effort estimate of actual influence). Only the first should support
hard security guarantees.

### Decentralized IFC

Myers and Liskov's decentralized IFC moves beyond a single global
classification toward policies involving multiple principals and
decentralised authority. This is closer to Conflux's organisational setting
than a simple high/low model. Decentralized IFC may contain prior art
closer to "principal-sensitive authority" than Biba alone; novelty claims
must be checked against it.

### Declassification, endorsement, and visibility

Strict information-flow policies are too restrictive for practical systems.
Declassification provides controlled relaxation of confidentiality, asking
*what* may be released, *who* may authorise release, *where* it may occur,
and *when* it is permitted. These dimensions map directly to Conflux
visibility and controlled disclosure.

Conflux should distinguish **visibility confinement** (effects remain
visible only to already-authorised observers) from **controlled
disclosure/declassification** (policy explicitly permits selected release
beyond strict confinement). They are not the same mechanism.

Endorsement is the integrity-side counterpart: untrusted information is
deliberately accepted as sufficiently trustworthy. This is relevant to
trusted transformations that can remove or reduce conservative influence.
Delegation should not be called endorsement; delegation changes authority,
endorsement changes the integrity status of information.

### Robust declassification and attacker influence

Robust declassification (Zdancewic and Myers) asks whether an attacker can
manipulate what or when trusted code declassifies. This is directly
relevant to prompt injection: a trusted user may be authorised to release
information, but an attacker-authored document should not automatically
gain the ability to influence the LLM into exercising that authority. A
future disclosure rule should ask both whether release is authorised and
which principals may influence the decision to perform it.

Nonmalleable IFC (Cecchetti, Myers, Arden) addresses the question of
whether explicit exceptions to monotonicity (delegation, disclosure, trusted
transformations, consent, policy updates) can be exploited by adversarial
influence. This is relevant to Conflux's multiple explicit exceptions to
simple authority monotonicity.

### Taint tracking and provenance enforcement

Conflux's provenance union is structurally similar to source-set taint:
sources A and B produce combined provenance {A, B}. Conflux then performs
the additional step of consulting each source principal's authorisation to
derive allowed effects. Source-set tainting and provenance-aware policy
enforcement have extensive prior literature; a targeted novelty search is
required for systems where sink permissions depend on source identities.

### Reference monitors and confused deputy

The ITES mediation boundary is a reference monitor: complete mediation of
privileged effects by a small, analysable, tamper-resistant mechanism
separating untrusted proposal generation from trusted effect execution. The
LLM is untrusted code requesting privileged operations, not a trusted
security decision-maker.

Tool-using prompt injection often resembles the confused-deputy problem:
attacker-controlled information reaches a privileged agent that can access
resources the attacker cannot. Conflux attenuates the deputy's effective
authority according to provenance, which parallels capability-based
approaches to the confused deputy.

### Access-control safety and delegation

Explicit delegation makes classical access-control safety relevant. The
Harrison-Ruzzo-Ullman result shows that unrestricted dynamic access-control
systems can make safety undecidable. This supports SLED-V's need for a
finite/restricted verification fragment and Conflux's use of typed
delegation transitions with bounded scope, expiry, and one-use constraints.

## Revised positioning

Tool-using LLM agents create a modern instance of an old systems-security
problem: untrusted information is processed by a component capable of
privileged effects. Classical integrity models, particularly Biba's
low-water-mark policies and systems such as LOMAC, address analogous
contamination. Information-flow-control research subsequently developed
richer lattice, noninterference, decentralized-policy, declassification,
and endorsement mechanisms.

Conflux applies this lineage to AI agents but represents contamination as
authenticated principal provenance and derives effective action authority
from the organisation's existing authorisation state. This provides a
conservative security kernel under arbitrary model behaviour. The
fourth-year project then asks how principal-sensitive authority can support
practical agent workflows through fine-grained policies, explicit delegation
and consent, controlled visibility, security-aware planning, attribution,
and formal verification.

This positioning remains a hypothesis until targeted prior-art searches are
complete. No novelty claim such as "first generalisation of Biba to
arbitrary permission sets" should be made until established by primary-source
verification.

## Rationale

Precise positioning is narrower but more defensible than claiming novelty for
all system-level mediation or provenance. Separating mechanism comparison from
implementation status also prevents a related-work update from silently
changing security or empirical claims.
