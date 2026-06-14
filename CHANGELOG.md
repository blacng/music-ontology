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
- `gist:` IRIs use the legacy `…/ontology/gistCore#` namespace; current gist publishes under
  `…/ns/ontology/gist/`, so the alignment is dangling at the IRI level — pending a decision.
- Classes carry `rdfs:label`, not `skos:prefLabel` (style guide targets SKOS-only).

## [2.0.0]
Baseline imported into this repo, then engineered through the GRL Workshop lifecycle:
gist:Category genre pattern, structured `:Place` geography, `:bornOn`, the
`:MusicalAgent` boundary fix, and SHACL shapes. See git history and `sdd/plan.md`.
