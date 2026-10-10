r"""Every reference in the current manuscript must resolve, with no LaTeX toolchain.

The host has no TeX distribution, so a dangling `\ref` or a missing `\input`
target would otherwise reach a reviewer unnoticed. This check reads the
manuscript and every file it inputs, and compares the label and reference sets.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "research/publications/manuscript/conflux_fourth_year_2026.tex"

INPUT = re.compile(r"\\input\{([^}]+)\}")
LABEL = re.compile(r"\\label\{([^}]+)\}")
REFERENCE = re.compile(r"\\(?:ref|eqref|autoref|Cref|cref)\{([^}]+)\}")
COMMENT = re.compile(r"(?<!\\)%.*")


def _source(path: Path) -> str:
    """Return the file with LaTeX comments removed, line by line."""
    return "\n".join(COMMENT.sub("", line) for line in path.read_text(encoding="utf-8").splitlines())


def _collect(
    path: Path,
    seen: set[Path],
    labels: set[str],
    references: set[str],
    problems: list[str],
) -> None:
    text = _source(path)
    labels |= set(LABEL.findall(text))
    references |= set(REFERENCE.findall(text))
    for target in INPUT.findall(text):
        candidates = (
            path.parent / target,
            path.parent / f"{target}.tex",
            ROOT / target,
            ROOT / f"{target}.tex",
        )
        found = next((item for item in candidates if item.is_file()), None)
        if found is None:
            problems.append(f"{path.name}: input target not found: {target}")
            continue
        if found not in seen:
            seen.add(found)
            _collect(found, seen, labels, references, problems)


def _manuscript() -> tuple[set[str], set[str], list[str]]:
    labels: set[str] = set()
    references: set[str] = set()
    problems: list[str] = []
    _collect(MANUSCRIPT, {MANUSCRIPT}, labels, references, problems)
    return labels, references, problems


def test_every_input_target_exists() -> None:
    """A manuscript that inputs a missing file fails here rather than at build time."""
    _, _, problems = _manuscript()
    assert problems == []


def test_every_reference_resolves() -> None:
    """Every \ref must name a label defined in the manuscript or a file it inputs."""
    labels, references, _ = _manuscript()
    assert references - labels == set()


def test_generated_agentdojo_tables_are_input_by_the_manuscript() -> None:
    """The results section cites two tables; both must reach the document."""
    labels, references, _ = _manuscript()
    cited = {"tab:agentdojo-breadth", "tab:agentdojo-fingerprints"}
    assert cited <= references
    assert cited <= labels
