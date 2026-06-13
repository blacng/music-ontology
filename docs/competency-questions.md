# Competency Questions — Comprehensive Music Vocabulary

**Artefact:** 1 of 7 (Competency Question Generation) · GRL Workshop methodology
**Target ontology:** `ontology/music_vocabulary_comprehensive.ttl`
**Status:** **v3 — SPARQL regenerated against the post-Artefact-4 model** (gist:Category genres, structured `:Place`, `:bornOn`). Supersedes v2.

## Generation parameters

| Parameter | Choice |
|-----------|--------|
| Downstream use case | **Music discovery / recommendation** (content-based candidate generation) |
| System maturity | **Research prototype** — rights/availability, provenance, and bias-audit CQs waived (see Waivers) |
| Testability stance | Full intended scope; each CQ carries a **measurable pass condition** and a ✅/⚠ flag |
| Complexity target | Multi-hop traversal, aggregation, subsumption-hierarchy reasoning |

## Scope statement (per critique 4.1)

This ontology supports **content-based candidate generation**, not end-to-end personalised
recommendation: it models no user, interaction, or rating. CQs surface entities *structurally
related* to a seed; ranking by individual user preference is out of scope.

## Shared convention: genre hierarchy (implemented in Artefact 4)

Genres now follow the **gist:Category** pattern: `:MusicGenre rdfs:subClassOf gist:Category`,
and `:hasGenre rdfs:subPropertyOf gist:isCategorizedBy`. The hierarchy uses the **transitive**
object property `:hasBroaderGenre` (subgenre → broader genre), and **top-level genres are
explicitly typed `:TopLevelGenre`** (a subclass of `:MusicGenre`). So:

- a top-level genre is matched by `?root a :TopLevelGenre` (no more fragile absence-of-broader);
- an entity's top-level root is `?x :hasGenre/:hasBroaderGenre* ?root . ?root a :TopLevelGenre`;
- "a genre and all its descendants" is `?sub :hasBroaderGenre* :Rock`.

`:hasBroaderGenre` is a real `owl:TransitiveProperty`, so the `*` path and a reasoner agree —
the v1/v2 SKOS non-transitivity gap is closed. Validated by `scripts/validate_fixes.py`.

## Domain description

This ontology describes the popular- and classical-music domain for a **music discovery /
recommendation application**. It models musical **agents** (solo artists, bands and their
members, composers, lyricists, producers, conductors, record labels), the **works** they
create (songs, albums and sub-types, classical compositions), a deep **genre** taxonomy
(top-level genres and subgenres linked by transitive `:hasBroaderGenre`), **instruments** and their families,
**events/venues**, **awards and charts**, and intrinsic **musical features** (key, tempo, time
signature). The relationships that matter for discovery are connective: genre membership
(`hasGenre`), collaboration (`collaboratesWith`), band membership (`hasMember`/`isMemberOf`),
label rosters (`isSignedTo`), authorship/performance (`performedBy`, `composedBy`, `writtenBy`,
`producedBy`), album composition (`hasTrack`/`belongsToAlbum`), instrumentation
(`hasInstrument`), recognition (`hasAward`, `chartedIn`, `peaksAt`), and origin/era
(`originatesFrom`, `startsCareerIn`, `releasedIn`).

---

## The 12 Competency Questions

### CQ-1 — Genre-similar artists ("more like this") ✅
- **Question:** Given a seed artist, which other artists share at least one **top-level genre**, counting subgenre matches via the hierarchy, ranked by number of shared top-level genres?
- **Use case:** Core "fans of X also like…" recommendation row.
- **Elements:** `:MusicalArtist`, `:hasGenre`, `:MusicGenre`, `:hasBroaderGenre`, `:TopLevelGenre`.
- **Pass condition:** Seed `:DavidBowie` (Rock, Pop) ⇒ `:Coldplay` ranked top (shares **both** Rock and Pop). Pass iff Coldplay's shared-root count = 2 and it ranks first.
- **SPARQL skeleton:**
  ```sparql
  SELECT ?other (COUNT(DISTINCT ?root) AS ?shared) WHERE {
    :DavidBowie :hasGenre/:hasBroaderGenre* ?root .  ?root a :TopLevelGenre .
    ?other     :hasGenre/:hasBroaderGenre* ?root .
    FILTER(?other != :DavidBowie)
  } GROUP BY ?other ORDER BY DESC(?shared)
  ```

