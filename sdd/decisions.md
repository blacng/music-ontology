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

## AD-10 — Musical roles are `gist:Category` instances, not classes (v3.0.0, breaking)
In the context of the agent hierarchy, facing "`:MusicProducer` sits under `gist:Person`, outside
`:MusicalAgent`, so a producer can hold no instrument and perform no work", we decided for **roles as
`gist:Category` individuals (`:ProducerRole`, `:ConductorRole`, `:LyricistRole`, `:ComposerRole`)
attached with `:hasRole` ⊑ `gist:isCategorizedBy`**, and neglected keeping them as OWL classes, to
achieve an anti-rigid, extensible role dimension (a new role is one ABox triple, not a TBox release —
real catalogues carry dozens), accepting that every guarantee the subclass axioms gave for free must
now be restated in SHACL (`:RoleBearerShape`, `:MusicalRoleShape`), because gist states plainly that
a Category carries "no formal semantics".

**Correcting the record.** The first version of this decision was justified with the claim that
roles-as-classes made multi-role agents *unsayable*. **That claim was false.** OWL individuals take
many types: `:QuincyJones a :MusicProducer, :Composer` would have made him a `:Musician` (via
`:Composer ⊑ :Musician`) and let him hold `:hasInstrument`. The catalogue simply never asserted it.
The original defect was a missing triple, not an impossibility. The real costs were anti-rigidity
(OntoClean), a query that had to enumerate every role class in a `VALUES` clause and broke whenever a
role was added, and a TBox release per new role. Those are the reasons; the impossibility claim is
withdrawn.

## AD-11 — `:MusicalPerson` as the person-side root
In the context of demoting the roles, facing "a pure producer (Rubin, Martin) has no class to be —
`:SoloArtist` drags in an instrument and a genre they do not have", we decided for a new
**`:MusicalPerson` (⊑ `:MusicalAgent`, ⊑ `gist:Person`)**, the counterpart to `:Band` on the
organisation side, with `:Musician` reparented beneath it, and neglected typing such agents as bare
`:MusicalAgent, gist:Person`, to achieve one targetable class meaning "a human working in music" —
which is what let `:MusicianShape` drop its `sh:class :Conductor` exemption outright (a conductor who
plays nothing is not a musician) — accepting one more class in the agent lattice.

## AD-12 — `rdfs:domain` stays in the TBox; SHACL validates against a taxonomy-only view
In the context of validation, facing "restoring `rdfs:domain :MusicalAgent` on the career properties
makes `:CareerOnsetShape` unfalsifiable, because RDFS reads a domain as an inference RULE and retypes
the offending node into the very class the shape checks for", we decided for **keeping the domain
axioms in the shipped TBox while handing pyshacl a taxonomy-only `ont_graph`** (domain/range stripped;
subClassOf/subPropertyOf kept), and neglected deleting the axioms outright, to achieve subclass
targeting without letting property *usage* manufacture types — proven by spike: with the full TBox as
`ont_graph` a `:RecordLabel` asserting `:startsCareerIn` **conforms**; with the strip it is rejected.

**Accepting a real, disclosed risk.** The shipped model and the validator's view of it are not the
same graph. A downstream store with RDFS entailment enabled will still *repair* bad data (retyping the
label into an agent) rather than reject it. **SHACL is the normative contract; entailment is not.**
Consumers must validate, not infer. We added `owl:disjointWith` so an OWL-DL reasoner has something to
contradict — but note that HermiT, as invoked here, does **not** catch domain-derived retyping in this
ontology, though it does in an isolated minimal one. That discrepancy is unexplained and is recorded
as an open question rather than papered over. Revisit by either deleting the domain axioms or writing
the `sh:class` shapes that would make the two views agree.

## AD-13 — Gates must be provably able to fail
In the context of the release gate, facing "`make shacl` reports 0 Violations and `make reason` reports
consistent — but a shape targeting nothing and a reasoner with no disjointness axioms report exactly
the same thing", we decided for **non-vacuity gates** (`tests/negative/` + `make shacl-negative`;
`make reason-negative`), and neglected trusting a green result, to achieve gates whose green means
something, accepting the upkeep of a fixture per shape.

This is not theoretical. `make shacl` **was** vacuously green (a previous release claimed a negative
test that was never committed), and `make reason` **was** vacuously green (the domain TBox carried
**zero** `owl:disjointWith` axioms, so HermiT could not fail on any input). Both are now mutation-tested:
revert the taxonomy-only strip and the record-label fixture goes green; delete the disjointness and the
reasoner accepts a group that is also a person. **A gate never observed failing has proved nothing.**
The negative gate reports its own coverage (currently 12/22 shapes) rather than claiming more.

## AD-14 — Roles attach to the AGENT, not the CREDIT (deliberate, deferred)
In the context of credits, facing "MusicBrainz, Discogs and DDEX all reify the credit (agent × role ×
work), while `:hasRole` puts a global flag on the person", we decided for **agent-level roles in
v3.0.0** and neglected reifying credits, to keep the breaking change to one pattern, accepting a real
limitation that must not be overstated: `:HoldsProducerRoleShape` can only catch an agent credited with
producing who produces **nothing anywhere** — it **cannot catch a wrong credit**. Give an artist
`:ProducerRole` and they validly "produce" any album. The model also cannot say Quincy produced
*Thriller* while playing trumpet on something *else*.

`:ConductorRole` is the exception that earns its keep: it is the one role not recoverable from a credit
property. Reified credits (`:Credit` = agent × role × work) are the real fix and are the next major
piece of work, together with the Work/Recording/Release distinction (FRBR) — the absence of which means
`:belongsToAlbum sh:maxCount 1` is false for any song on both a single and an album, and covers are
unrepresentable.

## AD-8 — AMENDED (2026-07-12)
`make reason` **is** now in the CI gate (`.github/workflows/ci.yml` runs it as a required job), together
with `make reason-negative`. The original "outside the CI gate" clause is stale and withdrawn.
