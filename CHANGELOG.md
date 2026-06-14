# Changelog

All notable changes to the Comprehensive Music Vocabulary. Versions follow the ontology's
`owl:versionInfo` / `owl:versionIRI`.

## [Unreleased]

### Added
- **gist alignment migrated to current gist v14.1.0** (`gist:` → `…/ns/ontology/gist/`), vendored
  locally (`ontology/imports/gistCore.ttl` + `ontology/catalog-v001.xml`) and reasoner-validated
  (0 unsatisfiable classes). Classes re-parented to real gist terms (the old `gistCore#` alignment
  was invalid). Applied via `scripts/migrate_gist.py`.
- `owl:versionIRI` on the ontology; `skos:related` declared as an `owl:AnnotationProperty`.
- Production Readiness audit (`docs/production-readiness.md`) + `make reason` (containerized
  HermiT consistency check).
- CQ regression suite (`tests/`, `scripts/run_cq_tests.py`) — 12/12 pass.
- Make task runner + GitHub Actions CI gate.

### Known limitations (see `docs/production-readiness.md`)
- Not strictly OWL 2 DL: `xsd:gYear` / `xsd:date` are outside the OWL 2 datatype map
  (accepted for the prototype).
- Classes carry `rdfs:label`, not `skos:prefLabel` (style guide targets SKOS-only).

## [2.0.0]
Baseline imported into this repo, then engineered through the GRL Workshop lifecycle:
gist:Category genre pattern, structured `:Place` geography, `:bornOn`, the
`:MusicalAgent` boundary fix, and SHACL shapes. See git history and `sdd/plan.md`.
