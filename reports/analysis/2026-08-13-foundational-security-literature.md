# Foundational Security Literature for Conflux: Biba, LOMAC, IFC, Declassification, and Implications

**Date:** 13 August 2026\
**Status:** Research analysis; not a canonical specification\
**Recommended repository path:**
`reports/analysis/2026-08-13-foundational-security-literature.md`

## Executive summary

Supervisor feedback identifies an important gap in the current Conflux
literature review: the modern LLM-agent security landscape is broad, but
the classical security lineage underlying Principal Context / ITES has
not yet been treated with comparable depth.

The most important correction is to position the core ITES mechanism
relative to **Biba's integrity models, especially low-water-mark
policies**, and the practical **LOMAC** system. The structural
resemblance is substantial: information consumption can monotonically
reduce the future effects a computation is permitted to have. Conflux
should not present monotonic authority attenuation under accumulated
influence as if it arose without classical precedent.

At the same time, Conflux should not simply be described as "Biba for
LLMs." Biba is principally an integrity-label model. Conflux retains
authenticated principal provenance and consults an organisation's
existing, potentially fine-grained authorisation relation to determine
which parameterised actions remain available. The right research
question is therefore not whether Conflux independently rediscovered
low-water-mark integrity, but exactly what is gained by replacing or
enriching a conventional integrity label with **principal-sensitive
provenance plus existing authorisation state**, and how the resulting
mechanism interacts with modern agent-specific concerns.

The second major gap is the classical information-flow-control
literature. Denning's lattice model, noninterference, Sabelfeld and
Myers' language-based IFC survey, decentralized IFC, declassification,
endorsement, robust declassification, attacker control/impact, and
nonmalleable information flow are directly relevant to Conflux's
confidentiality, visibility, delegation/trusted transformation,
attribution, and verification directions.

This changes the literature-review strategy. The existing modern-agent
landscape should be retained, but a new foundational stream should be
added and used to revise novelty claims. The strongest fourth-year story
is likely to be:

1.  Part B's Principal Context / ITES is a **principal-sensitive
    authority analogue/generalisation of low-water-mark contamination**,
    grounded in existing organisational authorisation rather than a
    single integrity classification.
2.  The fourth-year project develops the parts not supplied by that
    analogy: fine-grained authority semantics, explicit delegation and
    consent, visibility/controlled disclosure, planning that avoids
    unnecessary authority contamination, attribution, and substantially
    stronger verification.
3.  SLED-V should connect to classical IFC verification by
    distinguishing ordinary safety properties from relational
    confidentiality/noninterference properties.
4.  Contemporary LLM-agent systems such as CaMeL, Progent, PACT, and
    causal-provenance approaches remain the closest application-domain
    comparisons; classical security work supplies the conceptual and
    formal foundations.

No novelty claim such as "first generalisation of Biba to arbitrary
permission sets" should be made until a targeted primary-source and
citation search has established it.

## 1. Why this report exists

The Part B report framed the project primarily through prompt injection,
access control, Dual-LLM, and CaMeL. It defined an access-control
structure `(A, U, D, P, W, R)`, accumulated the writers/authors of data
supplied to an LLM, and authorised an action only when every influencing
principal possessed the required permission. It proved monotonicity of
the resulting effective permission set and used SLED for bounded
exhaustive evaluation.

That framing was coherent, but historically narrow. The current research
landscape has substantially improved coverage of modern agent security,
provenance, formal verification, planning, delegation, memory, and
benchmarks. The supervisor's observation that Biba's 1977 low-water-mark
policies are a natural starting point reveals that the foundational
lineage remains underdeveloped.

This report therefore has five goals:

-   identify the classical literature most directly relevant to Conflux;
-   compare that literature carefully with Principal Context / ITES;
-   revise the novelty and contribution story conservatively;
-   connect the literature to current fourth-year directions;
-   specify concrete repository, bibliography, manuscript, and research
    tasks.

## 2. The conceptual lineage Conflux should now investigate

``` text
Reference monitors / complete mediation / least privilege
                    |
                    v
      Mandatory information-flow models
        /                            \
       v                              v
Denning / confidentiality          Biba integrity
       |                              |
       v                              v
noninterference                low-water-mark policies
       |                              |
       v                              v
language-based IFC                  LOMAC
       |                              |
       +-------------+----------------+
                     v
          decentralized IFC
       declassification / endorsement
                     |
                     v
       robust attacker-influence models
                     |
                     v
 provenance / taint / whole-system IFC
                     |
                     v
 contemporary system-level LLM-agent security
                     |
                     v
        Principal Context / Conflux
```

