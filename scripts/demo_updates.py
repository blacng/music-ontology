"""SPARQL Update demo — inserts, updates, deletes, and a SHACL-gated write.

The CQ suite (`scripts/run_cq_tests.py`) covers the *read* side: 18 SELECT queries,
all with expected-result manifests. Nothing in the repo exercised the *write* side.
This script does, and it does it the way the deployed system would: every update is
aimed at a **named graph**, so the ABox can be mutated without the TBox or the shapes
graph ever being in scope.

Five scenarios, each asserting its expected before/after state:

  1. INSERT DATA         — add an artist to <…/abox>, and prove (via GRAPH ?g) that the
                           triples landed there and nowhere else.
  2. DELETE/INSERT       — correct a wrong :bornOn value in place.
  3. SHACL-gated write   — attempt a write the shapes must reject; show 0 Violations before,
                           >0 after, and 0 again once it is rolled back.
  4. DELETE WHERE        — retract the artist, and show that binding only the SUBJECT
                           position leaves inbound edges dangling.
  5. Complete retraction — sweep the object position too, and only then is the node gone.

This is a gate, not a printout: a scenario whose assertion fails exits non-zero. Scenario 3
is the one that can rot silently, so it measures the *transition* (clean → violating → clean)
rather than just the end state: a shape that targets nothing reports "0 Violations" exactly
like a graph that genuinely conforms.

Two design points worth not "simplifying" away
----------------------------------------------
* The dataset is assembled by importing `build_dataset()` from `load_graphs.py` rather
  than parsing `dist/music_dataset.trig`. `dist/` is a git-ignored build product and may
  be stale; the four-graph mapping in `load_graphs.GRAPHS` is the single source of truth.

* Scenario 4 validates by importing `validate_data()` from `check_shacl.py`. That is the
  one validation configuration CI enforces (taxonomy-only `ont_graph`, `inference="rdfs"`
  — see that module's docstring for why both halves are load-bearing). Re-rolling pyshacl
  options here would let the demo drift from the real gate and "prove" a conformance the
  release gate does not actually grant.

Run: uv run python scripts/demo_updates.py
     uv run python scripts/demo_updates.py --endpoint http://localhost:3030/music
     (live Fuseki; `make serve && make fuseki-load` first. Restore with `make fuseki-load`.)
"""
from __future__ import annotations

import argparse
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from rdflib import Dataset, Graph, URIRef

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_shacl import ONTOLOGY, SHAPES, tally, validate_data  # noqa: E402
from load_graphs import BASE, build_dataset  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ABOX = f"{BASE}/abox"
TBOX = f"{BASE}/tbox"
REPORT = ROOT / "docs" / "mc2-graph-queries.md"

PREFIXES = """PREFIX :     <https://www.somusicvocabulary.org/music#>
PREFIX gist: <https://w3id.org/semanticarts/ns/ontology/gist/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
"""

# The demo subject. Jeff Buckley is genuinely absent from the catalogue, so the insert
# is a real insert and the final delete restores the graph exactly.
SUBJ = ":JeffBuckley"


# --------------------------------------------------------------------------- helpers

def local(term) -> str:
    """Shorten an IRI to its local name for display."""
    s = str(term)
    return s.rsplit("#", 1)[-1] if "#" in s else s.rsplit("/", 1)[-1]


def snapshot(g: Graph) -> Graph:
    """A standalone copy of a named graph.

    pyshacl runs RDFS inference over the graph it is handed. Passing a context of a live
    Dataset risks the inferred triples being written back into the store, which would
    silently contaminate later scenarios. Copy first.
    """
    out = Graph()
    for t in g:
        out.add(t)
    return out


