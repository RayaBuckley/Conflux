"""Generate golden SVG fixtures for visualisation testing."""

import os
import sys
from pathlib import Path

os.environ["PATH"] = r"C:\Program Files\Graphviz\bin" + os.pathsep + os.environ["PATH"]

from conflux.visualisation.graph.graphviz import render_svg
from conflux.visualisation.model import (
    EdgeKind,
    EvidenceReference,
    NodeKind,
    VisualEdge,
    VisualField,
    VisualGraph,
    VisualNode,
    VisualStatus,
)

out = Path("tests/fixtures/visualisation/golden")
out.mkdir(parents=True, exist_ok=True)

g1 = VisualGraph(
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
r1 = render_svg(g1)
if r1.svg is None:
    print("ERROR: r1.svg is None", file=sys.stderr)
    sys.exit(1)
(out / "simple-allow.svg").write_text(r1.svg, encoding="utf-8", newline="\n")

g2 = VisualGraph(
    graph_id="blocked-action",
    title="Blocked Action",
    nodes=(
        VisualNode(node_id="n1", kind=NodeKind.EXECUTION, label="Branch root", status=VisualStatus.ACTIVE),
        VisualNode(node_id="n2", kind=NodeKind.ACTION, label="delete_file", status=VisualStatus.BLOCKED),
    ),
    edges=(VisualEdge(source="n1", target="n2", kind=EdgeKind.TRANSITION),),
)
r2 = render_svg(g2)
if r2.svg is None:
    print("ERROR: r2.svg is None", file=sys.stderr)
    sys.exit(1)
(out / "blocked-action.svg").write_text(r2.svg, encoding="utf-8", newline="\n")

g3 = VisualGraph(
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
r3 = render_svg(g3)
if r3.svg is None:
    print("ERROR: r3.svg is None", file=sys.stderr)
    sys.exit(1)
(out / "mixed-graph.svg").write_text(r3.svg, encoding="utf-8", newline="\n")

for f in sorted(out.iterdir()):
    print(f"{f.name}: {f.stat().st_size} bytes")
print("Done")
