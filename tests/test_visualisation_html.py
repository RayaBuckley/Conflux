"""Tests for the HTML report generator."""

from __future__ import annotations

import json
from pathlib import Path

from conflux.visualisation.html import render_html_report, write_manifest
from conflux.visualisation.model import (
    EdgeKind,
    EvidenceReference,
    NodeKind,
    VisualEdge,
    VisualGraph,
    VisualNode,
    VisualStatus,
)


def _make_graph(graph_id: str = "test") -> VisualGraph:
    return VisualGraph(
        graph_id=graph_id,
        title=f"Test {graph_id}",
        nodes=(
            VisualNode(
                node_id="n1",
                kind=NodeKind.EXECUTION,
                label="Node 1",
                status=VisualStatus.ALLOWED,
                source_ref=EvidenceReference(source_file="r.json", json_pointer="/n1"),
            ),
            VisualNode(
                node_id="n2",
                kind=NodeKind.ACTION,
                label="Node 2",
                status=VisualStatus.BLOCKED,
            ),
        ),
        edges=(VisualEdge(source="n1", target="n2", kind=EdgeKind.TRANSITION),),
        metadata={"run_id": "test-run"},
    )


class TestRenderHtmlReport:
    def test_writes_index_html(self, tmp_path: Path) -> None:
        graphs = {"execution": _make_graph("execution")}
        result = render_html_report(
            graphs=graphs,
            svg_filenames={"execution": "execution.svg"},
            run_id="test-run",
            output_dir=tmp_path,
        )
        assert result == tmp_path / "index.html"
        assert result.exists()
        content = result.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "test-run" in content

    def test_escapes_html_in_labels(self, tmp_path: Path) -> None:
        graph = VisualGraph(
            graph_id="evil",
            title="<script>alert(1)</script>",
            nodes=(
                VisualNode(
                    node_id="n1",
                    kind=NodeKind.ACTION,
                    label="<img src=x onerror=alert(1)>",
                ),
            ),
        )
        result = render_html_report(
            graphs={"evil": graph},
            svg_filenames={},
            run_id="test",
            output_dir=tmp_path,
        )
        content = result.read_text(encoding="utf-8")
        assert "<script>alert" not in content
        assert "<img src=x onerror" not in content
        assert "&lt;script&gt;" in content

    def test_includes_svg_link(self, tmp_path: Path) -> None:
        graphs = {"execution": _make_graph()}
        render_html_report(
            graphs=graphs,
            svg_filenames={"execution": "execution.svg"},
            run_id="test",
            output_dir=tmp_path,
        )
        content = (tmp_path / "index.html").read_text(encoding="utf-8")
        assert 'src="execution.svg"' in content

    def test_shows_unavailable_when_no_svg(self, tmp_path: Path) -> None:
        graphs = {"execution": _make_graph()}
        render_html_report(
            graphs=graphs,
            svg_filenames={"execution": None},
            run_id="test",
            output_dir=tmp_path,
        )
        content = (tmp_path / "index.html").read_text(encoding="utf-8")
        assert "unavailable" in content.lower()

    def test_nav_links_to_sections(self, tmp_path: Path) -> None:
        graphs = {
            "execution": _make_graph("execution"),
            "provenance": _make_graph("provenance"),
        }
        render_html_report(
            graphs=graphs,
            svg_filenames={"execution": "e.svg", "provenance": "p.svg"},
            run_id="test",
            output_dir=tmp_path,
        )
        content = (tmp_path / "index.html").read_text(encoding="utf-8")
        assert "#execution" in content
        assert "#provenance" in content

    def test_overview_section_exists(self, tmp_path: Path) -> None:
        render_html_report(
            graphs={"execution": _make_graph()},
            svg_filenames={},
            run_id="test-run",
            output_dir=tmp_path,
        )
        content = (tmp_path / "index.html").read_text(encoding="utf-8")
        assert "Overview" in content
        assert "test-run" in content


class TestWriteManifest:
    def test_writes_manifest_json(self, tmp_path: Path) -> None:
        path = write_manifest(
            run_id="test-run",
            views={"execution": "execution.svg", "provenance": None},
            output_dir=tmp_path,
        )
        assert path == tmp_path / "manifest.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["run_id"] == "test-run"
        assert data["views"]["execution"]["svg"] == "execution.svg"
        assert data["views"]["execution"]["available"] is True
        assert data["views"]["provenance"]["available"] is False
