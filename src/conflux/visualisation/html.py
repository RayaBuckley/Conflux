"""Minimal static HTML report generator for visualisation evidence.

Produces a self-contained ``index.html`` that links to SVG diagrams
and a manifest.  No JavaScript framework required; minimal vanilla JS
for navigation only.  All untrusted labels are HTML-escaped.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from conflux.visualisation.model import VisualGraph


def _escape(text: str) -> str:
    """HTML-escape text for safe rendering."""
    return html.escape(text, quote=True)


def _render_graph_section(graph: VisualGraph, svg_filename: str | None) -> str:
    """Render an HTML section for a visual graph with optional SVG."""
    title = _escape(graph.title)
    graph_id = _escape(graph.graph_id)

    parts = [f'<section id="{graph_id}">']
    parts.append(f"<h2>{title}</h2>")

    if svg_filename:
        parts.append(f'<img src="{_escape(svg_filename)}" alt="{title}" />')
    else:
        parts.append('<p class="unavailable">SVG unavailable (Graphviz not installed)</p>')

    parts.append("<table>")
    parts.append("<thead><tr><th>Node ID</th><th>Kind</th><th>Label</th><th>Status</th></tr></thead>")
    parts.append("<tbody>")
    for node in sorted(graph.nodes, key=lambda n: n.node_id):
        status = node.status.value if node.status else ""
        parts.append(
            f"<tr><td>{_escape(node.node_id)}</td>"
            f"<td>{_escape(node.kind.value)}</td>"
            f"<td>{_escape(node.label)}</td>"
            f"<td>{_escape(status)}</td></tr>",
        )
    parts.append("</tbody></table>")

    meta_items = ", ".join(f"{_escape(k)}={_escape(v)}" for k, v in sorted(graph.metadata.items()))
    parts.append(f'<p class="metadata">{meta_items}</p>')
    parts.append("</section>")
    return "".join(parts)


def render_html_report(
    *,
    graphs: dict[str, VisualGraph],
    svg_filenames: dict[str, str | None],
    run_id: str,
    output_dir: Path,
) -> Path:
    """Write a static HTML report to ``output_dir / index.html``.

    Parameters
    ----------
    graphs
        Mapping from view name (e.g. ``"execution"``, ``"provenance"``) to
        ``VisualGraph``.
    svg_filenames
        Mapping from view name to SVG filename relative to ``output_dir``.
        If a view has no SVG (Graphviz unavailable), pass ``None`` value
        or omit the key.
    run_id
        The run identifier for the report title.
    output_dir
        Directory to write ``index.html`` into.

    Returns
    -------
    Path
        Path to the written ``index.html``.
    """
    sections: list[str] = []
    nav_items: list[str] = []

    for view_name in sorted(graphs):
        graph = graphs[view_name]
        svg = svg_filenames.get(view_name)
        sections.append(_render_graph_section(graph, svg))
        nav_items.append(f'<a href="#{_escape(graph.graph_id)}">{_escape(view_name.title())}</a>')

    nav_html = '<nav class="views">' + " | ".join(nav_items) + "</nav>"

    overview = (
        f'<section id="overview"><h2>Overview</h2>'
        f"<table><tbody>"
        f"<tr><th>Run ID</th><td>{_escape(run_id)}</td></tr>"
        f"<tr><th>Views</th><td>{_escape(', '.join(sorted(graphs)))}</td></tr>"
        f"</tbody></table></section>"
    )

    doc = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8" />\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        f"<title>Conflux Evidence — {_escape(run_id)}</title>\n"
        "<style>\n"
        "body { font-family: Helvetica, Arial, sans-serif; margin: 1em; }\n"
        "nav.views { margin-bottom: 1em; }\n"
        "nav.views a { margin-right: 0.5em; }\n"
        "section { margin-bottom: 2em; }\n"
        "table { border-collapse: collapse; margin: 0.5em 0; }\n"
        "th, td { border: 1px solid #ccc; padding: 0.2em 0.5em; text-align: left; }\n"
        "th { background: #f0f0f0; }\n"
        ".unavailable { color: #888; font-style: italic; }\n"
        ".metadata { color: #555; font-size: 0.9em; }\n"
        "img { max-width: 100%; height: auto; }\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        f"<h1>Conflux Evidence Report</h1>\n"
        f"{nav_html}\n"
        f"{overview}\n" + "".join(sections) + "</body>\n</html>\n"
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "index.html"
    index_path.write_text(doc, encoding="utf-8", newline="\n")
    return index_path


def write_manifest(
    *,
    run_id: str,
    views: dict[str, str | None],
    output_dir: Path,
) -> Path:
    """Write a manifest JSON recording which views exist and their SVG status.

    Parameters
    ----------
    run_id
        The run identifier.
    views
        Mapping from view name to SVG filename (or ``None`` if unavailable).
    output_dir
        Directory to write ``manifest.json`` into.

    Returns
    -------
    Path
        Path to the written ``manifest.json``.
    """
    manifest: dict[str, object] = {
        "run_id": run_id,
        "views": {name: {"svg": filename, "available": filename is not None} for name, filename in sorted(views.items())},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "manifest.json"
    path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path
