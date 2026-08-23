"""Provenance overapproximation and precision metrics (SEM-017, SEM-018).

This module formalises the three-way distinction identified in the
related-work analysis:

1. **Security provenance**: conservative overapproximation used for
   enforcement.  This is the ``Provenance`` value in the domain model.

2. **Actual influence**: the true set of principals whose information
   influenced a decision.  This is a hypothetical ground-truth value
   that is not directly observable at enforcement time.

3. **Exposure**: empirical measure of information supplied to the
   model (token count, source count, duration in context).

SEM-017 (Overapproximation soundness): If ``actual_influence ⊆
security_provenance.principals``, then enforcement based on
``security_provenance`` is sound: no action allowed by ITES using
``security_provenance`` would be denied by ITES using
``actual_influence``.

SEM-018 (Precision metric): The precision loss of security provenance
relative to actual influence is measured by the set difference
``security_provenance.principals - actual_influence``.  An empty
difference means exact provenance; a non-empty difference means
conservative overapproximation that may deny actions an exact-influence
controller would allow.

These properties connect Conflux to the Sabelfeld & Myers vocabulary:
security provenance is an intentional overapproximation, not a claim of
exact causal dependence.
"""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import Principal, Provenance


@dataclass(frozen=True, slots=True)
class ProvenanceOverapproximation:
    """The relationship between security provenance and actual influence.

    Attributes:
        security_provenance: the conservative provenance used for
            enforcement.
        actual_influence: the ground-truth set of principals that
            actually influenced the decision.
        overapproximates: whether security provenance is a superset of
            actual influence.
        excess_principals: principals in security provenance but not in
            actual influence (the overapproximation).
        is_exact: whether security provenance equals actual influence.
    """

    security_provenance: Provenance
    actual_influence: frozenset[Principal]
    overapproximates: bool
    excess_principals: frozenset[Principal]
    is_exact: bool

    def to_dict(self) -> dict[str, object]:
        """Serialise this overapproximation result to a JSON-compatible dictionary."""
        return {
            "security_provenance": self.security_provenance.to_dict(),
            "actual_influence_ids": sorted(p.id for p in self.actual_influence),
            "overapproximates": self.overapproximates,
            "excess_principal_ids": sorted(p.id for p in self.excess_principals),
            "is_exact": self.is_exact,
        }


def measure_overapproximation(
    security_provenance: Provenance,
    actual_influence: frozenset[Principal],
) -> ProvenanceOverapproximation:
    """Measure the overapproximation of security provenance.

    SEM-017: Enforcement is sound when actual_influence is a subset of
    security_provenance.principals.  This function checks the subset
    relation and computes the excess principals.

    Args:
        security_provenance: the conservative provenance used for
            enforcement.
        actual_influence: the ground-truth set of principals that
            actually influenced the decision.

    Returns:
        A ProvenanceOverapproximation describing the relationship.
    """
    security_principals = security_provenance.principals
    excess = security_principals - actual_influence
    overapproximates = actual_influence.issubset(security_principals)
    is_exact = security_principals == actual_influence

    return ProvenanceOverapproximation(
        security_provenance=security_provenance,
        actual_influence=frozenset(actual_influence),
        overapproximates=overapproximates,
        excess_principals=excess,
        is_exact=is_exact,
    )


@dataclass(frozen=True, slots=True)
class AuthorityLoss:
    """The authority loss caused by provenance overapproximation.

    When security provenance overapproximates actual influence, the ITES
    intersection rule may deny actions that would be allowed under exact
    influence.  The authority loss is the set of actions that are denied
    under security provenance but would be allowed under actual
    influence.

    Attributes:
        denied_actions: actions denied under security provenance.
        would_allow_actions: actions that would be allowed under actual
            influence.
        authority_loss: the intersection — actions denied due to
            overapproximation.
        loss_ratio: authority_loss / (denied_actions + would_allow_actions)
            if both are non-empty, else 0.0.
    """

    denied_actions: frozenset[str]
    would_allow_actions: frozenset[str]
    authority_loss: frozenset[str]
    loss_ratio: float

    def to_dict(self) -> dict[str, object]:
        """Serialise this authority loss result to a JSON-compatible dictionary."""
        return {
            "denied_actions": sorted(self.denied_actions),
            "would_allow_actions": sorted(self.would_allow_actions),
            "authority_loss": sorted(self.authority_loss),
            "loss_ratio": self.loss_ratio,
        }


