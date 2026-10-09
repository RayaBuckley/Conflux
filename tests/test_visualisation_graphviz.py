"""Tests for the Graphviz SVG renderer."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

# The renderer shells out to ``dot``. A Windows install usually lives outside PATH, so its
# default location is added when it exists; on every other platform ``dot`` must already be
# on PATH, and its absence is reported in the skip reason rather than hidden.
_WINDOWS_GRAPHVIZ_BIN = Path(r"C:\Program Files\Graphviz\bin")
GRAPHVIZ_SKIP_REASON = "dot is not on PATH: the SVG rendering tests did not run on this host"


def _ensure_graphviz_on_path() -> bool:
    """Return whether ``dot`` is reachable, adding the Windows default install if needed."""
    if shutil.which("dot"):
        return True
    if os.name == "nt" and _WINDOWS_GRAPHVIZ_BIN.is_dir():
        os.environ["PATH"] = str(_WINDOWS_GRAPHVIZ_BIN) + os.pathsep + os.environ.get("PATH", "")
        return shutil.which("dot") is not None
    return False


_ensure_graphviz_on_path()

from conflux.visualisation.graph.graphviz import (  # noqa: E402
    _escape_label,
    _format_node_label,
    _is_graphviz_available,
    _node_fillcolor,
    _node_shape,
    _truncate_graph,
    render_svg,
)
from conflux.visualisation.graph.model import LayoutDirection, LayoutOptions  # noqa: E402
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


def _make_graph(
    *,
    node_count: int = 3,
    status: VisualStatus | None = None,
) -> VisualGraph:
    nodes = tuple(
        VisualNode(
            node_id=f"n{i}",
            kind=NodeKind.EXECUTION,
            label=f"Node {i}",
            fields=(VisualField(key="idx", value=str(i)),),
            status=status,
            source_ref=EvidenceReference(
                source_file="result.json",
                json_pointer=f"/nodes/{i}",
            ),
        )
        for i in range(node_count)
    )
    edges = tuple(VisualEdge(source=f"n{i}", target=f"n{i + 1}", kind=EdgeKind.TRANSITION) for i in range(node_count - 1))
    return VisualGraph(
        graph_id="test-graph",
        title="Test Graph",
        nodes=nodes,
        edges=edges,
    )


class TestEscapeLabel:
    def test_escapes_script_tag(self) -> None:
        result = _escape_label("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_escapes_quotes(self) -> None:
        result = _escape_label("\"hello\" & 'world'")
        assert "&quot;" in result
        assert "&amp;" in result

    def test_preserves_plain_text(self) -> None:
        assert _escape_label("hello world") == "hello world"


class TestNodeShape:
    def test_blocked_is_octagon(self) -> None:
        assert _node_shape(VisualStatus.BLOCKED) == "octagon"

    def test_allowed_is_box(self) -> None:
        assert _node_shape(VisualStatus.ALLOWED) == "box"

    def test_unknown_is_diamond(self) -> None:
        assert _node_shape(VisualStatus.UNKNOWN) == "diamond"

    def test_none_status_is_box(self) -> None:
        assert _node_shape(None) == "box"


class TestNodeFillcolor:
    def test_allowed_is_greenish(self) -> None:
        assert _node_fillcolor(VisualStatus.ALLOWED) == "#d4edda"

    def test_blocked_is_reddish(self) -> None:
        assert _node_fillcolor(VisualStatus.BLOCKED) == "#f8d7da"

    def test_none_is_white(self) -> None:
        assert _node_fillcolor(None) == "white"


class TestFormatNodeLabel:
    def test_includes_label_text(self) -> None:
        node = VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="Branch root")
        label = _format_node_label(node)
        assert "Branch root" in label

    def test_includes_status(self) -> None:
        node = VisualNode(
            node_id="n1",
            kind=NodeKind.EXECUTION,
            label="Action",
            status=VisualStatus.BLOCKED,
        )
        label = _format_node_label(node)
        assert "[BLOCKED]" in label

    def test_includes_fields(self) -> None:
        node = VisualNode(
            node_id="n1",
            kind=NodeKind.EXECUTION,
            label="Node",
            fields=(VisualField(key="depth", value="0"),),
        )
        label = _format_node_label(node)
        assert "depth" in label
        assert "0" in label

    def test_escapes_html_in_label(self) -> None:
        node = VisualNode(
            node_id="n1",
            kind=NodeKind.EXECUTION,
            label="<script>alert(1)</script>",
        )
        label = _format_node_label(node)
        assert "<script>" not in label
        assert "&lt;script&gt;" in label


class TestTruncateGraph:
    def test_no_truncation_under_limit(self) -> None:
        graph = _make_graph(node_count=5)
        result, truncated = _truncate_graph(graph, max_nodes=10)
        assert not truncated
        assert len(result.nodes) == 5

    def test_truncation_over_limit(self) -> None:
        graph = _make_graph(node_count=10)
        result, truncated = _truncate_graph(graph, max_nodes=5)
        assert truncated
        assert len(result.nodes) == 5
        assert result.metadata["truncated"] == "true"
        assert result.metadata["original_node_count"] == "10"

    def test_truncated_edges_only_kept_nodes(self) -> None:
        graph = _make_graph(node_count=10)
        result, _ = _truncate_graph(graph, max_nodes=5)
        kept_ids = {n.node_id for n in result.nodes}
        for edge in result.edges:
            assert edge.source in kept_ids
            assert edge.target in kept_ids


class TestGraphvizOnPath:
    """The PATH fix must help on Windows and stay inert everywhere else."""

    def test_a_posix_host_gains_no_windows_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PATH", raising=False)
        monkeypatch.setattr(shutil, "which", lambda _name: None)
        monkeypatch.setattr(os, "name", "posix")
        assert _ensure_graphviz_on_path() is False
        assert "PATH" not in os.environ

    def test_the_windows_default_is_added_only_when_it_holds_dot(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        bin_dir = tmp_path / "Graphviz" / "bin"
        bin_dir.mkdir(parents=True)
        seen: list[str] = []

        def fake_which(name: str) -> str | None:
            seen.append(name)
            return str(bin_dir / "dot.exe") if len(seen) > 1 else None

        monkeypatch.setenv("PATH", "/usr/bin")
        monkeypatch.setattr(shutil, "which", fake_which)
        monkeypatch.setattr(os, "name", "nt")
        monkeypatch.setattr(sys.modules[__name__], "_WINDOWS_GRAPHVIZ_BIN", bin_dir)
        assert _ensure_graphviz_on_path() is True
        assert os.environ["PATH"] == f"{bin_dir}{os.pathsep}/usr/bin"


class TestRenderSvg:
    @pytest.mark.skipif(
        not _is_graphviz_available(),
        reason=GRAPHVIZ_SKIP_REASON,
    )
    def test_produces_svg(self) -> None:
        graph = _make_graph(node_count=3)
        result = render_svg(graph)
        assert result.svg is not None
        assert result.status is VisualStatus.SUCCESS
        assert "<svg" in result.svg

    @pytest.mark.skipif(
        not _is_graphviz_available(),
        reason=GRAPHVIZ_SKIP_REASON,
    )
    def test_deterministic_output(self) -> None:
        graph = _make_graph(node_count=5)
        result1 = render_svg(graph)
        result2 = render_svg(graph)
        assert result1.svg == result2.svg

    @pytest.mark.skipif(
        not _is_graphviz_available(),
        reason=GRAPHVIZ_SKIP_REASON,
    )
    def test_hostile_labels_escaped(self) -> None:
        node = VisualNode(
            node_id="evil",
            kind=NodeKind.ACTION,
            label="<script>alert('xss')</script>",
            fields=(VisualField(key="payload", value="<img src=x onerror=alert(1)>"),),
        )
        graph = VisualGraph(
            graph_id="hostile",
            title="Hostile",
            nodes=(node,),
        )
        result = render_svg(graph)
        assert result.svg is not None
        assert "<script>alert" not in result.svg
        assert "<img src=x onerror" not in result.svg

    @pytest.mark.skipif(
        not _is_graphviz_available(),
        reason=GRAPHVIZ_SKIP_REASON,
    )
    def test_truncation_notice(self) -> None:
        graph = _make_graph(node_count=10)
        result = render_svg(graph, max_nodes=5)
        assert result.svg is not None
        assert "truncated" in result.svg

    def test_unavailable_when_no_graphviz(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "conflux.visualisation.graph.graphviz._is_graphviz_available",
            lambda: False,
        )
        graph = _make_graph(node_count=2)
        result = render_svg(graph)
        assert result.svg is None
        assert result.status is VisualStatus.UNAVAILABLE

    @pytest.mark.skipif(
        not _is_graphviz_available(),
        reason=GRAPHVIZ_SKIP_REASON,
    )
    def test_layout_options_respected(self) -> None:
        graph = _make_graph(node_count=3)
        layout = LayoutOptions(direction=LayoutDirection.LEFT_TO_RIGHT)
        result = render_svg(graph, layout=layout)
        assert result.svg is not None