class Store:
    """The dataset under test — in-memory, or a live SPARQL endpoint with --endpoint."""

    def __init__(self, endpoint: str | None = None):
        self.endpoint = endpoint
        if endpoint is None:
            self.ds, _ = build_dataset()
        else:
            self.ds = None

    def update(self, sparql: str) -> None:
        if self.endpoint is None:
            self.ds.update(PREFIXES + sparql)
        else:
            self._post(f"{self.endpoint}/update", {"update": PREFIXES + sparql})

    def select(self, sparql: str) -> list[tuple[str, ...]]:
        if self.endpoint is None:
            return [tuple(local(v) for v in row) for row in self.ds.query(PREFIXES + sparql)]
        body = self._post(
            f"{self.endpoint}/query",
            {"query": PREFIXES + sparql},
            accept="application/sparql-results+json",
        )
        import json

        res = json.loads(body)
        vars_ = res["head"]["vars"]
        return [
            tuple(local(b[v]["value"]) if v in b else "" for v in vars_)
            for b in res["results"]["bindings"]
        ]

    def abox(self) -> Graph:
        """The ABox named graph (in-memory mode only — SHACL scenarios need real triples)."""
        if self.ds is None:
            raise RuntimeError("SHACL scenarios require in-memory mode")
        return self.ds.graph(URIRef(ABOX))

    @staticmethod
    def _post(url: str, form: dict, accept: str = "*/*") -> bytes:
        data = urllib.parse.urlencode(form).encode()
        req = urllib.request.Request(url, data=data, headers={"Accept": accept})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()


# --------------------------------------------------------------------------- reporting