def measure_authority_loss(
    denied_actions: frozenset[str],
    would_allow_actions: frozenset[str],
) -> AuthorityLoss:
    """Measure the authority loss from provenance overapproximation.

    SEM-018: The authority loss is the set of actions denied under
    security provenance that would be allowed under actual influence.
    The loss ratio quantifies how much utility is lost due to
    conservative provenance.

    Args:
        denied_actions: actions denied by ITES using security provenance.
        would_allow_actions: actions that ITES would allow using actual
            influence.

    Returns:
        An AuthorityLoss describing the utility impact.
    """
    loss = denied_actions & would_allow_actions
    total = denied_actions | would_allow_actions
    ratio = len(loss) / len(total) if total else 0.0

    return AuthorityLoss(
        denied_actions=frozenset(denied_actions),
        would_allow_actions=frozenset(would_allow_actions),
        authority_loss=frozenset(loss),
        loss_ratio=ratio,
    )


def enforcement_is_sound(
    security_provenance: Provenance,
    actual_influence: frozenset[Principal],
) -> bool:
    """Check SEM-017: enforcement based on security provenance is sound.

    Soundness: if actual_influence ⊆ security_provenance.principals,
    then any action denied by ITES using security_provenance would also
    be denied by ITES using actual_influence.  Equivalently, no action
    allowed by ITES using actual_influence is denied by ITES using
    security_provenance.

    This holds because ITES uses authority intersection: a superset of
    principals can only reduce (or preserve) authority, never increase
    it.  So if an action is denied under security_provenance (which has
    more principals), it must also be denied under actual_influence
    (which has fewer principals), provided actual_influence ⊆
    security_provenance.principals.

    Returns:
        True if the overapproximation is sound (actual_influence ⊆
        security_provenance.principals).
    """
    return actual_influence.issubset(security_provenance.principals)


@dataclass(frozen=True, slots=True)
class ExposureMeasure:
    """Empirical measure of information supplied to the model.

    This is not a security guarantee; it is an empirical observation of
    how much information from each principal reached the model.  It is
    used for exposure analysis, not for enforcement.

    Attributes:
        principal_token_counts: mapping from principal ID to the number
            of tokens supplied from that principal's data.
        total_tokens: total token count across all principals.
        principal_count: number of distinct principals in the exposure.
    """

    principal_token_counts: dict[str, int]
    total_tokens: int
    principal_count: int

    def to_dict(self) -> dict[str, object]:
        """Serialise this exposure measure to a JSON-compatible dictionary."""
        return {
            "principal_token_counts": dict(sorted(self.principal_token_counts.items())),
            "total_tokens": self.total_tokens,
            "principal_count": self.principal_count,
        }


def measure_exposure(
    principal_token_counts: dict[str, int],
) -> ExposureMeasure:
    """Construct an empirical exposure measure.

    This is a measurement of information supplied to the model, not a
    security provenance value.  It may inform attribution and utility
    analysis but must not be used for enforcement unless it acquires an
    independent soundness guarantee.
    """
    return ExposureMeasure(
        principal_token_counts=dict(principal_token_counts),
        total_tokens=sum(principal_token_counts.values()),
        principal_count=len(principal_token_counts),
    )


__all__ = [
    "AuthorityLoss",
    "ExposureMeasure",
    "ProvenanceOverapproximation",
    "enforcement_is_sound",
    "measure_authority_loss",
    "measure_exposure",
    "measure_overapproximation",
]
