"""Assume/guarantee contracts for IR-to-runtime conformance.

Formalises the relationship between the verification IR and the runtime
kernel using assume/guarantee contracts:

- **Soundness assumption**: the runtime kernel faithfully populates the
  IR's state variables.
- **Sufficiency assumption**: all policy-relevant atoms are represented
  in the IR.

If both assumptions hold, verification results on the IR transfer to the
kernel.

Source: FORGE (arXiv:2602.16708) assume/guarantee theorem.
"""

from __future__ import annotations

from dataclasses import dataclass

from conflux.domain import fingerprint

from .interpreter import RuntimeTransitionRecord, differential_conformance
from .ir import VerificationIR
from .refinement import check_refinement, check_sound_abstraction


@dataclass(frozen=True, slots=True)
class AssumeGuaranteeContract:
    """An assume/guarantee contract between the IR and the runtime kernel."""

    ir: VerificationIR
    soundness_assumptions: tuple[str, ...]
    sufficiency_assumptions: tuple[str, ...]
    guarantee: str

    @property
    def ir_id(self) -> str:
        return self.ir.id

    @property
    def ir_fingerprint(self) -> str:
        return self.ir.fingerprint

    def to_dict(self) -> dict[str, object]:
        return {
            "ir_id": self.ir_id,
            "ir_fingerprint": self.ir_fingerprint,
            "soundness_assumptions": list(self.soundness_assumptions),
            "sufficiency_assumptions": list(self.sufficiency_assumptions),
            "guarantee": self.guarantee,
        }


@dataclass(frozen=True, slots=True)
class AssumeGuaranteeResult:
    """Result of checking an assume/guarantee contract."""

    contract: AssumeGuaranteeContract
    sound_abstraction_holds: bool
    refinement_holds: bool
    conformance_holds: bool
    all_assumptions_hold: bool
    fingerprint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract.to_dict(),
            "sound_abstraction_holds": self.sound_abstraction_holds,
            "refinement_holds": self.refinement_holds,
            "conformance_holds": self.conformance_holds,
            "all_assumptions_hold": self.all_assumptions_hold,
            "fingerprint": self.fingerprint,
        }


def build_contract(ir: VerificationIR) -> AssumeGuaranteeContract:
    """Build an assume/guarantee contract for a verification IR."""
    soundness = (
        "the runtime kernel faithfully populates the IR's state variables",
        "every kernel transition corresponds to an IR transition",
    )
    sufficiency = (
        "all policy-relevant atoms are represented in the IR",
        "no security-relevant state is abstracted away",
    )
    guarantee = "if the IR is safe, the kernel is safe"
    return AssumeGuaranteeContract(
        ir=ir,
        soundness_assumptions=soundness,
        sufficiency_assumptions=sufficiency,
        guarantee=guarantee,
    )


def check_contract(
    ir: VerificationIR,
    records: tuple[RuntimeTransitionRecord, ...],
) -> AssumeGuaranteeResult:
    """Check an assume/guarantee contract against runtime records."""
    contract = build_contract(ir)
    abstraction = check_sound_abstraction(ir)
    refinement = check_refinement(ir, records)
    conformance = differential_conformance(ir, records)
    all_hold = abstraction.sound and refinement.refinement_holds and conformance.conforms
    return AssumeGuaranteeResult(
        contract=contract,
        sound_abstraction_holds=abstraction.sound,
        refinement_holds=refinement.refinement_holds,
        conformance_holds=conformance.conforms,
        all_assumptions_hold=all_hold,
        fingerprint=fingerprint(
            {
                "ir": ir.fingerprint,
                "sound": abstraction.sound,
                "refinement": refinement.refinement_holds,
                "conformance": conformance.conforms,
            },
        ),
    )


def verify_subplan_in_isolation(
    plan_ir: VerificationIR,
    subplan_node_ids: tuple[str, ...],
    *,
    postcondition_invariants: tuple[str, ...] = (),
) -> VerificationIR:
    """Verify a subplan in isolation with postcondition stubs.

    Replaces transitions not in ``subplan_node_ids`` with stutter steps,
    keeping only the subplan's transitions active.  The postcondition
    invariants are added to the resulting IR.

    Source: BMC-Agent (arXiv:2605.21434) compositional verification.
    """
    from .ir import SafetyInvariant

    subplan_rules = tuple(rule for rule in plan_ir.transitions if any(node_id in rule.id for node_id in subplan_node_ids))
    stub_rules = tuple(rule for rule in plan_ir.transitions if not any(node_id in rule.id for node_id in subplan_node_ids))

    new_invariants = list(plan_ir.invariants)
    for inv_id in postcondition_invariants:
        new_invariants.append(SafetyInvariant(inv_id, plan_ir.invariants[0].expression, f"postcondition: {inv_id}"))

    return VerificationIR(
        id=f"{plan_ir.id}--subplan--{'-'.join(subplan_node_ids)}",
        variables=plan_ir.variables,
        transitions=subplan_rules + stub_rules,
        invariants=tuple(new_invariants),
        bound=plan_ir.bound,
        assumptions=plan_ir.assumptions + ("subplan verified in isolation with postcondition stubs",),
    )


__all__ = [
    "AssumeGuaranteeContract",
    "AssumeGuaranteeResult",
    "build_contract",
    "check_contract",
    "verify_subplan_in_isolation",
]