class Reporter:
    """Collects each scenario for stdout and for the generated markdown."""

    def __init__(self):
        self.blocks: list[str] = []
        self.failures: list[str] = []

    def scenario(self, n: int, title: str, sparql: str, note: str = "") -> None:
        print(f"\n\033[1m── Scenario {n}: {title}\033[0m")
        print("\n".join("    " + ln for ln in sparql.strip().splitlines()))
        self.blocks.append(f"\n## Scenario {n} — {title}\n")
        if note:
            self.blocks.append(f"{note}\n")
        self.blocks.append(f"```sparql\n{sparql.strip()}\n```\n")

    def table(self, caption: str, headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
        print(f"  {caption}:")
        if not rows:
            print("      (empty result set)")
        for r in rows[:12]:
            print("      " + " | ".join(r))
        if len(rows) > 12:
            print(f"      … (+{len(rows) - 12} more)")

        self.blocks.append(f"\n**{caption}**\n")
        if not rows:
            self.blocks.append("\n_(empty result set)_\n")
            return
        self.blocks.append("\n| " + " | ".join(headers) + " |")
        self.blocks.append("|" + "|".join(["---"] * len(headers)) + "|")
        for r in rows[:12]:
            self.blocks.append("| " + " | ".join(r) + " |")
        if len(rows) > 12:
            self.blocks.append(f"| _… (+{len(rows) - 12} more)_ |" + " |" * (len(headers) - 1))
        self.blocks.append("")

    def check(self, label: str, ok: bool, detail: str = "") -> None:
        mark = "\033[32m✓\033[0m" if ok else "\033[31m✗\033[0m"
        print(f"  {mark} {label}" + (f" — {detail}" if detail else ""))
        self.blocks.append(f"\n{'✅' if ok else '❌'} **{label}**"
                           + (f" — {detail}" if detail else "") + "\n")
        if not ok:
            self.failures.append(label)


# --------------------------------------------------------------------------- scenarios

def run(store: Store, r: Reporter, shacl: bool) -> None:
    abox_only = f"""ASK {{ GRAPH <{ABOX}> {{ {SUBJ} a :SoloArtist }} }}"""

    # -- 1. INSERT DATA -------------------------------------------------------
    r.scenario(
        1,
        "INSERT DATA — add an artist to the ABox graph",
        f"""INSERT DATA {{
  GRAPH <{ABOX}> {{
    {SUBJ} a :SoloArtist ;
        rdfs:label "Jeff Buckley"@en ;
        :bornOn "1994"^^xsd:gYear ;
        :hasGenre :Rock ;
        :hasInstrument :Guitar, :Voice ;
        :originatesFrom :UnitedStates ;
        :collaboratesWith :BobDylan .
  }}
}}""",
        note="The update names its target graph, so the TBox and shapes graphs are never in scope.",
    )
    before = store.select(f"SELECT ?a WHERE {{ GRAPH <{ABOX}> {{ ?a a :SoloArtist }} }}")
    r.table("Before — :SoloArtist count", ("artist",), [(f"{len(before)} artists",)])

    store.update(f"""INSERT DATA {{
  GRAPH <{ABOX}> {{
    {SUBJ} a :SoloArtist ;
        rdfs:label "Jeff Buckley"@en ;
        :bornOn "1994"^^xsd:gYear ;
        :hasGenre :Rock ;
        :hasInstrument :Guitar, :Voice ;
        :originatesFrom :UnitedStates ;
        :collaboratesWith :BobDylan .
  }}
}}""")

    after = store.select(f"SELECT ?a WHERE {{ GRAPH <{ABOX}> {{ ?a a :SoloArtist }} }}")
    r.table("After — :SoloArtist count", ("artist",), [(f"{len(after)} artists",)])
    r.check("INSERT DATA added exactly one :SoloArtist",
            len(after) == len(before) + 1, f"{len(before)} → {len(after)}")

    # Which graph did the triples land in? This is the named-graph payoff.
    where = store.select(f"SELECT ?g WHERE {{ GRAPH ?g {{ {SUBJ} a :SoloArtist }} }}")
    r.table("Which named graph holds the new triples?", ("graph",), where)
    r.check("New triples live in the ABox graph only",
            where == [("abox",)], f"found in {[g[0] for g in where]}")

    # -- 2. DELETE/INSERT (update in place) -----------------------------------
    r.scenario(
        2,
        "DELETE/INSERT — correct a wrong value in place",
        f"""WITH <{ABOX}>
DELETE {{ {SUBJ} :bornOn ?old }}
INSERT {{ {SUBJ} :bornOn "1966"^^xsd:gYear }}
WHERE  {{ {SUBJ} :bornOn ?old }}""",
        note="`WITH` scopes an entire DELETE/INSERT/WHERE modify operation to one graph. "
             "1994 was Buckley's *debut album* year, not his birth year — a plausible data error.",
    )
    b = store.select(f"SELECT ?y WHERE {{ GRAPH <{ABOX}> {{ {SUBJ} :bornOn ?y }} }}")
    r.table("Before", ("bornOn",), b)

    store.update(f"""WITH <{ABOX}>
DELETE {{ {SUBJ} :bornOn ?old }}
INSERT {{ {SUBJ} :bornOn "1966"^^xsd:gYear }}
WHERE  {{ {SUBJ} :bornOn ?old }}""")

    a = store.select(f"SELECT ?y WHERE {{ GRAPH <{ABOX}> {{ {SUBJ} :bornOn ?y }} }}")
    r.table("After", ("bornOn",), a)
    r.check("bornOn corrected 1994 → 1966", a == [("1966",)], f"now {a}")
    r.check("still exactly one bornOn value (no duplicate left behind)", len(a) == 1)

    # -- 3. SHACL-gated write -------------------------------------------------
    # Run BEFORE the delete so the demo artist is still present and the graph is otherwise
    # in a known-clean state.
    if shacl:
        r.scenario(
            3,
            "A write the shapes REJECT — validation as a write gate",
            f"""INSERT DATA {{
  GRAPH <{ABOX}> {{
    :HeyJude :writtenBy :EMI .
  }}
}}""",
            note="`:EMI` is a `:RecordLabel`. It is not a `:MusicalAgent` and holds no "
                 "`:LyricistRole`. `:WrittenByShape` is anchored on the **property** "
                 "(`sh:targetSubjectsOf :writtenBy`), not on the work's class — which is "
                 "exactly why this cannot slip through.",
        )
        tbox = Graph().parse(ROOT / ONTOLOGY, format="turtle")
        shapes = Graph().parse(ROOT / SHAPES, format="turtle")

        clean = snapshot(store.abox())
        _, rep, _ = validate_data(clean, shapes, tbox)
        v0, w0 = tally(rep)
        r.table("Before the bad write", ("Violations", "Warnings"), [(str(v0), str(w0))])
        r.check("Graph conforms before the bad write (0 Violations)", v0 == 0)

        store.update(f"INSERT DATA {{ GRAPH <{ABOX}> {{ :HeyJude :writtenBy :EMI . }} }}")

        dirty = snapshot(store.abox())
        _, rep2, _ = validate_data(dirty, shapes, tbox)
        v1, w1 = tally(rep2)
        r.table("After the bad write", ("Violations", "Warnings"), [(str(v1), str(w1))])
        r.check("SHACL REJECTS the write (Violations > 0)", v1 > 0,
                f"{v1} Violation(s) — the write gate is not vacuous")

        msgs = sorted({str(o) for o in rep2.objects(None, URIRef(
            "http://www.w3.org/ns/shacl#resultMessage"))})
        r.table("Violation messages", ("message",), [(m,) for m in msgs])

        # Roll back the rejected write.
        store.update(f"DELETE WHERE {{ GRAPH <{ABOX}> {{ :HeyJude :writtenBy :EMI }} }}")

        restored = snapshot(store.abox())
        _, rep3, _ = validate_data(restored, shapes, tbox)
        v2, _ = tally(rep3)
        r.check("Graph conforms again after rollback", v2 == 0, f"{v2} Violations")

    # -- 4. DELETE WHERE, and the dangling-inbound-edge trap -------------------
    # The inbound edge below is inserted BY THIS SCRIPT, and the INSERT is shown in the
    # scenario's SPARQL block rather than run off-camera. It has to be staged: the demo
    # subject is chosen precisely because he is absent from the catalogue (see SUBJ), so he
    # has no organic inbound edges to trip over. Hiding this setup would put a manufactured
    # row under a report header that says "captured from a real run".
    r.scenario(
        4,
        "DELETE WHERE — and why subject-position-only is not a deletion",
        f"""# Setup: another agent asserts an edge that points AT our artist.
INSERT DATA {{
  GRAPH <{ABOX}> {{ :DavidBowie :collaboratesWith {SUBJ} . }}
}} ;

# The retraction — note it binds the artist in the SUBJECT position only.
DELETE WHERE {{
  GRAPH <{ABOX}> {{ {SUBJ} ?p ?o }}
}}""",
        note="Note the form first: `DELETE WHERE` is its own production in the SPARQL 1.1 "
             "grammar and takes **no `WITH` clause** — only the `Modify` form (scenario 2) "
             "does, so the target graph is named with an inner `GRAPH` block. Rewriting this "
             "as `WITH <…> DELETE WHERE {…}` is a parse error, not a style preference.\n\n"
             "Now the substance. The delete pattern binds the artist as a **subject**, so "
             "anything pointing *at* him survives it. The inbound edge here is asserted by "
             "this demo (shown above) — the artist is new, so nothing in the catalogue points "
             "at him yet. In a real catalogue it is the normal case, not the exception.\n\n"
             "It also gets strictly worse under a reasoner: `:collaboratesWith` is declared "
             "`owl:SymmetricProperty`, so a store doing OWL entailment would *derive* an "
             "inbound edge from the artist's own outbound one — and a subject-only delete "
             "would leave that behind too. rdflib does no OWL reasoning, so this run only "
             "sees the asserted edge.",
    )
    store.update(f"INSERT DATA {{ GRAPH <{ABOX}> {{ :DavidBowie :collaboratesWith {SUBJ} . }} }}")

    b = store.select(f"SELECT ?p ?o WHERE {{ GRAPH <{ABOX}> {{ {SUBJ} ?p ?o }} }}")
    r.table("Before — triples with the artist as SUBJECT", ("predicate", "object"), b)
    inb = store.select(f"SELECT ?s WHERE {{ GRAPH <{ABOX}> {{ ?s :collaboratesWith {SUBJ} }} }}")
    r.table("Before — triples with the artist as OBJECT", ("subject",), inb)

    store.update(f"DELETE WHERE {{ GRAPH <{ABOX}> {{ {SUBJ} ?p ?o }} }}")

    a = store.select(f"SELECT ?p ?o WHERE {{ GRAPH <{ABOX}> {{ {SUBJ} ?p ?o }} }}")
    r.check("Subject-position triples are gone", len(a) == 0, f"{len(b)} → {len(a)}")

    dangling = store.select(
        f"SELECT ?s WHERE {{ GRAPH <{ABOX}> {{ ?s :collaboratesWith {SUBJ} }} }}")
    r.table("After — the inbound edge SURVIVED", ("subject",), dangling)
    r.check("The naive delete leaves a dangling inbound edge", len(dangling) == 1,
            f"{len(dangling)} edge(s) still point at a node that no longer exists")

    # -- 5. The retraction that is actually complete --------------------------
    r.scenario(
        5,
        "The complete retraction — sweep the object position too",
        f"""DELETE WHERE {{
  GRAPH <{ABOX}> {{ ?s ?p {SUBJ} }}
}}""",
        note="The companion to scenario 4's delete: same form, but the artist is bound in the "
             "**object** position. Only with both halves run is the node genuinely gone. In "
             "production these two would be issued as one request, separated by `;`.",
    )
    store.update(f"DELETE WHERE {{ GRAPH <{ABOX}> {{ ?s ?p {SUBJ} }} }}")

    dangling = store.select(
        f"SELECT ?s WHERE {{ GRAPH <{ABOX}> {{ ?s :collaboratesWith {SUBJ} }} }}")
    r.table("After — inbound edges", ("subject",), dangling)
    r.check("No dangling edges remain", len(dangling) == 0)

    final = store.select(f"SELECT ?a WHERE {{ GRAPH <{ABOX}> {{ ?a a :SoloArtist }} }}")
    r.check("ABox restored to its original :SoloArtist count",
            len(final) == len(before), f"{len(final)} (started at {len(before)})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--endpoint", help="SPARQL endpoint base URL, e.g. http://localhost:3030/music")
    # Writing the report is OFF by default, deliberately. This script runs inside `make check`
    # and in CI, and a gate that rewrites a tracked file on every run dirties the working tree
    # and invites a stale artifact to be committed. `make report` opts in.
    ap.add_argument("--report", action="store_true",
                    help=f"also (re)generate {REPORT.relative_to(ROOT)} from this run")
    args = ap.parse_args()

    live = args.endpoint is not None
    print(f"SPARQL Update demo — {'live endpoint ' + args.endpoint if live else 'in-memory dataset'}")
    print(f"Target graph: <{ABOX}>")

    store = Store(args.endpoint)
    r = Reporter()
    # The SHACL scenario needs the raw triples in hand; skip it against a remote endpoint.
    run(store, r, shacl=not live)

    if live:
        print("\n  note: SHACL-gated-write scenario skipped (needs local triples). "
              "Restore Fuseki with: make fuseki-load")

    if args.report:
        REPORT.parent.mkdir(exist_ok=True)
        header = (
            "# MC-2 — Graph Queries: inserts, updates, and a write gate\n\n"
            "> **Generated** by `scripts/demo_updates.py --report` (`make report`). Every "
            "result set below was captured from a real run — do not hand-edit.\n\n"
            "The 18 read queries live in `docs/competency-questions.md`. This file covers the "
            "*write* side: each update names the graph it targets, so the ABox can be modified "
            "while the TBox and shapes graphs stay out of scope.\n"
        )
        REPORT.write_text(header + "\n".join(r.blocks) + "\n")
        print(f"\nWrote {REPORT.relative_to(ROOT)}")

    if r.failures:
        print(f"\nFAIL — {len(r.failures)} check(s) failed: {r.failures}")
        return 1
    print("\nOK — all scenarios behaved as asserted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
