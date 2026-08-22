"""Capability-envelope and generated-code confinement tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from conflux.adapters.models import ScriptedPlanner, ScriptedValueModel
from conflux.adapters.providers.code_sandbox import (
    CommandOutcome,
    DockerCodeSandboxExecutor,
)
from conflux.application import DecisionPipeline, MediationService
from conflux.domain import (
    Action,
    EnvironmentSnapshot,
    Principal,
    Provenance,
    ResourceRef,
    Session,
    action_fingerprint,
)
from conflux.ites import MediatingITES, TransitionKernel
from conflux.planning import (
    ActionTemplate,
    ActionTemplateNode,
    ArgumentSpec,
    ArgumentType,
    BindingEnvironment,
    CapabilityEnvelope,
    CodeExecutionResult,
    DynamicPlanExecutor,
    LiteralBinding,
    OperationCatalogue,
    OperationSchema,
    Plan,
    TemplateArgument,
    TerminalNode,
    TerminalOutcome,
    code_operation_permission,
    ground_action,
)
from conflux.policy import (
    AllowInternalReadPolicy,
    ExplicitConsentPolicy,
    InMemoryAuthorisationPolicy,
    PolicyGrant,
    SessionVisibilityPolicy,
)

PINNED_IMAGE = "python@sha256:" + "a" * 64

pytestmark = pytest.mark.integration


def provenance(principal: Principal, source: str) -> Provenance:
    return Provenance.from_principal(principal, source=source)


def envelope(**changes: object) -> CapabilityEnvelope:
    values: dict[str, object] = {
        "runtime_image": PINNED_IMAGE,
        "workspace": "demo",
        "read_paths": ("source.py", "inputs.json"),
        "write_paths": ("outputs",),
    }
    values.update(changes)
    return CapabilityEnvelope(**values)  # type: ignore[arg-type]


def code_action(alice: Principal, capability: CapabilityEnvelope) -> Action:
    source = provenance(alice, "generated-source")
    schema = OperationSchema(
        "sandbox.execute",
        "1",
        "code-sandbox",
        "workspace",
        "execute_code",
        code_operation_permission(),
        (
            ArgumentSpec("workspace", ArgumentType.STRING),
            ArgumentSpec("source", ArgumentType.STRING),
            ArgumentSpec("inputs", ArgumentType.ARRAY),
            ArgumentSpec("output_contract", ArgumentType.OBJECT),
            ArgumentSpec("envelope", ArgumentType.OBJECT),
        ),
        "workspace",
    )
    template = ActionTemplate(
        "execute-generated-code",
        schema.id,
        schema.version,
        (
            TemplateArgument("workspace", LiteralBinding("demo", source)),
            TemplateArgument(
                "source",
                LiteralBinding(
                    "from pathlib import Path\nPath('outputs/result.txt').write_text('ok')\n",
                    source,
                ),
            ),
            TemplateArgument("inputs", LiteralBinding([{"value": 1}], source)),
            TemplateArgument(
                "output_contract",
                LiteralBinding({"result.txt": "text"}, source),
            ),
            TemplateArgument("envelope", LiteralBinding(capability.to_dict(), source)),
        ),
    )
    return ground_action(
        template,
        catalogue=OperationCatalogue((schema,)),
        environment=BindingEnvironment({}, {}),
        invocation_provenance=source,
        control_provenance=source,
    ).to_action()


@dataclass
class RecordingRunner:
    outcome: CommandOutcome
    commands: list[tuple[str, ...]] = field(default_factory=list)

    def run(
        self,
        command: tuple[str, ...],
        *,
        workspace: Path,
        timeout_seconds: float,
        output_bytes: int,
    ) -> CommandOutcome:
        assert workspace.is_dir()
        assert (workspace / "source.py").is_file()
        assert (workspace / "inputs.json").is_file()
        assert timeout_seconds > 0
        assert output_bytes > 0
        self.commands.append(command)
        return self.outcome


def test_pinned_container_command_has_no_shell_or_host_workspace_mount(
    tmp_path: Path,
    alice: Principal,
) -> None:
    runner = RecordingRunner(
        CommandOutcome(
            0,
            stdout=b"ok\n",
            outputs={"result.txt": b"ok"},
        )
    )
    runtime = Principal("runtime", "Pinned Python Runtime", "service")
    executor = DockerCodeSandboxExecutor(
        tmp_path,
        provenance(runtime, "runtime-attestation"),
        runner=runner,
        availability=lambda _: True,
    )
    action = code_action(alice, envelope())
    result = executor.execute(
        action,
        certificate_id="certificate",
        action_fingerprint=action_fingerprint(action),
    )
    assert result.success
    assert isinstance(result.outcome, CodeExecutionResult)
    sandbox = result.outcome
    assert sandbox.outputs[0].artifact.provenance.principals == frozenset({alice, runtime})
    command = runner.commands[0]
    assert command[:3] == ("docker", "run", "--rm")
    assert ("--network", "none") == command[3:5]
    assert "--cap-drop" in command
    assert "--read-only" in command
    assert "shell=True" not in command
    assert "unsafe proposal" not in command
    assert command[-4:] == (PINNED_IMAGE, "-I", "-S", "source.py")


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"network_allowlist": ("example.com",)}, "network allowlists"),
        ({"credential_capabilities": ("token",)}, "credential capabilities"),
        ({"read_paths": ("host.txt",)}, "unsupported read path"),
        ({"write_paths": ("anything",)}, "outputs directory"),
    ],
)
def test_unsupported_capabilities_fail_closed_before_process_start(
    tmp_path: Path,
    alice: Principal,
    changes: dict[str, object],
    message: str,
) -> None:
    runner = RecordingRunner(CommandOutcome(0))
    executor = DockerCodeSandboxExecutor(
        tmp_path,
        provenance(alice, "runtime"),
        runner=runner,
        availability=lambda _: True,
    )
    action = code_action(alice, envelope(**changes))
    result = executor.execute(
        action,
        certificate_id="certificate",
        action_fingerprint=action_fingerprint(action),
    )
    assert not result.success
    assert message in (result.error or "")
    assert not runner.commands


def test_unavailable_container_engine_is_explicit(
    tmp_path: Path,
    alice: Principal,
) -> None:
    action = code_action(alice, envelope())
    executor = DockerCodeSandboxExecutor(
        tmp_path,
        provenance(alice, "runtime"),
        runner=RecordingRunner(CommandOutcome(0)),
        availability=lambda _: False,
    )
    result = executor.execute(
        action,
        certificate_id="certificate",
        action_fingerprint=action_fingerprint(action),
    )
    assert result.error == "sandbox_unavailable:docker"


def test_timeout_output_bound_and_nonzero_exit_are_distinct(
    tmp_path: Path,
    alice: Principal,
) -> None:
    action = code_action(alice, envelope())
    cases = (
        (CommandOutcome(None, timed_out=True), "sandbox_timeout"),
        (CommandOutcome(None, output_limited=True), "sandbox_output_bound"),
        (CommandOutcome(7), "code_nonzero_exit"),
    )
    for outcome, category in cases:
        result = DockerCodeSandboxExecutor(
            tmp_path,
            provenance(alice, "runtime"),
            runner=RecordingRunner(outcome),
            availability=lambda _: True,
        ).execute(
            action,
            certificate_id="certificate",
            action_fingerprint=action_fingerprint(action),
        )
        assert not result.success
        assert result.error == category


def test_capability_envelope_rejects_unpinned_and_unconfined_values() -> None:
    with pytest.raises(ValueError, match="pinned"):
        envelope(runtime_image="python:latest")
    with pytest.raises(ValueError, match="unconfined"):
        envelope(workspace="../escape")
    with pytest.raises(ValueError, match="positive"):
        envelope(output_bytes=0)


def test_certificate_substitution_is_rejected(
    tmp_path: Path,
    alice: Principal,
) -> None:
    action = code_action(alice, envelope())
    executor = DockerCodeSandboxExecutor(
        tmp_path,
        provenance(alice, "runtime"),
        runner=RecordingRunner(CommandOutcome(0)),
        availability=lambda _: True,
    )
    result = executor.execute(
        action,
        certificate_id="certificate",
        action_fingerprint="wrong",
    )
    assert result.error == "certificate_action_mismatch"


def test_generated_code_effect_is_mediated_and_traced(
    tmp_path: Path,
    alice: Principal,
) -> None:
    capability = envelope()
    canonical_action = code_action(alice, capability)
    source_provenance = provenance(alice, "invocation")
    template = ActionTemplate(
        canonical_action.id,
        "sandbox.execute",
        "1",
        (
            TemplateArgument(
                "workspace",
                LiteralBinding("demo", source_provenance),
            ),
            *tuple(
                TemplateArgument(
                    artifact.label or "",
                    LiteralBinding(artifact.value, artifact.provenance),
                )
                for artifact in canonical_action.inputs
            ),
        ),
    )
    schema = OperationSchema(
        "sandbox.execute",
        "1",
        "code-sandbox",
        "workspace",
        "execute_code",
        code_operation_permission(),
        (
            ArgumentSpec("workspace", ArgumentType.STRING),
            ArgumentSpec("source", ArgumentType.STRING),
            ArgumentSpec("inputs", ArgumentType.ARRAY),
            ArgumentSpec("output_contract", ArgumentType.OBJECT),
            ArgumentSpec("envelope", ArgumentType.OBJECT),
        ),
        "workspace",
    )
    node = ActionTemplateNode(canonical_action.id, template, source_provenance)
    done = TerminalNode(
        "done",
        TerminalOutcome.SUCCEEDED,
        "code completed",
        source_provenance,
        (node.id,),
    )
    plan = Plan("code-plan", "run confined code", (node, done), source_provenance)
    pipeline = DecisionPipeline(
        InMemoryAuthorisationPolicy(frozenset({PolicyGrant(alice.id, "execute_code", "demo")})),
        AllowInternalReadPolicy(),
        SessionVisibilityPolicy(),
        ExplicitConsentPolicy(frozenset({node.id})),
    )
    runtime = Principal("runtime", "Runtime", "service")
    result = DynamicPlanExecutor(
        ScriptedPlanner({}, {}),
        ScriptedValueModel({}),
        MediationService(MediatingITES(TransitionKernel(pipeline))),
        DockerCodeSandboxExecutor(
            tmp_path,
            provenance(runtime, "attestation"),
            runner=RecordingRunner(CommandOutcome(0, outputs={"result.txt": b"ok"})),
            availability=lambda _: True,
        ),
        OperationCatalogue((schema,)),
        EnvironmentSnapshot(
            "code-env",
            resources=(ResourceRef("code-sandbox", "demo", "workspace"),),
        ),
        Session("code-session", frozenset({alice})),
        clock=lambda: 0.0,
    ).execute(plan)

    assert result.completed
    assert result.mediation_reports[0].executed_count == 1
    event_types = [event.event_type for event in result.state.events]
    assert event_types.count("code.requested") == 1
    assert event_types.count("code.completed") == 1
    output = result.state.node_outputs()[(node.id, node.output_name)]
    assert isinstance(output.value, CodeExecutionResult)
