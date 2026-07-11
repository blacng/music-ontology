# Changelog

All notable changes to the Comprehensive Music Vocabulary. Versions follow the ontology's
`owl:versionInfo` / `owl:versionIRI`.

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
