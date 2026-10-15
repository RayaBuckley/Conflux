"""Unbounded invariant checking by translation to constrained Horn clauses.

Where the Z3 backend unrolls the transition relation to ``ir.bound`` steps, this backend
encodes the same IR once as a constrained Horn clause system over a single state relation
and lets Z3's Spacer engine search for an inductive invariant. The verdict therefore does
not depend on unrolling: a SAFE verdict is a statement about every reachable state, not
about the first ``bound + 1`` states.

Encoding
--------
One relation ``Rel(state, ...)`` over the IR's state variables, with:

- one fact for the initial state;
- one Horn clause per transition rule, whose body is the rule guard conjoined with the
  relation on the current state and the variable domains, and whose head is the relation on
  the assigned next state;
- one query per safety invariant, asking whether a reachable state satisfies its negation.

A stutter step leaves every variable unchanged, so it does not add reachable states; the
bounded backends emit it to make the step relation total, and the Horn encoding omits it.

Fragment
--------
An IR outside the fragment is refused with ``unsupported_ir:...`` rather than weakened:

- a SET-sorted state variable is refused. The bounded backends expand a set over an explicit
  finite universe, and that expansion is what makes them bounded; there is no universe here,
  so there is no faithful translation.
- a rule guard with a disjunction at the top level is refused. Clause splitting would be an
  encoding change, not a translation detail.
- an assignment value that is not a variable, an integer constant, an addition or a Boolean
  formula is refused.

Step budgets
------------
The delegation factory emits a guard of the form ``step <= k``, which is a step budget. The
bounded backends keep it, because they instantiate ``step`` up to ``bound``. This encoder
drops that conjunct, which is what makes the route unbounded; ``step`` remains a state
variable with its own domain, so a property that constrains ``step`` is still checked, but no
rule is disabled for exceeding a budget. Dropping a conjunct widens the reachable set, so a
SAFE verdict is sound for the budgeted system as well, and a counterexample found without the
budget may not be reachable with it. The result records that as an assumption.
"""

from __future__ import annotations

from typing import Any

from conflux.domain import fingerprint

from .ir import Expression, ExpressionKind, Sort, StateVariable, VerificationIR
from .results import FormalVerdict, FormalVerificationResult

BACKEND = "z3-spacer"

_BUDGET_VARIABLE = "step"

_UNBOUNDED_ASSUMPTION = (
    "step_budget_dropped:the 'step' budget guard and its declared upper bound are removed, so reachability is "
    "unbounded and a safe verdict over-approximates the budgeted system"
)

_SET_OPERATORS = frozenset(
    {
        ExpressionKind.IN,
        ExpressionKind.SUBSET,
        ExpressionKind.UNION,
        ExpressionKind.INTERSECT,
        ExpressionKind.DIFFERENCE,
    },
)

_BOOLEAN_OPERATORS = frozenset(
    {
        ExpressionKind.NOT,
        ExpressionKind.AND,
        ExpressionKind.OR,
        ExpressionKind.IMPLIES,
        ExpressionKind.EQUAL,
        ExpressionKind.LESS_EQUAL,
        ExpressionKind.GREATER_EQUAL,
        ExpressionKind.GREATER_THAN,
        ExpressionKind.LESS_THAN,
    },
)


class HornEncodingError(Exception):
    """The IR lies outside the fragment the Horn encoder translates."""


def verify_with_horn(ir: VerificationIR, *, timeout_ms: int = 60_000) -> FormalVerificationResult:
    """Check every invariant of IR with Z3 Spacer, without unrolling.

    Each invariant is queried on its own. SAFE means every reachable state satisfies every
    invariant; UNSAFE means at least one reachable state refutes one, and the counterexample
    records which invariants were refuted. This encoding returns no concrete violating state,
    so the entry names the refuted invariant rather than a state; pair a UNSAFE verdict with a
    bounded backend when a state-level witness is needed.
    """
    if not ir.invariants:
        return _unknown(ir, "no_safety_invariants")
    if any(variable.sort == Sort.SET for variable in ir.variables):
        return _unknown(ir, "set_sort_not_supported_by_horn_backend")
    try:
        import z3
    except ImportError:
        return _unknown(ir, "optional_dependency_unavailable:z3")
    try:
        encoder = _HornEncoder(ir, z3=z3, timeout_ms=timeout_ms)
        encoder.build()
    except HornEncodingError as error:
        return _unknown(ir, f"unsupported_ir:{error}", z3)
    except Exception as error:  # engine-level failure is an obstruction, not a crash
        return _unknown(ir, f"z3_horn_error:{type(error).__name__}:{error}", z3)
    query_hash = fingerprint(
        {"backend": BACKEND, "encoding_version": "1", "ir": ir.to_dict(), "mode": "unbounded"},
    )
    solver_hash = fingerprint({"backend": "z3", "version": str(z3.get_version_string())})
    refuted: list[str] = []
    unsettled: list[str] = []
    try:
        for invariant in sorted(ir.invariants, key=lambda item: item.id):
            outcome = encoder.query(encoder.holds(invariant.expression, negate=True))
            if outcome == "sat":
                refuted.append(invariant.id)
            elif outcome != "unsat":
                unsettled.append(invariant.id)
    except Exception as error:  # engine-level failure is an obstruction, not a crash
        return _unknown(ir, f"z3_horn_error:{type(error).__name__}:{error}", z3)
    if refuted:
        return FormalVerificationResult(
            FormalVerdict.UNSAFE,
            BACKEND,
            ir.fingerprint,
            query_hash,
            solver_hash,
            None,
            ir.bound,
            (*ir.assumptions, _UNBOUNDED_ASSUMPTION),
            tuple({"invariant": name} for name in refuted),
        )
    if unsettled:
        return _unknown(ir, f"solver_unknown:{','.join(unsettled)}", z3)
    return FormalVerificationResult(
        FormalVerdict.SAFE,
        BACKEND,
        ir.fingerprint,
        query_hash,
        solver_hash,
        None,
        ir.bound,
        (*ir.assumptions, _UNBOUNDED_ASSUMPTION),
    )


