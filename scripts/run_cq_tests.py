"""Artefact 5 — CQ regression suite runner.

Loads the ontology + synthetic test data, runs each competency question's SPARQL
query, and checks that the designated yes-instances appear in the result and the
no-instances do not. Membership-based so it is robust to the illustrative real
catalog also being present.

Run: uv run python scripts/run_cq_tests.py
"""
import json
import sys
from pathlib import Path
from rdflib import Graph

NS = "https://www.somusicvocabulary.org/music#"
PREFIXES = f"""
PREFIX : <{NS}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

ONTOLOGY = "ontology/music_vocabulary_comprehensive.ttl"  # TBox (model)
CATALOG = "ontology/music_catalog_data.ttl"               # ABox (real instances)
TEST_DATA = "tests/test_data.ttl"                          # synthetic :TST_* fixtures
MANIFEST = "tests/cq_test_manifest.json"


def local(term):
    return str(term).split("#")[-1] if term is not None else None


def main():
    g = Graph()
    g.parse(ONTOLOGY, format="turtle")
    g.parse(CATALOG, format="turtle")
    g.parse(TEST_DATA, format="turtle")
    manifest = json.loads(Path(MANIFEST).read_text())

    results = []
    for t in manifest["tests"]:
        var = t["var"]
        got = set()
        for row in g.query(PREFIXES + t["sparql"]):
            v = row.asdict().get(var)
            if v is not None:
                got.add(local(v))
        contains = set(t["expect"]["contains"])
        excludes = set(t["expect"]["excludes"])
        missing = contains - got            # yes-instances that failed to appear
        leaked = excludes & got             # no-instances that wrongly appeared
        ok = not missing and not leaked
        results.append((t["id"], ok, missing, leaked, len(got)))

    print(f"CQ regression suite — {ONTOLOGY} + {CATALOG} + {TEST_DATA}\n")
    width = max(len(r[0]) for r in results)
    for cid, ok, missing, leaked, n in results:
        status = "PASS" if ok else "FAIL"
        detail = f"({n} rows)"
        if missing:
            detail += f"  missing yes-instance(s): {sorted(missing)}"
        if leaked:
            detail += f"  leaked no-instance(s): {sorted(leaked)}"
        print(f"  [{status}] {cid:<{width}}  {detail}")

    n_pass = sum(1 for r in results if r[1])
    print(f"\n{n_pass}/{len(results)} CQ tests passed")
    if n_pass != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