This is not a single direct inheritance chain. These literatures solve
different problems. The point is to prevent the dissertation from
discussing Conflux only against work published after LLM agents
appeared.

## 3. Biba: the most important immediate comparison

### 3.1 Primary-source requirement

Kenneth J. Biba's 1977 *Integrity Considerations for Secure Computer
Systems* should be treated as a primary source. Secondary summaries
often collapse "the Biba model" into one slogan. The original work
considers multiple integrity policies, including low-water-mark
variants. The dissertation should identify the exact policy relevant to
Conflux.

The important intuition is contamination: consuming information of lower
integrity can reduce the integrity at which a subject can subsequently
operate. A low-water-mark policy permits interaction with
lower-integrity information while preventing that information from
silently retaining the subject's previous ability to affect
higher-integrity state.

### 3.2 Structural similarity to ITES

Part B defines:

``` text
Influence(inputs) =
    union of principals that may have authored the inputs

Permitted(I) =
    intersection of permissions of principals in I
```

Adding an input can add principals to `I`; intersecting over more
permission sets cannot increase authority.

The analogous pattern is:

``` text
Biba / low-water mark

high-integrity subject
        |
        | observes lower-integrity information
        v
subject's effective integrity is lowered
        |
        v
future high-integrity effects are restricted
```

Conflux:

``` text
execution with Principal Context I
        |
        | observes information from principal p
        v
Principal Context becomes I union {p}
        |
        v
effective authority becomes
Authority(I) intersection Authority(p)
        |
        v
future effects unavailable to p are restricted
```

Both make a security-relevant property of computation depend
monotonically on information consumed.

### 3.3 Permission sets and lattices

If each principal `p` is represented by `Perm(p)`, the set of actions
that principal may perform, then:

``` text
EffectiveAuthority(I) = intersection_{p in I} Perm(p)
```

is naturally interpreted in the powerset lattice over actions, with
intersection as meet.

Therefore the dissertation should not distinguish Conflux from Biba
simply by saying organisational permissions are "non-lattice" or
incomparable. Incomparable permission sets can still inhabit a lattice.

A more defensible distinction is that Conflux preserves principal
identities/provenance and obtains action-specific authority from an
existing authorisation relation rather than requiring the organisation
to assign a conventional integrity level that encodes all effects.

### 3.4 Claims requiring revision

Treat the following as unsafe until carefully qualified:

-   monotonic reduction of authority after consuming lower-authority
    information is itself novel;
-   once low-privilege information influences a computation, privilege
    cannot later increase is unique to ITES;
-   using information provenance to constrain subsequent privileged
    effects has no classical precedent.

Part B's monotonicity theorem may remain mathematically useful and
correct. Its intellectual positioning should acknowledge low-water-mark
integrity.

### 3.5 Candidate distinctions requiring prior-art search

Potentially distinctive aspects include:

-   retaining authenticated principal identities rather than only a
    generic trust label;
-   deriving effective authority from the organisation's current ACS;
-   parameterised and argument-sensitive action authority;
-   nested LLM/tool/plan execution structure;
-   separating conservative provenance, exposure measurement, and causal
    attribution;
-   verifying the security layer under arbitrary model proposals.

These are hypotheses for comparison, not established novelty claims.

## 4. LOMAC: a close classical systems analogue

LOMAC operationalises low-water-mark integrity protection in commodity
operating-system settings. It matters because it confronts the same
broad engineering tension as Conflux: conservative contamination
tracking can preserve security while destroying utility.

A high-integrity process that consumes lower-integrity information can
be dynamically demoted so that it cannot subsequently modify
higher-integrity objects. This resembles an LLM execution reading
lower-authority information and losing the ability to perform effects
unavailable to the source principal.

  -----------------------------------------------------------------------
  Dimension               LOMAC-style low-water   Conflux / Principal
                          mark                    Context
  ----------------------- ----------------------- -----------------------
  Main concern            System integrity        Authority of agent
                                                  effects

  Source metadata         Integrity labels        Principal provenance

  Computation state       Current integrity       Principal Context /
                                                  derived authority

  On lower-trust input    Demote integrity        Accumulate principal

  Future restriction      Integrity-flow/MAC rule Existing ACS permission
                                                  intersection

  Typical object          Files/processes/OS      Data, messages, tool
                          resources               results, resources

  Policy granularity      Integrity labels + OS   Potentially
                          controls                parameterised
                                                  organisational actions

  Utility issue           Process contamination   Principal-Context
                                                  contamination
  -----------------------------------------------------------------------

LOMAC should also inform planning research. Conflux's idea of avoiding
unnecessary observations is closely related to the classical problem of
contamination or label creep: reading too much causes a long-running
computation to become increasingly restricted.

