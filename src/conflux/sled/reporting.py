"""
Reporting utilities for SLED and ITES runs.

This module turns raw evaluation outputs into compact summaries suitable for:
- debugging,
- benchmark comparison,
- paper figures,
- and CLI output.

The reporting layer is intentionally separate from the evaluator so that
evaluation semantics stay isolated from presentation and aggregation logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from conflux.core.actions import Action
from conflux.ites import Guarantee, ITESReport

from .statistics import EnvironmentStatistics, SuiteStatistics


@dataclass(frozen=True, slots=True)
class EnvironmentReport:
    """Serializable report wrapper for one environment's statistics."""

    statistics: EnvironmentStatistics

    def to_dict(self) -> dict[str, Any]:
        return asdict(self.statistics)


@dataclass(frozen=True, slots=True)
class SuiteReport:
    """Serializable report wrapper for a suite's statistics."""

    statistics: SuiteStatistics

    def to_dict(self) -> dict[str, Any]:
        return asdict(self.statistics)


def environment_report_from_statistics(statistics: EnvironmentStatistics) -> EnvironmentReport:
    """Build the canonical report wrapper for environment statistics."""
    return EnvironmentReport(statistics=statistics)


def suite_report_from_statistics(statistics: SuiteStatistics) -> SuiteReport:
    """Build the canonical report wrapper for suite statistics."""
    return SuiteReport(statistics=statistics)


@dataclass(frozen=True, slots=True)
class GuaranteeSummary:
    """
    A compact view of a single guarantee.
    """

    name: str
    holds: bool
    details: str = ""

    @classmethod
    def from_guarantee(cls, guarantee: Guarantee) -> "GuaranteeSummary":
        return cls(
            name=guarantee.name,
            holds=guarantee.holds,
            details=guarantee.details,
        )


@dataclass(frozen=True, slots=True)
class ITESReportSummary:
    """
    High-level summary of an ITES report.
    """

    guarantee_count: int
    passed_guarantees: int
    failed_guarantees: int
    declared_actions: int
    blocked_actions: int
    guarantees: tuple[GuaranteeSummary, ...] = field(default_factory=tuple)

    @classmethod
    def from_report(cls, report: ITESReport) -> "ITESReportSummary":
        guarantees = tuple(GuaranteeSummary.from_guarantee(g) for g in sorted(report.guarantees, key=lambda g: g.name))
        passed = sum(1 for g in guarantees if g.holds)
        failed = len(guarantees) - passed
        return cls(
            guarantee_count=len(guarantees),
            passed_guarantees=passed,
            failed_guarantees=failed,
            declared_actions=len(report.declared_actions),
            blocked_actions=len(report.blocked_actions),
            guarantees=guarantees,
        )

    @property
    def succeeded(self) -> bool:
        return self.failed_guarantees == 0


@dataclass(frozen=True, slots=True)
class BranchingSummary:
    """
    Summary of a search run's branching characteristics.
    """

    branches_explored: int
    terminal_branches: int
    max_depth_reached: int
    branch_option_count: int
    terminal_option_count: int
    used_representative_environment: bool
    compression_factor: float | None = None

    @property
    def effective_branching(self) -> float:
        """
        A simple derived measure useful for comparing runs.
        """
        if self.max_depth_reached <= 0:
            return 0.0
        return self.branches_explored / self.max_depth_reached


