"""Render a CQ's answer subgraph as a picture.

The CQ suite proves the queries return the right *rows*. Rows are the wrong medium for
explaining a graph to a human: the interesting thing about CQ-9 is not which entities come
back, it is that they come back through a **transitive chain** nobody asserted. That only
reads as a picture.

Two views, both lifted from real CQs rather than invented for the demo:

  genre   — CQ-9's `:hasBroaderGenre*` hierarchy under :Rock, with the entities each
            subgenre pulls in. Every edge here is asserted; the *closure* is not.
  collab  — CQ-2's two-hop neighbourhood around a seed artist, over
            `:collaboratesWith` and the inverse path `^:hasMember/:hasMember`
            (co-membership of a band).

Renders to **SVG with no external binary** — Graphviz is not a dependency of this repo and
`dot` is not installed. Layout is a seeded Fruchterman–Reingold spring embedding, so output
is byte-reproducible across runs. Also emits Mermaid (`.mmd`, pasteable into slides and
markdown) and Graphviz (`.dot`, for anyone who later installs it).

Run: uv run python scripts/viz_subgraph.py            (both views)
     uv run python scripts/viz_subgraph.py --view genre
"""
from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from rdflib import RDF, RDFS, Graph, URIRef

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "viz"
TBOX = ROOT / "ontology" / "music_vocabulary_comprehensive.ttl"
ABOX = ROOT / "ontology" / "music_catalog_data.ttl"
NS = "https://www.somusicvocabulary.org/music#"

PREFIXES = """PREFIX :     <https://www.somusicvocabulary.org/music#>
PREFIX gist: <https://w3id.org/semanticarts/ns/ontology/gist/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

SEED = 20260712  # fixed: the layout must not move between runs

# Each view names its node set with a SELECT (lifted from the real CQ) plus the predicates
# whose asserted triples get drawn. Edges are the triples of those predicates with BOTH
# endpoints in the node set — that keeps the picture closed, rather than trailing half-edges
# off to nodes that were never drawn.
VIEWS = {
    "genre": {
        # CQ-9's path is `:hasBroaderGenre*` — a STAR, which matches the zero-length path and
        # so admits :Rock itself as ?sub. Using `+` here instead silently dropped every entity
        # tagged directly `:Rock` (Queen, BobDylan, PinkFloyd, …): 8 entities drawn where the
        # CQ returns 22. If this view is titled CQ-9 it must run CQ-9's path.
        #
        # The subtitle's transitivity claim is load-bearing, so keep it honest: it is true only
        # while the catalogue actually holds a >= 2-hop chain. :PearlJam is tagged :Grunge and
        # nothing else, so its ONLY route to :Rock is :Grunge -> :AlternativeRock -> :Rock, and
        # it drops out of this picture the moment the closure stops being computed. If that
        # instance ever goes away, this caption becomes a lie again — the taxonomy was flat
        # (zero chains of length >= 2) until it was added, and the picture would have rendered
        # identically with the transitivity switched off.
        "title": "CQ-9 — every entity under :Rock, via :hasBroaderGenre*",
        "subtitle": "Every edge drawn is asserted; the closure is not. :PearlJam is only "
                    "'rock' because :Grunge → :AlternativeRock → :Rock is walked for you.",
        "nodes": """
SELECT DISTINCT ?n WHERE {
  { BIND(:Rock AS ?n) }
  UNION { ?n :hasBroaderGenre* :Rock . }
  UNION { ?sub :hasBroaderGenre* :Rock . ?n :hasGenre ?sub . }
}""",
        "predicates": [":hasBroaderGenre", ":hasGenre"],
    },
    "collab": {
        # Seeded on a band member, deliberately. :DavidBowie is a :SoloArtist in no band, so
        # seeding on him leaves CQ-2's ^:hasMember/:hasMember arm matching nothing and the
        # picture quietly degrades to "collaborators only" while still captioned as if the
        # co-membership hop ran. McCartney is in The Beatles, so that hop actually fires.
        #
        # The two path arms below are CQ-2's, verbatim (tests/cq_test_manifest.json), so the
        # ANSWER nodes drawn are exactly CQ-2's answer set. The one addition is the final
        # `{ ?n :hasMember ?seed }` arm, which pulls in the BAND itself — not an answer to
        # CQ-2, but the node the co-membership hop travels *through*. Without it the picture
        # shows McCartney mysteriously adjacent to Ringo with no edge explaining why.
        #
        # Resist the urge to also add `^:collaboratesWith` to fill the picture out.
        # `:collaboratesWith` is declared owl:SymmetricProperty, so the inverse is *entailed*
        # and a reasoner would traverse it — but the CQ suite runs on rdflib with no OWL
        # reasoning, so CQ-2 itself only ever sees the asserted direction. Adding the inverse
        # draws a neighbourhood twice the size of the one `make test` verifies, under a title
        # that says "CQ-2". The picture must show what the query returns, not what a reasoner
        # would have returned.
        "title": "CQ-2 — two-hop collaboration neighbourhood (:PaulMcCartney)",
        "subtitle": "Answers reachable by :collaboratesWith or by band co-membership "
                    "(^:hasMember/:hasMember); :TheBeatles is the node that hop travels through.",
        "nodes": """