class _HornEncoder:
    """A constrained Horn encoding of one IR, decided with Z3 Spacer."""

    def __init__(self, ir: VerificationIR, *, z3: Any, timeout_ms: int) -> None:
        self.ir = ir
        self.z3 = z3
        self.timeout_ms = timeout_ms
        self.variables: tuple[StateVariable, ...] = tuple(sorted(ir.variables, key=lambda item: item.name))
        self.env: dict[str, Any] = {}
        self.relation: Any = None
        self.program: Any = None

    def build(self) -> None:
        """Register the relation, the initial-state fact and one clause per transition rule."""
        z3 = self.z3
        self.env = {
            variable.name: (z3.Bool(variable.name) if variable.sort == Sort.BOOLEAN else z3.Int(variable.name))
            for variable in self.variables
        }
        self.relation = z3.Function(
            f"Rel__{self.ir.id.replace(':', '_').replace('+', '_')}",
            *[self.env[variable.name].sort() for variable in self.variables],
            z3.BoolSort(),
        )
        program = z3.Fixedpoint()
        program.set(engine="spacer")
        program.set("timeout", self.timeout_ms)
        program.register_relation(self.relation)
        program.declare_var(*[self.env[variable.name] for variable in self.variables])
        self.program = program
        program.fact(self.relation(*[self._initial(variable) for variable in self.variables]))
        for rule in sorted(self.ir.transitions, key=lambda item: item.id):
            guard = _drop_step_budget(rule.guard)
            if _has_top_level_disjunction(guard):
                raise HornEncodingError(f"rule {rule.id!r} has a disjunctive guard")
            assigned = {assignment.variable: assignment.expression for assignment in rule.assignments}
            head = [
                self._value(assigned[variable.name]) if variable.name in assigned else self.env[variable.name]
                for variable in self.variables
            ]
            body = [self._formula(guard, top_level=True), self.relation(*[self.env[v.name] for v in self.variables])]
            domain = self._domain(head)
            if not z3.is_true(z3.simplify(domain)):
                body.append(domain)
            program.rule(self.relation(*head), body)

    def reachable(self) -> Any:
        """The reachability atom over the current state variables."""
        return self.relation(*[self.env[variable.name] for variable in self.variables])

    def query(self, formula: Any) -> str:
        """Return ``sat``, ``unsat`` or ``unknown`` for a reachable state satisfying formula.

        The reachability atom is conjoined here, not by the caller: a query over the state
        variables alone is unconstrained, and Spacer would answer ``sat`` for every formula
        that some (unreachable) state satisfies.
        """
        result = self.program.query(self.z3.And(self.reachable(), formula))
        if result == self.z3.sat:
            return "sat"
        if result == self.z3.unsat:
            return "unsat"
        return "unknown"

    def holds(self, expression: Expression, *, negate: bool = False) -> Any:
        """Return the reachability query for an invariant, optionally negated."""
        formula = self._formula(expression, top_level=False)
        return self.z3.Not(formula) if negate else formula

    def _initial(self, variable: StateVariable) -> Any:
        if variable.sort == Sort.BOOLEAN:
            return self.z3.BoolVal(bool(variable.initial))
        initial = variable.initial
        if not isinstance(initial, int) or isinstance(initial, bool):
            raise HornEncodingError(f"state variable {variable.name!r} has a non-integer initial value")
        return self.z3.IntVal(initial)

    def _domain(self, terms: list[Any]) -> Any:
        parts = []
        for variable, term in zip(self.variables, terms, strict=True):
            if variable.sort != Sort.INTEGER:
                continue
            if variable.minimum is not None:
                parts.append(term >= variable.minimum)
            maximum = None if variable.name == _BUDGET_VARIABLE else variable.maximum
            if maximum is not None:
                parts.append(term <= maximum)
        return self.z3.And(*parts) if parts else self.z3.BoolVal(True)

    def _formula(self, expression: Expression, *, top_level: bool) -> Any:
        return _to_formula(expression, self.env, self.z3, top_level=top_level)

    def _value(self, expression: Expression) -> Any:
        return _to_value(expression, self.env, self.z3)


