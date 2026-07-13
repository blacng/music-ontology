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
members, and agents holding composer / lyricist / producer / conductor **roles**, record labels), the **works** they
create (songs, albums and sub-types, classical compositions), a deep **genre** taxonomy
(top-level genres and subgenres linked by transitive `:hasBroaderGenre`), **instruments** and their families,
**events/venues**, **awards and charts**, and intrinsic **musical features** (key, tempo, time
signature). The relationships that matter for discovery are connective: genre membership
(`hasGenre`), collaboration (`collaboratesWith`), band membership (`hasMember`/`isMemberOf`),
label rosters (`isSignedTo`), authorship/performance (`performedBy`, `composedBy`, `writtenBy`,
`producedBy`), album composition (`hasTrack`/`belongsToAlbum`), instrumentation
(`hasInstrument`), recognition (`hasAward`, `chartedIn`, `peaksAt`), and origin/era
(`originatesFrom`, `startsCareerIn`, `releasedIn`), conducting (`conductedBy`), and the capacity in
which an agent contributes (`hasRole` → `:MusicalRole`).

---

## The Competency Questions

*(12 original + CQ-1b below; three foundational CQs — CQ-13/14/15 — added in v2.2, see that section.)*

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
- **Elements:** `:Album`, `:producedBy`, `:MusicalAgent` holding `:ProducerRole`.
  *(v3.0.0: `:MusicProducer` the CLASS no longer exists — a producer is an agent who holds
  `:ProducerRole`. `:ProducedByShape` enforces it. Note the limit: the shape checks the agent
  produces something SOMEWHERE, not that they produced THIS album — see AD-14.)*
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

## v2.2 additions — foundational time, geography & history

Three CQs added in v2.2 (see `sdd/spec.md` §v2.2). They share **two reusable primitives**:
a **temporal-interval** pattern (`:activeFrom`/`:activeUntil`; `gist:actualStartDate`/`End`)
and the **place-containment graph** (`:locatedIn*` over category-typed `:Place`s). Geography
migrated from `:City`/`:Nation` **subclasses** to the `gist:Category` pattern:
`:Place :hasPlaceType :City|:Region|:Nation|:Continent`, ordered by transitive
`:broaderPlaceType` — mirroring the genre model (`scripts/migrate_place_typing.py`).

### CQ-13 — Same-era, same-genre peers ("90s Hip Hop artists") ✅
- **Question:** Which artists were active during the **same time period** as a seed (their activity interval overlaps) *and* share a top-level genre?
- **Use case:** Era-scoped discovery row — "90s Hip Hop like this", "80s synth-pop".
- **Elements:** `:activeFrom`/`:activeUntil` (`xsd:gYear`), `:hasGenre`/`:hasBroaderGenre*`/`:TopLevelGenre`.
- **Time model:** activity is an interval; **any-overlap** counts (Allen). A missing `:activeUntil` is **open** (still active) — treated as `+∞` via `COALESCE`. Canonical era signal is `:activeFrom` (`:startsCareerIn` is subordinate).
- **Pass condition:** Seed `:TST_Era90sA` (active 1991–1998, Rock) ⇒ `:TST_Era90sB` (1995–2003, Rock); excludes `:TST_Era80s` (no overlap) and `:TST_Era90sJazz` (overlaps era, wrong genre).
- **SPARQL skeleton:**
  ```sparql
  SELECT DISTINCT ?other WHERE {
    :TST_Era90sA :activeFrom ?af0 ; :hasGenre/:hasBroaderGenre* ?root . ?root a :TopLevelGenre .
    OPTIONAL { :TST_Era90sA :activeUntil ?au0 }
    BIND(xsd:integer(STR(?af0)) AS ?f0) BIND(COALESCE(xsd:integer(STR(?au0)), 9999) AS ?u0)
    ?other :activeFrom ?af ; :hasGenre/:hasBroaderGenre* ?root .
    OPTIONAL { ?other :activeUntil ?au }
    BIND(xsd:integer(STR(?af)) AS ?f) BIND(COALESCE(xsd:integer(STR(?au)), 9999) AS ?u)
    FILTER(?other != :TST_Era90sA && ?f0 <= ?u && ?f <= ?u0)   # interval overlap
  }
  ```

