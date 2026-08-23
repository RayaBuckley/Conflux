"""Tests for the maximal-permissiveness controller-synthesis experiment (RQ1)."""

from __future__ import annotations

import pytest

from conflux.verification import (
    ControllerStrategy,
    FiniteInstance,
    FormalVerdict,
    default_instance,
    evaluate_strategy,
    run_synthesis_experiment,
    synthesise_controller,
)

pytestmark = pytest.mark.security


class TestFiniteInstance:
    """The canonical finite instance used by the synthesis experiment."""

    def test_default_instance_has_two_principals(self) -> None:
        inst = default_instance()
        assert "alice" in inst.principals
        assert "mallory" in inst.principals

    def test_requester_is_authorised(self) -> None:
        inst = default_instance()
        assert inst.is_authorised("alice", "write")

    def test_attacker_is_not_authorised(self) -> None:
        inst = default_instance()
        assert not inst.is_authorised("mallory", "write")

    def test_instance_round_trips(self) -> None:
        inst = default_instance()
        restored = type(inst)(
            **{
                k: (frozenset(v) if k == "acs" else v)
                for k, v in {
                    "principals": inst.principals,
                    "actions": inst.actions,
                    "acs": [tuple(pair) for pair in inst.acs],
                    "requester": inst.requester,
                    "attacker": inst.attacker,
                    "authorised_action": inst.authorised_action,
                }.items()
            }
        )
        assert restored.acs == inst.acs


class TestITESSynthesis:
    """ITES intersection rule matches the synthesised maximally permissive safe controller."""

    def test_ites_is_pe_safe(self) -> None:
        result = evaluate_strategy(default_instance(), ControllerStrategy.ITES_INTERSECTION)
        assert result.pe_safe
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_synthesised_controller_matches_ites(self) -> None:
        result = evaluate_strategy(default_instance(), ControllerStrategy.ITES_INTERSECTION)
        assert result.equivalent
        active = [d for d in result.synthesised_decisions if not d.state.get("action_executed", False)]
        assert all(d.matches_ites for d in active)

    def test_ites_blocks_after_consuming_attacker_data(self) -> None:
        synth, ites = synthesise_controller(default_instance())
        consumed_state = next(d for d in ites if d.state.get("consumed_attacker") is True)
        assert not consumed_state.allow

    def test_ites_allows_without_attacker_influence(self) -> None:
        synth, ites = synthesise_controller(default_instance())
        clean_state = next(d for d in ites if d.state.get("consumed_attacker") is False)
        assert clean_state.allow


class TestNegativeControls:
    """Each defective controller must produce a PE counterexample."""

    def test_any_authorised_is_unsafe(self) -> None:
        result = evaluate_strategy(default_instance(), ControllerStrategy.ANY_AUTHORISED)
        assert result.verdict == FormalVerdict.UNSAFE
        assert len(result.counterexample) > 0

    def test_requester_only_is_unsafe(self) -> None:
        result = evaluate_strategy(default_instance(), ControllerStrategy.REQUESTER_ONLY)
        assert result.verdict == FormalVerdict.UNSAFE
        assert len(result.counterexample) > 0

    def test_drop_provenance_is_unsafe(self) -> None:
        result = evaluate_strategy(default_instance(), ControllerStrategy.DROP_PROVENANCE)
        assert result.verdict == FormalVerdict.UNSAFE
        assert len(result.counterexample) > 0

    def test_empty_is_privileged_is_unsafe(self) -> None:
        result = evaluate_strategy(default_instance(), ControllerStrategy.EMPTY_IS_PRIVILEGED)
        assert result.verdict == FormalVerdict.UNSAFE
        assert len(result.counterexample) > 0

    def test_stale_acs_is_unsafe(self) -> None:
        result = evaluate_strategy(default_instance(), ControllerStrategy.STALE_ACS)
        assert result.verdict == FormalVerdict.UNSAFE
        assert len(result.counterexample) > 0

    def test_counterexample_shows_pe_violation(self) -> None:
        """Each negative control's counterexample must show pe_violation=True."""
        safe_strategies = {ControllerStrategy.ITES_INTERSECTION, ControllerStrategy.READ_CHECK_ENABLED}
        for strategy in ControllerStrategy:
            if strategy in safe_strategies:
                continue
            result = evaluate_strategy(default_instance(), strategy)
            assert result.verdict == FormalVerdict.UNSAFE
            final_state = result.counterexample[-1]["state"]
            assert isinstance(final_state, dict)
            assert final_state.get("pe_violation") is True


