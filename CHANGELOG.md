# Changelog

All notable changes to the Comprehensive Music Vocabulary. Versions follow the ontology's
`owl:versionInfo` / `owl:versionIRI`.

## [2.4.0] — 2026-07-12

**SHACL now validates the graph the model implies** — and the first thing that revealed was an
`rdfs:domain` axiom quietly mistyping non-artists.

### Fixed (v2.4.0 — the inference gap)
- **`check_shacl.py` runs `inference='rdfs'`.** It previously ran with pyshacl's default
  (`inference='none'`), so `sh:targetClass` matched only *explicitly*-typed nodes — a `:SoloArtist`
  slipped straight past `:MusicalArtistShape`. (The docstring claimed passing the TBox as `ont_graph`
  handled this. It does not: `ont_graph` merges TBox triples but computes no entailment.) **No new
  dependency** — pyshacl already ships `owlrl`, and `inference` is a first-class pyshacl parameter.
  Full `owlrl` closure was rejected: it puns class IRIs as individuals, raising two spurious
  Violations on `:City` and `:Region` (classes, not instances).
- **Dropped `rdfs:domain :MusicalArtist` from `:startsCareerIn`, `:activeFrom`, `:activeUntil`.**
  In RDFS a domain is an *inference rule* — "anything with this property **is** a `:MusicalArtist`" —
  not the constraint the model meant. Producers, conductors and non-artist musicians all have career
  years, so RDFS silently retyped them: `:GeorgeMartin`, `:QuincyJones` and `:RickRubin` became musical
  artists and then tripped "a musical artist should have a genre." The data was right; the axiom was
  wrong. **SHACL 0 Violations / 0 Warnings** — the warnings vanished because the cause was fixed, not
  suppressed.
- **New `:CareerOnsetShape`** carries the constraint reading the domains were wrongly expressing:
  career-onset years belong to a `:MusicalAgent` or a `:MusicProducer`, and must be a single
  `xsd:gYear`. Verified with a negative test (a `:RecordLabel` claiming a career onset is rejected).

### Also in this release (ABox coverage — see #23)

Tooling, ABox data and documentation; no TBox change of its own.

### Added
- **`make coverage`** (`scripts/cq_coverage.py`) — an **ABox coverage report**. `make test` loads the
  synthetic `:TST_*` fixtures alongside the real catalogue, so a CQ can pass while the catalogue holds
  nothing for it to find. The report re-runs each manifest query over TBox + ABox **only**, with `?seed`
  left free, and counts how many real individuals can seed it. Advisory: always exits 0.
  It found three CQs green on fixtures alone — **CQ-8, CQ-11, CQ-15** — each with a *different* root
  cause (see Fixed). **Now 17/17 answerable.**
- **ABox backfill** (all documented public facts): `:bornOn` for `:JimiHendrix` (1942-11-27),
  `:BobDylan` (1941-05-24) and `:QuincyJones` (1933-03-14); albums `:SgtPepper` (1967, `:producedBy
  :GeorgeMartin`) and `:OffTheWall` (1979, `:producedBy :QuincyJones`), giving two traversable
  producer clusters alongside `:AbbeyRoad` and `:Thriller`.

### Changed
- **CQ queries are seed-parameterised.** The 14 queries that hardcoded a `:TST_*` seed now use a free
  `?seed` variable plus a `fixture_seed` field; `run_cq_tests.py` substitutes the fixture individual
  back in. Queries are reconstructed byte-identically — **all 17 still pass.**
- CQ-1, CQ-6, CQ-7 and CQ-9 gain rows (44→46, 14→15, 57→59, 39→40) — solely the two new albums;
  each delta was verified to be a genuine new fact, with nothing lost.

### Fixed
- **CQ-8 — genuine data gap.** Six studio albums, only two named a producer, and no producer was
  shared, so producer lineage was untraversable. Closed by the two albums above (0 → 4 seeds).
