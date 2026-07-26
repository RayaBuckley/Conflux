# Conflux AI Development Guide

> Migration notice: this legacy guide is retained for historical context.
> Follow [DEVELOPMENT.md](DEVELOPMENT.md), [AUDIT.md](AUDIT.md), and the
> templates for current work.

The [documentation hub](README.md), [feature specification template](templates/FEATURE_SPEC.md),
and [change checklist](templates/CHANGE_CHECKLIST.md) are the operational entry
points for agents.

> Canonical instructions for AI-assisted development of Conflux.
>
> This document defines the project's development workflow, architectural principles,
> implementation strategy, and expectations for AI-generated code.
>
> Unless explicitly instructed otherwise, all AI-assisted development should follow
> the guidance in this document.

---

# 1. Project Overview

This project implements a novel defence against prompt injection attacks in
agentic AI systems.

The core contribution is an execution model (currently named **ITES**) together
with the **SLED** evaluation framework.

The objective is **research quality**, not merely producing a working system.

The repository should therefore prioritise:

- Clean architecture
- Strong modularity
- Extensibility
- Realistic evaluation
- Maintainability
- Experimental reproducibility

The codebase should remain useful as both:

- a software project
- a research artefact

---

# 2. Overall Philosophy

Optimise for long-term quality rather than short-term implementation speed.

Whenever a design choice exists, prefer:

- loose coupling
- dependency inversion
- high cohesion
- explicit interfaces
- reusable abstractions
- testability
- future extensibility

Avoid tightly coupling implementations together.

Implementations should be replaceable without requiring widespread changes.

Prefer composition over inheritance where appropriate.

---

# 3. Development Workflow

For every change: inspect the relevant `AGENTS.md`, architecture, module guide,
tests, and ADRs; specify interfaces and security impact; implement; run focused
and complete validation; update documentation and roadmap; then review the
diff with the change checklist. Do not leave security or interface decisions
implicit.

## Development phases

Development proceeds in distinct phases.

## Phase 1 — Research

Investigate:

- academic literature
- industrial systems
- open-source projects
- benchmarks
- attack techniques
- policy systems

The objective is understanding, not implementation.

---

## Phase 2 — Architecture

Before writing code:

- define subsystem responsibilities
- identify dependencies
- determine extension points
- specify interfaces
- design package structure

Architecture should always precede implementation.

---

## Phase 3 — New File Creation (Current Phase)

The current focus is creating **new files**.

Avoid modifying existing files unless specifically requested.

New modules should be:

- self-contained
- documented
- loosely coupled
- ready for later integration

Where integration is required later, leave clear TODO comments.

---

## Phase 4 — Integration

Only after the major subsystems exist should existing files be edited to:

- register implementations
- wire dependency injection
- expose CLI functionality
- update imports
- integrate configuration
- connect benchmarks

---

## Phase 5 — Refactoring

After integration:

- simplify APIs
- remove duplication
- improve naming
- optimise structure
- increase consistency

---

## Phase 6 — Evaluation

Finally:

- run benchmarks
- compare against existing defences
- generate metrics
- produce reports
- analyse failures

---

# 4. Architectural Principles

Every subsystem should have:

- clear responsibilities
- stable public interfaces
- independent implementations

Avoid:

- circular dependencies
- hidden assumptions
- unnecessary global state
- tightly coupled modules

Prefer explicit dependency injection.

Shared models should exist in common packages rather than duplicated across
implementations.

---

# 5. Interface-First Development

Interfaces should generally be designed before implementations.

Typical implementation order:

1. Technical specification
2. Package structure
3. Abstract interfaces
4. Data models
5. Core implementation
6. Tests
7. Integration

Concrete implementations should depend on interfaces rather than one another.

---

# 6. Modular Design

The system should be divided into independently understandable packages.

Expected major packages include:

- policy
- runtime
- benchmarks
- extensions
- privacy
- observability
- reporting
- gateway
- targets
- control

