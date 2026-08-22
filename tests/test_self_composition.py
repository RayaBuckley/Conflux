"""Self-composition encoding for observational confidentiality verification."""

from __future__ import annotations

import pytest

from conflux.verification import (
    SELF_COMPOSITION_SCHEMA_VERSION,
    Assignment,
    Expression,
    ExpressionKind,
    FormalVerdict,
    SecretPartition,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
    compare_cone_of_influence,
    construct_product_ir,
    reduce_cone_of_influence,
    reference_safety_check,
)

pytestmark = pytest.mark.security


def _not(expression: Expression) -> Expression:
    return Expression.operator(ExpressionKind.NOT, expression)


def _equal(left: Expression, right: Expression) -> Expression:
    return Expression.operator(ExpressionKind.EQUAL, left, right)


def _and(*expressions: Expression) -> Expression:
    return Expression.operator(ExpressionKind.AND, *expressions)


def confidentiality_safe_ir() -> VerificationIR:
    """A model where the output does not depend on the secret input.

    Both copies start with the same output value and the secret only flows
    into a variable that is never observed.  The confidentiality invariant
    (output == output') should hold.
    """
    return VerificationIR(
        "confidentiality-safe",
        (
            StateVariable("secret", Sort.BOOLEAN, True),
            StateVariable("output", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "set-output",
                Expression.constant(True),
                (Assignment("output", Expression.constant(False)),),
            ),
        ),
        (),
        3,
        ("safe fixture: output is constant regardless of secret",),
    )


def confidentiality_unsafe_ir() -> VerificationIR:
    """A model where the output directly leaks the secret.

    The output variable is assigned the value of the secret.  In the product
    IR, the two copies may start with different secrets, so the output values
    will diverge, violating the confidentiality invariant.
    """
    return VerificationIR(
        "confidentiality-unsafe",
        (
            StateVariable("secret", Sort.BOOLEAN, True),
            StateVariable("output", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "leak-secret",
                Expression.constant(True),
                (Assignment("output", Expression.variable("secret")),),
            ),
        ),
        (),
        3,
        ("unsafe fixture: output copies the secret",),
    )


def _partition() -> SecretPartition:
    return SecretPartition(
        observable_variable_ids=frozenset({"output"}),
        secret_variable_ids=frozenset({"secret"}),
        observer_description="unauthorised principal who cannot read the secret",
    )


# ---------------------------------------------------------------------------
# SecretPartition
# ---------------------------------------------------------------------------


class TestSecretPartition:
    def test_requires_observable_variables(self) -> None:
        with pytest.raises(ValueError, match="at least one observable"):
            SecretPartition(
                observable_variable_ids=frozenset(),
                secret_variable_ids=frozenset({"secret"}),
            )

    def test_requires_secret_variables(self) -> None:
        with pytest.raises(ValueError, match="at least one secret"):
            SecretPartition(
                observable_variable_ids=frozenset({"output"}),
                secret_variable_ids=frozenset(),
            )

    def test_rejects_overlapping_sets(self) -> None:
        with pytest.raises(ValueError, match="disjoint"):
            SecretPartition(
                observable_variable_ids=frozenset({"leaked"}),
                secret_variable_ids=frozenset({"leaked"}),
            )

    def test_round_trip_serialisation(self) -> None:
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output", "effect"}),
            secret_variable_ids=frozenset({"secret", "hidden"}),
            observer_description="mallory",
            declassification_boundaries=("boundary-1",),
        )
        restored = SecretPartition.from_dict(partition.to_dict())
        assert restored == partition

    def test_from_dict_rejects_wrong_schema_version(self) -> None:
        payload = SecretPartition(
            observable_variable_ids=frozenset({"output"}),
            secret_variable_ids=frozenset({"secret"}),
        ).to_dict()
        payload["schema_version"] = "999"
        with pytest.raises(ValueError, match="unsupported"):
            SecretPartition.from_dict(payload)

    def test_schema_version_is_one(self) -> None:
        assert SELF_COMPOSITION_SCHEMA_VERSION == "1"


# ---------------------------------------------------------------------------
# construct_product_ir
# ---------------------------------------------------------------------------