- **CQ-11 — an unrepresentative fixture, not missing data.** `tests/test_data.ttl` asserted *both*
  halves of an `owl:inverseOf` pair (`:performs` **and** `:performedBy`) while the catalogue asserts
  only `:performedBy`. CQ-11 queried `:performs`, so it passed on fixtures and could never answer from
  real data. Fixed by asserting work-side only in the fixture and querying the direction the catalogue
  actually asserts. The real answer was there all along: `:ImagineSong :performedBy :JohnLennon`, and
  Lennon is a member of `:TheBeatles`.
- **CQ-15 — sparse birth dates, not missing events.** (An earlier note in this section wrongly claimed
  there was "no `:HistoricalEvent` instance at all"; **two exist** and are correctly typed, dated and
  placed.) Only 6 individuals had `:bornOn`, and none came of age within an event's interval. Closed by
  the three birth dates above (0 → 1 seed, via `:AmericanCivilRightsMovement`).
- `sdd/spec.md` — retired two "Known issues" entries fixed back in v2.1.0 (the vocalist instrument gap,
  closed by `:Voice`/`:VocalInstrument`; the mixed `rdfs:`/SKOS annotation style, closed by the SKOS-only
  migration). They went stale because no "Resolved in v2.1" section existed for them to move to; added.

## [2.3.0] — 2026-07-12

Curated **work collections** (Layer 1) and the **reasoner promoted to a CI gate**.

### Added
- **`:WorkCollection` (⊑ `gist:Collection`)** — a curated, identity-bearing grouping of related
  works (box set, anthology, compilation, thematic series); sibling of `:Playlist`/`:MusicChart`,
  distinct from `:Album` (a release).
- **`:collects`** (domain `:WorkCollection`, range `:MusicalWork`) — the plain membership relation.
  Mirrors `gist:isMemberOf` conceptually but is **not** declared its `owl:inverseOf` (see below).
- **`:CollectionType` (⊑ `gist:Category`)** — anthology / box set / compilation / thematic, assigned
  via `gist:isCategorizedBy` (same idiom as genres and place-types).
- **CQ-16** (browse a work collection) + `:WorkCollectionShape` (SHACL) + `:TST_*` fixtures and an
  illustrative `:GreatestRockAnthems`. **Suite now 17/17.**
- **CI `reason` job** — HermiT via containerized ROBOT runs on every push/PR, alongside `make check`.

### Fixed
- Reasoner caught a real inconsistency: `:collects` first declared `owl:inverseOf gist:isMemberOf`
  **with** `rdfs:domain :WorkCollection` leaked that domain onto the shared upper property, making
  `gist:UnitGroup`, `gist:IntergovernmentalOrganization`, and `gist:GeoRoute` unsatisfiable. SHACL and
  SPARQL were green; only `make reason` caught it — hence the new CI gate. A domain-constrained *local*
  property must not be `owl:inverseOf` a *shared gist* property.

### Scope / deferred
- **Curated ≠ derived:** a `:WorkCollection` is stored and named; "works related to a seed" stays a
  query (CQ-4/8/13). The **act-of-collecting event (L3)** and **time-indexed membership (L2)** are
  deferred with explicit triggers in `sdd/spec.md`.

## [2.2.0] — 2026-07-10

Foundational **time, geography, and history** modelling — three new competency questions
(CQ-13/14/15) built on two reusable primitives: an activity-interval pattern and the
place-containment graph. Design pressure-tested via `model_dialogue.md` +
`adversarial_critique_skill.md` before implementation.

### Added
- **Time (CQ-13):** `:activeFrom` / `:activeUntil` (`xsd:gYear`) — artist activity interval;
  `:activeFrom` is the canonical era signal. Era membership is any-overlap; a missing
  `:activeUntil` is an open interval (still active).
- **Geography (CQ-14):** `:PlaceType` (⊑ `gist:Category`), `:hasPlaceType` (⊑
  `gist:isCategorizedBy`), and transitive `:broaderPlaceType` for level ordering. Continents +
  nation→continent roll-up added to the catalog.
- **History (CQ-15):** `:HistoricalEvent` (⊑ `gist:HistoricalEvent`) with
  `gist:actualStartDate`/`gist:actualEndDate` + `:locatedIn`; "came of age" is **derived**
  (birth-date age-window ∩ event, filtered by origin), not an asserted edge.
