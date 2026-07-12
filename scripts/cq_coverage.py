"""ABox coverage report — can the *real catalogue* answer each competency question?

`run_cq_tests.py` proves each CQ's SPARQL is correct, but it loads the synthetic
`:TST_*` fixtures alongside the catalogue, so a CQ stays green even when the real
ABox holds nothing for it to find. That is a blind spot, not a bug: the regression
suite is a query test, and fixtures are how you pin a query.

This report closes the blind spot. It reuses the *same* manifest queries with the
`?seed` variable left free, over TBox + ABox only (no fixtures), and counts how many
real individuals yield at least one answer. Zero means the query is unanswerable
against the catalogue — the CQ is green on fixtures alone.

Advisory by design: always exits 0. A research-prototype ABox is legitimately thin,
and a gate that fails on it would only train the team to ignore the signal. It is
the same stance `check_shacl.py` takes toward completeness Warnings.

Run: uv run python scripts/cq_coverage.py   (or `make coverage`)
"""
import json
import sys
from pathlib import Path

from rdflib import Graph

NS = "https://www.somusicvocabulary.org/music#"
PREFIXES = f"""
PREFIX : <{NS}>
PREFIX gist: <https://w3id.org/semanticarts/ns/ontology/gist/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

ONTOLOGY = "ontology/music_vocabulary_comprehensive.ttl"  # TBox (model)
CATALOG = "ontology/music_catalog_data.ttl"               # ABox (real instances)
MANIFEST = "tests/cq_test_manifest.json"                  # fixtures deliberately NOT loaded

THIN = 3  # at or below this many answerable seeds, flag the CQ as thin


def where_block(sparql):
    """Return the brace-matched WHERE { ... } block, dropping solution modifiers.

    Modifiers (GROUP BY / HAVING / ORDER BY) are tied to the original projection,
    which we replace with `?seed` — so they must go with it. CQ-1b is the only
    seeded CQ that has any.
    """
    start = sparql.index("{", sparql.upper().index("WHERE"))
    depth = 0
    for i in range(start, len(sparql)):
        if sparql[i] == "{":
            depth += 1
        elif sparql[i] == "}":
            depth -= 1
            if depth == 0:
                return sparql[start:i + 1]
    raise ValueError("unbalanced braces in query")


def local(term):
    return str(term).split("#")[-1] if term is not None else None


def distinct(graph, sparql, var):
    return {local(r.asdict().get(var)) for r in graph.query(PREFIXES + sparql)} - {None}


def main():
    g = Graph()
    g.parse(ONTOLOGY, format="turtle")
    g.parse(CATALOG, format="turtle")
    manifest = json.loads(Path(MANIFEST).read_text())

    rows = []
    for t in manifest["tests"]:
        if "fixture_seed" in t:
            # Leave ?seed free and project it: how many real individuals can seed this CQ?
            n = len(distinct(g, "SELECT DISTINCT ?seed WHERE " + where_block(t["sparql"]), "seed"))
            unit = "seeds"
        else:
            # Unseeded CQs (6, 9, 10) already range over the catalogue; count answers.
            n = len(distinct(g, t["sparql"], t["var"]))
            unit = "answers"
        rows.append((t["id"], n, unit, t["question"]))

    print(f"CQ catalogue coverage — {ONTOLOGY} + {CATALOG}")
    print("(synthetic fixtures deliberately excluded)\n")

    width = max(len(r[0]) for r in rows)
    for cid, n, unit, question in rows:
        flag = "EMPTY" if n == 0 else ("thin " if n <= THIN else "     ")
        print(f"  [{flag}] {cid:<{width}}  {n:>3} {unit:<8} {question}")

    empty = [r[0] for r in rows if r[1] == 0]
    thin = [r[0] for r in rows if 0 < r[1] <= THIN]
    print(f"\n{len(rows) - len(empty)}/{len(rows)} CQs answerable from the real catalogue.")
    if empty:
        print(f"EMPTY (green on fixtures only, no real data): {', '.join(empty)}")
    if thin:
        print(f"Thin  (<={THIN} answerable): {', '.join(thin)}")
    print("\nAdvisory only — this report never fails the build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