def _to_formula(expression: Expression, env: dict[str, Any], z3: Any, *, top_level: bool) -> Any:
    kind = expression.kind
    if kind in _SET_OPERATORS:
        raise HornEncodingError(f"set operator {kind.value!r} has no Horn translation")
    if kind == ExpressionKind.CONSTANT:
        if isinstance(expression.value, bool):
            return z3.BoolVal(expression.value)
        raise HornEncodingError(f"a formula cannot be the constant {expression.value!r}")
    if kind == ExpressionKind.VARIABLE:
        return env[str(expression.value)]
    if kind == ExpressionKind.NOT:
        return z3.Not(_to_formula(expression.arguments[0], env, z3, top_level=False))
    if kind == ExpressionKind.AND:
        return z3.And(*[_to_formula(argument, env, z3, top_level=False) for argument in expression.arguments])
    if kind == ExpressionKind.OR:
        if top_level:
            raise HornEncodingError("disjunction at the top of a guard needs clause splitting")
        return z3.Or(*[_to_formula(argument, env, z3, top_level=False) for argument in expression.arguments])
    if kind == ExpressionKind.IMPLIES:
        left = _to_formula(expression.arguments[0], env, z3, top_level=False)
        right = _to_formula(expression.arguments[1], env, z3, top_level=False)
        return z3.Implies(left, right)
    if kind == ExpressionKind.EQUAL:
        return _to_value(expression.arguments[0], env, z3) == _to_value(expression.arguments[1], env, z3)
    if kind == ExpressionKind.LESS_EQUAL:
        return _to_value(expression.arguments[0], env, z3) <= _to_value(expression.arguments[1], env, z3)
    if kind == ExpressionKind.GREATER_EQUAL:
        return _to_value(expression.arguments[0], env, z3) >= _to_value(expression.arguments[1], env, z3)
    if kind == ExpressionKind.GREATER_THAN:
        return _to_value(expression.arguments[0], env, z3) > _to_value(expression.arguments[1], env, z3)
    if kind == ExpressionKind.LESS_THAN:
        return _to_value(expression.arguments[0], env, z3) < _to_value(expression.arguments[1], env, z3)
    raise HornEncodingError(f"operator {kind.value!r} is not a formula in this fragment")


def _to_value(expression: Expression, env: dict[str, Any], z3: Any) -> Any:
    kind = expression.kind
    if kind in _SET_OPERATORS:
        raise HornEncodingError(f"set operator {kind.value!r} has no Horn translation")
    if kind in _BOOLEAN_OPERATORS:
        return _to_formula(expression, env, z3, top_level=False)
    if kind == ExpressionKind.CONSTANT:
        value = expression.value
        if isinstance(value, bool):
            return z3.BoolVal(value)
        if not isinstance(value, int):
            raise HornEncodingError(f"a value expression cannot be the constant {value!r}")
        return z3.IntVal(value)
    if kind == ExpressionKind.VARIABLE:
        return env[str(expression.value)]
    if kind == ExpressionKind.ADD:
        return _to_value(expression.arguments[0], env, z3) + _to_value(expression.arguments[1], env, z3)
    raise HornEncodingError(f"operator {kind.value!r} cannot appear as an assignment value")


def _is_step_budget(expression: Expression) -> bool:
    """True for the pattern ``step <= <int constant>`` the delegation factory emits."""
    return (
        expression.kind == ExpressionKind.LESS_EQUAL
        and expression.arguments[0].kind == ExpressionKind.VARIABLE
        and expression.arguments[0].value == "step"
        and expression.arguments[1].kind == ExpressionKind.CONSTANT
        and isinstance(expression.arguments[1].value, int)
        and not isinstance(expression.arguments[1].value, bool)
    )


def _drop_step_budget(expression: Expression) -> Expression:
    """Replace every ``step <= k`` conjunct with true, leaving the rest of the guard alone."""
    if _is_step_budget(expression):
        return Expression.constant(True)
    if not expression.arguments:
        return expression
    arguments = tuple(_drop_step_budget(argument) for argument in expression.arguments)
    if arguments == expression.arguments:
        return expression
    return Expression(expression.kind, expression.value, arguments)


def _has_top_level_disjunction(expression: Expression) -> bool:
    """True when a disjunction can reach the top of a guard through conjunctions only."""
    if expression.kind == ExpressionKind.OR:
        return True
    if expression.kind == ExpressionKind.AND:
        return any(_has_top_level_disjunction(argument) for argument in expression.arguments)
    return False


def _unknown(ir: VerificationIR, error: str, z3: Any | None = None) -> FormalVerificationResult:
    return FormalVerificationResult(
        FormalVerdict.UNKNOWN,
        BACKEND,
        ir.fingerprint,
        fingerprint({"backend": BACKEND, "encoding_version": "1", "ir": ir.to_dict(), "mode": "unbounded"}),
        fingerprint({"backend": "z3", "version": (str(z3.get_version_string()) if z3 is not None else "unavailable")}),
        None,
        ir.bound,
        (*ir.assumptions, _UNBOUNDED_ASSUMPTION),
        error=error,
    )


__all__ = ["HornEncodingError", "verify_with_horn"]