@dataclass(frozen=True, slots=True)
class ActionSummary:
    """
    Lightweight serialisable view of an action.

    This is intentionally generic because the evaluation stack includes many
    action subclasses.
    """

    kind: str
    visibility: str
    label: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_action(cls, action: Action[Any]) -> "ActionSummary":
        label = action.__class__.__name__
        metadata: dict[str, Any] = {}

        if hasattr(action, "provider_operation"):
            metadata["provider_operation"] = getattr(action, "provider_operation")
        if hasattr(action, "permission"):
            permission = getattr(action, "permission")
            metadata["permission"] = getattr(permission, "name", str(permission))
        if hasattr(action, "reason"):
            metadata["reason"] = getattr(action, "reason")
        if hasattr(action, "message"):
            metadata["message"] = getattr(action, "message")
        if hasattr(action, "prompt"):
            metadata["prompt"] = getattr(action, "prompt")
        if hasattr(action, "label"):
            metadata["label"] = getattr(action, "label")
        if hasattr(action, "scope"):
            metadata["scope"] = getattr(action, "scope")

        return cls(
            kind=getattr(action, "kind", action.__class__.__name__),
            visibility=getattr(action.visibility, "value", str(action.visibility)),
            label=label,
            metadata=metadata,
        )


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    """
    Combined summary of a run.

    This is the object most benchmark and CLI code should consume.
    """

    run_name: str
    report: ITESReportSummary
    branching: BranchingSummary
    declared_actions: tuple[ActionSummary, ...] = field(default_factory=tuple)
    blocked_actions: tuple[ActionSummary, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_run(
        cls,
        *,
        run_name: str,
        report: ITESReport,
        branching: BranchingSummary,
        declared_actions: Iterable[Action[Any]] = (),
        blocked_actions: Iterable[Action[Any]] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> "EvaluationSummary":
        return cls(
            run_name=run_name,
            report=ITESReportSummary.from_report(report),
            branching=branching,
            declared_actions=tuple(ActionSummary.from_action(action) for action in declared_actions),
            blocked_actions=tuple(ActionSummary.from_action(action) for action in blocked_actions),
            metadata={} if metadata is None else dict(metadata),
        )

    @property
    def succeeded(self) -> bool:
        return self.report.succeeded

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to a JSON-friendly dictionary.
        """
        return {
            "run_name": self.run_name,
            "report": asdict(self.report),
            "branching": asdict(self.branching),
            "declared_actions": [asdict(action) for action in self.declared_actions],
            "blocked_actions": [asdict(action) for action in self.blocked_actions],
            "metadata": dict(self.metadata),
            "succeeded": self.succeeded,
        }


def summarise_report(report: ITESReport) -> ITESReportSummary:
    """
    Produce a compact summary of an ITES report.
    """
    return ITESReportSummary.from_report(report)


def summarise_branching(
    *,
    branches_explored: int,
    terminal_branches: int,
    max_depth_reached: int,
    branch_option_count: int,
    terminal_option_count: int,
    used_representative_environment: bool,
    compression_factor: float | None = None,
) -> BranchingSummary:
    """
    Produce a compact branching summary.
    """
    return BranchingSummary(
        branches_explored=branches_explored,
        terminal_branches=terminal_branches,
        max_depth_reached=max_depth_reached,
        branch_option_count=branch_option_count,
        terminal_option_count=terminal_option_count,
        used_representative_environment=used_representative_environment,
        compression_factor=compression_factor,
    )


def summarise_actions(actions: Iterable[Action[Any]]) -> tuple[ActionSummary, ...]:
    """
    Convert an iterable of actions into summaries.
    """
    return tuple(ActionSummary.from_action(action) for action in actions)


def merge_metadata(*mappings: Mapping[str, Any]) -> dict[str, Any]:
    """
    Merge metadata dictionaries left-to-right.
    """
    merged: dict[str, Any] = {}
    for mapping in mappings:
        merged.update(mapping)
    return merged


def format_summary(summary: EvaluationSummary) -> str:
    """
    Render a human-readable report summary.
    """
    lines = [
        f"Run: {summary.run_name}",
        f"Succeeded: {summary.succeeded}",
        f"Guarantees: {summary.report.passed_guarantees}/{summary.report.guarantee_count} passed",
        f"Declared actions: {len(summary.declared_actions)}",
        f"Blocked actions: {len(summary.blocked_actions)}",
        f"Branches explored: {summary.branching.branches_explored}",
        f"Terminal branches: {summary.branching.terminal_branches}",
        f"Max depth reached: {summary.branching.max_depth_reached}",
        f"Branch options: {summary.branching.branch_option_count}",
        f"Terminal options: {summary.branching.terminal_option_count}",
    ]

    if summary.branching.compression_factor is not None:
        lines.append(f"Representative compression factor: {summary.branching.compression_factor:.3f}")

    if summary.report.failed_guarantees:
        failed = [g.name for g in summary.report.guarantees if not g.holds]
        lines.append(f"Failed guarantees: {', '.join(failed)}")

    return "\n".join(lines)


__all__ = [
    "ActionSummary",
    "BranchingSummary",
    "EvaluationSummary",
    "GuaranteeSummary",
    "ITESReportSummary",
    "format_summary",
    "merge_metadata",
    "summarise_actions",
    "summarise_branching",
    "summarise_report",
]
