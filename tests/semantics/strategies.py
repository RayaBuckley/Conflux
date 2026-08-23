"""Hypothesis strategies for Conflux domain values."""

from __future__ import annotations

from hypothesis import strategies as st

from conflux.domain import (
    Artifact,
    Permission,
    PrimitiveAction,
    Principal,
    PrincipalContext,
    Provenance,
    ProvenancePrecision,
    ResourceRef,
)

_NAMES = st.sampled_from(
    [
        "alice",
        "bob",
        "carol",
        "dave",
        "eve",
        "frank",
        "grace",
        "heidi",
        "ivan",
        "judy",
        "mallory",
        "oscar",
        "peggy",
        "sybil",
        "trent",
        "victor",
        "walter",
    ],
)

_IDS = st.sampled_from(
    [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "doc",
        "msg",
        "input",
        "output",
        "nested",
        "source",
    ],
)


@st.composite
def principals(draw: st.DrawFn) -> Principal:
    name = draw(_NAMES)
    return Principal(name, name.capitalize())


@st.composite
def principal_sets(draw: st.DrawFn, max_size: int = 5) -> frozenset[Principal]:
    return frozenset(draw(st.lists(principals(), max_size=max_size, unique_by=lambda p: p.id)))


@st.composite
def principal_contexts(draw: st.DrawFn) -> PrincipalContext:
    ps = draw(principal_sets(max_size=5))
    unknown = draw(st.booleans()) if not ps else draw(st.booleans())
    return PrincipalContext(ps, unknown=unknown)


@st.composite
def provenances(draw: st.DrawFn) -> Provenance:
    ps = draw(principal_sets(max_size=5))
    precision = draw(st.sampled_from(ProvenancePrecision))
    attested = draw(st.booleans()) if ps else False
    return Provenance(ps, precision=precision, attested=attested)


@st.composite
def artifacts(draw: st.DrawFn) -> Artifact[object]:
    aid = draw(_IDS)
    prov = draw(provenances())
    return Artifact(aid, "x", prov)


@st.composite
def primitive_actions(draw: st.DrawFn) -> PrimitiveAction:
    action_id = draw(_IDS)
    has_inputs = draw(st.booleans())
    inputs = draw(st.tuples(artifacts())) if has_inputs else ()
    resource = ResourceRef("test", action_id, "document")
    return PrimitiveAction(
        action_id,
        "write",
        Permission("write"),
        resource,
        inputs,
    )
