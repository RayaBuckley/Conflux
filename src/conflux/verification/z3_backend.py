"""Optional Z3 bounded-safety backend for the serialisable IR."""

from __future__ import annotations

from typing import Any

from conflux.domain import canonical_json, fingerprint

from .ir import Expression, ExpressionKind, Sort, VerificationIR
from .results import FormalVerdict, FormalVerificationResult


def verify_with_z3(ir: VerificationIR) -> FormalVerificationResult:
    try:
        import z3  # type: ignore[import-not-found,import-untyped,unused-ignore]
    except ImportError:
        return _unknown(ir, "optional_dependency_unavailable:z3")
    try:
        return _verify(ir, z3)
    except Exception as error:
        return _unknown(ir, f"z3_model_error:{type(error).__name__}:{error}", z3)


def _verify(ir: VerificationIR, z3: Any) -> FormalVerificationResult:
    if not ir.invariants:
        return _unknown(ir, "no_safety_invariants", z3)
    variables: dict[tuple[str, int], Any] = {}
    for variable in ir.variables:
        for step in range(ir.bound + 1):
            variables[(variable.name, step)] = (
                z3.Bool(f"{variable.name}__{step}")
                if variable.sort == Sort.BOOLEAN
                else z3.Int(f"{variable.name}__{step}")
            )
    solver = z3.Solver()
    for variable in ir.variables:
        solver.add(variables[(variable.name, 0)] == variable.initial)
        for step in range(ir.bound + 1):
            symbol = variables[(variable.name, step)]
            if variable.minimum is not None:
                solver.add(symbol >= variable.minimum)
            if variable.maximum is not None:
                solver.add(symbol <= variable.maximum)
    for step in range(ir.bound):
        alternatives: list[Any] = []
        for rule in ir.transitions:
            assignments = {item.variable: item.expression for item in rule.assignments}
            updates = [
                variables[(variable.name, step + 1)]
                == _expression(
                    assignments.get(
                        variable.name,
                        Expression.variable(variable.name),
                    ),
                    step,
                    variables,
                    z3,
                )
                for variable in ir.variables
            ]
            alternatives.append(
                z3.And(
                    _expression(rule.guard, step, variables, z3),
                    *updates,
                )
            )
        stutter = z3.And(
            *(
                variables[(variable.name, step + 1)]
                == variables[(variable.name, step)]
                for variable in ir.variables
            )
        )
        solver.add(z3.Or(*alternatives, stutter))
    query_hash = fingerprint(
        {
            "backend": "z3-bmc",
            "encoding_version": "2",
            "ir": ir.to_dict(),
            "checked_steps": list(range(ir.bound + 1)),
        }
    )
    solver_hash = fingerprint(
        {
            "backend": "z3",
            "version": str(z3.get_version_string()),
        }
    )
    model = None
    failure_step = None
    for step in range(ir.bound + 1):
        solver.push()
        solver.add(
            z3.Or(
                *(
                    z3.Not(_expression(invariant.expression, step, variables, z3))
                    for invariant in ir.invariants
                )
            )
        )
        result = solver.check()
        if result == z3.unknown:
            reason = solver.reason_unknown()
            solver.pop()
            return FormalVerificationResult(
                FormalVerdict.UNKNOWN,
                "z3-bmc",
                ir.fingerprint,
                query_hash,
                solver_hash,
                None,
                ir.bound,
                ir.assumptions,
                error=f"solver_unknown:{reason}",
            )
        if result == z3.sat:
            model = solver.model()
            failure_step = step
            break
        solver.pop()
    if model is None or failure_step is None:
        return FormalVerificationResult(
            FormalVerdict.BOUNDED_SAFE,
            "z3-bmc",
            ir.fingerprint,
            query_hash,
            solver_hash,
            None,
            ir.bound,
            ir.assumptions,
        )
    trace = tuple(
        {
            "step": step,
            "state": {
                variable.name: _model_value(
                    model.evaluate(
                        variables[(variable.name, step)],
                        model_completion=True,
                    ),
                    variable.sort,
                    z3,
                )
                for variable in ir.variables
            },
        }
        for step in range(failure_step + 1)
    )
    return FormalVerificationResult(
        FormalVerdict.UNSAFE,
        "z3-bmc",
        ir.fingerprint,
        query_hash,
        solver_hash,
        fingerprint(canonical_json(trace)),
        ir.bound,
        ir.assumptions,
        trace,
    )


def _expression(
    expression: Expression,
    step: int,
    variables: dict[tuple[str, int], Any],
    z3: Any,
) -> Any:
    if expression.kind == ExpressionKind.CONSTANT:
        return z3.BoolVal(expression.value) if isinstance(expression.value, bool) else z3.IntVal(expression.value)
    if expression.kind == ExpressionKind.VARIABLE:
        assert isinstance(expression.value, str)
        return variables[(expression.value, step)]
    values = tuple(
        _expression(argument, step, variables, z3)
        for argument in expression.arguments
    )
    if expression.kind == ExpressionKind.NOT:
        return z3.Not(values[0])
    if expression.kind == ExpressionKind.AND:
        return z3.And(*values)
    if expression.kind == ExpressionKind.OR:
        return z3.Or(*values)
    if expression.kind == ExpressionKind.EQUAL:
        return values[0] == values[1]
    if expression.kind == ExpressionKind.LESS_EQUAL:
        return values[0] <= values[1]
    return values[0] + values[1]


def _model_value(value: Any, sort: Sort, z3: Any) -> bool | int:
    if sort == Sort.BOOLEAN:
        return bool(z3.is_true(value))
    return int(value.as_long())


def _unknown(
    ir: VerificationIR,
    error: str,
    z3: Any | None = None,
) -> FormalVerificationResult:
    return FormalVerificationResult(
        FormalVerdict.UNKNOWN,
        "z3-bmc",
        ir.fingerprint,
        fingerprint({"ir": ir.fingerprint, "bound": ir.bound}),
        fingerprint(
            {
                "backend": "z3",
                "version": (
                    str(z3.get_version_string()) if z3 is not None else "unavailable"
                ),
            }
        ),
        None,
        ir.bound,
        ir.assumptions,
        error=error,
    )


__all__ = ["verify_with_z3"]
