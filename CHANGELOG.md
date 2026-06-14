# Changelog

All notable changes to the Comprehensive Music Vocabulary. Versions follow the ontology's
`owl:versionInfo` / `owl:versionIRI`.

## [Unreleased]

### Added
- `owl:versionIRI` on the ontology; `skos:related` declared as an `owl:AnnotationProperty`.
- Production Readiness audit (`docs/production-readiness.md`) + `make reason` (containerized
  HermiT consistency check).
- CQ regression suite (`tests/`, `scripts/run_cq_tests.py`) — 12/12 pass.
- Make task runner + GitHub Actions CI gate.

### Known limitations (see `docs/production-readiness.md`)
- Not strictly OWL 2 DL: `xsd:gYear` / `xsd:date` are outside the OWL 2 datatype map
  (accepted for the prototype).
- **gist alignment is broken and its re-alignment is deferred** (tracked in `sdd/plan.md`): our
  `…/ontology/gistCore#` namespace matches no gist release, and `Agent`/`Concept`/`PhysicalThing`
  exist in no gist version. A clean version-pin is impossible; proper re-alignment to current gist
  is future work.
- Classes carry `rdfs:label`, not `skos:prefLabel` (style guide targets SKOS-only).

## [2.0.0]
Baseline imported into this repo, then engineered through the GRL Workshop lifecycle:
gist:Category genre pattern, structured `:Place` geography, `:bornOn`, the
`:MusicalAgent` boundary fix, and SHACL shapes. See git history and `sdd/plan.md`.