## 5. Denning and lattice-based information flow

Denning's 1976 lattice model is a foundational predecessor for secure
information flow. It provides mathematical vocabulary for security
classes, combination of labels, and permitted flows.

For Conflux it matters because:

1.  combining labels from multiple inputs has a long formal history;
2.  security lattices need not be scalar hierarchies;
3.  it leads naturally to noninterference and language-based IFC.

The union of provenance and intersection of authority should be
discussed against this lineage.

## 6. Noninterference: read access is not end-to-end confidentiality

Part B's confidentiality mechanism largely asks whether the relevant
principals are allowed to read a datum before supplying it to an
execution. That is an access-safety property.

However:

``` text
Every read is authorised
```

does not imply:

``` text
Secret information cannot affect an observation available
to an unauthorised observer.
```

A system can obey local ACL checks and leak information through outputs,
control flow, success/failure behaviour, timing, or other observations.

The dissertation should therefore cover Denning-style flow security,
Goguen and Meseguer's noninterference, Rushby's work on
noninterference/channel control, Sabelfeld and Myers' survey, and later
hyperproperty formulations where useful.

SLED-V should distinguish:

**Access safety:** no forbidden read occurs.

**Effect safety:** no action violates Principal-Context authority.

**Observational confidentiality:** varying secret information does not
alter unauthorised observations except through explicitly permitted
release.

The third is relational and requires comparing executions.

## 7. Sabelfeld and Myers: gateway into language-based IFC

Sabelfeld and Myers' *Language-Based Information-Flow Security* should
become a core background reference.

It provides vocabulary for:

-   explicit and implicit flows;
-   static and dynamic enforcement;
-   noninterference;
-   termination/timing concerns;
-   precision versus soundness;
-   language-level IFC.

This is directly useful for explaining what Conflux means by
"influence." Principal Context conservatively assumes that if
information from a principal reaches an execution, that principal may
influence its output. This is intentionally an overapproximation, not a
claim of exact causal dependence.

The project should retain the distinction:

1.  **Security provenance:** conservative overapproximation used for
    enforcement.
2.  **Exposure measurement:** empirical measure of information supplied
    to the model.
3.  **Attribution:** best-effort estimate of what actually influenced a
    decision.

Only the first should support hard security guarantees unless the other
mechanisms acquire independent soundness guarantees.

## 8. Declassification and visibility

Strict information-flow policies are too restrictive for practical
systems because systems intentionally release information.
Declassification provides controlled relaxation of confidentiality.

The declassification literature commonly asks questions resembling:

-   **what** information may be released;
-   **who** may authorise the release;
-   **where** release may occur;
-   **when** it is permitted.

These map naturally to Conflux:

  Dimension   Conflux analogue
  ----------- -----------------------------------------------------------
  What        Which fields, derived values, or effects may be disclosed
  Who         Which principal/authority may authorise disclosure
  Where       Which action/tool/output channel may expose it
  When        Session, purpose, approval, expiry, workflow state

Conflux should distinguish:

``` text
visibility confinement:
    effects remain visible only to already-authorised observers

controlled disclosure / declassification:
    policy explicitly permits selected release beyond strict confinement
```

They are not the same mechanism.

## 9. Robust declassification and attacker influence

Once declassification exists, a critical question is whether an attacker
can manipulate what or when trusted code declassifies.

This is directly relevant to prompt injection. A trusted user may be
authorised to release confidential information, but an attacker-authored
document should not automatically gain the ability to influence the LLM
into exercising that authority.

A future disclosure rule should therefore ask both:

``` text
Is this release authorised?
```

and:

``` text
Which principals may influence the decision to perform it?
```

Robust-declassification literature may supply stronger formal vocabulary
for this than an entirely new Conflux-specific concept.

## 10. Endorsement and robust integrity

Endorsement is the integrity-side counterpart to declassification:
untrusted information is deliberately accepted as sufficiently
trustworthy.

This is relevant if Conflux introduces trusted transformations that can
remove or reduce conservative influence. For example:

``` text
untrusted text
    -> trusted parser / validator
    -> trusted structured result
```

Delegation should not be called endorsement. Delegation changes
authority; endorsement changes the integrity status of information.

Askarov/Myers-style attacker-control and attacker-impact work is
particularly relevant to Principal Context, attribution, trusted
transformations, and prompt injection because it explicitly reasons
about adversarial influence over trusted computation.

## 11. Nonmalleable information flow

Once a system includes both confidentiality and integrity downgrading,
it needs to prevent attackers from exploiting those exceptions.

