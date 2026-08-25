"""Golden SVG comparison tests for the Graphviz renderer.

Regenerates SVG from known VisualGraph fixtures and compares against
committed golden files.  If the SVG changes intentionally, update the
golden in the same commit that caused the change.

To regenerate goldens:  set PATH=C:\\Program Files\\Graphviz\\bin;%PATH%
and run:  python _gen_golden.py
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Ensure Graphviz bin directory is on PATH for subprocess calls
_GRAPHVIZ_BIN = r"C:\Program Files\Graphviz\bin"
if Path(_GRAPHVIZ_BIN).is_dir() and _GRAPHVIZ_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _GRAPHVIZ_BIN + os.pathsep + os.environ.get("PATH", "")

from conflux.visualisation.graph.graphviz import (  # noqa: E402
    _is_graphviz_available,
    render_svg,
)
from conflux.visualisation.model import (  # noqa: E402
    EdgeKind,
    EvidenceReference,
    NodeKind,
    VisualEdge,
    VisualField,
    VisualGraph,
    VisualNode,
    VisualStatus,
)

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "visualisation" / "golden"


def _simple_allow() -> VisualGraph:
    return VisualGraph(
        graph_id="simple-allow",
        title="Simple Allow",
        nodes=(
            VisualNode(
                node_id="n1",
                kind=NodeKind.EXECUTION,
                label="Branch root",
                fields=(VisualField(key="depth", value="0"),),
                status=VisualStatus.ALLOWED,
                source_ref=EvidenceReference(source_file="r.json", json_pointer="/branches/root"),
            ),
            VisualNode(
                node_id="n2",
                kind=NodeKind.ACTION,
                label="send_email",
                fields=(VisualField(key="outcome", value="AUTHORISED"),),
                status=VisualStatus.ALLOWED,
            ),
        ),
        edges=(VisualEdge(source="n1", target="n2", kind=EdgeKind.TRANSITION),),
    )


def _blocked_action() -> VisualGraph:
    return VisualGraph(
        graph_id="blocked-action",
        title="Blocked Action",
        nodes=(
            VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="Branch root", status=VisualStatus.ACTIVE),
            VisualNode(node_id="n2", kind=NodeKind.ACTION, label="delete_file", status=VisualStatus.BLOCKED),
        ),
        edges=(VisualEdge(source="n1", target="n2", kind=EdgeKind.TRANSITION),),
    )


def _mixed_graph() -> VisualGraph:
    return VisualGraph(
        graph_id="mixed-graph",
        title="Mixed Graph",
        nodes=(
            VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="E0", status=VisualStatus.ALLOWED),
            VisualNode(node_id="n2", kind=NodeKind.EXECUTION, label="E1", status=VisualStatus.BLOCKED),
            VisualNode(node_id="n3", kind=NodeKind.ACTION, label="A0", status=VisualStatus.UNKNOWN),
            VisualNode(node_id="n4", kind=NodeKind.DECISION, label="D0", status=VisualStatus.SUCCESS),
        ),
        edges=(
            VisualEdge(source="n1", target="n2", kind=EdgeKind.PARENT_OF),
            VisualEdge(source="n1", target="n3", kind=EdgeKind.TRANSITION),
            VisualEdge(source="n2", target="n4", kind=EdgeKind.DEPENDS_ON),
        ),
    )


_FIXTURES = {
    "simple-allow": _simple_allow,
    "blocked-action": _blocked_action,
    "mixed-graph": _mixed_graph,
}


@pytest.mark.skipif(not _is_graphviz_available(), reason="Graphviz not available")
class TestGoldenSvgComparison:
    @pytest.mark.parametrize("fixture_name", sorted(_FIXTURES))
    def test_golden_svg_matches(self, fixture_name: str) -> None:
        graph = _FIXTURES[fixture_name]()
        result = render_svg(graph)
        assert result.svg is not None, f"render_svg returned None for {fixture_name}"

        golden_path = GOLDEN_DIR / f"{fixture_name}.svg"
        assert golden_path.exists(), f"golden file missing: {golden_path}"
        golden = golden_path.read_text(encoding="utf-8")

        assert result.svg.replace("\r\n", "\n").replace("\r", "\n") == golden.replace("\r\n", "\n").replace("\r", "\n"), (
            f"SVG output for {fixture_name} does not match golden. If this change is intentional, regenerate with: python _gen_golden.py"
        )