- New SHACL: `:PlaceShape`, `:CityRollupShape` (SPARQL-targeted), `:PlaceTypeShape`,
  `:HistoricalEventShape`, and activity-/event-interval ordering constraints.
- `scripts/migrate_place_typing.py`; three CQ regression tests. **Suite now 16/16.**

### Changed
- **Geography migrated from `:City`/`:Nation` subclasses to `gist:Category` place-typing**
  (matches the genre model and the "categorize over subclass" style rule). CQ-12 rewritten off
  the removed classes. SHACL still **fully conforms: 0 Violations, 0 Warnings.**

### Known approximations (documented, not fixed)
- CQ-15 uses `:originatesFrom` (birthplace) as a proxy for formative residence; event dates are
  editorial claims; the 15–25 age window is a culturally-loaded query parameter. See
  `sdd/spec.md` → Known issues for the deferred fixes.

## [2.1.0] — 2026-06-14

### Added
- **`:Voice`** modelling — `:VocalInstrument ⊑ :MusicalInstrument` + the `:Voice` individual
  (the `:MusicalInstrument` definition broadened to include the human voice). The 5 vocalist solo
  artists now `:hasInstrument :Voice`; `MusicianShape` exempts conductors via `sh:or`.
- **Catalog completeness (real data)** — real line-ups for Coldplay, Nirvana, Led Zeppelin,
  Radiohead, the Rolling Stones (+ orchestra principals); performing bands **Queen**, **Deep
  Purple**, **Pink Floyd** (with members) plus **John Lennon** and **Julie London** for songs/album
  that lacked a performer. ~30 new individuals.

### Changed
- SHACL now **fully conforms: 0 Violations, 0 Warnings** (was 19 completeness warnings in 2.0.0).

## [2.0.0] — 2026-06-14

First engineered release — a gist-aligned OWL 2 music ontology for discovery/recommendation,
produced through the full **GRL Workshop** lifecycle (CQ → adversarial critique → modeller
dialogue → SHACL → test data → production readiness). Research prototype.

### Highlights
- **gist alignment** to current **gist v14.1.0** — vendored (`ontology/imports/gistCore.ttl` +
  `catalog-v001.xml`) and reasoner-validated (0 unsatisfiable classes). The original `gistCore#`
  alignment was invalid; classes re-parented to real gist terms (`scripts/migrate_gist.py`).
- **Genre** on the `gist:Category` pattern: transitive `:hasBroaderGenre` + `:TopLevelGenre` marker.
- **Structured geography** — `:Place`/`:City`/`:Nation` with transitive `:locatedIn` roll-up
  (replaced free-text origins). `:bornOn` (replaced the time-varying `:hasAge`).
- **`:MusicalAgent`** superclass resolving the `:Musician`↔`:MusicalArtist` boundary; `:Country`
  (class)→`:Nation` collision fix.
- **SKOS-only vocabulary** (`skos:prefLabel`/`skos:definition`/`skos:scopeNote`); nine formal
  **Y-statement** decision records (`sdd/decisions.md`).
- **SHACL** shapes (`make shacl` — 0 Violations); **12-question CQ regression suite**
  (`scripts/run_cq_tests.py` — 12/12 pass).
- **Make** task runner + **GitHub Actions CI**; containerized **HermiT** reasoner (`make reason`).
- `owl:versionIRI`; Production Readiness audit (`docs/production-readiness.md` — **10/12 green**).

### Known limitations (see `docs/production-readiness.md`)
- Not strictly OWL 2 DL: `xsd:gYear` / `xsd:date` are outside the OWL 2 datatype map (prototype
  waiver; production fix = `xsd:dateTime` / integer years).
- 19 SHACL **completeness** warnings on the *illustrative* catalog (some bands lack members, some
  songs/albums lack a performer, some musicians lack an instrument). The synthetic CQ-test fixture
  is complete; the real catalog is intentionally partial.
- gist re-alignment to current gist is genuine but mid-level mappings (e.g. `:MusicKey`→`gist:Aspect`)
  are pragmatic; revisit for a deeper alignment if needed.