Conflux is moving toward several explicit exceptions to simple
monotonicity:

-   delegation changes authority;
-   disclosure may relax confidentiality;
-   trusted transformations may reduce influence;
-   consent may authorise execution for particular actors;
-   policy updates may change available authority.

This motivates a stronger question:

> Under which explicit trusted transitions may authority or
> information-flow restrictions change without allowing adversarial
> influence to control those changes?

Nonmalleable IFC is therefore a relevant later-stage formal comparison.

## 12. Decentralized information-flow control

Myers and Liskov's decentralized IFC is important because it moves
beyond a single global classification scheme toward policies involving
multiple principals and decentralized authority.

This is closer to Conflux's organisational setting than a simple
high/low model.

The review should investigate:

-   principal representation;
-   ownership of policies;
-   authority to declassify;
-   principal hierarchies / acts-for relations;
-   label joins and policy composition;
-   integrity extensions;
-   dynamic delegation and revocation.

Jif and related systems provide concrete descendants.

This literature may contain prior art closer to "principal-sensitive
authority" than Biba alone, so novelty claims must be checked against
it.

## 13. Dynamic IFC systems to review

Priority practical systems include:

-   LOMAC;
-   Asbestos;
-   HiStar;
-   Flume;
-   DStar;
-   LIO;
-   CamFlow.

For each system, extract:

1.  what label is attached to data;
2.  how labels combine;
3.  what happens when a process reads more restrictive data;
4.  whether restrictions can be removed;
5.  who is trusted to remove them;
6.  how authority is represented;
7.  the trusted computing base;
8.  utility/compatibility problems;
9.  policy-change semantics;
10. what maps to an LLM-agent setting.

## 14. Taint tracking, provenance, and influence

Conflux's provenance union is structurally similar to source-set taint:

``` text
source A -> {A}
source B -> {B}
combine(A, B) -> {A, B}
```

Conflux then performs the important additional step:

``` text
source/provenance set
        ->
consult each source principal's authorisation
        ->
derive allowed effects
```

However, source-set tainting and provenance-aware policy enforcement
have extensive prior literature.

A targeted novelty search is required for systems where sink permissions
depend on source identities, including:

-   provenance-based authorization;
-   source-sensitive access control;
-   taint-based privilege attenuation;
-   compound/conjunctive principals;
-   permission-set low-water marks.

## 15. Reference monitors and least privilege

Conflux should also be grounded in classical systems-security
principles:

-   complete mediation;
-   least privilege / least authority;
-   tamper resistance;
-   a small analysable trusted mechanism;
-   separation of untrusted decision generation from trusted effect
    execution.

Its architecture can be understood as a reference monitor:

``` text
arbitrary model proposal
          |
          v
   mediation boundary
          |
    policy decision
     /         \
   deny        allow
                |
                v
             executor
```

This helps explain why arbitrary LLM behaviour is an appropriate threat
model: the LLM is untrusted code requesting privileged operations, not a
trusted security decision-maker.

## 16. Confused deputy and capabilities

Tool-using prompt injection often resembles the confused-deputy problem:

``` text
attacker-controlled information
          |
          v
privileged agent / deputy
          |
          v
resource attacker cannot access directly
```

Conflux attenuates the deputy's effective authority according to
provenance.

Capability literature is relevant to least authority, scoped delegation,
attenuation, revocation, avoiding ambient authority, and resource/action
binding.

A scoped, expiring, non-redelegable delegation should therefore be
compared with established capability and authorization mechanisms.

## 17. Access-control safety and delegation

Explicit delegation makes classical access-control safety relevant:

> Can a sequence of authorised policy mutations eventually cause a
> principal to acquire a right that should not be obtainable?

The Harrison-Ruzzo-Ullman safety result is important because
unrestricted dynamic access-control systems can make safety undecidable.

This supports SLED-V's need for a finite/restricted verification
fragment.

Delegation should use typed transitions such as:

``` text
CreateDelegation(
    delegator,
    delegate,
    action_pattern,
    resource_scope,
    expiry,
    use_limit,
    redelegation_allowed
)
```

and verification claims should state exactly which fragment is
decidable/supported.

## 18. Quantitative information flow and exposure metrics

The project has proposed measuring how much information reaches an LLM
as an empirical estimate of prompt-injection exposure.

Calling this "bits of information" would imply an information-theoretic
definition. Quantitative information-flow research provides formal
leakage measures based on uncertainty, entropy/min-entropy, gain
functions, and related models.

If Conflux does not implement a genuine QIF measure, use operational
terms such as:

-   token exposure;
-   byte exposure;
-   source-token fraction;
-   number of provenance sources;
-   duration of source presence in context;
-   context-position exposure.

QIF is a secondary reading stream unless a formal information-theoretic
metric becomes a contribution.

## 19. Mapping fourth-year ideas to classical literature

  ------------------------------------------------------------------------
  Conflux direction       Classical foundation    Key question
  ----------------------- ----------------------- ------------------------
  Principal Context       Biba / low-water mark / Is PC best understood as
                          dynamic IFC             a richer contamination
                                                  label?

  Authority intersection  lattices /              What is gained by
                          authorization           deriving the meet from
                                                  existing ACS
                                                  permissions?

  Provenance              taint / provenance      Which prior systems
                                                  retain source identity
                                                  and enforce sink policy
                                                  from it?

  Visibility              confidentiality IFC     What observations are
                                                  permitted?

  Controlled disclosure   declassification        What, who, where, and
                                                  when may information be
                                                  released?

  Trusted provenance      endorsement             When may influence
  reduction                                       safely be removed?

  Delegation              capabilities /          How may authority
                          authorization           increase explicitly
                                                  without attacker
                                                  control?

  Consent                 authorization / agency  Whose agency is being
                                                  exercised?

  Attribution             attacker control /      Who actually influenced
                          causal provenance       a decision versus merely
                                                  could have?

  Argument-level          fine-grained IFC /      Which parameters carry
  authority               authorization           authority?

  Planning                label creep / least     Can plans minimise
                          privilege               contamination while
                                                  retaining reachability?

  SLED-V safety           model checking /        Can
                          reference monitors      no-unauthorised-effect
                                                  be proved?

  SLED-V confidentiality  noninterference /       Can forbidden secrets be
                          hyperproperties         proved observationally
                                                  irrelevant?

  Persistent memory       persistent IFC state    How does low-authority
                                                  influence survive
                                                  sessions?

  Denial feedback         observable channels     Can policy outcomes leak
                                                  or influence later
                                                  behaviour?
  ------------------------------------------------------------------------

## 20. Implications for novelty claims

Avoid broad claims equivalent to:

> Conflux introduces the idea that consuming untrusted information
> should reduce future authority.

Biba/LOMAC make this historically unsafe.

Avoid:

> Existing systems use only binary trust labels whereas Conflux first
> tracks richer security context.

Decentralized IFC, provenance systems, and modern agent work make this
unsafe.

Avoid:

> Permission intersection is fundamentally outside lattice-based IFC.

Intersection is a standard meet over permission sets.

Avoid:

> Authorised reads establish confidentiality.

They do not establish noninterference.

A more defensible formulation is:

> Conflux applies low-water-mark-style contamination to tool-using AI
> agents using authenticated principal provenance and an organisation's
> existing authorization relation. Rather than assigning each input only
> a global integrity level, it retains the principals that may have
> influenced an execution and derives action-specific effective
> authority from their current permissions.

For the fourth-year work:

> Building on this foundation, the project investigates how
> principal-sensitive authority interacts with fine-grained action
> arguments, explicit delegation and consent, controlled disclosure,
> secure planning, attribution, and formal verification under arbitrary
> model proposals.

These remain positioning hypotheses until targeted prior-art searches
are complete.

## 21. Implications for the Part B interpretation

The supervisor's observation does not invalidate Part B's implementation
or theorem.

Part B established within its model:

-   a concrete principal-provenance representation for LLM-agent
    executions;
-   an ACS-based action rule;
-   authority monotonicity;
-   a bounded worst-case evaluator;
-   evidence over generated environments.

It did not adequately establish:

-   historical novelty of monotone contamination;
-   relationship to integrity IFC;
-   full confidentiality/noninterference;
-   relationship to declassification/endorsement;
-   relationship to decentralized IFC and provenance systems.

The fourth-year manuscript should correct and deepen the framing without
rewriting the archived report.

## 22. Implications for the fourth-year contribution

Principal Context and the ACS intersection rule should increasingly be
treated as inherited Part B foundation, explicitly connected to
low-water-mark integrity.

The strongest candidate fourth-year contributions are:

1.  **SLED-V / verification:** stronger formal verification of
    system-level agent defences, implementation conformance, and
    potentially relational confidentiality.
2.  **Fine-grained Principal Context semantics:** argument-sensitive
    authority, observer-sensitive disclosure, and explicit roles for
    influencing versus acting principals.
3.  **Explicit authority change:** delegation and consent semantics
    preserving clear invariants.
4.  **Security-aware planning:** minimising unnecessary
    information/authority contamination while preserving utility.
