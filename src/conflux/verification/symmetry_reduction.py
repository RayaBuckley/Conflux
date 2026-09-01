"""Principal symmetry reduction for self-composition product IRs.

When two principals have identical policy decisions (same permission set),
they are symmetric: swapping them produces equivalent observations.
Symmetry-breaking constraints reduce the product IR state space by
requiring that the first copy's principal ID is lexicographically <=
the second copy's principal ID when their policies match.

Source: SecIC3 (arXiv:2601.21353) symmetric state exploration;
observational confidentiality design doc principal symmetry.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ir import (
    Expression,
    ExpressionKind,
    SafetyInvariant,
    VerificationIR,
)
from .self_composition import SecretPartition, _primed


@dataclass(frozen=True, slots=True)
class SymmetryClass:
    """A class of principals with identical policy decisions."""

    principal_ids: frozenset[str]
    policy_signature: str


def identify_symmetry_classes(
    principal_policies: dict[str, str],
) -> tuple[SymmetryClass, ...]:
    """Group principals by policy signature.

    Args:
        principal_policies: mapping of principal ID to policy signature
            (e.g., "read:write" or "deny-all").

    Returns:
        Tuple of SymmetryClass, one per distinct policy signature.
    """
    groups: dict[str, frozenset[str]] = {}
    for principal_id, sig in principal_policies.items():
        if sig not in groups:
            groups[sig] = frozenset()
        groups[sig] = groups[sig] | {principal_id}
    return tuple(SymmetryClass(principals, sig) for sig, principals in sorted(groups.items()))


def add_symmetry_breaking_constraints(
    ir: VerificationIR,
    partition: SecretPartition,
    symmetric_variables: tuple[str, ...] = (),
) -> VerificationIR:
    """Add symmetry-breaking invariants to a product IR.

    For each symmetric variable pair (v, v'), add an invariant
    ``v <= v'`` (for integers) or ``v implies v'`` (for booleans) to
    break the symmetry and reduce the explored state space.

    Args:
        ir: a product IR from ``construct_product_ir``.
        partition: the secret partition used to construct the product.
        symmetric_variables: variable names to add symmetry-breaking
            constraints for. If empty, all non-secret variables are used.

    Returns:
        A new VerificationIR with additional symmetry-breaking invariants.
    """
    var_names = {v.name for v in ir.variables}
    if not symmetric_variables:
        primed_names = {n for n in var_names if n.endswith("__prime")}
        unprimed = var_names - primed_names - partition.secret_variable_ids
        symmetric_variables = tuple(sorted(n for n in unprimed if _primed(n) in var_names))

    new_invariants = list(ir.invariants)
    var_lookup = {v.name: v for v in ir.variables}

    for var_name in symmetric_variables:
        primed_name = _primed(var_name)
        if primed_name not in var_names:
            continue
        variable = var_lookup.get(var_name)
        if variable is None:
            continue
        if variable.sort.value == "integer":
            expr = Expression.operator(
                ExpressionKind.LESS_EQUAL,
                Expression.variable(var_name),
                Expression.variable(primed_name),
            )
        else:
            expr = Expression.operator(
                ExpressionKind.IMPLIES,
                Expression.variable(var_name),
                Expression.variable(primed_name),
            )
        new_invariants.append(
            SafetyInvariant(
                f"symmetry_break__{var_name}",
                expr,
                f"Symmetry-breaking: {var_name} <= {primed_name}",
            ),
        )

    return VerificationIR(
        id=f"{ir.id}--symmetry-reduced",
        variables=ir.variables,
        transitions=ir.transitions,
        invariants=tuple(new_invariants),
        bound=ir.bound,
        assumptions=ir.assumptions + ("symmetry-breaking constraints reduce equivalent state permutations",),
    )


def project_to_read_policy(
    ir: VerificationIR,
    observer_readable: frozenset[str],
) -> VerificationIR:
    """Project a product IR onto only variables the observer can read.

    This is a COI-style reduction: variables not in the observer's read
    policy are removed from the invariants scope, reducing state space.

    Source: observational confidentiality design doc read-policy projection.
    """
    from .reduction import reduce_cone_of_influence

    inv_ids = tuple(
        inv.id for inv in ir.invariants if any(obs_var in inv.id for obs_var in observer_readable) or "symmetry_break" in inv.id
    )
    if not inv_ids:
        inv_ids = tuple(inv.id for inv in ir.invariants)
    reduction = reduce_cone_of_influence(ir, inv_ids)
    return reduction.reduced_ir


__all__ = [
    "SymmetryClass",
    "add_symmetry_breaking_constraints",
    "identify_symmetry_classes",
    "project_to_read_policy",
]
