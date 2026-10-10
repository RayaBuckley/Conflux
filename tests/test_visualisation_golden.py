"""Golden SVG comparison tests for the Graphviz renderer.

Regenerates SVG from known VisualGraph fixtures and compares against
committed golden files.  If the SVG changes intentionally, update the
golden in the same commit that caused the change.

The comparison ignores the two things that differ between hosts: the Graphviz
version comment and element geometry, because two Graphviz builds lay the same
graph out at different coordinates.  Structure, presentation attributes and
text are compared, so a changed label, style or edge is still caught.

To regenerate the goldens, install Graphviz so ``dot`` is on PATH and run:
python _gen_golden.py
"""

from __future__ import annotations

import os
import shutil
from html.parser import HTMLParser
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

# Graphviz stamps its own version into a comment and places every element with layout
# coordinates that move between builds, so a byte comparison would only hold for the build that
# produced the golden. The comparison drops the version and the geometry and keeps what the fixture
# is for: element structure, presentation attributes and text. Attribute names are compared
# lower case, the way the tokenizer reports them.
_GEOMETRY_ATTRIBUTES = frozenset(
    {
        "cx",
        "cy",
        "d",
        "height",
        "points",
        "rx",
        "ry",
        "transform",
        "viewbox",
        "width",
        "x",
        "x1",
        "x2",
        "y",
        "y1",
        "y2",
    },
)


class _SvgDescription(HTMLParser):
    """Collect element names, presentation attributes and text from an SVG.

    A tokenizer is enough here: the description needs element structure, style
    attributes and text, and the input is a rendered document this process
    produced rather than untrusted markup.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self._depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._emit(tag, attrs)
        self._depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._emit(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        self._depth = max(0, self._depth - 1)

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.lines.append(f"{'  ' * self._depth}~{text}")

    def handle_comment(self, data: str) -> None:
        """Drop comments: Graphviz puts its own version in the first one."""

    def _emit(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        kept = " ".join(f"{name}={value!r}" for name, value in sorted(attrs) if name.lower() not in _GEOMETRY_ATTRIBUTES)
        self.lines.append(f"{'  ' * self._depth}<{tag} {kept}>")


def normalise_svg(svg: str) -> str:
    """Return a host-independent description of a rendered SVG.

    The description holds one line per element and one per non-blank text run:
    the element name, its sorted presentation attributes and its text. The
    Graphviz version comment and all geometry are dropped, so two Graphviz builds
    that place the same graph at different coordinates agree.
    """
    description = _SvgDescription()
    description.feed(svg)
    description.close()
    return "\n".join(description.lines)


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


def test_the_normalised_description_ignores_geometry_and_keeps_structure() -> None:
    """The comparison must ignore layout numbers and still see a real change.

    Both directions are pinned: two builds that place the same graph at
    different coordinates agree, and a changed label or fill colour does not.
    """
    left = (
        '<svg width="10pt" height="10pt" viewBox="0 0 10 10">'
        '<g class="node"><ellipse cx="1" cy="2" rx="3" ry="4" fill="white"/>'
        "<text>send_email</text></g></svg>"
    )
    right = (
        '<svg width="99pt" height="99pt" viewBox="0 0 99 99">'
        '<g class="node"><ellipse cx="9" cy="8" rx="7" ry="6" fill="white"/>'
        "<text>send_email</text></g></svg>"
    )
    changed_label = right.replace("send_email", "delete_file")
    changed_style = right.replace('fill="white"', 'fill="#ffcccc"')

    assert normalise_svg(left) == normalise_svg(right)
    assert normalise_svg(left) != normalise_svg(changed_label)
    assert normalise_svg(left) != normalise_svg(changed_style)


@pytest.mark.skipif(not _is_graphviz_available(), reason=GRAPHVIZ_SKIP_REASON)
class TestGoldenSvgComparison:
    @pytest.mark.parametrize("fixture_name", sorted(_FIXTURES))
    def test_golden_svg_matches(self, fixture_name: str) -> None:
        graph = _FIXTURES[fixture_name]()
        result = render_svg(graph)
        assert result.svg is not None, f"render_svg returned None for {fixture_name}"

        golden_path = GOLDEN_DIR / f"{fixture_name}.svg"
        assert golden_path.exists(), f"golden file missing: {golden_path}"
        golden = golden_path.read_text(encoding="utf-8")

        assert normalise_svg(result.svg) == normalise_svg(golden), (
            f"SVG structure for {fixture_name} does not match golden. The comparison ignores the "
            f"Graphviz version and element geometry; if the change is intentional, regenerate with: "
            f"python _gen_golden.py"
        )