5.  **Empirical validation:** AgentDojo and realistic benchmarks plus
    mechanism ablations.

## 23. Planning as contamination minimisation

The Biba/LOMAC connection suggests a precise planning objective.

Given candidate plans, minimise contamination/authority cost subject to
security and task completion:

``` text
minimise:
    observations
    + Principal Context growth
    + loss of effective authority
    + sensitive-information exposure
    + irreversible effects

subject to:
    security invariants
    + task reachability
```

Possible measurements include:

``` text
max_t |PC_t|
sum_t |PC_t|
number of newly introduced principals
```

and action-risk-weighted authority loss.

A stronger formulation is controller synthesis:

> Is there a strategy reaching the goal without entering an authority
> state that prevents required future actions?

This connects low-water-mark contamination directly to SLED-V.

## 24. Visibility and confidentiality hierarchy

The current visibility model can be separated into:

### Level 1 --- read access

Required inputs satisfy read policy.

### Level 2 --- observer confinement

Effects influenced by confidential data are observable only by
principals authorised for the relevant information.

### Level 3 --- controlled release

A trusted policy permits selected information derived from confidential
inputs to reach a broader audience.

Level 3 is declassification and should carry explicit release authority
and robust-influence conditions.

## 25. Delegation semantics

Delegation should remain an authorization transition, not be described
as declassification or endorsement.

``` text
State S
  |
  | authorised CreateDelegation
  v
State S' with scoped modified authority
  |
  | ordinary action under new authority
  v
effect
```

Verification should ask:

1.  Was delegation authorised in the old state?
2.  Did attacker influence improperly control it?
3.  Is scope bounded?
4.  Can it expire/revoke?
5.  Can it be redelegated?
6.  Does the subsequent action pass ordinary checks?

## 26. Attribution semantics

Recommended terminology:

``` text
Security influence:
    all principals that may have influenced an action

Causal attribution:
    best-supported estimate of principals/information that
    actually influenced the model decision

Exposure:
    amount/distribution of information supplied to the model
```

Attribution should not weaken enforcement unless it becomes a sound
trusted mechanism.

## 27. SLED-V property hierarchy

### Authority safety

``` text
AG(
  Execute(a) ->
  forall p in PrincipalContext:
      Authorised(p, a)
)
```

### Provenance monotonicity

Absent an explicit trusted transformation:

``` text
PC(parent) subseteq PC(child)
```

### Delegation safety

Any authority increase is explained by an independently authorised
delegation transition.

### Read safety

No execution receives a resource contrary to read policy.

### Observational confidentiality

Executions differing only in secret information produce equivalent
observations for unauthorised principals, modulo declared
declassification.

### Robust disclosure

An unauthorised influencing principal cannot control disclosure beyond
the permitted release policy.

### Liveness / utility

Under an explicit competence/controller assumption, an authorised task
reaches its goal or a defined safe abort.

## 28. Literature coverage assessment

### Strong

-   modern prompt-injection attacks/defences;
-   contemporary system-level agent defences;
-   agent benchmarks;
-   planning;
-   formal model-checking techniques;
-   modern provenance/causal approaches;
-   persistent-memory and multi-agent risks.

### Partial

-   general IFC;
-   capabilities;
-   access control;
-   provenance;
-   noninterference;
-   formal security properties.

### Insufficient

-   Biba primary source;
-   low-water-mark integrity as direct ancestor;
-   LOMAC;
-   Denning;
-   decentralized IFC;
-   declassification taxonomy;
-   robust declassification;
-   endorsement / robust integrity;
-   attacker control and impact;
-   nonmalleable IFC;
-   dynamic IFC contamination/label-creep lessons;
-   source-identity taint/provenance enforcement;
-   access safety versus noninterference.

The missing layer is therefore foundational security literature and its
synthesis with the modern agent work.

## 29. Priority reading list

### Priority A

1.  Biba (1977), *Integrity Considerations for Secure Computer Systems*.
2.  Fraser's LOMAC papers.
3.  Denning (1976), *A Lattice Model of Secure Information Flow*.
4.  Sabelfeld & Myers (2003), *Language-Based Information-Flow
    Security*.
5.  Myers & Liskov, decentralized information-flow control.
6.  Sabelfeld/Sands declassification survey work.
7.  Zdancewic & Myers, robust declassification.
8.  Askarov & Myers, attacker control and impact.
9.  Cecchetti, Myers & Arden, nonmalleable information flow.

### Priority B

-   Asbestos
-   HiStar
-   Flume
-   DStar
-   LIO
-   CamFlow
-   dynamic taint / Data-Flow Integrity systems

### Priority C