### CQ-2 — Collaboration & bandmate proximity ✅
- **Question:** Which artists are within two hops of a seed artist via `collaboratesWith` or shared band membership?
- **Use case:** "Discover artists connected to X" — credits-graph discovery.
- **Elements:** `:collaboratesWith` (symmetric), `:hasMember`/`:isMemberOf`, `:Band`.
- **Pass condition:** Seed `:PaulMcCartney` ⇒ `{:JohnLennon, :GeorgeHarrison, :RingoStarr}` (bandmates via The Beatles; Lennon also via `collaboratesWith`). Pass iff all three returned.
- **SPARQL skeleton:**
  ```sparql
  SELECT DISTINCT ?reachable WHERE {
    { :PaulMcCartney (:collaboratesWith|^:hasMember/:hasMember) ?reachable }
    UNION
    { :PaulMcCartney (:collaboratesWith|^:hasMember/:hasMember)/(:collaboratesWith|^:hasMember/:hasMember) ?reachable }
    FILTER(?reachable != :PaulMcCartney)
  }
  ```
- **Note:** the `{1,2}` path quantifier (used in the v1–v3 skeleton) is **not** standard SPARQL 1.1 and is rejected by rdflib — Artefact 5 caught this; rewritten above as an explicit 1-hop ∪ 2-hop union. `collaboratesWith` is sparse (one pair today); the bandmate path is well populated.

### CQ-3 — Labelmates ✅
- **Question:** Which artists are signed to the same record label as a seed artist?
- **Use case:** "Others on this label" discovery shelf.
- **Elements:** `:isSignedTo`, `:RecordLabel`.
- **Pass condition:** Seed `:PaulMcCartney` (Parlophone) ⇒ `{:TheBeatles, :Coldplay}`. Pass iff both returned and no non-Parlophone artist appears.
- **SPARQL skeleton:**
  ```sparql
  SELECT ?labelmate WHERE {
    :PaulMcCartney :isSignedTo ?label . ?labelmate :isSignedTo ?label .
    FILTER(?labelmate != :PaulMcCartney)
  }
  ```

### CQ-4 — Same-era, same-genre works (release-era based) ✅
- **Question:** Which works were **released in the same decade** as a seed work *and* share a top-level genre with it? *(Revised from artist career-start to work release era, per critique 2.2.)*
- **Use case:** "More from this era and sound" catalog discovery.
- **Elements:** `:MusicalWork`, `:releasedIn` (`xsd:gYear`), `:hasGenre`, `:MusicGenre`.
- **Pass condition:** Seed `:Thriller` (1982, Pop) ⇒ `:BillieJean` (1983, Pop). Pass iff BillieJean returned.
- **SPARQL skeleton:**
  ```sparql
  SELECT ?work WHERE {
    :Thriller :releasedIn ?y0 ; :hasGenre/:hasBroaderGenre* ?root . ?root a :TopLevelGenre .
    ?work    :releasedIn ?y  ; :hasGenre/:hasBroaderGenre* ?root .
    FILTER(FLOOR(YEAR(?y)/10) = FLOOR(YEAR(?y0)/10) && ?work != :Thriller)
  }
  ```

### CQ-5 — Shared-instrument discovery ✅
- **Question:** Which musicians play the same instrument, or one in the same family (via the instrument subsumption tree), as a seed musician?
- **Use case:** "Great guitarists like X" / instrumentation-driven discovery.
- **Elements:** `:Musician`, `:hasInstrument`, `:MusicalInstrument` subclass tree.
- **Pass condition:** Seed `:JohnLennon` (Guitar → PluckedString) ⇒ same-instrument includes `:GeorgeHarrison`, `:JimiHendrix`; same-family adds `:PaulMcCartney` (Bass). Pass iff Harrison (exact) and McCartney (family) both returned.
- **SPARQL skeleton:**
  ```sparql
  SELECT ?m ?i2 WHERE {
    :JohnLennon :hasInstrument ?i . ?i a ?fam .
    ?m :hasInstrument ?i2 . ?i2 a ?fam .
    FILTER(?m != :JohnLennon)
  }
  ```