### CQ-14 — Multi-level geographic peers (same country / continent) ✅
- **Question:** Which artists share a geographic ancestor **at a chosen granularity level** (city / region / nation / continent) with a seed, via the `:locatedIn` roll-up?
- **Use case:** "Artists from your country", "from your continent" — nested geographic discovery.
- **Elements:** `:originatesFrom`, transitive `:locatedIn`, `:hasPlaceType` (→ `:PlaceType` category), `:broaderPlaceType`.
- **Level selection:** filter the shared ancestor by `?anc :hasPlaceType :Nation` (or `:Continent`, …).
- **Pass condition:** Seed `:TST_SoloA` (Testland) at **nation** level ⇒ `:TST_SoloC` (same nation, different city); excludes `:TST_GeoFar` (same continent, **different** nation).
- **SPARQL skeleton:**
  ```sparql
  SELECT DISTINCT ?other WHERE {
    :TST_SoloA :originatesFrom/:locatedIn* ?anc . ?anc :hasPlaceType :Nation .
    ?other     :originatesFrom/:locatedIn* ?anc .
    FILTER(?other != :TST_SoloA)
  }
  ```

### CQ-15 — Came of age during a historical event ✅
- **Question:** Which artists **came of age** during a historical event — their ~15–25 window overlaps the event interval *and* they originated from within the event's place?
- **Use case:** "Artists shaped by the Civil Rights Movement / the Irish War of Independence" — formative-context discovery.
- **Elements:** `:HistoricalEvent` (`gist:actualStartDate`/`gist:actualEndDate`, `:locatedIn`), `:bornOn`, `:originatesFrom/:locatedIn*`.
- **Derivation, not assertion (decided):** no artist→event edge; the link is computed. The **age window (15–25) is a query parameter**, not a modelled fact.
- **Known approximations (per adversarial critique — documented, not fixed):**
  1. `:originatesFrom` is **birthplace**, used as a *proxy* for formative residence — lossy for emigrant artists.
  2. Scoped to **persons**: `:bornOn` is meaningless for `:Band`s; the query's `:bornOn` requirement naturally excludes them.
  3. Event boundary dates are **sourced editorial claims**, not exact facts.
  4. Corpus is Anglo-American-skewed (existing waiver) — the age window itself is culturally loaded.
- **Pass condition:** Event `:TST_EventE` (1960–1968, Testland) ⇒ `:TST_ComeOfAge` (born 1948, from Testland); excludes `:TST_TooYoung` (born 1965) and `:TST_WrongPlace` (right age, origin outside Testland).
- **SPARQL skeleton:**
  ```sparql
  SELECT DISTINCT ?artist WHERE {
    :TST_EventE gist:actualStartDate ?es ; gist:actualEndDate ?ee ; :locatedIn ?ep .
    ?artist :bornOn ?b ; :originatesFrom/:locatedIn* ?ep .
    BIND(YEAR(?b) AS ?by)
    FILTER(?by + 15 <= YEAR(?ee) && YEAR(?es) <= ?by + 25)   # age-window ∩ event ≠ ∅
  }
  ```

## v2.3 addition — curated work collections

### CQ-16 — Browse a work collection ✅
- **Question:** Which works belong to a given **curated** work collection (box set, anthology, compilation, thematic series)?
- **Use case:** "What's in this collection" — browsing a curated grouping of related works.
- **Elements:** `:WorkCollection` (`⊑ gist:Collection`), `:collects` (plain membership relation — mirrors `gist:isMemberOf` but not declared its `owl:inverseOf`, which would make gist classes unsatisfiable), `:MusicalWork`, `:CollectionType` (`gist:Category`).
- **Curated ≠ derived:** a `:WorkCollection` is an **identity-bearing individual** (it has a name, a `:CollectionType`, and could carry a curator/date later). It is **not** a query result — "works *related to* a seed" stays a SPARQL/CQ (CQ-4 era, CQ-8 producer, CQ-13 era+genre) with nothing stored. Only reify a collection when a human would point at it and say *that one*.
- **Scope (L1 only):** membership is the **plain relation** `:collects`, atemporal. The *act of collecting* (a `gist:Event`) and *time-indexed membership* (a reified state) are **deliberately deferred** — see `sdd/spec.md` → Known issues for the L2/L3 triggers.
- **Pass condition:** Seed `:TST_Collection` ⇒ `{:TST_Album1, :TST_Song1}`; excludes `:TST_Album3`, `:TST_Song2` (not collected).
- **SPARQL skeleton:**
  ```sparql
  SELECT DISTINCT ?work WHERE { :TST_Collection :collects ?work }
  ```

