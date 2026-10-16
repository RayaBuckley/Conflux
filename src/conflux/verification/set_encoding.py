"""Expand SET-sorted IR state into the Boolean fragment every backend accepts.

`Sort.SET` is refused by every backend, so a model with a set variable has no solver
verdict at all. This module rewrites such an IR into an equivalent one over Boolean
membership variables, which the existing backends already handle.

The expansion is a pure function. The input IR is unchanged, and the result carries a
distinct id, so it has its own fingerprint and cannot be confused with the original.

Fragment: an element membership test (`element in set`), a subset test (`a subset b`) and a
union used as an assignment value. Any other set-valued construct is refused by name rather
than weakened, because a weakened expansion would report a verdict about a different system.

The universe of a set is a declared modelling decision - the elements the finite abstraction
represents - and is required to be non-empty, so the expansion is always finite.
"""

from __future__ import annotations

from collections.abc import Iterable

from .ir import (
    Assignment,
    Expression,
    ExpressionKind,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
)

_MEMBER_SEPARATOR = "__member__"

#: Expression kinds whose value is a set rather than a Boolean or an integer.
_SET_VALUED_KINDS = frozenset(
    {ExpressionKind.UNION, ExpressionKind.INTERSECT, ExpressionKind.DIFFERENCE},
)

#: Boolean connectives this expansion recurses through.
_BOOLEAN_CONNECTIVES = frozenset(
    {ExpressionKind.AND, ExpressionKind.OR, ExpressionKind.NOT, ExpressionKind.IMPLIES},
)


def member_variable(set_name: str, element: str) -> str:
    """Return the name of the Boolean membership variable for one universe element."""
    return f"{set_name}{_MEMBER_SEPARATOR}{element}"


class SetExpansionError(ValueError):
    """Raised when an IR uses a set construct outside the expandable fragment."""


def _set_names(ir: VerificationIR) -> dict[str, tuple[str, ...]]:
    return {variable.name: variable.universe for variable in ir.variables if variable.sort == Sort.SET}


def _element(expression: Expression) -> str:
    if expression.kind != ExpressionKind.CONSTANT or not isinstance(expression.value, str):
        raise SetExpansionError("the left operand of a membership test must be a string constant")
    return expression.value


def _set_operand(expression: Expression, universe: dict[str, tuple[str, ...]]) -> str:
    if expression.kind != ExpressionKind.VARIABLE or not isinstance(expression.value, str):
        raise SetExpansionError("the right operand of a membership test must be a set variable")
    if expression.value not in universe:
        raise SetExpansionError(f"{expression.value} is not a declared set variable")
    return expression.value


def _membership(element: str, set_name: str, universe: dict[str, tuple[str, ...]]) -> Expression:
    """Return the Boolean that says whether one element is a member of one set variable."""
    if element not in universe[set_name]:
        return Expression.constant(False)
    return Expression.variable(member_variable(set_name, element))


def _rewrite_boolean(expression: Expression, universe: dict[str, tuple[str, ...]]) -> Expression:
    """Rewrite a Boolean-sorted expression, replacing set tests with membership variables."""
    kind = expression.kind
    if kind in _SET_VALUED_KINDS:
        raise SetExpansionError(f"{kind.value} is a set value and cannot appear where a Boolean is required")
    if kind == ExpressionKind.VARIABLE:
        if isinstance(expression.value, str) and expression.value in universe:
            raise SetExpansionError(f"set variable {expression.value} cannot appear where a Boolean is required")
        return expression
    if kind == ExpressionKind.IN:
        element, container = expression.arguments
        return _membership(_element(element), _set_operand(container, universe), universe)
    if kind == ExpressionKind.SUBSET:
        left, right = expression.arguments
        left_name = _set_operand(left, universe)
        right_name = _set_operand(right, universe)
        return _conjunction(
            Expression.operator(
                ExpressionKind.IMPLIES,
                Expression.variable(member_variable(left_name, element)),
                _membership(element, right_name, universe),
            )
            for element in universe[left_name]
        )
    return Expression(
        kind,
        expression.value,
        tuple(_rewrite_boolean(argument, universe) for argument in expression.arguments),
    )