### CQ-6 — Genre-spanning (versatile) artists ✅
- **Question:** Which artists span **more than one top-level genre**?
- **Use case:** Surfacing crossover artists for diverse recommendation sets.
- **Elements:** `:hasGenre`, `:MusicGenre`, `:hasBroaderGenre`, `:TopLevelGenre`, aggregation.
- **Pass condition:** Result includes `:BobDylan` (Folk+Rock), `:DavidBowie` (Rock+Pop), `:SadeAdu` (Jazz+Soul), `:TaylorSwift` (Country+Pop) — each count = 2. Pass iff all four present with count ≥ 2.
- **SPARQL skeleton:**
  ```sparql
  SELECT ?artist (COUNT(DISTINCT ?root) AS ?n) WHERE {
    ?artist :hasGenre/:hasBroaderGenre* ?root . ?root a :TopLevelGenre .
  } GROUP BY ?artist HAVING(?n > 1)
  ```

### CQ-7 — Recommendation explainability (evidence path) ✅  *(NEW — critique #3/#4)*
- **Question:** For a seed artist, which candidate artists are related, and **on what evidence** (shared top-level genre, same label, or same instrument)?
- **Use case:** Surfacing the "because you liked X" justification — content-based explanation (DSA-style transparency, even for a prototype).
- **Elements:** `:hasGenre`+`:hasBroaderGenre`/`:TopLevelGenre`, `:isSignedTo`, `:hasInstrument`.
- **Pass condition:** Seed `:MilesDavis` ⇒ `:SadeAdu` with reason "shared genre Jazz". Pass iff at least one candidate returns with a non-empty reason.
- **SPARQL skeleton:**
  ```sparql
  SELECT ?candidate ?reason WHERE {
    { :MilesDavis :hasGenre/:hasBroaderGenre* ?r . ?r a :TopLevelGenre .
      ?candidate :hasGenre/:hasBroaderGenre* ?r . BIND(CONCAT("shared genre ", STR(?r)) AS ?reason) }
    UNION { :MilesDavis :isSignedTo ?l . ?candidate :isSignedTo ?l . BIND("same label" AS ?reason) }
    UNION { :MilesDavis :hasInstrument ?i . ?candidate :hasInstrument ?i . BIND("same instrument" AS ?reason) }
    FILTER(?candidate != :MilesDavis)
  }
  ```

### CQ-8 — Producer lineage ⚠
- **Question:** Given an album a user likes, which other albums share its producer?
- **Use case:** "From the producer of…" discovery.
- **Elements:** `:Album`, `:producedBy`, `:MusicProducer`.
- **Pass condition (needs data):** After adding ≥2 albums per producer, seed `:Thriller` (Quincy Jones) returns Jones's other album(s). Currently each producer has one album ⇒ empty. Test-data target (Artefact 5).
- **SPARQL skeleton:**
  ```sparql
  SELECT ?other WHERE {
    :Thriller :producedBy ?p . ?other :producedBy ?p . FILTER(?other != :Thriller)
  }
  ```

### CQ-9 — Browse a genre and all descendants ✅
- **Question:** For a chosen top-level genre, which artists and works belong to it or any of its subgenres (transitive)?
- **Use case:** Genre-browse landing page — catalog navigation backbone.
- **Elements:** `:MusicGenre`, `:hasBroaderGenre`, `:hasGenre`.
- **Pass condition:** Genre `:Rock` ⇒ result includes `:Nirvana` (via `:AlternativeRock :hasBroaderGenre :Rock`), proving transitive descent. Pass iff Nirvana present.
- **SPARQL skeleton:**
  ```sparql
  SELECT ?entity WHERE { ?sub :hasBroaderGenre* :Rock . ?entity :hasGenre ?sub . }
  ```

### CQ-10 — Chart-topping hits, grouped by genre ✅
- **Question:** Which songs reached #1 on a chart, and how do they distribute across top-level genres?
- **Use case:** "Biggest hits" rows and trend exploration.
- **Elements:** `:Song`, `:peaksAt`, `:chartedIn`, `:hasGenre`, aggregation.
- **Pass condition:** Rock bucket = 3 (`:HeyJude`, `:BohemianRhapsody`, `:ImagineSong`). Pass iff Rock count = 3.
- **SPARQL skeleton:**
  ```sparql
  SELECT ?root (COUNT(DISTINCT ?song) AS ?hits) WHERE {
    ?song :peaksAt 1 ; :hasGenre/:hasBroaderGenre* ?root . ?root a :TopLevelGenre .
  } GROUP BY ?root ORDER BY DESC(?hits)
  ```

