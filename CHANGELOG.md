# Changelog

All notable changes to the Comprehensive Music Vocabulary. Versions follow the ontology's
`owl:versionInfo` / `owl:versionIRI`.

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
