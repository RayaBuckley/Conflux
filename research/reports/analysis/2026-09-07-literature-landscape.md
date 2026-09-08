# Conflux: Final Corrected Literature Landscape

**Date:** 7 September 2026  
**Purpose:** repository-ready research reference for novelty checking, paper writing, brainstorming, and AI-coder integration.

## Method and evidence discipline

This landscape starts from the previous 40-entry Conflux matrix, corrects known bibliographic errors, audits the uniqueness and limitations of every existing entry, then expands citation chains into missing classical and 2024–2026 literatures. It deliberately separates **source-supported paper content** from **reviewer synthesis/inference**. A row marked “Needs citation verification before publication” may be used for brainstorming, but its exact BibTeX metadata should be checked before inclusion in a manuscript.

The main systematic expansion axes were: (1) history/origin-sensitive access control, (2) trust management and delegation, (3) decentralized and robust information-flow control, (4) provenance-based access control, (5) policy specification/refinement, (6) natural-language and LLM autoformalization, (7) modern symbolic agent guardrails, and (8) verification/conformance methods relevant to SLED-V.

## Executive novelty conclusions

The expanded literature substantially narrows the safe novelty claims. Conflux should **not** claim novelty for: formal policy languages; reference monitors; policy compilation/refinement; natural-language-to-formal translation; LLM-generated policies; provenance-based access control; authority depending on execution history/origin; principal-labelled information-flow control; integration of authorization and IFC; argument-sensitive policy checks; causal-history policy enforcement; or formal model-checking/conformance workflows in the abstract.

The strongest defensible research center is narrower: **a principal-context security kernel for LLM agents that conservatively propagates authenticated information-principal influence and constrains externally visible effect authority using the organization’s current authorization semantics under worst-case model behavior, then composes that hard invariant with richer policy, consent, visibility, delegation, planning and verification layers.** This remains a synthesis/working hypothesis, not a “first” claim.

The most threatening classical precedents are Abadi–Fournet execution-history access control, Myers–Liskov decentralized IFC, FLAM/FLAC, and provenance-based access control. The most threatening modern neighbors are CaMeL, Progent, FORGE/PCAS, PACT, AgentGuardian, AgentSpec, solver-aided policy verification, symbolic guardrails, and AgentRFC/AgentThread.

## Corrections to the previous landscape

- **L009:** Year corrected 2007 -> 2009. IBM primary publication page dates the CCS position paper to 2009.
- **L013:** Year corrected 2021 -> 2024. Cedar OOPSLA paper/extended version published in 2024.
- **L027:** Year corrected 2026 -> 2025. arXiv and AISec publication are 2025.
- **L033:** Year corrected 2014 -> 2010. Clarkson & Schneider Hyperproperties journal article is 2010.
- **L035:** Canonical citation standardized to 2003. Uses Advances in Computers Bounded Model Checking survey; technique was introduced earlier.
- **L037:** Replaced duplicate/mislabelled Zanzibar row. Now Abadi, Burrows, Lampson & Plotkin 1993 access-control calculus.

## Foundational access control, delegation, privilege, and dynamic policy

### L003 — The Policy Machine: A Novel Architecture and Framework for Access Control Policy Management (2001)

**Authors:** David Ferraiolo et al.  
**Stream:** Access control / policy architecture  
**Source:** https://www.nist.gov/publications/policy-machine-security-policy-management  
**Review status:** Needs full-text review

**Key contribution.** Unifying policy-machine architecture for multiple access-control models

**What is distinctive about this work.** Unifying access-control architecture intended to realize multiple policy models through a common mechanism.

**Limitations / boundary.** Does not solve policy acquisition, ambiguous intent or data-influence attribution.

**Conflux relationship.** Useful historical basis for treating organisational authorization as a substrate rather than inventing agent-specific permissions

**Recommended use.** Use as ACS substrate/background; Conflux should consume or map to established authorization semantics rather than claim to replace them.

**Connected literature:** Role-Based Access Control Models; Current Research and Open Problems in Attribute-Based Access Control; Zanzibar: Google’s Consistent, Global Authorization System; Defending Against Indirect Prompt Injection Attacks With Spotlighting

### L005 — Preventing Privilege Escalation (2003)

**Authors:** Niels Provos; Markus Friedl; Peter Honeyman  
**Stream:** Privilege separation  
**Source:** https://www.usenix.org/conference/12th-usenix-security-symposium/preventing-privilege-escalation  
**Review status:** Existing Conflux reference

**Key contribution.** Privilege separation and reduction

**What is distinctive about this work.** Practical privilege-separation redesign of OpenSSH showing that least-privilege architecture can contain compromise.

**Limitations / boundary.** Relies on trusted decomposition, OS boundaries and a small privileged monitor; does not track information influence.

**Conflux relationship.** Already cited; retain as classical security anchor

**Recommended use.** Already cited; retain as classical security anchor

**Connected literature:** Protection in Operating Systems; Enforceable Security Policies; Defeating Prompt Injections by Design (CaMeL); Contextual Integrity in LLMs via Reasoning and Reinforcement Learning

### L013 — Cedar: A New Language for Expressive, Fast, Safe, and Analyzable Authorization (2024)

**Authors:** Joseph W. Cutler; Craig Disselkoen; Aaron Eline; Shaobo He; Kyle Headley; Michael Hicks; Kesha Hietala; Eleftherios Ioannidis; John Kastner; Anwar Mamat; Darin McAdams; Matt McCutchen; Neha Rungta; Emina Torlak; Andrew Wells  
**Stream:** Authorization language  
**Source:** https://arxiv.org/abs/2403.04651  
**Review status:** Verified primary; metadata corrected

**Key contribution.** Fine-grained authorization policy language and evaluator

**What is distinctive about this work.** Production-oriented authorization language combining RBAC/ABAC/ReBAC expressiveness with analyzability and fast evaluation.

**Limitations / boundary.** Engine correctness does not prove policy completeness/intent; history requires explicit external state.

**Conflux relationship.** Must cite when Cedar is part of implementation; separates ACS decision engine from Conflux influence semantics

**Recommended use.** Use as ACS substrate/background; Conflux should consume or map to established authorization semantics rather than claim to replace them.

**Connected literature:** Defending Against Indirect Prompt Injection Attacks With Spotlighting; Autoformalization of Agent Instructions into Policy-as-Code; Zanzibar: Google’s Consistent, Global Authorization System; XACML 2.0 / 3.0 policy language lineage

### L029 — Role-Based Access Control Models (1996)

**Authors:** Ravi Sandhu; Edward Coyne; Hal Feinstein; Charles Youman  
**Stream:** Access control  
**Source:** https://doi.org/10.1109/2.485845  
**Review status:** Add foundational citation

**Key contribution.** Canonical RBAC family/model

**What is distinctive about this work.** Canonical role-centered organizational authorization abstraction.

**Limitations / boundary.** Role engineering, role explosion and context/history-sensitive decisions remain hard.

**Conflux relationship.** Useful canonical access-control citation beyond a survey when discussing role-based organisational authority

**Recommended use.** Use as ACS substrate/background; Conflux should consume or map to established authorization semantics rather than claim to replace them.

**Connected literature:** The Policy Machine: A Novel Architecture and Framework for Access Control Policy Management; Current Research and Open Problems in Attribute-Based Access Control; Zanzibar: Google’s Consistent, Global Authorization System

### L030 — Current Research and Open Problems in Attribute-Based Access Control (2017)

**Authors:** Daniel Servos; Sylvia L. Osborn  
**Stream:** Access control / ABAC  
**Source:** https://doi.org/10.1145/3007204  
**Review status:** Existing Conflux reference

**Key contribution.** Survey/formal framing of ABAC

**What is distinctive about this work.** Comprehensive ABAC survey and open-problem map for attributes, administration, delegation and scalability.

**Limitations / boundary.** Expressiveness increases policy complexity and does not automatically model causal influence.

**Conflux relationship.** Retain, but supplement with RBAC/policy-machine/Cedar where appropriate

**Recommended use.** Use as ACS substrate/background; Conflux should consume or map to established authorization semantics rather than claim to replace them.

**Connected literature:** The Policy Machine: A Novel Architecture and Framework for Access Control Policy Management; Role-Based Access Control Models; Cedar: A New Language for Expressive, Fast, Safe, and Analyzable Authorization; Defending Against Indirect Prompt Injection Attacks With Spotlighting

### L031 — Protection in Operating Systems (1976)

**Authors:** Michael A. Harrison; Walter L. Ruzzo; Jeffrey D. Ullman  
**Stream:** Access-control safety  
**Source:** https://dl.acm.org/doi/10.1145/360303.360333  
**Review status:** Add foundational citation

**Key contribution.** HRU access-control model and safety problem

**What is distinctive about this work.** Canonical access-control safety result showing unrestricted right-acquisition reachability can be undecidable.

**Limitations / boundary.** General undecidability does not apply to every finite/restricted fragment.

**Conflux relationship.** Important when claiming decidability/completeness of policy/authority verification

**Recommended use.** Use to make SLED-V verdicts precise: distinguish runtime-enforceable safety, bounded checking, unbounded invariant proofs, and relational confidentiality.

**Connected literature:** Preventing Privilege Escalation; Enforceable Security Policies; Principles of Model Checking; Bounded Model Checking; SAT-Based Model Checking without Unrolling (IC3)

### L032 — Enforceable Security Policies (2000)

**Authors:** Fred B. Schneider  
**Stream:** Runtime enforcement theory  
**Source:** https://www.cs.cornell.edu/fbs/publications/EnfSecPols.pdf  
**Review status:** Add foundational citation

**Key contribution.** Security automata characterize execution-monitor enforceable policies

**What is distinctive about this work.** Foundational characterization of runtime monitor-enforceable security/safety policies.

**Limitations / boundary.** Execution monitors cannot enforce arbitrary hyperproperties/liveness and assume complete mediation.

**Conflux relationship.** Clarifies which Conflux/SLED properties can be enforced as safety properties versus hyperproperties/liveness

**Recommended use.** Direct comparison target: identify what is trusted, what provenance granularity is tracked, where policy comes from, and whether enforcement is model-independent.

**Connected literature:** Preventing Privilege Escalation; Policy Compiler for Secure Agentic Systems / FORGE; Principles of Model Checking; Hyperproperties

### L037 — A Calculus for Access Control in Distributed Systems (1993)

**Authors:** Martín Abadi; Michael Burrows; Butler W. Lampson; Gordon D. Plotkin  
**Stream:** Delegation / access-control logic  
**Source:** https://era.ed.ac.uk/handle/1842/207  
**Review status:** Verified primary; replaced mislabelled duplicate Zanzibar row

**Key contribution.** Logical account of principals, requests, ACLs, delegation, and “speaks for” / acting-on-behalf-of relationships in distributed systems.

**What is distinctive about this work.** Foundational logic of principals speaking/acting on behalf of others and delegated distributed authority.

**Limitations / boundary.** Credential/policy grounding must be trustworthy; does not model data influence.

**Conflux relationship.** Direct foundation for distinguishing InfluencingPrincipals from ActingFor/delegation/consent principals; does not model information provenance as authority contamination.

**Recommended use.** Use as ACS substrate/background; Conflux should consume or map to established authorization semantics rather than claim to replace them.

**Connected literature:** Zanzibar: Google’s Consistent, Global Authorization System; The Policy Machine: A Novel Architecture and Framework for Access Control Policy Management; Defending Against Indirect Prompt Injection Attacks With Spotlighting

### L038 — Zanzibar: Google’s Consistent, Global Authorization System (2019)

**Authors:** Ruoming Pang et al.  
**Stream:** Distributed authorization  
**Source:** https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/  
**Review status:** Verified primary

**Key contribution.** Relationship-based global authorization

**What is distinctive about this work.** Production demonstration of global, consistent, relationship-based authorization at enormous scale.

**Limitations / boundary.** Assumes applications maintain correct relation tuples/configuration; no agent influence or policy acquisition semantics.

**Conflux relationship.** Commercial relevance for mapping principal/resource authority at scale

**Recommended use.** Use as ACS substrate/background; Conflux should consume or map to established authorization semantics rather than claim to replace them.