### CQ-11 — Band-member crossover ⚠
- **Question:** Given a band, what other works or bands are associated with its individual members?
- **Use case:** "If you like this band, explore its members' other work."
- **Elements:** `:Band`, `:hasMember`, `:Musician`, `:performs`/`:isMemberOf`.
- **Pass condition (needs data):** After linking a member to a solo work (e.g., `:JohnLennon :performs :ImagineSong`), seed `:TheBeatles` returns that work. Currently member→work links are absent ⇒ empty. Test-data target (Artefact 5).
- **SPARQL skeleton:**
  ```sparql
  SELECT ?member ?otherWork WHERE {
    :TheBeatles :hasMember ?member .
    OPTIONAL { ?member :performs ?otherWork }
    OPTIONAL { ?member :isMemberOf ?b FILTER(?b != :TheBeatles) }
  }
  ```

### CQ-12 — Local-scene discovery ✅
- **Question:** Which artists originate from the same place as a seed artist?
- **Use case:** "Artists from your scene / from Liverpool" geographic discovery.
- **Elements:** `:MusicalArtist`, `:originatesFrom` (→ `:Place`), `:locatedIn` (roll-up).
- **Pass condition:** Seed `:PaulMcCartney` ("Liverpool, England") ⇒ `{:JohnLennon, :GeorgeHarrison, :RingoStarr, :TheBeatles}`. Pass iff the three members returned by exact string match.
- **SPARQL skeleton:**
  ```sparql
  SELECT ?artist WHERE {
    :PaulMcCartney :originatesFrom ?p . ?artist :originatesFrom ?p .
    FILTER(?artist != :PaulMcCartney)
  }
  ```
- **Resolved (Artefact 4):** `:originatesFrom` now points to a structured `:Place`; exact-place match still works, and regional discovery is possible via `?city :locatedIn* :England`. Pass condition unchanged.

---

## Regression suite (Artefact 5)

Every CQ now has an executable test in `tests/cq_test_manifest.json`, run against
`ontology/music_vocabulary_comprehensive.ttl` + `tests/test_data.ttl` (synthetic `:TST_*`
fixtures) by `scripts/run_cq_tests.py`. Each test is membership-based — a designated
yes-instance must appear and a no-instance must not — so it is robust to the illustrative
real catalog. **12/12 pass.** Run: `uv run python scripts/run_cq_tests.py`.

## Coverage, flags & waivers

- **All 12 CQs now testable** against the synthetic fixture; CQ-8 (producer lineage) and
  CQ-11 (member crossover) — previously ⚠ — are covered by `:TST_*` data and pass.
- **Signal balance (critique #3):** genre-only CQs reduced; the set now also exercises label, collaboration/membership, instrument, producer, era, charts, and an explicit explainability CQ.
- **Waivers (research prototype, critique #3/#4):**
  - *Rights/availability* modelling — out of scope for a prototype.
  - *Provenance/confidence* on assertions — deferred; revisit before any production use.
  - *Bias/diversity audit* CQ — deferred; note the corpus is Anglo-American-skewed.
  - *`:hasAge` / `:hasHeight`* — removed in Artefact 4; `:hasAge` replaced by `:bornOn` (`xsd:date`), `:hasHeight` deleted outright.

## Changelog

- **v4** (Artefact 5): added the executable regression suite (`tests/`, `scripts/run_cq_tests.py`);
  fixed CQ-2's non-standard `{1,2}` path quantifier (→ explicit 1∪2-hop union) caught by running
  the queries; all 12 CQs pass.
- **v3** (post-Artefact-4): regenerated all genre SPARQL to the gist:Category model
  (`:hasBroaderGenre*` + `:TopLevelGenre`); CQ-12 origin now structured `:Place` with
  `:locatedIn` roll-up; updated Elements lines; marked the geography and personal-attribute
  smells resolved. Verified by `scripts/validate_fixes.py`.
- **v2** (post-critique): fixed top-level-genre traversal (CQ-1/4/6/9/10); added measurable
  pass conditions to all CQs; reworked CQ-4 to release-era; replaced award-within-genre CQ
  with explainability CQ-7; recorded prototype waivers and deferred modelling fixes.
- **v1**: initial 12 CQs.