Each package should expose a stable public API.

Internal implementation details should remain private.

---

# 7. Planned Extension Points

The architecture should support interchangeable implementations.

Examples include:

## Attack Generation

- Promptfoo
- HarmBench
- garak

---

## Policy Engines

- Cedar
- Open Policy Agent (OPA)

Future policy engines should be implementable without modifying existing code.

---

## Runtime Isolation

- Local execution
- gVisor
- Firecracker

---

## Observability

- OpenTelemetry
- Structured JSON logging

---

## Privacy

- Microsoft Presidio
- Future privacy filters

---

## Deployment Targets

- Open WebUI
- MCP
- OpenAPI-based systems
- Future agent platforms

---

## Evaluation

Support multiple benchmark suites including:

- SLED
- AgentDojo
- Promptfoo
- HarmBench
- Future external benchmarks

---

# 8. Technical Specifications

Before implementing a subsystem, prefer producing a technical specification.

Specifications should include:

- purpose
- responsibilities
- public interfaces
- data models
- dependency graph
- extension points
- implementation order
- future work

The specification becomes the contract for implementation.

---

# 9. Implementation Guidelines

When generating code:

- produce complete files
- avoid placeholders where practical
- document assumptions
- minimise coupling
- follow existing repository conventions

If assumptions are required, clearly document them.

Avoid speculative integration.

---

# 10. File Generation

When creating files:

Always provide the full relative path.

Example:

src/conflux/policy/base.py

Generate complete file contents.

Where practical, files should compile independently.

---

# 11. Existing Files

Avoid modifying existing files unless explicitly requested.

Prefer:

creating new abstractions

over

editing existing implementations.

Integration occurs later.

---

# 12. Tests

New subsystems should gain tests as early as practical.

Tests should validate:

- interfaces
- behaviour
- edge cases
- extension compatibility

Tests should avoid unnecessary coupling to implementation details.

---

# 13. Documentation

Major packages should eventually contain:

- README
- technical specification
- examples

Documentation should explain:

- purpose
- architecture
- extension mechanisms

---

# 14. Mobile Development Workflow

Development is currently performed primarily from an iPhone.

Responses should therefore minimise manual effort.

Preferred workflow:

Research

↓

Technical specification

↓

Package plan

↓

File generation

↓

Bulk download

↓

GitHub upload

↓

Integration later

When multiple files are requested:

- preserve directory structure
- clearly identify file paths
- package into downloadable archives where supported

---

# 15. Context Management

Avoid repeatedly reproducing completed code.

Treat implemented subsystems as stable unless redesign is explicitly requested.

Prefer referencing established architecture rather than reconstructing it.

---

# 16. Research Mindset

The project is expected to make genuine research contributions.

Where appropriate:

- identify weaknesses
- suggest improvements
- compare alternatives
- discuss trade-offs

Do not change the architecture without explaining why.

Recommendations should always include justification.

---

# 17. Decision Quality

When making recommendations:

Prioritise:

1. research quality
2. architectural quality
3. extensibility
4. maintainability
5. implementation effort

Short-term convenience should rarely dominate long-term design.

---

# 18. Response Priorities

When asked what to implement next, generally prioritise:

1. new interfaces
2. abstract models
3. reusable infrastructure
4. backend implementations
5. tests
6. integration

This keeps the architecture clean while minimising future refactoring.

---

# 19. Repository Roadmap

Maintain a long-term implementation roadmap.

Track:

- planned packages
- planned files
- implementation status
- deferred integration work
- architectural decisions
- future research ideas

This roadmap should evolve alongside the repository.

---

# 20. Guiding Principle

Every implementation should improve one or more of the following:

- architectural quality
- extensibility
- evaluation capability
- realism
- maintainability
- research contribution

If a proposed change does not meaningfully improve at least one of these areas,
consider whether it should be implemented at all.
