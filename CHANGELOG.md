# Changelog

All notable changes to the Comprehensive Music Vocabulary. Versions follow the ontology's
`owl:versionInfo` / `owl:versionIRI`.

## [3.0.0] — 2026-07-12

**BREAKING.** `:Composer`, `:Lyricist`, `:MusicProducer` and `:Conductor` are no longer classes. They
are `:MusicalRole` individuals (`:ComposerRole`, `:LyricistRole`, `:ProducerRole`, `:ConductorRole`)
attached with `:hasRole`. **`?x a :MusicProducer` now returns zero rows.** They were removed rather
than renamed in place so the break is loud: reusing the IRIs would have flipped them from class to
individual and returned zero rows *silently*.

### Why

`:MusicProducer` sat under `gist:Person`, *outside* `:MusicalAgent`. Quincy Jones — whose own
`rdfs:comment` in this catalogue reads *"record producer, conductor, and composer"* — was typed
`:MusicProducer` and nothing else, so he could hold no `:hasInstrument` and perform no work.

**Be precise about the defect, because the loose version is false.** Roles-as-classes did **not** make
multi-role agents *unsayable* — OWL individuals take many types, and `:QuincyJones a :MusicProducer,
:Composer` would have made him a `:Musician` and let him hold an instrument. The catalogue simply never
asserted it. That was a missing triple, not an impossibility. What roles-as-classes actually cost:

- **Anti-rigidity (OntoClean).** A class should hold what is essential to identity. Rubin cannot stop
  being a person; he can stop producing.
- **Query brittleness.** "Who holds more than one role?" had to enumerate every role class in a
  `VALUES` clause, and broke whenever a role was added.
- **Extensibility.** Each new role was a TBox release. Real catalogues carry dozens (engineer,
  arranger, mixer, librettist). Now a role is one ABox triple.

### Added
- **`:MusicalPerson`** (⊑ `:MusicalAgent`, ⊑ `gist:Person`) — the person-side counterpart to `:Band`;
  `:Musician` reparented beneath it. `:MusicalPersonShape` validates it.
- **`:MusicalRole`** (⊑ `gist:Category`) and **`:hasRole`** (⊑ `gist:isCategorizedBy`), mirroring the
  genre / place-type / collection-type pattern the model already used.
- **`:conductedBy`** — conducting had no property at all. Karajan could be *labelled* a conductor and
  then linked to nothing. Now `:Symphony9Beethoven :composedBy :LudwigVanBeethoven ; :conductedBy
  :HerbertVonKarajan ; :performedBy :BerlinPhilharmonic` — three agents, three capacities, one work.
- **`owl:disjointWith` / `owl:AllDisjointClasses`** — the domain TBox previously had **none**.
- **`tests/negative/`** (17 fixtures) + **`make shacl-negative`** and **`make reason-negative`**,
  both wired into CI.
- **CQ-17** — "which agents hold more than one musical role?"
- **LICENSE** (CC-BY-4.0) and **NOTICE** — gist is CC-BY and `make dataset` redistributes it, which
  requires attribution. Neither existed.
- **`docs/data-protection.md`**.

### Changed
- **`make shacl` now validates under RDFS inference with a taxonomy-only `ont_graph`.** It previously
  ran with **no inference at all**, so `sh:targetClass :MusicalArtist` never reached a node asserted as
  `:SoloArtist` — the shape hierarchy simply did not apply. Turning inference on is necessary; doing it
  naively is a trap, because RDFS materialises `rdfs:domain`, and a domain is an inference *rule*, not
  a constraint. It makes any `sh:class` check on that property's subject **unfalsifiable**. Stripping
  domain/range from the validator's view of the TBox restores non-vacuity. Proven, not asserted: with
  the full TBox as `ont_graph` a `:RecordLabel` asserting `:startsCareerIn` **conforms**.
- **`rdfs:domain` on `:startsCareerIn`/`:activeFrom`/`:activeUntil`** is now `:MusicalAgent` (was
  `:MusicalArtist`, which was false — producers and conductors have careers).
- **`:producedBy`/`:writtenBy`/`:composedBy`** range over `:MusicalAgent`; the role requirement moved
  into SHACL, anchored on the **property** (`sh:targetSubjectsOf`) not the work's class.
- **`:writtenBy` domain widened to `:MusicalWork`** — under `:Song` a librettist was unsayable.
- **`:bornOn` narrowed to `xsd:gYear`** — nine full birth dates were stored to serve one consumer that
  only ever read the year (GDPR Art. 5(1)(c) minimisation). CQ-15 updated accordingly.

### Removed
- **`:MusicianShape`'s conductor exemption** (`sh:or ( … [sh:class :Conductor] )`) and
  **`:CareerOnsetShape`'s producer arm** (`sh:or ( … [sh:class :MusicProducer] )`). Both band-aids
  existed *only* because of the bad hierarchy; fixing it dissolved them rather than relocating them.
- **`:MusicalArtist skos:broader :Artist`** — pointed at a class this ontology has never defined. It
  had dangled quietly for several releases; a new undeclared-reference check caught it.

### Fixed (found by the adversarial critique, before release)
- **The credit guards were bypassable.** Anchored to the work's class, so `:SomeAlbum :writtenBy
  :SomeRecordLabel` passed with **zero violations** — `:AlbumShape` never mentioned `:writtenBy`.
- **`:MusicalPerson` had no shape**, a coverage regression this release introduced: it moved conductors
  and producers out of `:Musician` (policed) into a class nothing validated.
- **A `:Band` could hold `:ConductorRole`.** Demoting the role classes discarded what subclassing gave
  free — gist states a Category has *"no formal semantics"*, so every such guarantee had to be restated.
- **`make reason` was vacuously green.** Zero disjointness axioms meant HermiT had nothing to
  contradict and could not fail on any input — the same defect as `make shacl`, one level up.

### Known limits (see `sdd/decisions.md` AD-12, AD-14)
- **The role is on the AGENT, not the CREDIT.** `:HoldsProducerRoleShape` can only catch an agent who
  produces nothing *anywhere*; it **cannot catch a wrong credit**. Reifying credits (agent × role ×
  work, as MusicBrainz/Discogs/DDEX do) is the real fix and is deferred.
- **The shipped TBox and the validator's view are not the same graph.** A downstream RDFS store will
  still *retype* bad data rather than reject it. **SHACL is the normative contract; entailment is not.**
- **No Work/Recording/Release distinction.** `:belongsToAlbum sh:maxCount 1` is false for any song on
  both a single and an album; covers and remasters are unrepresentable.
- **No statement-level provenance.** Do not use this catalogue for rights administration.

## [Unreleased]

Tooling, ABox data, and documentation. **No TBox change**, so no version bump — the model is untouched;
what changed is the instance data and the tests that measure it.

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