**Connected literature:** The Policy Machine: A Novel Architecture and Framework for Access Control Policy Management; Defending Against Indirect Prompt Injection Attacks With Spotlighting; Role-Based Access Control Models; Cedar / fine-grained authorization lineage: Zanzibar

### L039 — XACML 2.0 / 3.0 policy language lineage (2005)

**Authors:** OASIS XACML Technical Committee  
**Stream:** Authorization policy standard  
**Source:** https://www.oasis-open.org/standard/xacmlv3-0/  
**Review status:** Standards reference

**Key contribution.** Attribute-based policy decision and enforcement architecture

**What is distinctive about this work.** Standard PDP/PEP architecture and attribute-based policy/combining semantics used across enterprise authorization.

**Limitations / boundary.** Policy can be verbose/complex; history/provenance require external attributes/state; no intent inference.

**Conflux relationship.** Historical standard relevant to Text2Policy and modern Cedar comparison

**Recommended use.** Use as ACS substrate/background; Conflux should consume or map to established authorization semantics rather than claim to replace them.

**Connected literature:** Automated Extraction of Security Policies from Natural-Language Software Documents (Text2Policy); Cedar: A New Language for Expressive, Fast, Safe, and Analyzable Authorization; Defending Against Indirect Prompt Injection Attacks With Spotlighting

### L040 — Conflicts in Policy-Based Distributed Systems Management (1999)

**Authors:** Emil Lupu; Morris Sloman  
**Stream:** Policy analysis  
**Source:** https://doi.org/10.1109/32.798323  
**Review status:** Add foundational citation

**Key contribution.** Detects/characterizes policy conflicts in distributed systems

**What is distinctive about this work.** Early systematic analysis of authorization/obligation policy conflicts and resolution strategies.

**Limitations / boundary.** Conflict-free policy can still be incomplete or semantically wrong.

**Conflux relationship.** Important precursor to contradiction/conflict checking in FORGE and autoformalized policy sets

**Recommended use.** Use to position Conflux policy compilation as part of a long policy-engineering lineage; distinguish specification/refinement from runtime authority derivation.

**Connected literature:** Security Policy Specification Using a Graphical Approach (LaSCO); The Ponder Policy Specification Language; Security and Management Policy Specification; Security Policy Refinement Using Data Integration: A Position Paper; Policy Compiler for Secure Agentic Systems / FORGE

### N001 — Access Control Based on Execution History (2003)

**Authors:** Martín Abadi; Cédric Fournet  
**Stream:** History-based access control / privilege attenuation  
**Source:** https://www.microsoft.com/en-us/research/publication/access-control-based-execution-history/  
**Review status:** Verified primary

**Key contribution.** Determines run-time rights from attributes and origins of any code that has executed, plus explicit requests to augment rights; proposed as an alternative to stack inspection.

**What is distinctive about this work.** Early explicit model where authority is a function of execution history and code origins, addressing limitations of stack-based access control.

**Limitations / boundary.** The paper concerns code-origin history in extensible software, not natural-language data provenance, multi-principal information influence, or LLM tool selection.

**Reviewer inference for Conflux.** Mapping “code that has run” to “information that influenced an LLM” is non-trivial because semantic influence is much less observable than call history.

**Conflux relationship.** Conflux must not claim that accumulated origins/history constraining authority is itself novel; the candidate distinction is authenticated information-principal provenance plus current ACS semantics under arbitrary model behavior.

**Recommended use.** Mandatory historical comparison in Principal Context / authority monotonicity related work.

**Connected literature:** Preventing Privilege Escalation; IFC agent defense; CaMeL; stack inspection

### N002 — Decentralized Trust Management (PolicyMaker) (1996)

**Authors:** Matt Blaze; Joan Feigenbaum; Jack Lacy  
**Stream:** Trust management / distributed authorization  
**Source:** https://archive.dimacs.rutgers.edu/TechnicalReports/abstracts/1996/96-17.html  
**Review status:** Verified primary

**Key contribution.** Separates trust management as a problem of expressing security policy and credentials, checking compliance, and delegating trust to third parties; introduces PolicyMaker.

**What is distinctive about this work.** One of the foundational trust-management systems that directly binds principals/credentials to authorized actions.

**Limitations / boundary.** Assumes policies/credentials already encode intended authority; does not model information flows or data-origin influence.

**Reviewer inference for Conflux.** Trust-management proofs answer whether a request is authorized, not whether untrusted information causally produced that request.

**Conflux relationship.** Strong foundation for ACS/delegation semantics; Conflux adds influence-derived restriction rather than replacing trust management.

**Recommended use.** Use in delegation/ACS lineage and to separate authorization proof from influence tracking.

**Connected literature:** Ponder; access-control calculus; KeyNote; Delegation Logic; RT framework

### N003 — The KeyNote Trust-Management System Version 2 (1999)

**Authors:** Matt Blaze; Joan Feigenbaum; John Ioannidis; Angelos D. Keromytis  
**Stream:** Trust management / policy credentials  
**Source:** https://www.rfc-editor.org/info/rfc2704/  
**Review status:** Verified standard/primary

**Key contribution.** General-purpose language and architecture for policies, credentials, action attributes, and direct authorization of security-critical actions.

**What is distinctive about this work.** Operationalized trust management with a compact, application-independent policy language and credential semantics.

**Limitations / boundary.** No causal/information-provenance model; correctness depends on policy and credential issuance.

**Reviewer inference for Conflux.** Agent actions with semantically rich arguments may require richer structured schemas than KeyNote-style attribute sets.

**Conflux relationship.** Important predecessor for action/argument policy and delegation; Conflux should not claim argument-sensitive authorization as new.

**Recommended use.** Historical policy/credential reference for structured action authorization.

**Connected literature:** PolicyMaker; Binder; Delegation Logic; Progent

### N004 — Binder, a Logic-Based Security Language (2002)

**Authors:** John DeTreville  
**Stream:** Logic-based security policy / delegation  
**Source:** https://www.microsoft.com/en-us/research/publication/binder-a-logic-based-security-language/  
**Review status:** Verified primary

**Key contribution.** Represents security statements as distributed logic programs, clarifying certificates, delegation, and policy reasoning.

**What is distinctive about this work.** Treats security language as open logic programs rather than fixed certificate/ACL data structures.

**Limitations / boundary.** Expressive policy language, not policy acquisition or provenance enforcement; assumes trustworthy statements and communication.

**Reviewer inference for Conflux.** Logical expressiveness increases policy-analysis and authoring complexity and does not solve contextual ambiguity.

**Conflux relationship.** FORGE’s Datalog lineage has deep precedent; Conflux uniqueness cannot be “logic-based formal policy enforcement.”

**Recommended use.** Policy-language ancestry and FORGE contextualization.

**Connected literature:** KeyNote; Cassandra; FORGE

### N005 — Cassandra: Distributed Access Control Policies with Tunable Expressiveness (2004)

**Authors:** Moritz Y. Becker; Peter Sewell  
**Stream:** Distributed access control / trust management  
**Source:** https://www.microsoft.com/en-us/research/publication/cassandra-distributed-access-control-policies-with-tunable-expressiveness/  
**Review status:** Verified primary

**Key contribution.** Role-based trust-management language based on Datalog with constraints; supports hierarchy, delegation, separation of duties, revocation, credential discovery, and trust negotiation with formal semantics.

**What is distinctive about this work.** Adjustable constraint domain trades expressiveness and complexity while retaining formal query/enforcement semantics.

**Limitations / boundary.** No information-influence tracking; the model presupposes formal policy credentials.

**Reviewer inference for Conflux.** Complex organizational semantics still require correct policy engineering and can become difficult to explain to end users.

**Conflux relationship.** Relevant to explicit delegation/ACS mutation and to FORGE-like Datalog policy; Principal Context should compose with such engines.

**Recommended use.** Delegation, revocation, and rich ACS prior art.

**Connected literature:** Ponder; Binder; RT; FORGE

### N006 — The UCONABC Usage Control Model (2004)

**Authors:** Jaehong Park; Ravi Sandhu  
**Stream:** Usage control / dynamic authorization  
**Source:** https://doi.org/10.1145/984334.984339  
**Review status:** Verified primary

**Key contribution.** Generalizes access control with Authorizations, oBligations, Conditions, continuity of decision, and mutable attributes during use.

**What is distinctive about this work.** Integrates ongoing authorization, obligations, environmental conditions, and mutability in one model.

**Limitations / boundary.** Does not attribute decisions to information provenance; core model leaves administration/delegation for later work.

**Reviewer inference for Conflux.** Continuous checks can interact subtly with long-running agent plans and side effects, requiring transactional semantics.

**Conflux relationship.** Useful for consent, approval, ongoing validity, and dynamic ACS semantics; Conflux should not present continuous policy checking as novel.

**Recommended use.** Stateful policy/obligation background for production semantics.

**Connected literature:** ABAC; Cedar; PolicyBank

### N029 — A Comparison of Commercial and Military Computer Security Policies (Clark-Wilson) (1987)

**Authors:** David D. Clark; David R. Wilson  
**Stream:** Integrity / commercial security policy  
**Source:** https://dblp.org/rec/conf/sp/ClarkW87  
**Review status:** Verified bibliographic

**Key contribution.** Argues commercial systems require integrity policies distinct from confidentiality lattices, emphasizing well-formed transactions, constrained data, and separation of duties.

**What is distinctive about this work.** Canonical formalization of commercial data integrity and separation-of-duty concerns.

**Limitations / boundary.** Does not model information provenance, contextual privacy, or probabilistic decision components.

**Reviewer inference for Conflux.** An action may be authorized for all influencers yet violate transaction integrity or separation-of-duty rules.

**Conflux relationship.** Supports keeping a separate safety/integrity policy layer beyond the PE theorem.

**Recommended use.** Classical integrity boundary around PE security objective.

**Connected literature:** Chinese Wall; UCON; policy conflicts

### N030 — The Chinese Wall Security Policy (1989)

**Authors:** David F. C. Brewer; Michael J. Nash  
**Stream:** History-based commercial confidentiality  
**Source:** https://dblp.dagstuhl.de/rec/conf/sp/BrewerN89.html  
**Review status:** Verified bibliographic

**Key contribution.** Access decisions depend on prior accesses/conflict-of-interest classes, giving a dynamic policy not expressible by simple static Bell-LaPadula labels.

**What is distinctive about this work.** Canonical dynamic commercial policy where access history changes future permissible accesses.

**Limitations / boundary.** Narrow conflict-of-interest scenario; no causal influence or action-generation model.

**Reviewer inference for Conflux.** Agent planning must preserve history-dependent constraints across sessions and parallel branches.

**Conflux relationship.** Useful for demonstrating that the ACS may itself be history-dependent; Principal Context should query current policy rather than assume static permissions.

**Recommended use.** Dynamic ACS/history examples and SLED-V environment state.

**Connected literature:** History-based access control; Clark-Wilson; UCON

### N033 — Design of a Role-Based Trust-Management Framework (RT) (2002)

**Authors:** Ninghui Li; John C. Mitchell; William H. Winsborough  
**Stream:** Trust management / roles / delegation  
**Source:** https://www.cs.purdue.edu/homes/ninghui/abstracts/rt_oakland02.html  
**Review status:** Verified primary

**Key contribution.** Family of role-based trust-management languages with localized role authority, linked and parameterized roles, delegation, threshold/separation-of-duty constructs, translated to Datalog.

**What is distinctive about this work.** Combines RBAC and trust management with compact credential forms and tractable formal semantics.

**Limitations / boundary.** No information-provenance/influence model or natural-language policy acquisition.

**Reviewer inference for Conflux.** Role-based abstractions may hide resource/argument distinctions needed by agents unless parameterized roles are used carefully.

**Conflux relationship.** Useful for formal delegation semantics and provider-neutral ACS; Conflux should not reinvent role/delegation logic.

**Recommended use.** Delegation and distributed organizational authorization.

**Connected literature:** PolicyMaker; Cassandra; Delegation Logic; RBAC

### N034 — Delegation Logic: A Logic-Based Approach to Distributed Authorization (2003)

**Authors:** Ninghui Li; Benjamin N. Grosof; Joan Feigenbaum  
**Stream:** Delegation / trust management logic  
**Source:** https://doi.org/10.1145/605434.605438  
**Review status:** Verified primary

