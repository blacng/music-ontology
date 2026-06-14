# Architecture Decisions (Y-statements)

Production Readiness item 9. Each decision uses the Y-statement template:
*In the context of … facing … we decided for … and neglected … to achieve … accepting …*
The informal log lives in [`plan.md`](plan.md) → Decisions log; these are the formal records.

## AD-1 — Knowledge representation: RDF/OWL
In the context of a music **discovery/recommendation** vocabulary, facing a choice of graph
technology, we decided for **RDF/OWL** and neglected a labelled property graph (LPG), to achieve
formal reasoning, SHACL validation, SPARQL, and interoperability with shared vocabularies,
accepting that high-throughput serving may later need an LPG projection of the canonical model.

## AD-2 — Single upper ontology: gist
In the context of upper-ontology alignment, facing gist vs BFO vs DOLCE (and mixing them), we
decided for **gist alone** and neglected mixing in BFO/DOLCE, to achieve a coherent, pragmatic
top level without reasoner conflicts, accepting that a few domain classes (`:MusicalAgent`,
`:MusicAward`) have no gist parent — which is legitimate.

## AD-3 — gist version: migrate to current v14.1.0, vendored
In the context of a broken legacy `gistCore#` alignment, facing migrate / pin-old / drop, we
decided for **migrating to current gist v14.1.0, vendored locally** and neglected pinning a legacy
release (none matched) or dropping the import, to achieve a valid, reasoner-checked alignment that
is reproducible offline, accepting a re-modelling of agent/work/instrument/place parents.

## AD-4 — Genre modelling: gist:Category + transitive property
In the context of a cross-cutting genre facet over artists, albums, and songs, facing OWL
subclassing vs SKOS vs gist categorisation, we decided for **`gist:Category` instances with a
transitive `:hasBroaderGenre` and a `:TopLevelGenre` marker** and neglected OWL subclassing
(wouldn't deliver transitivity through `:hasGenre`) and raw SKOS `broader` (non-transitive), to
achieve sound hierarchy traversal that matches the team style guide, accepting a custom
`:hasBroaderGenre` rather than native `skos:broaderTransitive`.

## AD-5 — Agent boundary: shared `:MusicalAgent` superclass
In the context of SHACL violations where band members and collaborators spanned the
`:Musician`/`:MusicalArtist` divide, facing data-level multi-typing vs a structural fix, we decided
for a **`:MusicalAgent` superclass with `:SoloArtist ⊑ :Musician`** and neglected multi-typing
individuals, to achieve a fix at the schema level that future data can't re-break, accepting a few
new completeness warnings for vocalists with no modelled instrument.

## AD-6 — Geography: structured `:Place`
In the context of "artists from a region" discovery, facing free-text origins vs a place graph, we
decided for a **structured `:Place`/`:City`/`:Nation` graph with transitive `:locatedIn`** and
neglected free-text strings, to achieve regional roll-up, accepting the cost of modelling place
entities and a one-time data rewrite.

## AD-7 — Maturity: research prototype with documented waivers
In the context of the Production Readiness gate, facing full production rigor vs a prototype, we
decided for a **research prototype** and neglected production hardening, to achieve momentum on the
modelling, accepting documented waivers: rights/provenance/bias CQs, and the OWL-2-DL datatype
deviation (`xsd:gYear`/`xsd:date`).

## AD-8 — Tooling: Make + CI now, Docker for the reasoner only
In the context of automation, facing "set up Docker + Make as standard practice", we decided for a
**`Makefile` + GitHub Actions CI now, and Docker only for the reasoner** and neglected containerising
the whole pure-Python stack, to achieve a validation gate without ceremony (`uv` + lockfile already
give reproducibility), accepting that the reasoner step needs Docker and is outside the CI gate.

## AD-9 — Vocabulary annotations: SKOS-only
In the context of the style guide's SKOS standard, facing mixed `rdfs:label`/`rdfs:comment` vs SKOS,
we decided for **`skos:prefLabel`/`skos:definition`/`skos:scopeNote` on classes and properties** and
neglected keeping `rdfs:label`, to achieve a consistent SKOS vocabulary, accepting that instance
data keeps `rdfs:label` (instances are data, not vocabulary terms).
