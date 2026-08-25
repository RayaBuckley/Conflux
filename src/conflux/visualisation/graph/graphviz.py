"""Graphviz SVG renderer for VisualGraph.

Converts a ``VisualGraph`` to SVG using the Python ``graphviz`` package.
The ``dot`` binary is detected at runtime via ``shutil.which("dot")``.
If unavailable, the renderer returns an ``UNAVAILABLE`` result rather
than raising.  All labels are HTML-escaped to prevent injection.
"""

from __future__ import annotations

import html
import shutil
from dataclasses import dataclass

from conflux.visualisation.graph.model import LayoutOptions
from conflux.visualisation.model import VisualGraph, VisualNode, VisualStatus
from conflux.visualisation.normalise import truncate_label

DEFAULT_MAX_NODES = 500


@dataclass(frozen=True)
class RenderResult:
    """Result of a graph rendering operation.

    When ``svg`` is ``None``, the renderer was unable to produce output
    (e.g. Graphviz not installed).  The ``status`` field indicates why.
    """

    svg: str | None
    status: VisualStatus
    message: str = ""


def _is_graphviz_available() -> bool:
    """Return True when the ``dot`` binary is on PATH."""
    return shutil.which("dot") is not None


def _escape_label(text: str) -> str:
    """HTML-escape a label for safe SVG/HTML rendering."""
    return html.escape(text, quote=True)


def _node_shape(status: VisualStatus | None) -> str:
    """Return a Graphviz shape name for a visual status.

    Shape distinction ensures status is not encoded exclusively through
    colour.
    """
    if status is None:
        return "box"
    return {
        VisualStatus.ALLOWED: "box",
        VisualStatus.BLOCKED: "octagon",
        VisualStatus.SAFE: "box",
        VisualStatus.UNSAFE: "octagon",
        VisualStatus.UNKNOWN: "diamond",
        VisualStatus.UNAVAILABLE: "diamond",
        VisualStatus.INCOMPLETE: "diamond",
        VisualStatus.PRUNED: "point",
        VisualStatus.REVISITED: "point",
        VisualStatus.ACTIVE: "box",
        VisualStatus.SUCCESS: "box",
        VisualStatus.FAILED: "octagon",
        VisualStatus.NOT_APPLICABLE: "box",
    }.get(status, "box")


def _node_fillcolor(status: VisualStatus | None) -> str:
    """Return a fill colour for a visual status.

    Colour is supplementary to shape, never the sole indicator.
    """
    if status is None:
        return "white"
    return {
        VisualStatus.ALLOWED: "#d4edda",
        VisualStatus.BLOCKED: "#f8d7da",
        VisualStatus.SAFE: "#d4edda",
        VisualStatus.UNSAFE: "#f8d7da",
        VisualStatus.UNKNOWN: "#fff3cd",
        VisualStatus.UNAVAILABLE: "#e2e3e5",
        VisualStatus.INCOMPLETE: "#fff3cd",
        VisualStatus.PRUNED: "#e2e3e5",
        VisualStatus.REVISITED: "#e2e3e5",
        VisualStatus.ACTIVE: "#cce5ff",
        VisualStatus.SUCCESS: "#d4edda",
        VisualStatus.FAILED: "#f8d7da",
        VisualStatus.NOT_APPLICABLE: "white",
    }.get(status, "white")


def _format_node_label(node: VisualNode) -> str:
    """Format a node label with fields as an HTML-like table string."""
    parts = [_escape_label(node.label)]
    if node.status is not None:
        parts.append(f"[{node.status.value}]")
    for field_obj in node.fields:
        key = _escape_label(field_obj.key)
        val = _escape_label(truncate_label(field_obj.value))
        parts.append(f"\\n{key}: {val}")
    return "".join(parts)


def _truncate_graph(
    graph: VisualGraph,
    max_nodes: int,
) -> tuple[VisualGraph, bool]:
    """Return a graph truncated to ``max_nodes`` nodes.

    Returns the (possibly truncated) graph and a flag indicating whether
    truncation occurred.
    """
    if len(graph.nodes) <= max_nodes:
        return graph, False
    sorted_nodes = sorted(graph.nodes, key=lambda n: n.node_id)
    kept_ids = {n.node_id for n in sorted_nodes[:max_nodes]}
    kept_nodes = tuple(n for n in sorted_nodes if n.node_id in kept_ids)
    kept_edges = tuple(e for e in graph.edges if e.source in kept_ids and e.target in kept_ids)
    truncated = VisualGraph(
        graph_id=graph.graph_id,
        title=f"{graph.title} (truncated to {max_nodes} nodes)",
        nodes=kept_nodes,
        edges=kept_edges,
        metadata=dict(graph.metadata),
    )
    truncated.metadata["truncated"] = "true"
    truncated.metadata["original_node_count"] = str(len(graph.nodes))
    return truncated, True


def render_svg(
    graph: VisualGraph,
    *,
    layout: LayoutOptions | None = None,
    max_nodes: int = DEFAULT_MAX_NODES,
) -> RenderResult:
    """Render a VisualGraph to SVG using Graphviz.

    Returns a ``RenderResult``.  When Graphviz is not available, returns
    a result with ``svg=None`` and ``status=UNAVAILABLE``.
    """
    if not _is_graphviz_available():
        return RenderResult(
            svg=None,
            status=VisualStatus.UNAVAILABLE,
            message="Graphviz 'dot' binary not found on PATH",
        )

    import graphviz as gv

    opts = layout or LayoutOptions()
    truncated_graph, was_truncated = _truncate_graph(graph, max_nodes)

    dot = gv.Digraph(
        name=truncated_graph.graph_id,
        format="svg",
    )
    dot.attr(
        rankdir=opts.direction.value,
        ranksep=opts.ranksep,
        nodesep=opts.nodesep,
        fontname=opts.fontname,
        fontsize=opts.fontsize,
    )
    dot.attr("node", fontname=opts.fontname, fontsize=opts.fontsize)
    dot.attr("edge", fontname=opts.fontname, fontsize=opts.fontsize)

    for node in sorted(truncated_graph.nodes, key=lambda n: n.node_id):
        shape = _node_shape(node.status)
        fillcolor = _node_fillcolor(node.status)
        label = _format_node_label(node)
        tooltip = node.source_ref.json_pointer if node.source_ref else node.node_id

        dot.node(
            node.node_id,
            label=label,
            shape=shape,
            style="filled",
            fillcolor=fillcolor,
            tooltip=_escape_label(tooltip),
        )

    for edge in sorted(
        truncated_graph.edges,
        key=lambda e: (e.source, e.target, e.kind.value),
    ):
        dot.edge(
            edge.source,
            edge.target,
            label=_escape_label(edge.label) if edge.label else "",
        )

    svg_output = dot.pipe(format="svg").decode("utf-8")

    if was_truncated:
        svg_output = svg_output + f"\n<!-- truncated: original {len(graph.nodes)} nodes, showing {max_nodes} -->"

    return RenderResult(
        svg=svg_output,
        status=VisualStatus.SUCCESS,
        message=f"rendered {len(truncated_graph.nodes)} nodes" if was_truncated else "",
    )