**Key contribution.** Treats authorization as proof of compliance and defines a logic for policies, credentials, requests and delegation in open distributed systems.

**What is distinctive about this work.** Provides expressive logic semantics for chains and restrictions of delegated authority.

**Limitations / boundary.** No provenance-based contamination or contextual information-flow model.

**Reviewer inference for Conflux.** Delegating action authority should be separate from trusting data produced by the delegate; Conflux needs both concepts.

**Conflux relationship.** Supports modelling CreateDelegation as an ACS-controlled action distinct from ordinary permission possession.

**Recommended use.** Formal delegation semantics and ActingFor distinction.

**Connected literature:** Access-control calculus; PolicyMaker; RT; Ponder

### N035 — Stack Inspection: Theory and Variants / Java Stack Inspection Lineage (1999)

**Authors:** Dan S. Wallach; Andrew W. Appel; Edward W. Felten  
**Stream:** Stack inspection / history-sensitive privilege  
**Source:** https://www.cs.princeton.edu/research/techreps/536  
**Review status:** Needs exact canonical citation verification before publication

**Key contribution.** Formal and practical analysis of stack inspection, where current privileges depend on the call stack and code-origin permissions.

**What is distinctive about this work.** Made stack-dependent access checking a tractable object of formal analysis in mobile-code runtimes.

**Limitations / boundary.** Call-stack provenance is explicit and syntactic; it does not capture semantic data influence.

**Reviewer inference for Conflux.** LLM execution erases ordinary call-stack causality, motivating explicit provenance propagation.

**Conflux relationship.** Use alongside Abadi/Fournet to show lineage from stack -> execution history -> data/influence history.

**Recommended use.** Historical lineage only; verify exact citation before BibTeX insertion.

**Connected literature:** Execution-history access control; privilege separation; Biba

### N039 — Capability Myths Demolished (2003)

**Authors:** Mark S. Miller; Ka-Ping Yee; Jonathan Shapiro  
**Stream:** Capability security / least authority  
**Source:** http://srl.cs.jhu.edu/pubs/SRL2003-02.pdf  
**Review status:** Needs exact canonical citation verification before publication

**Key contribution.** Clarifies object-capability semantics and rebuts common claims that capability systems inherently lack confinement, revocation, or least-privilege structure.

**What is distinctive about this work.** Influential clarification that capability authority is concrete, composable, delegable, and compatible with least authority.

**Limitations / boundary.** Does not model natural-language influence, contextual norms, or policy discovery; capability distribution itself must be correct.

**Reviewer inference for Conflux.** A capability held by an agent process can still be misused due to prompt injection unless capability acquisition/use is bound to influence semantics.

**Conflux relationship.** Useful to compare ACS-intersection authority with capability-based least authority and scoped delegation; Conflux should support capability-backed providers without conflating capabilities with provenance.

**Recommended use.** Capability/delegation design-space comparison.

**Connected literature:** CaMeL capabilities; Delegation Logic; Capsicum

### N040 — Capsicum: Practical Capabilities for UNIX (2010)

**Authors:** Robert N. M. Watson; Jonathan Anderson; Ben Laurie; Kris Kennaway  
**Stream:** Capability security / sandboxing  
**Source:** https://www.usenix.org/legacy/events/sec10/tech/full_papers/Watson.pdf  
**Review status:** Needs exact canonical citation verification before publication

**Key contribution.** Introduces capability mode and capability-oriented descriptors for practical least-privilege sandboxing of UNIX applications.

**What is distinctive about this work.** Demonstrates capabilities can be integrated into a mainstream UNIX API with practical compartmentalization.

**Limitations / boundary.** Process/resource isolation does not decide which agent-generated action should be authorized.

**Reviewer inference for Conflux.** Conflux can use Capsicum-like confinement to reduce impact of mediator/executor bugs, but it does not replace the Principal Context decision rule.

**Conflux relationship.** Strong production-hardening reference for least-privilege executors and capability tokens.

**Recommended use.** Production architecture / sandboxing background.

**Connected literature:** Capability Myths; privilege separation; CaMeL

### N044 — The Protection of Information in Computer Systems (1975)

**Authors:** Jerome H. Saltzer; Michael D. Schroeder  
**Stream:** Security design principles / reference monitoring  
**Source:** https://web.mit.edu/Saltzer/www/publications/protection/  
**Review status:** Needs exact canonical citation verification before publication

**Key contribution.** Systematizes security design principles including least privilege, complete mediation, separation of privilege, economy of mechanism, fail-safe defaults, and psychological acceptability.

**What is distinctive about this work.** Canonical synthesis of practical security principles that still structure modern reference-monitor designs.

**Limitations / boundary.** Design principles rather than a formal agent threat model or executable policy language.

**Reviewer inference for Conflux.** Conflux’s novelty should be in its specific agent security semantics, not standard reference-monitor/least-privilege architecture.

**Conflux relationship.** Mandatory foundational citation for security-kernel architecture and claims about complete mediation/least privilege.

**Recommended use.** Foundational system-security design section.

**Connected literature:** Enforceable Security Policies; privilege separation; CaMeL; FORGE

## Information flow, provenance, contextual norms, and authority from origins

### L006 — Privacy as Contextual Integrity (2004)

**Authors:** Helen Nissenbaum  
**Stream:** Contextual integrity / privacy  
**Source:** https://digitalcommons.law.uw.edu/wlr/vol79/iss1/10/  
**Review status:** Verified primary

**Key contribution.** Privacy as conformity with context-specific informational norms

**What is distinctive about this work.** Reframes privacy as context-relative informational norms rather than secrecy or user control alone.

**Limitations / boundary.** Conceptual framework; norm grounding, context identification and disagreement remain hard.

**Conflux relationship.** Shows authorization alone is not sufficient to capture appropriateness of information flows

**Recommended use.** Treat contextual appropriateness as a policy dimension distinct from bare ACS authorization; use it to motivate visibility/consent/context policies without weakening the hard Principal-Context authority invariant.

**Connected literature:** Privacy and Contextual Integrity: Framework and Applications; A Critical Evaluation of Defenses Against Prompt Injection Attacks; AI Agents May Always Fall for Prompt Injections

### L007 — Privacy and Contextual Integrity: Framework and Applications (2006)

**Authors:** Adam Barth; Anupam Datta; John C. Mitchell; Helen Nissenbaum  
**Stream:** Contextual integrity / formalization  
**Source:** https://theory.stanford.edu/~jcm/papers/barth-datta-mitchell-nissenbaum-2006.pdf  
**Review status:** Verified primary

**Key contribution.** Formalizes transmission norms including actors, information and temporal conditions

**What is distinctive about this work.** Turns Contextual Integrity into machine-reasonable transmission norms over actors, information and history.

**Limitations / boundary.** Correctness depends on faithful norm formalization and trustworthy event facts; no automatic norm discovery.

**Conflux relationship.** Provides a formal bridge from CI to trace-level verification; particularly relevant to richer Conflux policies

**Recommended use.** Treat contextual appropriateness as a policy dimension distinct from bare ACS authorization; use it to motivate visibility/consent/context policies without weakening the hard Principal-Context authority invariant.

**Connected literature:** Privacy as Contextual Integrity; A Critical Evaluation of Defenses Against Prompt Injection Attacks; AI Agents May Always Fall for Prompt Injections; Hyperproperties

### L019 — Contextual Integrity in LLMs via Reasoning and Reinforcement Learning (2025)

**Authors:** Guangchen Lan et al.  
**Stream:** Contextual integrity / model alignment  
**Source:** https://arxiv.org/abs/2506.04245  
**Review status:** Verified primary

**Key contribution.** Explicit CI reasoning and RL to reduce inappropriate disclosure

**What is distinctive about this work.** Operationalizes Contextual Integrity as an LLM reasoning/training objective for privacy-sensitive agent decisions.

**Limitations / boundary.** Model-level and probabilistic; norm correctness/generalization remain fallible.

**Conflux relationship.** Useful complement: Conflux can enforce hard authority while CI model handles context-sensitive appropriateness

**Recommended use.** Treat contextual appropriateness as a policy dimension distinct from bare ACS authorization; use it to motivate visibility/consent/context policies without weakening the hard Principal-Context authority invariant.

**Connected literature:** StruQ: Defending Against Prompt Injection with Structured Queries; Defeating Prompt Injections by Design (CaMeL); Progent: Programmable Privilege Control for LLM Agents; Policy Compiler for Secure Agentic Systems / FORGE; The Granularity Mismatch in Agent Security: Argument-Level Provenance Solves Enforcement and Isolates the LLM Reasoning Bottleneck (PACT); Preventing Privilege Escalation

### N007 — A Decentralized Model for Information Flow Control (1997)

**Authors:** Andrew C. Myers; Barbara Liskov  
**Stream:** Decentralized information-flow control  
**Source:** https://www.cs.cornell.edu/andru/papers/iflow-sosp97/paper.html  
**Review status:** Verified primary

**Key contribution.** Introduces decentralized labels/owners/readers so mutually distrustful principals can control dissemination and selectively declassify.

**What is distinctive about this work.** Combines fine-grained IFC with decentralized authority and owner-controlled declassification.

**Limitations / boundary.** Primarily confidentiality/flow, not action authority derived from all information influencers; assumes explicit labels and language/runtime enforcement.

**Reviewer inference for Conflux.** LLM influence is semantically broad, whereas static IFC tracks syntactic/data dependencies; correspondence must be specified carefully.

**Conflux relationship.** Mandatory comparison: principal-labelled information predates Conflux; candidate novelty is converting influencing-principal provenance into action authority under an ACS rather than simply constraining flows.

**Recommended use.** Central classical comparison in security semantics.

**Connected literature:** DLM journal; robust declassification; NMIFC; FLAM; IFC agent defense

### N008 — Protecting Privacy Using the Decentralized Label Model (2000)

**Authors:** Andrew C. Myers; Barbara Liskov  
**Stream:** Decentralized information-flow control  
**Source:** https://dblp.org/rec/journals/tosem/MyersL00.html  
**Review status:** Verified bibliographic/primary lineage

**Key contribution.** Extended treatment and language implementation of the decentralized label model, with static checking and decentralized declassification.

**What is distinctive about this work.** Connects decentralized IFC semantics to a practical static language system.

**Limitations / boundary.** Requires programs that can be statically checked; not aimed at opaque nondeterministic LLM components.

**Reviewer inference for Conflux.** A direct port to LLM agents would either overtaint aggressively or require trusted semantic abstractions around model calls.

**Conflux relationship.** Useful contrast for why Conflux treats the LLM as an opaque influence amplifier and mediates effects instead of verifying internal flow.

**Recommended use.** Explain relation between program IFC and opaque-LLM system enforcement.

**Connected literature:** DLM; robust declassification; NMIFC; FLAM

### N009 — Robust Declassification (2001)

**Authors:** Steve Zdancewic; Andrew C. Myers  
**Stream:** Information-flow control / attacker influence  
**Source:** https://dblp.org/rec/conf/csfw/ZdancewicM01.html  
**Review status:** Verified bibliographic

**Key contribution.** Defines robust declassification so attackers cannot influence what confidential information is declassified.

**What is distinctive about this work.** Makes confidentiality release depend explicitly on integrity/control of the declassification decision.

**Limitations / boundary.** Targets declassification of information, not general tool/action authority or organizational permissions.

**Reviewer inference for Conflux.** Agent effects often combine integrity, authority and confidentiality; one declassification condition alone will not capture all harms.

**Conflux relationship.** Strong conceptual precursor to “low-integrity influence must not cause higher-authority effects”; should inform visibility and confidential output rules.

**Recommended use.** Use to ground attacker-influence/declassification comparisons rather than inventing this intuition anew.

**Connected literature:** DLM; nonmalleable IFC; FLAM; contextual manipulation

### N010 — Nonmalleable Information Flow Control (2017)

**Authors:** Ethan Cecchetti; Andrew C. Myers; Owen Arden  
**Stream:** Information-flow control / integrity and downgrading  
**Source:** https://www.cs.cornell.edu/andru/papers/nmifc/  
**Review status:** Verified primary

**Key contribution.** Unifies robust declassification and transparent endorsement in nonmalleable information flow, controlling both confidentiality and integrity downgrades.

