# Conflux Overview

A plain-language explanation of what Conflux is, why it exists, and what it
does. If you are new to the project, start here.

## The problem

AI agents that use tools — reading files, sending messages, calling APIs —
can be manipulated by the very content they process. A document that contains
hidden instructions can trick an agent into performing an action the user never
asked for. This is **prompt injection**, and it is a modern instance of the
**confused deputy problem**: a privileged component (the agent) is tricked by
untrusted input into misusing its authority.

The core question is not whether the model can *detect* malicious
instructions — it cannot, reliably — but whether the security mechanism
prevents unauthorised actions *even when the model is fully compromised*.

## The approach

Conflux introduces **Principal Context**: the set of Principals (people,
services, or systems) whose information may have influenced a proposed action.
A Principal is any entity whose access permissions the organisation's
access-control system (ACS) tracks.

The rule is simple: **every Principal whose information influenced an action
must be independently authorised to perform that action.** If an attacker's
document influenced the agent's proposal, the attacker becomes part of the
Principal Context. If the attacker is not authorised for the proposed action,
the action is blocked — regardless of what the model does.

This means additional influence can only *reduce* an agent's effective
authority, never increase it. Provenance (the record of who influenced what)
is never silently discarded.

## How it works

The security boundary is called **ITES** (Influence Tracking with
Extrapolated Security). It sits between the model and the tools:

1. The model proposes an action.
2. ITES checks the Principal Context — every influencing Principal must be
   authorised by the organisation's policy.
3. Authorisation, read access, visibility, and consent are checked
   **separately**. Consent cannot override authority; visibility cannot
   override read policy.
4. If all checks pass, ITES issues a certificate and the executor carries
   out the action. If any check fails, the proposal is **blocked**.
5. Policy is re-checked at execution time, so revocation or context changes
   between decision and execution are honoured.

A blocked proposal is a **security success**, not a failure. The agent was
prevented from performing an unauthorised action.

## What is built

- An **offline CLI** that runs the full mediation pipeline without
  credentials, models, or external services.
- **Native SLED verification**: bounded state-space exploration that proves
  security properties on finite models and produces minimal counterexamples
  for defective variants.
- **Serialisable verification IR** with optional Z3 and nuXmv solver backends
  and property-scoped cone-of-influence reduction.
- **Authenticated dynamic planning**: plans with bounded continuation,
  action-time re-authorisation, and inert modeled programs that are never
  executed as code.
- **External adapters**: pinned AgentDojo benchmark translation, optional
  Cedar policy decision point, and self-hosted model adapters — all
  fail-closed and externally gated.

## What is next

Live model-backed evidence (planning and AgentDojo efficacy), delegation
activation (currently modelled but runtime-disabled), richer argument-level
provenance, and observational confidentiality properties.

## Where to go deeper

| Topic | Document |
|---|---|
| How the system is structured | [Architecture](reference/ARCHITECTURE.md) |
| What it enforces and why | [Security model](reference/SECURITY_MODEL.md) |
| What is implemented | [Status](evidence/STATUS.md) |
| Verification semantics | [SLED](reference/SLED.md) |
| Research framing | [Research overview](research/RESEARCH_OVERVIEW.md) |
| Related work and positioning | [Related work](research/RELATED_WORK.md) |

## Rationale

A separate plain-language entry point helps external readers — supervisors,
examiners, or developers — understand the project without first navigating
implementation or research documentation written for contributors. The README
remains the concise landing page; this document provides the narrative bridge
to the deeper technical documentation.