SELECT DISTINCT ?n WHERE {
  VALUES ?seed { :PaulMcCartney }
  { BIND(?seed AS ?n) }
  UNION { ?seed (:collaboratesWith|^:hasMember/:hasMember) ?n }
  UNION { ?seed (:collaboratesWith|^:hasMember/:hasMember)/(:collaboratesWith|^:hasMember/:hasMember) ?n }
  UNION { ?n :hasMember ?seed }
}""",
        "predicates": [":collaboratesWith", ":hasMember"],
    },
}

# Node fill by asserted type. Anything unmatched falls through to the last entry.
PALETTE = [
    ("TopLevelGenre", "#7c3aed"),
    ("MusicGenre", "#a78bfa"),
    ("Band", "#0891b2"),
    ("RockBand", "#0891b2"),
    ("SoloArtist", "#e11d48"),
    ("Musician", "#f43f5e"),
    ("MusicalPerson", "#fb7185"),
    ("Album", "#ea580c"),
    ("Song", "#f59e0b"),
    ("", "#64748b"),
]


def local(term) -> str:
    s = str(term)
    return s.rsplit("#", 1)[-1] if "#" in s else s.rsplit("/", 1)[-1]


def colour_for(types: set[str]) -> str:
    for name, col in PALETTE:
        if name in types or name == "":
            return col
    return "#64748b"


# ---------------------------------------------------------------- layout (no deps)

def spring_layout(nodes: list[str], edges: list[tuple[str, str, str]],
                  iterations: int = 600) -> dict[str, list[float]]:
    """Fruchterman–Reingold in unbounded space. Seeded, so the picture never moves.

    Deliberately does NOT clamp positions into the frame. Clamping makes the walls act as
    an attractor: any node the repulsion pushes outward gets pinned flat against the border,
    and clusters end up smeared along the edges instead of laid out. Let the graph settle
    at whatever scale it wants; `fit()` rescales it into the canvas afterwards.
    """
    rng = random.Random(SEED)
    if len(nodes) < 2:
        return {n: [0.0, 0.0] for n in nodes}

    # Start on a circle rather than at random: same seed, but a far more stable basin.
    pos = {n: [math.cos(2 * math.pi * i / len(nodes)) * 100 + rng.uniform(-3, 3),
               math.sin(2 * math.pi * i / len(nodes)) * 100 + rng.uniform(-3, 3)]
           for i, n in enumerate(nodes)}

    adj = [(s, o) for s, _, o in edges if s != o]
    k = 110.0        # ideal edge length, in layout units
    temp = 60.0

    for _ in range(iterations):
        disp = {n: [0.0, 0.0] for n in nodes}

        # Repulsion: every pair pushes apart.
        for i, u in enumerate(nodes):
            for v in nodes[i + 1:]:
                dx, dy = pos[u][0] - pos[v][0], pos[u][1] - pos[v][1]
                d = math.hypot(dx, dy) or 0.01
                f = (k * k) / d
                ux, uy = dx / d * f, dy / d * f
                disp[u][0] += ux; disp[u][1] += uy
                disp[v][0] -= ux; disp[v][1] -= uy

        # Attraction: edges pull together.
        for u, v in adj:
            dx, dy = pos[u][0] - pos[v][0], pos[u][1] - pos[v][1]
            d = math.hypot(dx, dy) or 0.01
            f = (d * d) / k
            ux, uy = dx / d * f, dy / d * f
            disp[u][0] -= ux; disp[u][1] -= uy
            disp[v][0] += ux; disp[v][1] += uy

        for n in nodes:
            dx, dy = disp[n]
            d = math.hypot(dx, dy) or 0.01
            pos[n][0] += (dx / d) * min(d, temp)
            pos[n][1] += (dy / d) * min(d, temp)
        temp = max(temp * 0.985, 0.4)

    return pos


def relax_overlaps(pos: dict[str, list[float]], node_w: dict[str, float],
                   box: tuple[float, float, float, float], rounds: int = 80) -> None:
    """Push apart node pills whose LABELS collide. Mutates `pos` in place.

    The spring layout treats every node as a dimensionless point, so it happily settles
    "OkComputer" and "TheDarkSideOfTheMoon" a comfortable 30px apart — centre to centre,
    while their 150px-wide pills sit right on top of each other. This pass is the only thing
    that knows a node has a width. Runs after fit(), in final pixel space.
    """
    x0, y0, w, h = box
    names = list(pos)
    pad_x, pad_y = 10.0, 8.0
    for _ in range(rounds):
        moved = False
        for i, u in enumerate(names):
            for v in names[i + 1:]:
                need_x = (node_w[u] + node_w[v]) / 2 + pad_x
                need_y = 26 + pad_y                      # pill height + gap
                dx = pos[v][0] - pos[u][0]
                dy = pos[v][1] - pos[u][1]
                ox = need_x - abs(dx)                    # overlap on each axis
                oy = need_y - abs(dy)
                if ox <= 0 or oy <= 0:
                    continue                             # boxes clear on at least one axis
                moved = True
                # Separate along whichever axis needs the least travel.
                if ox < oy:
                    shift = (ox / 2 + 0.5) * (1 if dx >= 0 else -1)
                    pos[u][0] -= shift
                    pos[v][0] += shift
                else:
                    shift = (oy / 2 + 0.5) * (1 if dy >= 0 else -1)
                    pos[u][1] -= shift
                    pos[v][1] += shift
        if not moved:
            break

    # Separation can shove a node out of frame; pull everything back inside.
    for n in names:
        half = node_w[n] / 2
        pos[n][0] = min(x0 + w - half - 2, max(x0 + half + 2, pos[n][0]))
        pos[n][1] = min(y0 + h - 15, max(y0 + 15, pos[n][1]))


def fit(pos: dict[str, list[float]], box: tuple[float, float, float, float],
        node_w: dict[str, float]) -> dict[str, list[float]]:
    """Rescale a settled layout into (x, y, w, h), inset so no node pill crosses the frame."""
    x0, y0, w, h = box
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    span_x = (max(xs) - min(xs)) or 1.0
    span_y = (max(ys) - min(ys)) or 1.0

    pad_x = max(node_w.values()) / 2 + 8   # widest label must not overhang
    pad_y = 22
    inner_w = max(w - 2 * pad_x, 1.0)
    inner_h = max(h - 2 * pad_y, 1.0)
    scale = min(inner_w / span_x, inner_h / span_y)

    # Centre whatever slack is left over.
    off_x = x0 + pad_x + (inner_w - span_x * scale) / 2
    off_y = y0 + pad_y + (inner_h - span_y * scale) / 2
    return {n: [off_x + (p[0] - min(xs)) * scale, off_y + (p[1] - min(ys)) * scale]
            for n, p in pos.items()}


# ---------------------------------------------------------------- renderers

def node_width(label: str) -> float:
    return max(58.0, 7.2 * len(label) + 20)


def to_svg(view: dict, nodes: list[str], edges: list[tuple[str, str, str]],
           types: dict[str, set[str]]) -> str:
    W, H = 1200, 800
    TOP, BOTTOM = 96, 34          # title band, footer band
    widths = {n: node_width(n) for n in nodes}
    box = (0, TOP, W, H - TOP - BOTTOM)
    pos = fit(spring_layout(nodes, edges), box, widths)
    relax_overlaps(pos, widths, box)

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'font-family="Inter, Helvetica, Arial, sans-serif">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
        'markerHeight="6" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8"/></marker></defs>',
        f'<text x="32" y="46" font-size="24" font-weight="700" fill="#0f172a">'
        f'{esc(view["title"])}</text>',
        f'<text x="32" y="72" font-size="14" fill="#64748b">{esc(view["subtitle"])}</text>',
    ]

    # Edges first, so node pills always sit on top of the lines.
    for s, pred, o in edges:
        x1, y1 = pos[s]
        x2, y2 = pos[o]
        # Stop the line at the target pill's edge so the arrowhead is visible, not buried.
        dx, dy = x2 - x1, y2 - y1
        d = math.hypot(dx, dy) or 1.0
        back = widths[o] / 2 + 6
        ex, ey = x2 - dx / d * back, y2 - dy / d * back
        p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                 f'stroke="#cbd5e1" stroke-width="1.5" marker-end="url(#arrow)"/>')

        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        # A white plate behind the label — without it, labels vanish where edges cross.
        plate = 6.2 * len(pred)
        p.append(f'<rect x="{mx - plate/2:.1f}" y="{my - 7:.1f}" width="{plate:.1f}" height="12" '
                 f'fill="#ffffff" opacity="0.85"/>')
        p.append(f'<text x="{mx:.1f}" y="{my + 2:.1f}" font-size="9" fill="#94a3b8" '
                 f'text-anchor="middle">{esc(pred)}</text>')

    for n in nodes:
        x, y = pos[n]
        col = colour_for(types.get(n, set()))
        wdt = widths[n]
        p.append(f'<rect x="{x - wdt/2:.1f}" y="{y - 13:.1f}" width="{wdt:.1f}" height="26" '
                 f'rx="13" fill="{col}"/>')
        p.append(f'<text x="{x:.1f}" y="{y + 4:.1f}" font-size="11" font-weight="600" '
                 f'fill="#ffffff" text-anchor="middle">{esc(n)}</text>')

    p.append(f'<text x="32" y="{H - 12}" font-size="11" fill="#94a3b8">'
             f'{len(nodes)} nodes · {len(edges)} edges · generated by scripts/viz_subgraph.py</text>')
    p.append("</svg>")
    return "\n".join(p)


def to_mermaid(view: dict, edges: list[tuple[str, str, str]]) -> str:
    lines = [f"%% {view['title']}", "graph LR"]
    for s, pred, o in edges:
        lines.append(f"  {s}[{s}] -->|{pred}| {o}[{o}]")
    return "\n".join(lines) + "\n"


def to_dot(view: dict, edges: list[tuple[str, str, str]]) -> str:
    lines = [f'// {view["title"]}', "digraph G {", '  rankdir=LR;',
             '  node [shape=box style=rounded fontname="Helvetica" fontsize=10];']
    for s, pred, o in edges:
        lines.append(f'  "{s}" -> "{o}" [label="{pred}" fontsize=8];')
    lines.append("}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- main

def type_closure(g: Graph, node: URIRef) -> set[str]:
    """A node's asserted types *plus their superclasses*.

    Colouring on asserted types alone gets this wrong: the catalogue types instances to
    leaf classes (`:StudioAlbum`, `:RockBand`), so a palette keyed on `:Album` or `:Band`
    silently falls through to the default grey. Walk rdfs:subClassOf up to the roots.
    """
    seen: set[str] = set()
    frontier = list(g.objects(node, RDF.type))
    while frontier:
        t = frontier.pop()
        name = local(t)
        if name in seen:
            continue
        seen.add(name)
        frontier.extend(g.objects(t, RDFS.subClassOf))
    return seen


def build(name: str, view: dict, g: Graph) -> tuple[int, int]:
    nodes_res = g.query(PREFIXES + view["nodes"])
    node_iris = {row[0] for row in nodes_res if isinstance(row[0], URIRef)}

    # Draw an asserted edge only when both of its endpoints made the node set.
    edges = set()
    for pred in view["predicates"]:
        p = URIRef(NS + pred.lstrip(":"))
        for s, o in g.subject_objects(p):
            if s in node_iris and o in node_iris:
                edges.add((local(s), local(p), local(o)))

    edges = sorted(edges)
    nodes = sorted({local(n) for n in node_iris})
    types = {local(n): type_closure(g, n) for n in node_iris}

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.svg").write_text(to_svg(view, nodes, edges, types))
    (OUT / f"{name}.mmd").write_text(to_mermaid(view, edges))
    (OUT / f"{name}.dot").write_text(to_dot(view, edges))
    return len(nodes), len(edges)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--view", choices=sorted(VIEWS), help="render only this view")
    args = ap.parse_args()

    g = Graph()
    g.parse(TBOX, format="turtle")
    g.parse(ABOX, format="turtle")

    chosen = [args.view] if args.view else sorted(VIEWS)
    for name in chosen:
        n, e = build(name, VIEWS[name], g)
        if e == 0:
            print(f"  {name}: EMPTY — the CONSTRUCT matched nothing. A blank picture is a "
                  f"broken query, not a sparse graph.")
            return 1
        print(f"  {name}: {n} nodes, {e} edges  →  dist/viz/{name}.svg  (+ .mmd, .dot)")

    print(f"\nOK — open {OUT.relative_to(ROOT)}/*.svg in a browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