**What is distinctive about this work.** Provides a dual treatment of confidentiality and integrity downgrading with compositional security guarantees.

**Limitations / boundary.** Static typed-language setting; not an organizational ACS or tool-action policy system.

**Reviewer inference for Conflux.** Applying NMIFC to LLM outputs still requires deciding what structured facts/actions count as trusted endorsement.

**Conflux relationship.** Important for any “trusted provenance removal”, endorsement, summarization, or privileged-instruction feature.

**Recommended use.** Security conditions for provenance downgrading/endorsement extensions.

**Connected literature:** Robust declassification; FLAM; FLAC; PACT

### N011 — Flow-Limited Authorization (FLAM) (2014)

**Authors:** Owen Arden; Jed Liu; Andrew C. Myers  
**Stream:** Authorization + information-flow control  
**Source:** https://www.cs.cornell.edu/andru/papers/flam/  
**Review status:** Verified primary

**Key contribution.** Integrates authorization and IFC and introduces robust authorization, ensuring attackers cannot improperly influence authorization decisions or learn confidential trust relationships.

**What is distinctive about this work.** Unifies authorization and IFC instead of treating access decisions and information flow as separate subsystems.

**Limitations / boundary.** Not designed for natural-language agent actions or provenance derived from arbitrary documents/tool outputs.

**Reviewer inference for Conflux.** Its abstract principal algebra may be richer but less directly mappable to provider ACSs than Conflux’s intended adapter model.

**Conflux relationship.** Mandatory novelty boundary: Conflux cannot claim first integration of authorization and information-flow ideas; it must explain Principal Context/ACS mapping and LLM-specific threat model.

**Recommended use.** Core classical comparator for Principal Context semantics.

**Connected literature:** DLM; robust declassification; NMIFC; FLAC; IFC agent defense

### N012 — A Calculus for Flow-Limited Authorization (FLAC) (2016)

**Authors:** Owen Arden; Andrew C. Myers  
**Stream:** Authorization + information-flow control  
**Source:** https://privacytools.seas.harvard.edu/publications/calculus-flow-limited-authorization  
**Review status:** Verified primary

**Key contribution.** A language/calculus for securely implementing dynamic authorization mechanisms with noninterference and robust declassification guarantees.

**What is distinctive about this work.** Verifies authorization implementations by construction while supporting policy changes and rich decentralized mechanisms.

**Limitations / boundary.** Requires implementing mechanisms in the restricted calculus; not a general verifier for arbitrary Python/agent frameworks.

**Reviewer inference for Conflux.** Production Conflux adapters would still require refinement/conformance evidence from the formal core to effectful providers.

**Conflux relationship.** Relevant to making the verified transition kernel executable rather than separately modelling the implementation.

**Recommended use.** Formal-kernel architecture and authorization/IFC verification lineage.

**Connected literature:** FLAM; Principles of Model Checking; IC3

### N013 — A Provenance-Based Access Control Model (2012)

**Authors:** Jaehong Park; Dang Nguyen; Ravi S. Sandhu  
**Stream:** Provenance-based access control  
**Source:** https://dblp.org/rec/conf/pst/ParkNS12.html  
**Review status:** Verified bibliographic

**Key contribution.** Uses provenance information and dependency paths as attributes for access-control decisions.

**What is distinctive about this work.** Makes provenance a first-class source of authorization conditions rather than merely an audit record.

**Limitations / boundary.** Data provenance is used to decide resource access; the work does not model adversarial semantic influence of data on LLM-generated actions.

**Reviewer inference for Conflux.** General provenance policies can be highly application-specific; Conflux’s universal intersection rule is simpler but more conservative.

**Conflux relationship.** Critical novelty constraint: provenance-based access control predates LLM agents. Conflux must specify the novel provenance semantics and authority rule.

**Recommended use.** Mandatory PBAC subsection; explicitly distinguish data lineage policy from influencing-principal authority.

**Connected literature:** Secure PBAC cloud work; FORGE; history-based access control

### N014 — Towards Secure Provenance-Based Access Control in Cloud Environments (2013)

**Authors:** Adam Bates; Kevin Butler; Thomas Moyer; Patrick McDaniel; Michael Hicks  
**Stream:** Provenance-based access control / cloud security  
**Source:** https://adambates.org/documents/Bates_Codaspy13.pdf  
**Review status:** Verified primary PDF

**Key contribution.** Secures provenance collection and uses provenance attributes for access decisions in distributed cloud environments, with prototype performance evaluation.

**What is distinctive about this work.** Combines secure provenance infrastructure with enforcement in a real cloud deployment.

**Limitations / boundary.** Focuses on data/cloud operations, not opaque model reasoning or prompt injection.

**Reviewer inference for Conflux.** A production Conflux deployment faces the same trustworthy-provenance and instrumentation problem at tool/MCP/service boundaries.

**Conflux relationship.** Strong systems precedent for provenance TCB and policy enforcement; useful for production provenance architecture.

**Recommended use.** Production provenance and trusted-computing-base discussion.

**Connected literature:** PBAC model; FORGE; Zanzibar

### N031 — Integrity Considerations for Secure Computer Systems (Biba) (1977)

**Authors:** Kenneth J. Biba  
**Stream:** Integrity / information-flow control  
**Source:** https://www.researchgate.net/publication/235043659_Integrity_Considerations_for_Secure_Computer_Systems  
**Review status:** Verified secondary/primary-report metadata

**Key contribution.** Formal integrity policies prevent low-integrity subjects/data from improperly modifying high-integrity objects.

**What is distinctive about this work.** Canonical integrity dual to confidentiality models, emphasizing contamination of trusted state by lower-integrity sources.

**Limitations / boundary.** Coarse security levels and system subjects/objects; not principal-specific organizational permissions.

**Reviewer inference for Conflux.** Principal Context is more identity/permission-specific than a scalar integrity lattice, but the contamination intuition is not new.

**Conflux relationship.** Important foundational citation when describing influence contamination and monotonic authority reduction.

**Recommended use.** Integrity lineage for influence tracking.

**Connected literature:** DLM; robust declassification; IFC agent defense

### N032 — A Lattice Model of Secure Information Flow (1976)

**Authors:** Dorothy E. Denning  
**Stream:** Information-flow control foundations  
**Source:** https://doi.org/10.1145/360051.360056  
**Review status:** Verified primary/bibliographic

**Key contribution.** Formalizes secure information flow over a lattice of security classes and motivates mechanisms/program certification to enforce the permitted flow relation.

**What is distinctive about this work.** Unifying mathematical treatment of secure flows across security classes.

**Limitations / boundary.** Centralized/coarse classes; not decentralized principals, contextual norms, or action permissions.

**Reviewer inference for Conflux.** Intersection of arbitrary ACS permissions forms a related but distinct authority lattice; terminology should avoid implying a new monotonicity idea.

**Conflux relationship.** Useful mathematical ancestor for lattice/monotonicity framing, but Conflux authority is derived from principal permissions rather than static data classes.

**Recommended use.** Foundational IFC/lattice citation.

**Connected literature:** DLM; Biba; IFC agent defense

### N041 — Why and Where: A Characterization of Data Provenance (2001)

**Authors:** Peter Buneman; Sanjeev Khanna; Wang-Chiew Tan  
**Stream:** Data provenance foundations  
**Source:** https://doi.org/10.1007/3-540-44503-X_20  
**Review status:** Needs exact canonical citation verification before publication

**Key contribution.** Distinguishes forms of database provenance such as why-provenance and where-provenance, formalizing what source data explains an output.

**What is distinctive about this work.** Canonical distinction between different questions that the word “provenance” can mean.

**Limitations / boundary.** Database query semantics are deterministic and structured; LLM semantic influence is not captured by relational lineage.

**Reviewer inference for Conflux.** Conflux should define exactly whether its provenance means authorship, possible influence, causal dependence, or derivation history rather than using “provenance” generically.

**Conflux relationship.** Strengthens terminology and motivates conservative “possible influence” provenance as distinct from exact causal provenance.

**Recommended use.** Provenance semantics/background and terminology discipline.

**Connected literature:** PBAC; secure PBAC; FORGE; PACT

### N042 — Provenance Semirings (2007)

**Authors:** Todd J. Green; Gregory Karvounarakis; Val Tannen  
**Stream:** Data provenance / algebraic provenance  
**Source:** https://doi.org/10.1145/1265530.1265535  
**Review status:** Needs exact canonical citation verification before publication

**Key contribution.** Uses semiring annotations to provide a general algebra for relational data provenance, subsuming several lineage notions and supporting compositional derivations.

**What is distinctive about this work.** Provides an algebraic, compositional foundation for provenance annotations across query operations.

**Limitations / boundary.** Structured database operations, not opaque LLM transformations or security authority.

**Reviewer inference for Conflux.** A principal-set union is deliberately much coarser than semiring provenance; richer provenance may improve attribution but complicate security-state reduction.

**Conflux relationship.** Useful if Conflux develops fine-grained explanation/attribution provenance separate from conservative security provenance.

**Recommended use.** Fine-grained provenance/interpretability future work.

**Connected literature:** Why/where provenance; PBAC; FORGE

### N043 — Security Policies and Security Models (Noninterference) (1982)

**Authors:** Joseph A. Goguen; José Meseguer  
**Stream:** Information-flow security / noninterference  
**Source:** https://www.cs.cornell.edu/courses/cs5430/2012sp/noninterference.pdf  
**Review status:** Needs exact canonical citation verification before publication

**Key contribution.** Introduces noninterference-style reasoning in which actions of high/security domains should not affect observations of low domains except as permitted.

**What is distinctive about this work.** Canonical semantic foundation for information-flow confidentiality independent of implementation mechanisms.

**Limitations / boundary.** Classical domains/observations; does not directly encode organizational tool permissions or modern agent state.

**Reviewer inference for Conflux.** Conflux’s no-unauthorized-read rule is weaker than observational confidentiality; SLED-V should not conflate them.

**Conflux relationship.** Should underpin any claim about information exfiltration/noninterference beyond access safety.

**Recommended use.** Confidentiality semantics and SLED-V property taxonomy.

**Connected literature:** Hyperproperties; HyperLTL; robust declassification

## Policy specification, refinement, controlled language, and autoformalization

### L001 — Security Policy Specification Using a Graphical Approach (LaSCO) (1998)

**Authors:** James A. Hoagland; Raju Pandey; Karl N. Levitt  
**Stream:** Policy specification / enforcement  
**Source:** https://arxiv.org/abs/cs/9809124  
**Review status:** Verified primary

**Key contribution.** Graph-based security constraints; executable wrappers

**What is distinctive about this work.** Early graph-and-first-order-logic policy language designed to support executable enforcement wrappers.

**Limitations / boundary.** Assumes policy intent is already formalized and instrumentation is complete; it does not derive policy from provenance or an ACS.

**Conflux relationship.** Shows formal policies can be compiled to enforcement; historical predecessor to FORGE and Conflux policy layer

**Recommended use.** Use to position Conflux policy compilation as part of a long policy-engineering lineage; distinguish specification/refinement from runtime authority derivation.

**Connected literature:** The Ponder Policy Specification Language; Security and Management Policy Specification; Security Policy Refinement Using Data Integration: A Position Paper; Conflicts in Policy-Based Distributed Systems Management; Policy Compiler for Secure Agentic Systems / FORGE

### L002 — The Ponder Policy Specification Language (2001)

**Authors:** Nicodemos Damianou; Naranker Dulay; Emil Lupu; Morris Sloman  
**Stream:** Policy specification / management  
**Source:** https://link.springer.com/chapter/10.1007/3-540-44569-2_2  
**Review status:** Verified primary

**Key contribution.** Authorization, refrain, obligation, delegation and role policies

**What is distinctive about this work.** Rich enterprise policy vocabulary combining authorization, prohibition/refrain, obligation, delegation, roles and domains.

**Limitations / boundary.** Substantial policy-authoring, conflict and refinement burden; policy-language correctness is not organizational-intent correctness.

**Conflux relationship.** Prior art for richer policy semantics beyond ACS permission intersection

**Recommended use.** Use to position Conflux policy compilation as part of a long policy-engineering lineage; distinguish specification/refinement from runtime authority derivation.