---

## Regression suite (Artefact 5)

Every CQ now has an executable test in `tests/cq_test_manifest.json`, run against
`ontology/music_vocabulary_comprehensive.ttl` + `tests/test_data.ttl` (synthetic `:TST_*`
fixtures) by `scripts/run_cq_tests.py`. Each test is membership-based — a designated
yes-instance must appear and a no-instance must not — so it is robust to the illustrative
real catalog. **17/17 pass** (12 original + CQ-1b + three v2.2 CQs + CQ-16). Run: `uv run python scripts/run_cq_tests.py`.

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

- **v6** (v2.3): added **CQ-16** (browse a curated `:WorkCollection` via the plain `:collects`
  relation, `⊑ gist:Collection`; kind via `:CollectionType` `gist:Category`). Scoped to L1
  (plain membership); the act-of-collecting event and time-indexed membership are deferred with
  triggers recorded in `sdd/spec.md`. Suite now 17/17.
- **v5** (v2.2): added **CQ-13** (same-era + genre, activity-interval overlap), **CQ-14**
  (multi-level geography via `:hasPlaceType` + `:locatedIn*`), and **CQ-15** (came-of-age
  during a `:HistoricalEvent`, derived by birth-date + place). Migrated geography from
  `:City`/`:Nation` subclasses to the `gist:Category` place-typing pattern
  (`scripts/migrate_place_typing.py`); CQ-12 rewritten off the removed classes. Suite now
  16/16. Design pressure-tested via `model_dialogue.md` + `adversarial_critique_skill.md`
  (approximations in CQ-15 documented, not silently fixed).
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

### CQ-17 — Multi-role agents ✅
- **Question:** Which agents hold more than one musical role (e.g. producer *and* composer)?
- **Use case:** Surfacing the polymaths — "Quincy Jones, who also conducted and composed."
- **Elements:** `:MusicalAgent`, `:hasRole`, `:MusicalRole`.
- **Pass condition:** `:QuincyJones` (3 roles) and `:BobDylan` (2) are returned; `:GeorgeMartin`
  (1 role) is not. Answerable from the real catalogue (2 seeds — thin).
- **SPARQL:**
  ```sparql
  SELECT ?agent (COUNT(DISTINCT ?r) AS ?n) WHERE {
    ?agent :hasRole ?r . ?r a :MusicalRole .
  } GROUP BY ?agent HAVING(COUNT(DISTINCT ?r) > 1)
  ```
- **Honest note on provenance:** this CQ was authored *with* the v3.0.0 model change, not before it,
  which inverts the CQ-first rule in `CQ_generator.md`. It was initially justified with the claim that
  the question was "unanswerable by construction" under roles-as-classes. **That claim was false** —
  `:QuincyJones a :MusicProducer, :Composer` was always legal OWL and a `VALUES` clause over the four
  role classes would have answered it. What the old model actually cost was that the query had to
  *enumerate every role class*, so it broke whenever a role was added, and each new role needed a TBox
  release. Read CQ-17 as a **regression test for `:hasRole`**, not as a stakeholder requirement.

---

## Changelog (v3.0.0)
- Added **CQ-17** (multi-role agents) — 18 CQs total, 18/18 passing, 18/18 answerable from the real
  catalogue (`make coverage`).
- **CQ-8**: `:MusicProducer` the class is gone; a producer is an agent holding `:ProducerRole`.
- **CQ-15**: `:bornOn` narrowed to `xsd:gYear` (personal-data minimisation), so the year is read with
  `xsd:integer(STR(?b))` — SPARQL's `YEAR()` accepts only `xsd:date`/`xsd:dateTime`.
