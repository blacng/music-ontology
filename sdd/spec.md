# Specification — Comprehensive Music Vocabulary

## Purpose

An OWL 2 ontology of the popular- and classical-music domain, aligned to the **gist** upper
ontology, intended to power a **music discovery / recommendation application**. The ontology
is the canonical, reasoned, validated source of truth; serving layers (including any future
property-graph projection) derive from it.

## Scope

In scope: musical agents (artists, bands, composers, lyricists, producers, conductors,
labels), works (songs, albums, classical compositions), a genre taxonomy, instruments,
events/venues, awards/charts, and musical features (key, tempo, time signature), plus the
connective relationships used for recommendation (genre, collaboration, membership, label
roster, authorship/performance, album composition, instrumentation, recognition, origin/era).

Out of scope (currently): structured geography, streaming/usage signals, audio features
beyond key/tempo/time-signature.

## Contract: competency questions

The ontology's functional contract is the competency-question set in
[`docs/competency-questions.md`](../docs/competency-questions.md) — 12 CQs oriented to discovery
and recommendation. "Done" for the ontology means every CQ has a passing SPARQL test against
canonical instance data (Production Readiness Checklist item 1).

## Conventions

Follows the team style guide (`prompt_library/style_guide_system_prompt.md`): gist alignment
by IRI, PascalCase singular classes, camelCase properties, SKOS labels/definitions in
Aristotelian form, SHACL paired with every constraint change. See `CLAUDE.md`.

## System maturity

**Research prototype.** Rights/availability, assertion provenance/confidence, and bias-audit
CQs are explicitly waived (see `docs/competency-questions.md` → Waivers); revisit before any
production use. Scope is **content-based candidate generation**, not personalised recommendation
(no user/interaction/rating is modelled).

## Resolved in Artefact 4 (Modeller Dialogue)

- **Genre** now follows the gist:Category pattern: `:MusicGenre rdfs:subClassOf gist:Category`,
  `:hasGenre rdfs:subPropertyOf gist:isCategorizedBy`, hierarchy via transitive
  `:hasBroaderGenre`, top level marked `:TopLevelGenre`. Semantically sound transitivity.
- **Geography** is structured: `:originatesFrom` (agents) and `:locatedIn` (orgs/venues/places,
  transitive) point to `:Place`/`:City`/`:Country`, enabling regional roll-up.
- **Personal attrs:** `:hasHeight` removed; `:hasAge` replaced by `:bornOn` (`xsd:date`).
- **Agent boundary** (Artefact-4 loop-back, SHACL-driven): `:MusicalAgent` is the shared parent
  of `:MusicalArtist` and `:Musician`; `:SoloArtist ⊑ :Musician`; `:collaboratesWith` relates
  `:MusicalAgent`s. Clears the 2 SHACL Violations at the schema level (no individual patching).

Applied via `music_ontology/scripts/apply_structural_fixes.py`; verified by `music_ontology/scripts/validate_fixes.py`
(parse + SPARQL checks all pass) and `pyshacl` (0 Violations).

## Known issues / decisions pending

- CQ-8 (producer lineage) and CQ-11 (member crossover) need richer instance data (Artefact 5).
- **Vocalist instrument gap:** with `:SoloArtist ⊑ :Musician`, vocalists trip the soft
  "a musician should play an instrument" warning (voice isn't modelled). Resolve by modelling
  `:Voice` or relaxing the expectation to "sings or plays."
- Annotation style is still mixed `rdfs:label`/`rdfs:comment` + SKOS; the style guide targets
  SKOS-only `skos:prefLabel`/`skos:definition` — a separate cleanup, not yet scheduled.
- `:locatedIn` is left domain-open (permissive) to span orgs, venues, events, and places.

> Living document — update before completing each feature/development task.