**Connected literature:** Security Policy Specification Using a Graphical Approach (LaSCO); Security and Management Policy Specification; Security Policy Refinement Using Data Integration: A Position Paper; Conflicts in Policy-Based Distributed Systems Management; Policy Compiler for Secure Agentic Systems / FORGE

### L004 — Security and Management Policy Specification (2002)

**Authors:** Morris Sloman; Emil Lupu  
**Stream:** Policy specification / refinement  
**Source:** https://doi.org/10.1109/65.993218  
**Review status:** Verified primary

**Key contribution.** Survey of policy specification and implementable policy systems

**What is distinctive about this work.** Canonical early survey framing high-level policy-to-enforcement refinement as a systems-management problem.

**Limitations / boundary.** Survey rather than a complete automatic refinement solution.

**Conflux relationship.** Establishes long-running policy-specification/refinement problem that Conflux should cite

**Recommended use.** Use to position Conflux policy compilation as part of a long policy-engineering lineage; distinguish specification/refinement from runtime authority derivation.

**Connected literature:** The Ponder Policy Specification Language; Security Policy Refinement Using Data Integration: A Position Paper; Conflicts in Policy-Based Distributed Systems Management; An Empirical Study of Natural Language Parsing of Privacy Policy Rules Using the SPARCLE Policy Workbench; A Controlled Natural Language Interface for Authoring Access Control Policies; Automated Extraction of Security Policies from Natural-Language Software Documents (Text2Policy)

### L008 — An Empirical Study of Natural Language Parsing of Privacy Policy Rules Using the SPARCLE Policy Workbench (2006)

**Authors:** Carolyn A. Brodie; Clare-Marie Karat; John Karat  
**Stream:** Natural language policy extraction  
**Source:** https://doi.org/10.1145/1143120.1143123  
**Review status:** Verified primary

**Key contribution.** Parses organisational privacy rules into machine-readable XML

**What is distinctive about this work.** Early practical natural-language privacy-policy workbench producing machine-readable policies.

**Limitations / boundary.** Parser/grammar coverage and semantic extraction errors remain security-critical.

**Conflux relationship.** Historical precedent for linking prose policy to machine-readable enforcement/audit

**Recommended use.** Use as prior art for policy acquisition. Generated/learned policy should carry provenance, confidence/review status, and should not silently become part of Conflux hard security assumptions.

**Connected literature:** Security and Management Policy Specification; A Controlled Natural Language Interface for Authoring Access Control Policies; Automated Extraction of Security Policies from Natural-Language Software Documents (Text2Policy); Autoformalization of Agent Instructions into Policy-as-Code

### L009 — Security Policy Refinement Using Data Integration: A Position Paper (2009)

**Authors:** Robert Craven; Jorge Lobo; Emil Lupu; Alessandra Russo; Morris Sloman  
**Stream:** Policy refinement  
**Source:** https://research.ibm.com/publications/security-policy-refinement-using-data-integration-a-position-paper  
**Review status:** Verified primary; metadata corrected

**Key contribution.** Derives lower-level runnable policies from high-level policies/goals

**What is distinctive about this work.** Recasts policy refinement as structured data-integration-style mappings over subject/action/target/conditions.

**Limitations / boundary.** Position paper with initial ideas; semantic burden moves into trusted transformation mappings.

**Conflux relationship.** Frames exactly the high-level-to-enforceable-policy gap modern agent autoformalization revisits

**Recommended use.** Use to position Conflux policy compilation as part of a long policy-engineering lineage; distinguish specification/refinement from runtime authority derivation.

**Connected literature:** Security and Management Policy Specification; The Ponder Policy Specification Language; Conflicts in Policy-Based Distributed Systems Management; Autoformalization of Agent Instructions into Policy-as-Code

### L010 — A Controlled Natural Language Interface for Authoring Access Control Policies (2011)

**Authors:** Leilei Shi; David W. Chadwick  
**Stream:** Natural language policy authoring  
**Source:** https://kar.kent.ac.uk/31980/  
**Review status:** Verified primary

**Key contribution.** Controlled-English interface compiles policies for a PDP

**What is distinctive about this work.** Uses controlled natural language to make access-control policy translation deterministic and usable by non-specialists.

**Limitations / boundary.** Expressiveness/usability trade-off; users must stay inside the controlled grammar.

**Conflux relationship.** Shows an alternative to probabilistic NL-to-policy translation: constrain the input language

**Recommended use.** Use as prior art for policy acquisition. Generated/learned policy should carry provenance, confidence/review status, and should not silently become part of Conflux hard security assumptions.

**Connected literature:** An Empirical Study of Natural Language Parsing of Privacy Policy Rules Using the SPARCLE Policy Workbench; Automated Extraction of Security Policies from Natural-Language Software Documents (Text2Policy); Autoformalization of Agent Instructions into Policy-as-Code

### L011 — Automated Extraction of Security Policies from Natural-Language Software Documents (Text2Policy) (2012)

**Authors:** Xusheng Xiao; Amit Paradkar; Suresh Thummalapenta; Tao Xie  
**Stream:** Natural language policy extraction  
**Source:** https://www.microsoft.com/en-us/research/publication/automated-extraction-of-security-policies-from-natural-language-software-documents/  
**Review status:** Verified primary

**Key contribution.** Extracts access-control rules and resource-access information from requirements

**What is distinctive about this work.** Automatically extracts access-control rules from ordinary software documents rather than controlled English.

**Limitations / boundary.** Reported extraction is imperfect, so omissions/misbindings can silently weaken policy.

**Conflux relationship.** Important evidence that translation accuracy is imperfect; Conflux must not treat generated policy as trusted by default

**Recommended use.** Use as prior art for policy acquisition. Generated/learned policy should carry provenance, confidence/review status, and should not silently become part of Conflux hard security assumptions.

**Connected literature:** An Empirical Study of Natural Language Parsing of Privacy Policy Rules Using the SPARCLE Policy Workbench; A Controlled Natural Language Interface for Authoring Access Control Policies; Policy by Example: An Approach for Security Policy Specification; Autoformalization of Agent Instructions into Policy-as-Code

### L012 — Policy by Example: An Approach for Security Policy Specification (2017)

**Authors:** Adwait Nadkarni; William Enck; Somesh Jha; Jessica Staddon  
**Stream:** Policy synthesis / usable security  
**Source:** https://arxiv.org/abs/1707.03967  
**Review status:** Verified primary

**Key contribution.** Learns user-specific policies from allow/deny examples with active learning

**What is distinctive about this work.** Learns policy from allow/deny examples via active learning rather than prose/formal rules.

**Limitations / boundary.** Examples may be sparse, noisy or normatively wrong; learned behavior is not proof of intended policy.

**Conflux relationship.** Alternative policy-acquisition mechanism; useful comparison to autoformalization and learned agent policies

**Recommended use.** Use as prior art for policy acquisition. Generated/learned policy should carry provenance, confidence/review status, and should not silently become part of Conflux hard security assumptions.

**Connected literature:** Automated Extraction of Security Policies from Natural-Language Software Documents (Text2Policy); Design Patterns for Securing LLM Agents against Prompt Injections; Autoformalization of Agent Instructions into Policy-as-Code; PolicyBank

### L026 — Autoformalization of Agent Instructions into Policy-as-Code (2026)

**Authors:** Adam Mondl; Matthew Maisel; John H. Brock  
**Stream:** LLM autoformalization / policy-as-code  
**Source:** https://arxiv.org/abs/2606.26649  
**Review status:** Verified primary

**Key contribution.** Generator-critic pipeline translates prompts, MCP descriptions and prose policy to Cedar

**What is distinctive about this work.** End-to-end LLM generator-critic translating prompts, MCP schemas and policy corpora into analyzable Cedar policies.

**Limitations / boundary.** Hard checks prove properties of generated Cedar, not semantic equivalence to source prose; soft semantic checking remains model-dependent.

**Conflux relationship.** Potential policy-source layer above Conflux; generated policy must remain outside hard theorem unless translation is trusted/verified

**Recommended use.** Potential policy-source layer above Conflux; generated policy must remain outside hard theorem unless translation is trusted/verified

**Connected literature:** An Empirical Study of Natural Language Parsing of Privacy Policy Rules Using the SPARCLE Policy Workbench; A Controlled Natural Language Interface for Authoring Access Control Policies; Automated Extraction of Security Policies from Natural-Language Software Documents (Text2Policy); Policy by Example: An Approach for Security Policy Specification; Cedar: A New Language for Expressive, Fast, Safe, and Analyzable Authorization; Defending Against Indirect Prompt Injection Attacks With Spotlighting; Policy Compiler for Secure Agentic Systems / FORGE; PolicyBank

### N015 — Assisting Requirement Formalization by Means of Natural Language Translation (1994)

**Authors:** Alessandro Fantechi; Stefania Gnesi; Gioia Ristori; Michele Carenini; Massimo Vanocchi; Paolo Moreschini  
**Stream:** Natural-language autoformalization / requirements  
**Source:** https://dblp.dagstuhl.de/rec/journals/fmsd/FantechiGRCVM94.html  
**Review status:** Verified bibliographic

**Key contribution.** NL2ACTL prototype translates natural-language behavioral requirements into ACTL temporal-logic formulae to assist reactive-system formalization.

**What is distinctive about this work.** Demonstrates NL-to-temporal-logic translation decades before LLM autoformalization.

**Limitations / boundary.** Restricted domain and older NLP; translation correctness and ambiguity remain central.

**Reviewer inference for Conflux.** Security policy mistranslation is more dangerous than ordinary requirements mistranslation because omissions can silently create authority.

**Conflux relationship.** Moves the autoformalization lineage back to the early 1990s; modern Cedar work is not the beginning of the field.

**Recommended use.** Historical start of autoformalization section.

**Connected literature:** Attempto; policy refinement; FRET; nl2spec; LLM autoformalization; Cedar autoformalization

### N016 — Attempto Controlled English (ACE) (1996)

**Authors:** Norbert E. Fuchs; Rolf Schwitter  
**Stream:** Controlled natural language / executable specification  
**Source:** https://arxiv.org/abs/cmp-lg/9603003  
**Review status:** Verified primary/bibliographic

**Key contribution.** Controlled English with restricted grammar translated unambiguously into discourse representations and Prolog for querying, simulation, and validation.

**What is distinctive about this work.** Uses controlled natural language as a human-friendly textual view of formal executable specifications.

**Limitations / boundary.** Users must learn and remain inside the controlled grammar; expressiveness and naturalness are intentionally constrained.

**Reviewer inference for Conflux.** For organizational policy, controlled-language authoring may be more deployable than unrestricted NL when the policy is security-critical.

**Conflux relationship.** Provides a design alternative: controlled policy authoring can reduce reliance on probabilistic translation.

**Recommended use.** Policy acquisition design space and safe alternative to opaque autoformalization.

**Connected literature:** Controlled NL access policy; NL2ACTL; FRET; Cedar autoformalization

### N017 — A Goal-Based Approach to Policy Refinement (2004)

**Authors:** Arosha Bandara; Emil Lupu; Jonathan Moffett; Alessandra Russo  
**Stream:** Policy refinement / requirements to enforcement  
**Source:** https://doi.org/10.1109/POLICY.2004.1309175  
**Review status:** Verified bibliographic

**Key contribution.** Derives implementable policies from high-level goals using goal refinement and system-model information.

**What is distinctive about this work.** Targets the missing step from high-level goals to implementable policies rather than only policy analysis.

**Limitations / boundary.** Requires a sufficiently complete system model and formal goal structure; refinement correctness remains the central challenge.

**Reviewer inference for Conflux.** LLM-based refinement may reduce authoring cost but does not eliminate the need to validate the mapping from goals to concrete tool arguments/resources.

**Conflux relationship.** Important bridge between Ponder-era policy engineering and modern agent autoformalization.

**Recommended use.** Policy-refinement lineage and discussion of semantic fidelity.

**Connected literature:** Ponder; policy specification survey; data-integration refinement; NL2ACTL; Cedar autoformalization

### N018 — Formal Requirements Elicitation with FRET (2020)

**Authors:** Dimitra Giannakopoulou; Thomas Pressburger; Anastasia Mavridou; Julian Rhein; Johann Schumann; Nija Shi  
**Stream:** Controlled requirements / formalization  
**Source:** https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20200001989.pdf  
**Review status:** Verified NASA primary

