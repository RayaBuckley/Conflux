# Implementation Status

This document records progress separately from the stable project overview in
the README.

Implemented areas include the immutable core model, provenance and artifacts,
action taxonomy, authorisation, ITES mediation/state, SLED environments and
traces, representative defences, benchmark runners, provider adapters, and
initial policy adapters.

The typed ITES MVP core is now specified in
[ITES_MVP_SEMANTICS.md](ITES_MVP_SEMANTICS.md) and implemented in
`conflux.ites.mvp`; its synthetic results remain pending a runnable Python
environment.

The principal follow-up areas are stronger interface specifications, broader
provider and external-benchmark integration tests, reproducible experiment
entry points, fuller reporting, and organisational-environment modelling.

This is a research foundation rather than a complete production runtime. The
[roadmap](ROADMAP.md) is the source of truth for planned work; this document
records capabilities supported by the code and tests today.

Status claims should be updated alongside tests and documentation rather than
used as a substitute for either.
