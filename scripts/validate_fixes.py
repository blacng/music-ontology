"""Validate the structural fixes: parse the ontology and run SPARQL checks
that exercise the new genre / place / time modelling.

Run: uv run python scripts/validate_fixes.py
"""
import sys
from rdflib import Graph

PRE = """
PREFIX : <https://www.somusicvocabulary.org/music#>
PREFIX gist: <https://w3id.org/semanticarts/ns/ontology/gist/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

# Model checks exercise both the TBox (genre/place/time modelling) and the ABox
# (real instances they traverse), so load both files — they are separate since the
# TBox/ABox split.
g = Graph()
g.parse("ontology/music_vocabulary_comprehensive.ttl", format="turtle")  # TBox
g.parse("ontology/music_catalog_data.ttl", format="turtle")              # ABox
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

# The genre taxonomy must stay DEEP ENOUGH for transitivity to be falsifiable.
#
# :hasBroaderGenre is owl:TransitiveProperty and CQ-9 walks it with a `*` path — but for most
# of this project's life the catalogue was FLAT: every genre was a direct child of a top-level
# genre, so no entity's membership depended on the closure, and CQ-9 would have returned the
# identical answer with the transitivity switched off entirely. The axiom was correct and
# completely unexercised — a green light wired to nothing.
#
# This ASK requires at least one entity whose ONLY route to :Rock is a chain of length >= 2
# (today: :PearlJam, tagged :Grunge -> :AlternativeRock -> :Rock and nothing else). Delete that
# instance, or give it a shortcut edge like `:hasGenre :Rock`, and this check goes RED — which
# is the entire point. Without it the invariant was defended by a code comment, and a comment
# has never failed a build.
q("transitivity is load-bearing: some entity reaches :Rock ONLY via a >=2-hop genre chain",
  """ASK {
       ?e :hasGenre ?deep .
       ?deep :hasBroaderGenre/:hasBroaderGenre+ :Rock .
       FILTER NOT EXISTS { ?e :hasGenre ?shallow . ?shallow :hasBroaderGenre? :Rock }
     }""")

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

# v3.0.0 - roles as gist:Category (mirrors the genre checks above)
q(":hasRole is a sub-property of gist:isCategorizedBy",
  "ASK { :hasRole rdfs:subPropertyOf gist:isCategorizedBy }")
q(":MusicalRole subClassOf gist:Category",
  "ASK { :MusicalRole rdfs:subClassOf gist:Category }")
q("the four musical roles exist as individuals",
  "SELECT ?r WHERE { ?r a :MusicalRole }", expect=4)
q("every :hasRole object is a :MusicalRole",
  "SELECT ?o WHERE { ?s :hasRole ?o . FILTER NOT EXISTS { ?o a :MusicalRole } }", expect=0)

# The role classes are gone. If any of these come back, the migration regressed.
for _cls in ("Composer", "Lyricist", "MusicProducer", "Conductor"):
    q(f"no individual is still typed :{_cls}",
      "SELECT ?s WHERE { ?s a :%s }" % _cls, expect=0)
    q(f":{_cls} is no longer a class",
      "SELECT ?c WHERE { VALUES ?c { :%s } ?c a owl:Class }" % _cls, expect=0)

# Quincy Jones is the individual the whole redesign is for: a producer AND a conductor AND
# a composer AND a trumpeter. Under roles-as-classes he could be typed only one of those,
# and so could hold no instrument at all.
q("Quincy Jones holds three roles and plays an instrument",
  "SELECT ?r WHERE { :QuincyJones :hasRole ?r ; :hasInstrument :Trumpet }", expect=3)

# :MusicalPerson must reach :MusicalAgent through ASSERTED subClassOf. run_cq_tests.py and
# cq_coverage.py apply NO inference — CQ-1b walks `a/rdfs:subClassOf*` over asserted triples.
# Link :MusicalPerson only to gist:Person and that path breaks SILENTLY: the CQ suite keeps
# passing, because it checks :TST_* fixtures that never exercise it.
q(":MusicalPerson reaches :MusicalAgent via asserted subClassOf+",
  "ASK { :MusicalPerson rdfs:subClassOf+ :MusicalAgent }")
q(":Musician reaches :MusicalAgent via asserted subClassOf+",
  "ASK { :Musician rdfs:subClassOf+ :MusicalAgent }")

# The restored rdfs:domain on the career properties is only TRUE while every career-holder
# really is an agent. This is the trip-wire that keeps it true as the catalogue grows.
q("every career-onset subject is a :MusicalAgent",
  """SELECT DISTINCT ?s WHERE {
       { ?s :startsCareerIn ?y } UNION { ?s :activeFrom ?y } UNION { ?s :activeUntil ?y }
       FILTER NOT EXISTS { ?s a/rdfs:subClassOf* :MusicalAgent }
     }""", expect=0)

# Deleting a class can leave skos:related/broader/narrower pointing into the void. The TBox
# carried three such dangling refs to the role classes; :MusicalArtist skos:broader :Artist
# has dangled since long before this release. Catch the next one at the gate.
q("no skos:related/broader/narrower points at an undeclared : term",
  """SELECT DISTINCT ?o WHERE {
       ?s ?p ?o .
       VALUES ?p { skos:related skos:broader skos:narrower }
       FILTER(STRSTARTS(STR(?o), "https://www.somusicvocabulary.org/music#"))
       FILTER NOT EXISTS { ?o a ?anyType }
     }""", expect=0, show=True)

print()
if all(checks):
    print("ALL CHECKS PASSED")
else:
    print(f"{checks.count(False)} CHECK(S) FAILED")
    sys.exit(1)