**Key contribution.** FRETISH restricted natural language has precise semantics, is explained through diagrams/text, translated to temporal logics, and interactively simulated to validate intended meaning.

**What is distinctive about this work.** Treats understanding and debugging the formalization as a first-class requirement, not just automatic translation.

**Limitations / boundary.** Requires structured input and model mappings; not designed specifically for authorization policies.

**Reviewer inference for Conflux.** Conflux policy tooling should emulate FRET’s bidirectional explanations and simulation rather than silently accepting generated Cedar.

**Conflux relationship.** Potential design template for a policy compiler UI with reviewable semantics and counterexamples.

**Recommended use.** Human validation workflow for autoformalized policy.

**Connected literature:** NL2ACTL; ACE; nl2spec; Cedar autoformalization

### N019 — nl2spec: Interactively Translating Unstructured Natural Language to Temporal Logics with Large Language Models (2023)

**Authors:** Nianjun Zhou; A. et al.  
**Stream:** LLM autoformalization / requirements  
**Source:** https://link.springer.com/chapter/10.1007/978-3-031-37703-7_18  
**Review status:** Verified primary metadata; author list to verify before publication citation

**Key contribution.** Uses LLMs to translate unstructured requirements to temporal logic and maps formal subformulae back to source fragments for interactive correction.

**What is distinctive about this work.** Makes subformula-to-text alignment part of the correction loop, directly addressing ambiguity.

**Limitations / boundary.** Interactive correction is still required; correctness depends on user review and the expressiveness of the target logic.

**Reviewer inference for Conflux.** Security policy compilers should preserve source-to-formula provenance so reviewers can audit every authority-bearing clause.

**Conflux relationship.** Strong method precedent for policy autoformalization provenance and reviewability.

**Recommended use.** Source-linked policy compilation and human review design.

**Connected literature:** FRET; LLM autoformalization; Cedar autoformalization

### N020 — Autoformalization with Large Language Models (2022)

**Authors:** Yuhuai Wu; Albert Q. Jiang; Wenda Li; Markus N. Rabe; Charles Staats; Mateja Jamnik; Christian Szegedy  
**Stream:** LLM autoformalization / theorem proving  
**Source:** https://arxiv.org/abs/2205.12615  
**Review status:** Verified primary

**Key contribution.** Few-shot LLM translation from informal mathematical statements to Isabelle/HOL formalizations; demonstrates usefulness but imperfect exact formalization.

**What is distinctive about this work.** Early influential demonstration that large pretrained models can perform nontrivial formalization without task-specific supervised translators.

**Limitations / boundary.** Reported perfect formalization is only a subset; mathematical statements differ from ambiguous organizational policies.

**Reviewer inference for Conflux.** Formal typechecking/proof of generated policy does not establish semantic equivalence to source prose.

**Conflux relationship.** General methodological predecessor to LLM policy compilers; supports explicit semantic-validation boundaries.

**Recommended use.** General autoformalization limitations and terminology.

**Connected literature:** nl2spec; Cedar autoformalization; FRET

## Modern LLM-agent security, benchmarks, and runtime policy enforcement

### L014 — Defending Against Indirect Prompt Injection Attacks With Spotlighting (2024)

**Authors:** Keegan Hines et al.  
**Stream:** Model-level prompt-injection defence  
**Source:** https://arxiv.org/abs/2403.14720  
**Review status:** Existing Conflux reference

**Key contribution.** Marks/encodes untrusted content to improve model discrimination

**What is distinctive about this work.** Lightweight provenance cue to the model that substantially reduces indirect-injection success in tested settings.

**Limitations / boundary.** Security remains empirical/model-dependent; arbitrary model behavior can ignore the cue.

**Conflux relationship.** Complementary model-level layer; not a substitute for system-level authorization

**Recommended use.** Use to make SLED-V verdicts precise: distinguish runtime-enforceable safety, bounded checking, unbounded invariant proofs, and relational confidentiality.

**Connected literature:** Cedar: A New Language for Expressive, Fast, Safe, and Analyzable Authorization; Autoformalization of Agent Instructions into Policy-as-Code; Zanzibar: Google’s Consistent, Global Authorization System; The Policy Machine: A Novel Architecture and Framework for Access Control Policy Management

### L015 — StruQ: Defending Against Prompt Injection with Structured Queries (2024)

**Authors:** Sizhe Chen; Julien Piet; Chawin Sitawarin; David Wagner  
**Stream:** Model-level prompt-injection defence  
**Source:** https://arxiv.org/abs/2402.06363  
**Review status:** Existing Conflux reference

**Key contribution.** Separates instructions and data structurally

**What is distinctive about this work.** Makes trusted instruction vs data separation an explicit interface/training objective rather than only prompting.

**Limitations / boundary.** Depends on trained model behavior and fixed channel assumptions; data-dependent control remains difficult.

**Conflux relationship.** Useful defence-in-depth baseline; security remains model-dependent

**Recommended use.** Use to make SLED-V verdicts precise: distinguish runtime-enforceable safety, bounded checking, unbounded invariant proofs, and relational confidentiality.

**Connected literature:** System-Level Defense against Indirect Prompt Injection Attacks: An Information Flow Control Perspective; Defeating Prompt Injections by Design (CaMeL); Progent: Programmable Privilege Control for LLM Agents; Contextual Integrity in LLMs via Reasoning and Reinforcement Learning; Policy Compiler for Secure Agentic Systems / FORGE

### L016 — System-Level Defense against Indirect Prompt Injection Attacks: An Information Flow Control Perspective (2024)

**Authors:** Fangzhou Wu; Ethan Cecchetti; Chaowei Xiao  
**Stream:** System-level / IFC  
**Source:** https://arxiv.org/abs/2409.19091  
**Review status:** Existing Conflux reference

**Key contribution.** Information-flow-control framing for indirect PI

**What is distinctive about this work.** Explicitly applies information-flow-control ideas to system-level LLM-agent defense with trusted planning/flow restrictions.

**Limitations / boundary.** Utility and security depend on plan/control assumptions and trust-label granularity.

**Conflux relationship.** Important predecessor for provenance/information-flow based agent security

**Recommended use.** Important predecessor for provenance/information-flow based agent security

**Connected literature:** StruQ: Defending Against Prompt Injection with Structured Queries; Defeating Prompt Injections by Design (CaMeL); Progent: Programmable Privilege Control for LLM Agents; Contextual Integrity in LLMs via Reasoning and Reinforcement Learning

### L017 — Defeating Prompt Injections by Design (CaMeL) (2025)

**Authors:** Edoardo Debenedetti et al.  
**Stream:** System-level agent security  
**Source:** https://arxiv.org/abs/2503.18813  
**Review status:** Existing Conflux reference

**Key contribution.** Dual-LLM planning + capabilities + policy checks

**What is distinctive about this work.** End-to-end agent architecture combining control/data separation, capabilities/provenance and deterministic policy enforcement.

**Limitations / boundary.** Application policy and trusted planning/control assumptions remain part of the TCB; data-dependent planning can lose utility.

**Conflux relationship.** Conflux must distinguish ACS-derived principal authority from CaMeL policy semantics and planning assumptions

**Recommended use.** Direct comparison target: identify what is trusted, what provenance granularity is tracked, where policy comes from, and whether enforcement is model-independent.

**Connected literature:** StruQ: Defending Against Prompt Injection with Structured Queries; System-Level Defense against Indirect Prompt Injection Attacks: An Information Flow Control Perspective; Progent: Programmable Privilege Control for LLM Agents; Contextual Integrity in LLMs via Reasoning and Reinforcement Learning; Policy Compiler for Secure Agentic Systems / FORGE; The Granularity Mismatch in Agent Security: Argument-Level Provenance Solves Enforcement and Isolates the LLM Reasoning Bottleneck (PACT)

### L018 — Progent: Programmable Privilege Control for LLM Agents (2025)

**Authors:** Tianneng Shi et al.  
**Stream:** Agent privilege control  
**Source:** https://arxiv.org/abs/2504.11703  
**Review status:** Verified primary

**Key contribution.** Fine-grained DSL constraints on tool calls; fallbacks; LLM-generated policies

**What is distinctive about this work.** Makes task-specific least-privilege policy and policy evolution/expansion explicit security artifacts, with argument-sensitive rules and deterministic checks.

**Limitations / boundary.** Generated policy can be semantically wrong; least-privilege-allowed harms and natural-language harms remain possible.

**Conflux relationship.** Invalidates broad novelty claims around privilege control; compare policy source, argument sensitivity, ACS derivation, guarantees

**Recommended use.** Direct comparison target: identify what is trusted, what provenance granularity is tracked, where policy comes from, and whether enforcement is model-independent.

**Connected literature:** StruQ: Defending Against Prompt Injection with Structured Queries; System-Level Defense against Indirect Prompt Injection Attacks: An Information Flow Control Perspective; Defeating Prompt Injections by Design (CaMeL); Contextual Integrity in LLMs via Reasoning and Reinforcement Learning; Policy Compiler for Secure Agentic Systems / FORGE

### L020 — Design Patterns for Securing LLM Agents against Prompt Injections (2025)

**Authors:** Luca Beurer-Kellner et al.  
**Stream:** Agent security architecture  
**Source:** https://arxiv.org/abs/2506.08837  
**Review status:** Existing Conflux reference

**Key contribution.** Catalogues isolation and system-level design patterns

**What is distinctive about this work.** Synthesizes reusable architectural patterns for prompt-injection-resistant agents and their conditional guarantees/trade-offs.

**Limitations / boundary.** Pattern guarantees depend on assumptions and correct implementation; policy origin remains separate.

**Conflux relationship.** Useful taxonomy/context for where Conflux sits among system-level patterns

**Recommended use.** Direct comparison target: identify what is trusted, what provenance granularity is tracked, where policy comes from, and whether enforcement is model-independent.

**Connected literature:** Policy by Example: An Approach for Security Policy Specification; Autoformalization of Agent Instructions into Policy-as-Code; PolicyBank; Policy Compiler for Secure Agentic Systems / FORGE

### L021 — A Critical Evaluation of Defenses Against Prompt Injection Attacks (2025)

**Authors:** Yuqi Jia et al.  
**Stream:** Evaluation / attacks  
**Source:** https://arxiv.org/abs/2505.18333  
**Review status:** Existing Conflux reference

**Key contribution.** Adaptive evaluation of PI defences

**What is distinctive about this work.** Shows benchmark saturation can overstate security when defenses face stronger/adaptive attacks and utility is measured carefully.

**Limitations / boundary.** Still finite empirical evaluation, not universal proof.

**Conflux relationship.** Supports revised stance: model defences provide useful probabilistic security but not hard guarantees

**Recommended use.** Supports revised stance: model defences provide useful probabilistic security but not hard guarantees

**Connected literature:** Privacy as Contextual Integrity; Privacy and Contextual Integrity: Framework and Applications; AI Agents May Always Fall for Prompt Injections; Hyperproperties

### L022 — AgentGuardian: Learning Access Control Policies to Govern AI Agent Behavior (2026)

**Authors:** Nadya Abaev et al.  
**Stream:** Learned agent access control  
**Source:** https://arxiv.org/abs/2601.10440  
**Review status:** Verified primary

**Key contribution.** Learns per-tool context-aware policies and control-flow constraints from staging traces

**What is distinctive about this work.** Learns context-sensitive runtime policies from legitimate staging traces/control-flow dependencies.

**Limitations / boundary.** Coverage, rare benign behavior, free-form arguments and poisoned staging traces are bottlenecks.

**Conflux relationship.** Alternative to ACS derivation and NL autoformalization; raises soundness/generalization questions for learned policies

**Recommended use.** Direct comparison target: identify what is trusted, what provenance granularity is tracked, where policy comes from, and whether enforcement is model-independent.

**Connected literature:** StruQ: Defending Against Prompt Injection with Structured Queries; Defeating Prompt Injections by Design (CaMeL); Contextual Integrity in LLMs via Reasoning and Reinforcement Learning; How Not to Detect Prompt Injections with an LLM

### L023 — Policy Compiler for Secure Agentic Systems / FORGE (2026)