-   Saltzer & Schroeder;
-   reference-monitor literature;
-   confused deputy;
-   capability attenuation;
-   Harrison-Ruzzo-Ullman;
-   authorization/delegation logics;
-   quantitative information flow if formal "bits" become a
    contribution.

## 30. Questions for the supervisor

1.  Do you view Principal Context primarily as a low-water-mark
    integrity mechanism or as a broader authority label derived from
    provenance?
2.  Which exact Biba low-water-mark variant did you have in mind?
3.  Should LOMAC's treatment of contamination directly inform the
    planner?
4.  Should Principal Context be presented as inherited foundation while
    SLED-V/richer semantics carry the main Part C novelty?
5.  Should the project target a noninterference-style confidentiality
    theorem or keep confidentiality to explicit access/visibility
    safety?
6.  Is visibility strict confinement, with declassification treated
    separately?
7.  Could robust-declassification/attacker-control literature form the
    basis for delegation/disclosure influence rules?
8.  Which Sabelfeld papers beyond the survey/declassification line
    should be prioritised?

## 31. Repository integration plan

Keep this report as dated analysis:

``` text
reports/analysis/2026-08-13-foundational-security-literature.md
```

Then migrate confirmed conclusions into canonical owners.

### Literature matrix

Add fields such as:

``` text
work
year
stream
security_objective
label_or_provenance_model
authority_model
downgrading_model
formal_guarantee
implementation
relation_to_conflux
novelty_risk
primary_source_verified
```

### Manuscript structure

Suggested background/related-work organization:

``` text
Security foundations
  - Integrity and low-water-mark policies
  - IFC and noninterference
  - Declassification, endorsement, decentralized authority

System-level LLM-agent security
  - Dual-LLM / CaMeL
  - IFC-oriented agent defences
  - Progent
  - PACT
  - causal provenance / FORGE-PCAS

Verification and evaluation
  - classical model checking / IFC verification
  - behavioural agent benchmarks
  - SLED/SLED-V positioning
```

### Claims ledger

Audit claims involving:

-   novelty of monotonic authority reduction;
-   novelty of provenance-based restriction;
-   novelty of source-sensitive context;
-   maximal authorization;
-   confidentiality/exfiltration guarantees.

Mathematical claims that remain correct need not be weakened;
novelty/evidence interpretation may need revision.

## 32. Tasks for coding/research agents

### Bibliography audit

``` text
Read the foundational-security report and current bibliography.
Add primary-source bibliography entries for Priority A papers.
Verify metadata from original/publisher/institutional sources.
Do not change manuscript prose or security semantics.
```

### Literature matrix

``` text
Add a classical integrity/IFC stream.
Separate paper-stated facts from inferred relationships to Conflux.
Mark primary-source verification explicitly.
```

### Novelty audit

``` text
Search the repository for novelty claims involving provenance,
monotonic authority, permission intersection, information flow,
and confidentiality. Produce a report only. Identify claims made
unsafe or ambiguous by Biba, LOMAC, decentralized IFC,
taint/provenance systems, or modern agent work.
```

### Manuscript migration

After primary reading:

``` text
Update background/related work with the classical lineage.
Preserve the distinction between historical precedent and the
project's contribution. Do not claim first generalisation of Biba
or first principal-sensitive IFC without evidence.
```

## 33. Targeted search protocol

Seed papers:

``` text
Biba 1977
Denning 1976
LOMAC Fraser
Sabelfeld & Myers 2003
Myers & Liskov decentralized IFC
robust declassification
attacker control and impact
nonmalleable information flow
```

Search terms:

``` text
"low water mark" permissions
"low water mark" provenance
provenance authorization source
taint privileges
source effective permissions
principal integrity label
compound principal authorization
decentralized IFC delegation
integrity attacker influence
dynamic IFC label creep
```

Use backward citation search for foundations and forward citation search
for later generalisations.

## 34. Source-quality policy

For foundational claims prefer:

1.  original paper/technical report;
2.  publisher or author's institutional copy;
3.  authoritative project documentation;
4.  peer-reviewed survey;
5.  secondary summaries only for discovery.

For every novelty-critical comparison, retain:

``` text
claim
supporting source
source section/passage
interpretation
confidence
remaining ambiguity
```

## 35. Conceptual cautions

**"Biba is scalar; Conflux is not."**\
Too simplistic. Security lattices may be partially ordered.

**"Biba tracks integrity; Conflux tracks permissions."**\
Closer, but explain the operational distinction carefully.

**"Provenance is new."**\
False as a broad claim.

**"Intersection makes it novel."**\
Intersection/meet is standard mathematics.