class TestProductIRConstruction:
    def test_doubles_variables(self) -> None:
        ir = confidentiality_safe_ir()
        product = construct_product_ir(ir, _partition())
        names = {v.name for v in product.variables}
        assert names == {"secret", "secret__prime", "output", "output__prime"}

    def test_doubles_rules(self) -> None:
        ir = confidentiality_safe_ir()
        product = construct_product_ir(ir, _partition())
        rule_ids = {r.id for r in product.transitions}
        assert rule_ids == {"set-output"}

    def test_combined_rule_updates_both_copies(self) -> None:
        ir = confidentiality_unsafe_ir()
        product = construct_product_ir(ir, _partition())
        rule = product.transitions[0]
        assert rule.id == "leak-secret"
        assigned_vars = {a.variable for a in rule.assignments}
        # Lockstep: both primed and unprimed variables are updated
        assert assigned_vars == {"output", "output__prime"}
        # The primed assignment should reference the primed secret
        primed_assignment = next(a for a in rule.assignments if a.variable == "output__prime")
        assert primed_assignment.expression.kind == ExpressionKind.VARIABLE
        assert primed_assignment.expression.value == "secret__prime"
        # The guard is the conjunction of original and primed guards
        assert rule.guard.kind == ExpressionKind.AND

    def test_adds_confidentiality_invariant(self) -> None:
        ir = confidentiality_safe_ir()
        product = construct_product_ir(ir, _partition())
        inv_ids = {inv.id for inv in product.invariants}
        assert inv_ids == {"confidentiality__output"}

    def test_invariant_checks_equality(self) -> None:
        ir = confidentiality_safe_ir()
        product = construct_product_ir(ir, _partition())
        inv = product.invariants[0]
        assert inv.expression.kind == ExpressionKind.EQUAL
        args = inv.expression.arguments
        assert args[0].kind == ExpressionKind.VARIABLE
        assert args[0].value == "output"
        assert args[1].kind == ExpressionKind.VARIABLE
        assert args[1].value == "output__prime"

    def test_product_is_valid_ir(self) -> None:
        ir = confidentiality_safe_ir()
        product = construct_product_ir(ir, _partition())
        # If it constructs without error, it passed VerificationIR.__post_init__
        assert product.id == "confidentiality-safe--product"
        assert product.bound == ir.bound

    def test_rejects_unknown_observable(self) -> None:
        ir = confidentiality_safe_ir()
        partition = SecretPartition(
            observable_variable_ids=frozenset({"nonexistent"}),
            secret_variable_ids=frozenset({"secret"}),
        )
        with pytest.raises(ValueError, match="not in IR"):
            construct_product_ir(ir, partition)

    def test_rejects_unknown_secret(self) -> None:
        ir = confidentiality_safe_ir()
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output"}),
            secret_variable_ids=frozenset({"nonexistent"}),
        )
        with pytest.raises(ValueError, match="not in IR"):
            construct_product_ir(ir, partition)

    def test_preserves_initial_values_for_non_secret(self) -> None:
        ir = confidentiality_safe_ir()
        product = construct_product_ir(ir, _partition())
        output = next(v for v in product.variables if v.name == "output")
        output_prime = next(v for v in product.variables if v.name == "output__prime")
        assert output.initial == output_prime.initial

    def test_assumptions_document_encoding(self) -> None:
        ir = confidentiality_safe_ir()
        product = construct_product_ir(ir, _partition())
        joined = " | ".join(product.assumptions)
        assert "self-composition" in joined
        assert "output" in joined
        assert "secret" in joined


# ---------------------------------------------------------------------------
# Reference interpreter: safe fixture
# ---------------------------------------------------------------------------


class TestSafeFixture:
    def test_reference_safety_holds(self) -> None:
        ir = confidentiality_safe_ir()
        partition = _partition()
        product = construct_product_ir(ir, partition)
        result = reference_safety_check(product)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_reference_safety_fails_on_leak(self) -> None:
        ir = confidentiality_unsafe_ir()
        partition = _partition()
        product = construct_product_ir(ir, partition)
        result = reference_safety_check(product)
        assert result.verdict == FormalVerdict.UNSAFE
        assert len(result.counterexample) > 0

    def test_counterexample_shows_divergence(self) -> None:
        ir = confidentiality_unsafe_ir()
        partition = _partition()
        product = construct_product_ir(ir, partition)
        result = reference_safety_check(product)
        assert result.verdict == FormalVerdict.UNSAFE
        final_state = result.counterexample[-1]["state"]
        assert isinstance(final_state, dict)
        # The output values should differ after the leak rule fires
        output = final_state.get("output")
        output_prime = final_state.get("output__prime")
        assert output != output_prime


# ---------------------------------------------------------------------------
# COI reduction on product IR
# ---------------------------------------------------------------------------


class TestCOIReduction:
    def test_coi_preserves_verdict_safe(self) -> None:
        ir = confidentiality_safe_ir()
        partition = _partition()
        product = construct_product_ir(ir, partition)
        inv_ids = tuple(inv.id for inv in product.invariants)
        comparison = compare_cone_of_influence(product, inv_ids)
        assert comparison.equivalent

    def test_coi_preserves_verdict_unsafe(self) -> None:
        ir = confidentiality_unsafe_ir()
        partition = _partition()
        product = construct_product_ir(ir, partition)
        inv_ids = tuple(inv.id for inv in product.invariants)
        comparison = compare_cone_of_influence(product, inv_ids)
        assert comparison.equivalent
        assert comparison.original.verdict == FormalVerdict.UNSAFE
        assert comparison.reduced.verdict == FormalVerdict.UNSAFE

    def test_coi_removes_secret_variables(self) -> None:
        """The COI should be able to remove variables not relevant to the
        confidentiality invariant when the secret does not directly appear
        in the invariant expression."""
        ir = confidentiality_safe_ir()
        partition = _partition()
        product = construct_product_ir(ir, partition)
        inv_ids = tuple(inv.id for inv in product.invariants)
        reduction = reduce_cone_of_influence(product, inv_ids)
        # The invariant references output and output__prime.
        # Secret and secret__prime should be pulled in via the leak rule's
        # assignment dependency.  In the safe fixture, the rule sets output
        # to a constant, so secret is NOT a dependency.
        # Therefore secret and secret__prime should be removed.
        removed = set(reduction.removed_variables)
        assert "secret" in removed or "secret__prime" in removed


