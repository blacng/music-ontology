"""Validate the structural fixes: parse the ontology and run SPARQL checks
that exercise the new genre / place / time modelling.

Run: uv run python scripts/validate_fixes.py
"""
import sys
from rdflib import Graph

PRE = """
PREFIX : <https://www.somusicvocabulary.org/music#>
PREFIX gist: <https://w3id.org/semanticarts/ontology/gistCore#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

g = Graph()
g.parse("ontology/music_vocabulary_comprehensive.ttl", format="turtle")
print(f"parsed OK: {len(g)} triples\n")

checks = []


def q(label, sparql, expect=None, show=False):
    res = g.query(PRE + sparql)
    if res.type == "ASK":
        ok = bool(res.askAnswer)
        checks.append(ok)
        print(f"[{'ok ' if ok else 'FAIL'}] {label}: {res.askAnswer}")
        return
    rows = list(res)
    vals = [tuple(str(x).split("#")[-1] for x in r) for r in rows]
    ok = True if expect is None else (len(rows) == expect)
    checks.append(ok)
    status = "ok " if ok else "FAIL"
    extra = f" (expected {expect})" if expect is not None and not ok else ""
    print(f"[{status}] {label}: {len(rows)} rows{extra}")
    if show:
        for v in sorted(vals)[:12]:
            print("        ", v)


# Fix 1 - genre
q("top-level genres (:TopLevelGenre)", "SELECT ?g WHERE { ?g a :TopLevelGenre }", expect=15)
q("Rock + descendants via :hasBroaderGenre*",
  "SELECT ?s WHERE { ?s :hasBroaderGenre* :Rock }", show=True)
q("Nirvana rolls up to Rock (transitive subgenre)",
  "SELECT DISTINCT ?a WHERE { ?a :hasGenre/:hasBroaderGenre* :Rock . FILTER(?a = :Nirvana) }", expect=1)
q(":hasGenre is a sub-property of gist:isCategorizedBy",
  "ASK { :hasGenre rdfs:subPropertyOf gist:isCategorizedBy }")
q("MusicGenre subClassOf gist:Category",
  "ASK { :MusicGenre rdfs:subClassOf gist:Category }")
q("US-origin artists via city :locatedIn* :UnitedStates",
  "SELECT DISTINCT ?a WHERE { ?a :originatesFrom ?c . ?c :locatedIn* :UnitedStates }", show=True)
q("no skos:broader triples remain among genres",
  "SELECT ?s WHERE { ?s <http://www.w3.org/2004/02/skos/core#broader> ?o . ?s a :MusicGenre }", expect=0)

# Fix 2 - geography / roll-up
q("artists originating in England (city :locatedIn* :England)",
  "SELECT DISTINCT ?a WHERE { ?a :originatesFrom ?c . ?c :locatedIn* :England }", show=True)
q("EMI located in (org uses :locatedIn, not :originatesFrom)",
  "SELECT ?p WHERE { :EMI :locatedIn ?p }", expect=1)
q("no string-valued :originatesFrom remains",
  'SELECT ?s WHERE { ?s :originatesFrom ?o . FILTER(isLiteral(?o)) }', expect=0)

# Fix 3 - time / personal attrs
q("McCartney has :bornOn", "SELECT ?d WHERE { :PaulMcCartney :bornOn ?d }", expect=1)
q("no :hasAge triples remain", "SELECT ?s WHERE { ?s :hasAge ?o }", expect=0)
q("no :hasHeight triples remain", "SELECT ?s WHERE { ?s :hasHeight ?o }", expect=0)

print()
if all(checks):
    print("ALL CHECKS PASSED")
else:
    print(f"{checks.count(False)} CHECK(S) FAILED")
    sys.exit(1)
