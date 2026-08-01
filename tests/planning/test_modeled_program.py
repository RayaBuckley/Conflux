"""Modeled programs are inert, bounded, and dependency ordered."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from conflux.planning import ModeledEffect, ModeledProgram, parse_modeled_program


def _program() -> ModeledProgram:
    return ModeledProgram(
        "program",
        2,
        (
            ModeledEffect("read", "read-choice", (), ("choice",), ()),
            ModeledEffect("write", "write-choice", ("read",), ("choice",), ("output",)),
        ),
    )


def test_modeled_program_round_trip_and_order() -> None:
    program = _program()
    assert parse_modeled_program(program.to_dict()) == program
    assert program.action_ids == ("read-choice", "write-choice")


def test_modeled_program_rejects_cycles_duplicates_and_excess_steps() -> None:
    with pytest.raises(ValueError, match="forward_or_unknown"):
        ModeledProgram("cycle", 1, (ModeledEffect("a", "write", ("a",), (), ()),))
    with pytest.raises(ValueError, match="duplicate"):
        ModeledProgram(
            "duplicate",
            2,
            (ModeledEffect("a", "one", (), (), ()), ModeledEffect("a", "two", (), (), ())),
        )
    with pytest.raises(ValueError, match="step_bound"):
        ModeledProgram(
            "long",
            1,
            (ModeledEffect("a", "one", (), (), ()), ModeledEffect("b", "two", ("a",), (), ())),
        )


def test_modeled_program_module_has_no_code_execution_surface() -> None:
    path = Path(__file__).resolve().parents[2] / "src" / "conflux" / "planning" / "modeled_program.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden_calls = {"eval", "exec", "compile", "system", "run", "Popen"}
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not calls & forbidden_calls
    assert not imports & {"subprocess", "runpy", "importlib"}
