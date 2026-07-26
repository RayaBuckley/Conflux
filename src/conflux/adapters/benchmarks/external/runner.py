"""Shared execution utilities for external benchmark integrations.

Nearly every external defence integration follows the same pattern:

    build command
        ↓
    execute repository
        ↓
    collect stdout/stderr
        ↓
    parse JSON artefacts
        ↓
    return ExternalExecutionResult

This module centralises that behaviour so that individual integrations only
need to describe repository-specific command-line arguments and output
translation.

It intentionally contains no defence-specific logic.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from .base import ExternalExecutionResult


def extract_execution_time(artefacts: Mapping[str, Any]) -> float | None:
    """Extract a common runtime field from external benchmark output."""
    for key in ("execution_time_seconds", "runtime_seconds", "duration_seconds", "elapsed_seconds"):
        value = artefacts.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def run_external_command(
    *,
    command: Sequence[str],
    working_directory: Path,
    timeout_seconds: int | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ExternalExecutionResult:
    """Execute an external repository command.

    Parameters
    ----------
    command
        Command line to execute.
    working_directory
        Repository working directory.
    timeout_seconds
        Optional timeout.
    metadata
        Extra metadata attached to the result.

    Returns
    -------
    ExternalExecutionResult
    """

    start = time.perf_counter()

    completed = subprocess.run(
        list(command),
        cwd=str(working_directory),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )

    elapsed = time.perf_counter() - start

    artefacts = {}

    stdout_json = try_parse_json(completed.stdout)
    if stdout_json is not None:
        artefacts.update(stdout_json)

    stderr_json = try_parse_json(completed.stderr)
    if stderr_json is not None:
        artefacts.update(stderr_json)

    return ExternalExecutionResult(
        stdout=completed.stdout,
        stderr=completed.stderr,
        exit_code=completed.returncode,
        execution_time_seconds=elapsed,
        model_name=artefacts.get("model_name"),
        artefacts=artefacts,
        metadata={
            **dict(metadata or {}),
            "command": list(command),
            "working_directory": str(working_directory),
        },
    )


def try_parse_json(text: str) -> dict[str, Any] | None:
    """Attempt to parse a JSON object from text."""

    text = text.strip()

    if not text:
        return None

    try:
        obj = json.loads(text)
    except Exception:
        return None

    if not isinstance(obj, dict):
        return None

    return obj


def build_standard_command(
    *,
    python_executable: str,
    entrypoint: Sequence[str],
    scenario_id: str,
    scenario_name: str,
    principals: Sequence[str],
    data_items: Sequence[str],
    tools: Sequence[str],
    extra_args: Sequence[str] = (),
    environment_file: str | None = None,
    output_file: str | None = None,
    additional_flags: Mapping[str, str] | None = None,
) -> list[str]:
    """Construct a standard command line for an external benchmark."""

    cmd = [python_executable]
    cmd.extend(str(x) for x in entrypoint)

    if environment_file is not None:
        cmd.extend(
            [
                "--environment-file",
                environment_file,
            ]
        )

    if output_file is not None:
        cmd.extend(
            [
                "--output-file",
                output_file,
            ]
        )

    cmd.extend(
        [
            "--scenario-id",
            scenario_id,
            "--scenario-name",
            scenario_name,
        ]
    )

    for principal in principals:
        cmd.extend(
            [
                "--principal",
                principal,
            ]
        )

    for datum in data_items:
        cmd.extend(
            [
                "--datum",
                datum,
            ]
        )

    for tool in tools:
        cmd.extend(
            [
                "--tool",
                tool,
            ]
        )

    if additional_flags:
        for key, value in additional_flags.items():
            cmd.extend([key, value])

    cmd.extend(extra_args)

    return cmd
