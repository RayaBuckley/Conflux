"""Generate VerificationIR fixtures for formal verification."""

from __future__ import annotations

import json
import os
from pathlib import Path

from conflux.verification import (
    Assignment,
    Expression,
    ExpressionKind,
    SafetyInvariant,
    Sort,
    StateVariable,
    TransitionRule,
    VerificationIR,
)

ROOT = Path(__file__).resolve().parents[1]


def security_monitor_ir(*, authorised: bool = True) -> VerificationIR:
    authorised_expression = Expression.variable("authorised")
    executed_expression = Expression.variable("executed_unauthorised")
    return VerificationIR(
        "security-monitor" if authorised else "security-monitor-unsafe",
        (
            StateVariable("authorised", Sort.BOOLEAN, authorised),
            StateVariable("executed_unauthorised", Sort.BOOLEAN, False),
        ),
        (
            TransitionRule(
                "execute",
                Expression.constant(True),
                (
                    Assignment(
                        "executed_unauthorised",
                        Expression.operator(
                            ExpressionKind.NOT,
                            authorised_expression,
                        ),
                    ),
                ),
            ),
        ),
        (
            SafetyInvariant(
                "no-unauthorised-execution",
                Expression.operator(
                    ExpressionKind.NOT,
                    executed_expression,
                ),
            ),
        ),
        3,
        ("the action authorisation bit is an exact abstraction",),
    )


def main() -> None:
    runs = ROOT / "runs"
    runs.mkdir(parents=True, exist_ok=True)

    safe_ir = security_monitor_ir(authorised=True)
    safe_path = runs / "ir-security-monitor.json"
    safe_path.write_text(json.dumps(safe_ir.to_dict(), indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote safe IR to {safe_path} ({os.path.getsize(safe_path)} bytes)")

    unsafe_ir = security_monitor_ir(authorised=False)
    unsafe_path = runs / "ir-security-monitor-unsafe.json"
    unsafe_path.write_text(json.dumps(unsafe_ir.to_dict(), indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote unsafe IR to {unsafe_path} ({os.path.getsize(unsafe_path)} bytes)")


if __name__ == "__main__":
    main()