class TestReadCheckAblation:
    """The read-check ablation is PE-safe but stricter than ITES."""

    def test_read_check_is_pe_safe(self) -> None:
        result = evaluate_strategy(default_instance(), ControllerStrategy.READ_CHECK_ENABLED)
        assert result.verdict in (FormalVerdict.SAFE, FormalVerdict.BOUNDED_SAFE)

    def test_read_check_no_counterexample(self) -> None:
        result = evaluate_strategy(default_instance(), ControllerStrategy.READ_CHECK_ENABLED)
        assert len(result.counterexample) == 0


class TestEnvironmentDerivedInstance:
    """FiniteInstance can be derived from an EnvironmentSnapshot."""

    def test_from_environment_extracts_principals(self) -> None:
        from conflux.domain import DataItem, EnvironmentSnapshot, Principal

        alice = Principal("alice", "Alice")
        mallory = Principal("mallory", "Mallory")
        env = EnvironmentSnapshot(
            id="test-env",
            data=(
                DataItem(id="d1", value="hello", authors={alice}, readers={alice, mallory}),
                DataItem(id="d2", value="world", authors={mallory}, readers={alice}),
            ),
        )
        instance = FiniteInstance.from_environment(
            environment=env,
            requester="alice",
            attacker="mallory",
            authorised_action="write",
        )
        assert "alice" in instance.principals
        assert "mallory" in instance.principals
        assert len(instance.principals) == 2

    def test_from_environment_rejects_unknown_requester(self) -> None:
        from conflux.domain import DataItem, EnvironmentSnapshot, Principal

        alice = Principal("alice", "Alice")
        env = EnvironmentSnapshot(
            id="test-env",
            data=(DataItem(id="d1", value="hello", authors={alice}, readers={alice}),),
        )
        with pytest.raises(ValueError, match="requester"):
            FiniteInstance.from_environment(
                environment=env,
                requester="bob",
                attacker="alice",
                authorised_action="write",
            )

    def test_from_environment_with_explicit_acs(self) -> None:
        from conflux.domain import DataItem, EnvironmentSnapshot, Principal

        alice = Principal("alice", "Alice")
        mallory = Principal("mallory", "Mallory")
        env = EnvironmentSnapshot(
            id="test-env",
            data=(DataItem(id="d1", value="hello", authors={alice}, readers={alice, mallory}),),
        )
        instance = FiniteInstance.from_environment(
            environment=env,
            requester="alice",
            attacker="mallory",
            authorised_action="write",
            acs=frozenset({("alice", "write")}),
        )
        assert instance.is_authorised("alice", "write")
        assert not instance.is_authorised("mallory", "write")

    def test_from_environment_synthesis_works(self) -> None:
        from conflux.domain import DataItem, EnvironmentSnapshot, Principal

        alice = Principal("alice", "Alice")
        mallory = Principal("mallory", "Mallory")
        env = EnvironmentSnapshot(
            id="test-env",
            data=(DataItem(id="d1", value="hello", authors={alice}, readers={alice, mallory}),),
        )
        instance = FiniteInstance.from_environment(
            environment=env,
            requester="alice",
            attacker="mallory",
            authorised_action="write",
            acs=frozenset({("alice", "write")}),
        )
        result = evaluate_strategy(instance, ControllerStrategy.ITES_INTERSECTION)
        assert result.pe_safe


class TestExperimentResult:
    """The full experiment result is well-formed."""

    def test_experiment_returns_valid_dict(self) -> None:
        result = run_synthesis_experiment()
        assert result["schema_version"] == "1"
        assert "ites" in result
        assert "controls" in result
        assert "summary" in result

    def test_ites_is_pe_safe_in_experiment(self) -> None:
        result = run_synthesis_experiment()
        assert result["summary"]["ites_pe_safe"] is True

    def test_ites_matches_synthesis_in_experiment(self) -> None:
        result = run_synthesis_experiment()
        assert result["summary"]["ites_matches_synthesis"] is True

    def test_all_controls_unsafe(self) -> None:
        result = run_synthesis_experiment()
        assert result["summary"]["all_controls_unsafe"] is True

    def test_control_count(self) -> None:
        result = run_synthesis_experiment()
        assert result["summary"]["control_count"] == 5

    def test_experiment_has_fingerprint(self) -> None:
        result = run_synthesis_experiment()
        assert "fingerprint" in result
        assert len(result["fingerprint"]) == 64