**Authors:** Nils Palumbo et al.  
**Stream:** Agent policy compiler / provenance  
**Source:** https://arxiv.org/abs/2602.16708  
**Review status:** Verified primary; version/title history needs note

**Key contribution.** Causal dependency graph + Datalog-derived policies + reference monitor + instrumentation

**What is distinctive about this work.** Combines AOP instrumentation, causal execution facts, Datalog policies and a reference monitor across agent/multi-agent histories.

**Limitations / boundary.** Guarantees are conditional on complete observability/instrumentation and correct policies; policy intent is external.

**Conflux relationship.** Conflux cannot claim novelty for provenance-aware deterministic enforcement; compare principal-context derivation, policy burden and SLED-V verification

**Recommended use.** Direct comparison target: identify what is trusted, what provenance granularity is tracked, where policy comes from, and whether enforcement is model-independent.

**Connected literature:** Security Policy Specification Using a Graphical Approach (LaSCO); The Ponder Policy Specification Language; Defeating Prompt Injections by Design (CaMeL); Progent: Programmable Privilege Control for LLM Agents; Contextual Integrity in LLMs via Reasoning and Reinforcement Learning; Autoformalization of Agent Instructions into Policy-as-Code; Enforceable Security Policies

### L024 — AI Agents May Always Fall for Prompt Injections (2026)

**Authors:** Sahar Abdelnabi; Eugene Bagdasarian  
**Stream:** Contextual integrity / prompt injection  
**Source:** https://arxiv.org/abs/2605.17634  
**Review status:** Verified primary

**Key contribution.** Reframes PI as contextual manipulation; attacks via flow/norm manipulation and mixed flows

**What is distinctive about this work.** Reframes prompt injection as contextual manipulation and constructs misrepresented-flow, norm-manipulation and mixed-flow attacks with an impossibility-style trade-off.

**Limitations / boundary.** Does not itself provide deterministic enforcement of arbitrary contextual norms; scope differs from a narrowly defined authorization invariant.

**Conflux relationship.** Supports focusing Conflux security on authority while acknowledging contextual appropriateness as separate objective

**Recommended use.** Treat contextual appropriateness as a policy dimension distinct from bare ACS authorization; use it to motivate visibility/consent/context policies without weakening the hard Principal-Context authority invariant.

**Connected literature:** Privacy as Contextual Integrity; Privacy and Contextual Integrity: Framework and Applications; A Critical Evaluation of Defenses Against Prompt Injection Attacks; Defeating Prompt Injections by Design (CaMeL)

### L025 — The Granularity Mismatch in Agent Security: Argument-Level Provenance Solves Enforcement and Isolates the LLM Reasoning Bottleneck (PACT) (2026)

**Authors:** Linfeng Fan et al.  
**Stream:** Argument-level provenance / capabilities  
**Source:** https://arxiv.org/abs/2605.11039  
**Review status:** Verified primary

**Key contribution.** Semantic roles for tool arguments + cross-step provenance + trust contracts

**What is distinctive about this work.** Introduces semantic roles and cross-step argument-level provenance so only authority-bearing arguments require trusted origins.

**Limitations / boundary.** Provenance inference, role/contract synthesis and semantic ambiguity remain bottlenecks; not every harm is argument-provenance harm.

**Conflux relationship.** Shows whole-call provenance is too coarse for some workflows; motivates argument-level Principal Context or authority-bearing argument semantics

**Recommended use.** Shows whole-call provenance is too coarse for some workflows; motivates argument-level Principal Context or authority-bearing argument semantics

**Connected literature:** Defeating Prompt Injections by Design (CaMeL); Contextual Integrity in LLMs via Reasoning and Reinforcement Learning; Policy Compiler for Secure Agentic Systems / FORGE; Hyperproperties

### L027 — How Not to Detect Prompt Injections with an LLM (2025)

**Authors:** Sarthak Choudhary; Divyam Anshumaan; Nils Palumbo; Somesh Jha  
**Stream:** Model-level detection critique  
**Source:** https://arxiv.org/abs/2507.05630  
**Review status:** Verified primary; metadata corrected

**Key contribution.** Shows limitations of LLM-based PI detection

**What is distinctive about this work.** Targets the prompt-injection detector paradigm itself with adversarial/statistical failure constructions.

**Limitations / boundary.** Results do not imply impossibility of deterministic external authorization/reference monitors.

**Conflux relationship.** Supports separating model robustness from hard authorization guarantees

**Recommended use.** Use to make SLED-V verdicts precise: distinguish runtime-enforceable safety, bounded checking, unbounded invariant proofs, and relational confidentiality.

**Connected literature:** StruQ: Defending Against Prompt Injection with Structured Queries; Defeating Prompt Injections by Design (CaMeL); AgentGuardian: Learning Access Control Policies to Govern AI Agent Behavior

### L028 — PolicyBank (2026)

**Authors:** Somesh Jha et al.  
**Stream:** Policy interpretation / agent policy  
**Source:** https://scholar.google.com/scholar?q=PolicyBank+Somesh+Jha  
**Review status:** Discovery candidate - verify exact metadata

**Key contribution.** Agent-facing benchmark/framework for ambiguous or incomplete policies and feedback-driven refinement

**What is distinctive about this work.** Treats incomplete/ambiguous policy as online feedback-driven policy-memory refinement.

**Limitations / boundary.** Depends on trusted feedback; bad feedback can poison policy and silently expand behavior.

**Conflux relationship.** Potential evaluation source for policy-interpretation layer; exact relation requires full-paper review

**Recommended use.** Use as prior art for policy acquisition. Generated/learned policy should carry provenance, confidence/review status, and should not silently become part of Conflux hard security assumptions.

**Connected literature:** Policy by Example: An Approach for Security Policy Specification; Design Patterns for Securing LLM Agents against Prompt Injections; Autoformalization of Agent Instructions into Policy-as-Code

### N021 — AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents (2025)

**Authors:** Haoyu Wang; Christopher M. Poskitt; Jun Sun  
**Stream:** Agent runtime policy / DSL  
**Source:** https://arxiv.org/abs/2503.18666  
**Review status:** Verified primary

**Key contribution.** Lightweight DSL with triggers, predicates and enforcement actions; applies rules at runtime across code, embodied, and autonomous-driving agents; also evaluates LLM-generated rules.

**What is distinctive about this work.** Generalizes a compact enforcement DSL across very different agent domains and multiple enforcement strategies.

**Limitations / boundary.** Coverage depends on rule quality and instrumentation; generated-rule recall is imperfect; some enforcement strategies re-invoke the LLM.

**Reviewer inference for Conflux.** A rule DSL can block specified hazards but does not automatically derive least authority from provenance or existing organizational permissions.

**Conflux relationship.** Conflux cannot claim general runtime DSL enforcement or LLM-generated safety rules as novel; Principal Context can serve as a non-optional lower layer beneath AgentSpec-style rules.

**Recommended use.** Direct modern policy-enforcement comparator.

**Connected literature:** Progent; FORGE; solver-aided policy; symbolic guardrails

### N022 — Solver-Aided Verification of Policy Compliance in Tool-Augmented LLM Agents (2026)

**Authors:** Cailin Winston; Claris Winston; René Just  
**Stream:** Agent policy formalization / SMT runtime checking  
**Source:** https://arxiv.org/abs/2603.20449  
**Review status:** Verified primary

**Key contribution.** Human-guided LLM translation of natural-language tool policies into SMT constraints over observable state and arguments; intercepts tool calls and checks Z3 preconditions.

**What is distinctive about this work.** Makes solver-backed formal constraints a precondition for agent tool calls while explicitly incorporating human guidance in formalization.

**Limitations / boundary.** Guarantees apply to encoded constraints and modeled observable state, not faithful translation of prose; evaluation remains benchmark-based.

**Reviewer inference for Conflux.** Incomplete state observability or omitted tool effects can make formally correct constraints insufficient.

**Conflux relationship.** Mandatory comparator for Cedar/policy compiler work and SLED-V; Conflux distinction should be ACS-derived hard invariant plus defence-level verification.

**Recommended use.** Direct 2026 formal-policy/runtime comparison.

**Connected literature:** Cedar autoformalization; FORGE; symbolic guardrails; PACT

### N023 — Symbolic Guardrails for Domain-Specific Agents: Stronger Safety and Security Guarantees Without Sacrificing Utility (2026)

**Authors:** Yining Hong; Yining She; Eunsuk Kang; Christopher S. Timperley; Christian Kästner  
**Stream:** Agent symbolic guardrails / benchmark policy analysis  
**Source:** https://arxiv.org/abs/2604.15579  
**Review status:** Verified primary

**Key contribution.** Systematic review of 80 agent safety/security benchmarks, classifies concrete policies and tests which can be enforced with symbolic guardrails; evaluates utility/security effects.

**What is distinctive about this work.** Combines literature-scale policy extraction with an empirical enforceability study, not just a new guardrail.

**Limitations / boundary.** Only specified/observable policies are amenable to symbolic enforcement; many benchmarks lack concrete policies.

**Reviewer inference for Conflux.** The remaining unsymbolizable requirements may need model judgement, human review, or richer state semantics, and should not be conflated with hard guarantees.

**Conflux relationship.** Important for scoping what Conflux policy layers can guarantee and for justifying a split between hard Principal Context invariants and softer safety layers.

**Recommended use.** Policy enforceability taxonomy and evaluation baseline.

**Connected literature:** AgentSpec; solver-aided verification; design patterns; critical benchmark evaluation

### N026 — AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents (2024)

**Authors:** Edoardo Debenedetti; Jie Zhang; Mislav Balunović; Luca Beurer-Kellner; Marc Fischer; Florian Tramèr  
**Stream:** Agent-security benchmark / prompt injection  
**Source:** https://proceedings.neurips.cc/paper_files/paper/2024/file/97091a5177d8dc64b1da8bf3e1f6fb54-Paper-Datasets_and_Benchmarks_Track.pdf  
**Review status:** Verified primary

**Key contribution.** Extensible tool environment with realistic tasks, security test cases, attacks and defenses for agents operating on untrusted data.

**What is distinctive about this work.** Dynamic benchmark designed for adaptive attacks/defenses rather than a fixed prompt dataset.

**Limitations / boundary.** Finite tasks/attacks cannot prove universal security; metrics depend on benchmark task construction and attack implementations.

**Reviewer inference for Conflux.** Adding ACS/provenance annotations is necessary before it can directly test Conflux’s PE property.

**Conflux relationship.** Complement to SLED-V; use for ecological validity and utility, not as replacement for formal guarantees.

**Recommended use.** Empirical benchmark integration and external validity.

**Connected literature:** Critical benchmark evaluation; InjecAgent; ASB; CaMeL

### N027 — InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents (2024)

**Authors:** Qiusi Zhan; Zhixiang Liang; Zifan Ying; Daniel Kang  
**Stream:** Agent-security benchmark / indirect prompt injection  
**Source:** https://aclanthology.org/2024.findings-acl.624/  
**Review status:** Verified primary

**Key contribution.** 1,054 indirect prompt injection cases spanning 17 user tools and 62 attacker tools, covering direct harm and private-data exfiltration.

**What is distinctive about this work.** Systematic tool-integrated IPI benchmark with explicit attacker/user tool split.

**Limitations / boundary.** Finite attacks and tool templates; success does not establish system-level guarantee or organizational authorization semantics.

**Reviewer inference for Conflux.** Attack success labels can diverge from Conflux PE labels when an attacker-induced action is nevertheless authorized.

**Conflux relationship.** Useful empirical attack source but requires ACS/provenance relabeling for security semantics.

**Recommended use.** Attack corpus / benchmark conversion work.

**Connected literature:** AgentDojo; ASB; critical defense evaluation

### N028 — Agent Security Bench (ASB): Formalizing and Benchmarking Attacks and Defenses in LLM-based Agents (2025)

**Authors:** Hanrong Zhang; Jingyuan Huang; Kai Mei; Yifei Yao; Zhenting Wang; Chenlu Zhan; Hongwei Wang; Yongfeng Zhang  
**Stream:** Agent-security benchmark / broad attack surface  
**Source:** https://proceedings.iclr.cc/paper_files/paper/2025/hash/5750f91d8fb9d5c02bd8ad2c3b44456b-Abstract-Conference.html  
**Review status:** Verified primary