def _conjunction(terms: Iterable[Expression]) -> Expression:
    collected = tuple(terms)
    if not collected:
        return Expression.constant(True)
    return Expression.operator(ExpressionKind.AND, *collected)


def _disjunction(terms: list[Expression]) -> Expression:
    if not terms:
        return Expression.constant(False)
    return Expression.operator(ExpressionKind.OR, *terms)


def _members_of_set_value(expression: Expression, universe: dict[str, tuple[str, ...]]) -> dict[str, Expression]:
    """Expand a set-valued expression into a map from element to membership Boolean."""
    kind = expression.kind
    if kind == ExpressionKind.VARIABLE:
        if not isinstance(expression.value, str) or expression.value not in universe:
            raise SetExpansionError(f"{expression.value} is not a declared set variable")
        name = expression.value
        return {element: Expression.variable(member_variable(name, element)) for element in universe[name]}
    if kind == ExpressionKind.CONSTANT and isinstance(expression.value, str):
        return {expression.value: Expression.constant(True)}
    if kind == ExpressionKind.UNION:
        left, right = expression.arguments
        merged = _members_of_set_value(left, universe)
        for element, term in _members_of_set_value(right, universe).items():
            merged[element] = _disjunction([merged[element], term]) if element in merged else term
        return merged
    raise SetExpansionError(f"{kind.value} is not an expandable set-valued expression")


def _expanded_variables(ir: VerificationIR, universe: dict[str, tuple[str, ...]]) -> tuple[StateVariable, ...]:
    names = {variable.name for variable in ir.variables}
    expanded: list[StateVariable] = []
    for variable in ir.variables:
        if variable.sort != Sort.SET:
            expanded.append(variable)
            continue
        initial = variable.initial if isinstance(variable.initial, frozenset) else frozenset()
        for element in variable.universe:
            name = member_variable(variable.name, element)
            if name in names:
                raise SetExpansionError(f"expansion name {name} collides with a declared variable")
            expanded.append(StateVariable(name, Sort.BOOLEAN, element in initial))
    return tuple(expanded)


def _expanded_rule(
    rule: TransitionRule,
    variables: dict[str, StateVariable],
    universe: dict[str, tuple[str, ...]],
) -> TransitionRule:
    target_members: dict[str, dict[str, Expression]] = {}
    assignments: list[Assignment] = []
    for assignment in rule.assignments:
        variable = variables.get(assignment.variable)
        if variable is None:
            raise SetExpansionError(f"rule {rule.id} assigns undeclared variable {assignment.variable}")
        if variable.sort != Sort.SET:
            assignments.append(Assignment(assignment.variable, _rewrite_boolean(assignment.expression, universe)))
            continue
        target_members[assignment.variable] = _members_of_set_value(assignment.expression, universe)
    for set_name, members in target_members.items():
        for element in universe[set_name]:
            if element not in members:
                raise SetExpansionError(f"an assignment to {set_name} does not determine element {element}")
            assignments.append(Assignment(member_variable(set_name, element), members[element]))
    return TransitionRule(rule.id, _rewrite_boolean(rule.guard, universe), tuple(assignments))


def expand_sets(ir: VerificationIR) -> VerificationIR:
    """Expand every SET state variable into Boolean membership variables.

    Returns the input unchanged when it declares no set variable.
    """
    universe = _set_names(ir)
    if not universe:
        return ir
    undeclared = sorted(name for name, elements in universe.items() if not elements)
    if undeclared:
        raise SetExpansionError(
            f"set variable(s) {undeclared} declare no universe, so the expansion would have to guess the elements",
        )
    variables = _expanded_variables(ir, universe)
    by_name = {variable.name: variable for variable in ir.variables}
    transitions = tuple(_expanded_rule(rule, by_name, universe) for rule in ir.transitions)
    invariants = tuple(
        SafetyInvariant(item.id, _rewrite_boolean(item.expression, universe), item.description) for item in ir.invariants
    )
    return VerificationIR(
        f"{ir.id}:set-expanded",
        variables,
        transitions,
        invariants,
        ir.bound,
        (*ir.assumptions, "set variables expanded into Boolean membership variables over their declared universe"),
    )


__all__ = [
    "SetExpansionError",
    "expand_sets",
    "member_variable",
]