# ---------------------------------------------------------------------------
# Multiple observables
# ---------------------------------------------------------------------------


class TestMultipleObservables:
    def test_multiple_invariants_created(self) -> None:
        ir = VerificationIR(
            "multi-observable",
            (
                StateVariable("secret", Sort.BOOLEAN, True),
                StateVariable("output_a", Sort.BOOLEAN, False),
                StateVariable("output_b", Sort.BOOLEAN, False),
            ),
            (
                TransitionRule(
                    "set-a",
                    Expression.constant(True),
                    (Assignment("output_a", Expression.constant(False)),),
                ),
                TransitionRule(
                    "set-b",
                    Expression.constant(True),
                    (Assignment("output_b", Expression.constant(False)),),
                ),
            ),
            (),
            3,
        )
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output_a", "output_b"}),
            secret_variable_ids=frozenset({"secret"}),
        )
        product = construct_product_ir(ir, partition)
        inv_ids = {inv.id for inv in product.invariants}
        assert inv_ids == {"confidentiality__output_a", "confidentiality__output_b"}

    def test_multiple_observables_all_safe(self) -> None:
        ir = VerificationIR(
            "multi-observable",
            (
                StateVariable("secret", Sort.BOOLEAN, True),
                StateVariable("output_a", Sort.BOOLEAN, False),
                StateVariable("output_b", Sort.BOOLEAN, False),
            ),
            (
                TransitionRule(
                    "set-a",
                    Expression.constant(True),
                    (Assignment("output_a", Expression.constant(False)),),
                ),
                TransitionRule(
                    "set-b",
                    Expression.constant(True),
                    (Assignment("output_b", Expression.constant(False)),),
                ),
            ),
            (),
            3,
        )
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output_a", "output_b"}),
            secret_variable_ids=frozenset({"secret"}),
        )
        product = construct_product_ir(ir, partition)
        result = reference_safety_check(product)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_one_observable_leaks(self) -> None:
        ir = VerificationIR(
            "multi-observable-partial-leak",
            (
                StateVariable("secret", Sort.BOOLEAN, True),
                StateVariable("output_a", Sort.BOOLEAN, False),
                StateVariable("output_b", Sort.BOOLEAN, False),
            ),
            (
                TransitionRule(
                    "leak-a",
                    Expression.constant(True),
                    (Assignment("output_a", Expression.variable("secret")),),
                ),
                TransitionRule(
                    "safe-b",
                    Expression.constant(True),
                    (Assignment("output_b", Expression.constant(False)),),
                ),
            ),
            (),
            3,
        )
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output_a", "output_b"}),
            secret_variable_ids=frozenset({"secret"}),
        )
        product = construct_product_ir(ir, partition)
        result = reference_safety_check(product)
        assert result.verdict == FormalVerdict.UNSAFE


# ---------------------------------------------------------------------------
# Integer secrets
# ---------------------------------------------------------------------------


class TestIntegerSecret:
    def test_integer_secret_leak_detected(self) -> None:
        ir = VerificationIR(
            "integer-leak",
            (
                StateVariable("secret", Sort.INTEGER, 0, 0, 3),
                StateVariable("output", Sort.INTEGER, 0, 0, 3),
            ),
            (
                TransitionRule(
                    "leak",
                    Expression.constant(True),
                    (Assignment("output", Expression.variable("secret")),),
                ),
            ),
            (),
            3,
        )
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output"}),
            secret_variable_ids=frozenset({"secret"}),
        )
        product = construct_product_ir(ir, partition)
        result = reference_safety_check(product)
        assert result.verdict == FormalVerdict.UNSAFE

    def test_integer_secret_no_leak_safe(self) -> None:
        ir = VerificationIR(
            "integer-safe",
            (
                StateVariable("secret", Sort.INTEGER, 0, 0, 3),
                StateVariable("output", Sort.INTEGER, 0, 0, 3),
            ),
            (
                TransitionRule(
                    "set-output",
                    Expression.constant(True),
                    (Assignment("output", Expression.constant(1)),),
                ),
            ),
            (),
            3,
        )
        partition = SecretPartition(
            observable_variable_ids=frozenset({"output"}),
            secret_variable_ids=frozenset({"secret"}),
        )
        product = construct_product_ir(ir, partition)
        result = reference_safety_check(product)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)