**Key contribution.** Benchmarks multiple attack/defense types across 10 scenarios, over 400 tools, 13 LLM backbones and seven metrics, including prompt injection, memory poisoning and backdoors.

**What is distinctive about this work.** Broad attack-stage and defense coverage across diverse agent environments.

**Limitations / boundary.** Benchmarks observed model/agent behavior; does not provide formal guarantee or a canonical ACS/provenance model.

**Reviewer inference for Conflux.** Breadth makes semantic alignment with Conflux’s precise PE/confidentiality properties nontrivial.

**Conflux relationship.** Useful complementary empirical suite; SLED/SLED-V should map outcomes carefully instead of comparing aggregate ASR blindly.

**Recommended use.** Broad external benchmark and persistent-memory attack coverage.

**Connected literature:** AgentDojo; InjecAgent; critical defense evaluation

## Formal verification, hyperproperties, conformance, and SLED-V methods

### L033 — Hyperproperties (2010)

**Authors:** Michael R. Clarkson; Fred B. Schneider  
**Stream:** Information-flow verification  
**Source:** https://dblp.org/rec/journals/jcs/ClarksonS10.html  
**Review status:** Verified bibliographic; metadata corrected

**Key contribution.** Properties over sets of traces

**What is distinctive about this work.** Introduces hyperproperties for security properties relating sets of traces, including noninterference.

**Limitations / boundary.** Framework is not itself an enforcement or verification algorithm.

**Conflux relationship.** Needed if SLED-V claims observational confidentiality/noninterference rather than only authorized-read safety

**Recommended use.** Needed if SLED-V claims observational confidentiality/noninterference rather than only authorized-read safety

**Connected literature:** Privacy and Contextual Integrity: Framework and Applications; A Critical Evaluation of Defenses Against Prompt Injection Attacks; The Granularity Mismatch in Agent Security: Argument-Level Provenance Solves Enforcement and Isolates the LLM Reasoning Bottleneck (PACT); Enforceable Security Policies

### L034 — Principles of Model Checking (2008)

**Authors:** Christel Baier; Joost-Pieter Katoen  
**Stream:** Formal verification  
**Source:** https://mitpress.mit.edu/9780262026499/principles-of-model-checking/  
**Review status:** Add methodology citation

**Key contribution.** Comprehensive model-checking foundations

**What is distinctive about this work.** Authoritative model-checking methodology reference spanning transition systems, temporal logic and reductions.

**Limitations / boundary.** A proof establishes only the model/property actually encoded; implementation conformance is separate.

**Conflux relationship.** General formal-method reference for state exploration, CTL/LTL, fairness and verification claims

**Recommended use.** Use to make SLED-V verdicts precise: distinguish runtime-enforceable safety, bounded checking, unbounded invariant proofs, and relational confidentiality.

**Connected literature:** Protection in Operating Systems; Bounded Model Checking; SAT-Based Model Checking without Unrolling (IC3)

### L035 — Bounded Model Checking (2003)

**Authors:** Armin Biere; Alessandro Cimatti; Edmund M. Clarke; Ofer Strichman; Yunshan Zhu  
**Stream:** Formal verification  
**Source:** https://www.cs.cmu.edu/~emc/papers/Books%20and%20Edited%20Volumes/Bounded%20Model%20Checking.pdf  
**Review status:** Verified primary; canonical survey metadata corrected

**Key contribution.** SAT-based bounded counterexample search

**What is distinctive about this work.** SAT-based bounded model checking makes short counterexample search practical.

**Limitations / boundary.** No counterexample up to k is only bounded safety unless completeness/induction is established.

**Conflux relationship.** Supports bounded-safe versus unbounded-safe distinction

**Recommended use.** Use to make SLED-V verdicts precise: distinguish runtime-enforceable safety, bounded checking, unbounded invariant proofs, and relational confidentiality.

**Connected literature:** Principles of Model Checking; SAT-Based Model Checking without Unrolling (IC3)

### L036 — SAT-Based Model Checking without Unrolling (IC3) (2011)

**Authors:** Aaron R. Bradley  
**Stream:** Formal verification  
**Source:** https://doi.org/10.1007/978-3-642-18275-4_7  
**Review status:** Add methodology citation

**Key contribution.** Inductive invariant / property-directed reachability

**What is distinctive about this work.** IC3/PDR constructs inductive strengthenings for unbounded finite-state safety without fixed-depth unrolling.

**Limitations / boundary.** Performance/applicability depend on encoding and finite symbolic structure; implementation refinement remains separate.

**Conflux relationship.** Candidate backend for proving ITES authority invariant without depth bounds

**Recommended use.** Use to make SLED-V verdicts precise: distinguish runtime-enforceable safety, bounded checking, unbounded invariant proofs, and relational confidentiality.

**Connected literature:** Principles of Model Checking; Bounded Model Checking

### N024 — AgentRFC: Security Design Principles and Conformance Testing for Agent Protocols (2026)

**Authors:** Shenghan Zheng; Qifan Zhang  
**Stream:** Agent protocol formal verification / conformance  
**Source:** https://www.alphaxiv.org/abs/2603.23801  
**Review status:** Verified primary/author manuscript listing

**Key contribution.** Defines an agent protocol stack and security principles as TLA+ invariants; compiles protocol clauses to a typed IR, model-checks them, and replays counterexamples against SDKs.

**What is distinctive about this work.** Source-links formal checks to protocol clauses and distinguishes protocol non-conformance from additional hardening requirements.

**Limitations / boundary.** Targets protocol specifications rather than agent authorization semantics; correctness still depends on clause extraction/modeling.

**Reviewer inference for Conflux.** LLM-assisted extraction of normative clauses itself becomes a translation boundary requiring evidence.

**Conflux relationship.** Conflux should acknowledge this as direct precedent for counterexample replay/conformance; SLED-V novelty must be in defence semantics, properties, or reductions rather than the general workflow.

**Recommended use.** Mandatory SLED-V/conformance related work.

**Connected literature:** AgentThread; model checking; IC3; FORGE

### N025 — Formal Security Analysis of Agent Protocol Composition (AgentThread) (2026)

**Authors:** Shenghan Zheng; Qifan Zhang; Zheng Zhang; Haonan Li; Christophe Hauser  
**Stream:** Agent protocol composition / formal verification  
**Source:** https://arxiv.org/abs/2606.28690  
**Review status:** Verified primary

**Key contribution.** Extends source-linked protocol verification to composition, identifying specification, implementation, and cross-protocol responsibility gaps using TLA+ and replay tests.

**What is distinctive about this work.** Explicitly demonstrates that individually secure protocol properties can fail under composition and classifies responsibility gaps.

**Limitations / boundary.** Protocol-level focus; does not provide a general organizational authorization or provenance model.

**Reviewer inference for Conflux.** Composition results can depend on environment/adapters beyond the protocol abstraction.

**Conflux relationship.** Supports compositional SLED-V and provider/MCP adapter verification; not a direct competitor to Principal Context.

**Recommended use.** Multi-agent/protocol composition and implementation-conformance section.

**Connected literature:** AgentRFC; model checking; FORGE

### N036 — Temporal Logics for Hyperproperties (HyperLTL) (2014)

**Authors:** Michael R. Clarkson; Bernd Finkbeiner; Masoud Koleini; Kristopher K. Micinski; Markus N. Rabe; César Sánchez  
**Stream:** Hyperproperties / formal verification  
**Source:** https://arxiv.org/abs/1401.4492  
**Review status:** Needs exact bibliographic verification before publication

**Key contribution.** Introduces temporal logics with explicit trace quantification for specifying information-flow and other hyperproperties.

**What is distinctive about this work.** Provides practical logical syntax for properties over multiple execution traces.

**Limitations / boundary.** Specification logic, not automatic agent semantics or enforcement; verification can be expensive.

**Reviewer inference for Conflux.** Modeling what an agent/user can observe is as important as writing the HyperLTL formula.

**Conflux relationship.** Complements L033 Hyperproperties with a concrete specification language for future relational confidentiality checks.

**Recommended use.** SLED-V confidentiality/hyperproperty roadmap.

**Connected literature:** Hyperproperties; model checking; formal CI

### N037 — Counterexample-Guided Abstraction Refinement (CEGAR) (2000)

**Authors:** Edmund M. Clarke; Orna Grumberg; Somesh Jha; Yuan Lu; Helmut Veith  
**Stream:** Formal verification / abstraction  
**Source:** https://doi.org/10.1007/10722167_15  
**Review status:** Needs exact canonical source verification before publication

**Key contribution.** Iteratively refines abstractions when abstract counterexamples are spurious, enabling scalable verification while preserving soundness.

**What is distinctive about this work.** Canonical automated loop connecting abstraction, counterexample feasibility, and targeted refinement.

**Limitations / boundary.** Refinement can diverge or scale poorly; useful abstractions are domain dependent.

**Reviewer inference for Conflux.** Conflux-specific abstractions must preserve PE/confidentiality semantics, especially provenance identity and policy state.

**Conflux relationship.** Methodological tool rather than novelty comparator; could underpin scalable SLED-V.

**Recommended use.** Verification optimization / research direction.

**Connected literature:** model checking; IC3; PBAC

### N038 — Dynamic Partial-Order Reduction for Model Checking Software (2005)

**Authors:** Cormac Flanagan; Patrice Godefroid  
**Stream:** Formal verification / state-space reduction  
**Source:** https://doi.org/10.1145/1040305.1040315  
**Review status:** Needs exact canonical source verification before publication

**Key contribution.** Dynamically identifies dependent transitions and explores representative interleavings instead of all equivalent schedules.

**What is distinctive about this work.** Adaptive state-space reduction based on dependencies discovered during exploration.

**Limitations / boundary.** Correctness depends on an accurate independence/dependence relation and property class.

**Reviewer inference for Conflux.** Shared call budgets, provenance, policy state or visible ordering can make apparently independent agent actions dependent.

**Conflux relationship.** Useful SLED-V technique; any Conflux-specific reduction needs a preservation proof.

**Recommended use.** State-space reduction roadmap.

**Connected literature:** model checking; IC3; AgentThread

## Literature gaps that remain after this expansion

The matrix is now broad enough for Conflux writing, but the following areas still warrant targeted follow-up rather than another undirected search:

- Capability systems and object-capability security beyond the current high-level treatment (e.g. KeyKOS, E, Capsicum) to sharpen the relationship between delegation/capabilities and Principal Context.
- Decentralized IFC implementations and dynamic IFC systems beyond DLM/FLAM, especially systems that handle implicit flows, concurrency, and declassification in effectful distributed applications.
- Policy provenance, policy versioning, and policy-conflict diagnosis in production policy-as-code ecosystems (OPA/Rego, Cedar, XACML, Zanzibar/OpenFGA).
- Formal methods for policy synthesis and repair: inductive policy learning, program synthesis from examples, and proof-carrying or certified policy compilation.
- Multi-session/persistent-memory authority and revocation; current benchmark literature is growing quickly and should be refreshed close to submission.
- MCP/A2A/agent-protocol security standards and formal analyses, because AgentRFC/AgentThread indicate a rapidly changing composition-security literature.
- Causal provenance and dynamic slicing literature outside security, which may offer more precise influence semantics than set-union provenance.
- Human factors for security-policy authoring, review, and explanation: the main practical failure mode of autoformalization may be organizational misunderstanding rather than parser failure.

## Repo integration guidance

1. Add the CSV/XLSX matrix under `docs/research/` or `research/literature/` as the canonical tracking artifact.
2. Generate BibTeX only for rows whose `Claim-safe status` is `Publication-safe metadata`; verify the flagged rows first.
3. Update `docs/research/RELATED_WORK.md` by research stream, not as an 80-paper list. The landscape is the backing evidence; manuscripts should cite only papers needed for a concrete claim.
4. Add a `claim -> nearest prior art` table for Principal Context, policy compilation, argument-level authorization, delegation, visibility/confidentiality, and SLED-V.
5. Treat `Reviewer-inferred limitations` as internal analysis, not claims attributed to the cited authors.
6. When an AI coder adds citations, it should preserve exact paper titles/years/URLs from the matrix and never promote `Needs citation verification` rows without checking the primary source.