**"Declassification equals delegation."**\
False: one changes information release, the other authority.

**"Endorsement equals delegation."**\
False: endorsement changes trust in information.

**"Authorised reads prove confidentiality."**\
They do not establish noninterference.

**"Attribution can safely remove provenance."**\
Only if attribution is sound enough to join the trusted computing base.

## 36. Revised thesis narrative

A stronger historical narrative is:

> Tool-using LLM agents create a modern instance of an old
> systems-security problem: untrusted information is processed by a
> component capable of privileged effects. Classical integrity models,
> particularly Biba's low-water-mark policies and systems such as LOMAC,
> address analogous contamination by reducing a subject's effective
> integrity after it consumes less-trusted information.
> Information-flow-control research subsequently developed richer
> lattice, noninterference, decentralized-policy, declassification, and
> endorsement mechanisms.
>
> Conflux applies this lineage to AI agents but represents contamination
> as authenticated principal provenance and derives effective action
> authority from the organisation's existing authorization state. This
> provides a conservative security kernel under arbitrary model
> behaviour. The fourth-year project then asks how such
> principal-sensitive authority can support practical agent workflows
> through fine-grained policies, explicit delegation and consent,
> controlled visibility, security-aware planning, attribution, and
> formal verification.

## 37. Immediate actions

Before the next major manuscript rewrite:

-   read Biba;
-   read LOMAC;
-   read Denning;
-   read Sabelfeld & Myers;
-   read the declassification survey;
-   read decentralized IFC;
-   read robust declassification / attacker control-impact;
-   update Zotero and the literature matrix.

Before finalising novelty:

-   search provenance-aware authorization;
-   search source-set taint with sink permissions;
-   search compound/conjunctive principal authorization;
-   search decentralized integrity policies;
-   search low-water-mark policies over rich labels/permission sets;
-   re-audit PACT, Progent, CaMeL, and causal-provenance systems.

Before claiming confidentiality verification:

-   define observers;
-   define permitted disclosure;
-   distinguish access safety from noninterference;
-   implement relational verification only if making relational claims.

## 38. Final assessment

The supervisor feedback identifies a real weakness, but one that can be
repaired cleanly.

The project has a strong contemporary agent-security landscape and
substantial formal-verification coverage. What is missing is the
historical and theoretical bridge between classical integrity/IFC and
Principal Context.

Biba and LOMAC are likely central ancestors of the core Part B
mechanism. Sabelfeld/Myers, decentralized IFC, declassification,
endorsement, and attacker-influence work then provide much of the
vocabulary required for the fourth-year extensions.

The correct response is not to abandon Principal Context or conclude
that the project was already done in 1977. It is to sharpen the
contribution:

``` text
Biba / LOMAC:
    dynamic integrity contamination

Conflux foundation:
    dynamic principal-provenance contamination
    -> existing-ACS-derived action authority

Fourth-year Conflux:
    fine-grained authority
    + explicit authority change
    + controlled disclosure
    + contamination-aware planning
    + attribution
    + formal verification
    + realistic agent evaluation
```

The most important remaining literature task is to determine exactly how
much of the middle line already exists in decentralized IFC,
provenance-aware authorization, taint-based security, and
compound-principal systems. Until then, it should be treated as a
promising positioning hypothesis rather than a novelty claim.

This framing strengthens the dissertation by placing Conflux within
nearly fifty years of security research while retaining technically
substantial fourth-year questions specific to modern AI-agent systems.

## Primary-source leads

Bibliographic metadata should be verified before importing these into
the manuscript bibliography.

-   K. J. Biba. *Integrity Considerations for Secure Computer Systems*.
    1977.
-   D. E. Denning. *A Lattice Model of Secure Information Flow*. 1976.
-   T. Fraser. LOMAC / low-water-mark integrity protection work.
-   A. Sabelfeld and A. C. Myers. *Language-Based Information-Flow
    Security*. 2003.
-   A. C. Myers and B. Liskov. *A Decentralized Model for Information
    Flow Control*. 1997.
-   A. Sabelfeld and D. Sands. Declassification survey/principles work.
-   S. Zdancewic and A. C. Myers. *Robust Declassification*.
-   A. Askarov and A. C. Myers. *Attacker Control and Impact for
    Confidentiality and Integrity*.
-   E. Cecchetti, A. C. Myers, and O. Arden. *Nonmalleable Information
    Flow*.
-   J. Rushby. *Noninterference, Transitivity, and Channel-Control
    Security Policies*.
-   Saltzer and Schroeder. *The Protection of Information in Computer
    Systems*.
-   Harrison, Ruzzo, and Ullman. Access-control safety work.
