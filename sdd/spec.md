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

Out of scope (currently): streaming/usage signals, audio features beyond key/tempo/time-
signature, assertion provenance/confidence (waived for the prototype — see below).

## Contract: competency questions

The ontology's functional contract is the competency-question set in
[`docs/competency-questions.md`](../docs/competency-questions.md) — 16 CQs (+ CQ-1b) oriented to
discovery and recommendation. "Done" for the ontology means every CQ has a passing SPARQL test
against canonical instance data (Production Readiness Checklist item 1). **Realized in Artefact 5,
extended in v2.2–v2.3:** `tests/cq_test_manifest.json` + `tests/test_data.ttl`, run by
`scripts/run_cq_tests.py` — **17/17 pass**.

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

Applied via `scripts/apply_structural_fixes.py`; verified by `scripts/validate_fixes.py`
(parse + SPARQL checks all pass) and `pyshacl` (0 Violations).

## Resolved in v2.2 (Foundational time, geography & history)

Three foundational CQs added, sharing **two reusable primitives** — a temporal-interval
pattern and the place-containment graph. Design pressure-tested via `model_dialogue.md` +
`adversarial_critique_skill.md` before implementation.

- **Time (CQ-13):** artist **activity interval** `:activeFrom`/`:activeUntil` (`xsd:gYear`);
  `:activeFrom` is the canonical era signal, `:startsCareerIn` is subordinate. Era membership
  is **any-overlap** (Allen); a missing `:activeUntil` is an **open** interval (still active),
  handled with `COALESCE`, never a baked current date.
- **Geography (CQ-14):** migrated from `:City`/`:Nation` **subclasses** to the **`gist:Category`
  place-typing** pattern — `:Place :hasPlaceType :City|:Region|:Nation|:Continent`, ordered
  finest→coarsest by transitive `:broaderPlaceType`; roll-up still via transitive `:locatedIn`.
  This matches the genre model and the style-guide "categorize over subclass" rule, and scales
  to arbitrary admin levels as data. Applied by `scripts/migrate_place_typing.py`; CQ-12
  rewritten off the removed classes.
- **History (CQ-15):** `:HistoricalEvent ⊑ gist:HistoricalEvent` with `gist:actualStartDate`/
  `gist:actualEndDate` + `:locatedIn`. "Came of age" is **derived** (birth-date age-window ∩
  event, filtered by origin), not an asserted edge; the age window is a **query parameter**.

## Resolved in v2.3 (Curated work collections — L1)

- **`:WorkCollection` (⊑ `gist:Collection`)** groups related works; membership is the **plain
  relation `:collects`** (mirrors `gist:isMemberOf` but is *not* declared its `owl:inverseOf` —
  that coupling made three gist classes unsatisfiable; `make reason` caught it), atemporal. Kind carried by
  `:CollectionType` (`gist:Category`). Sibling of `:Playlist`/`:MusicChart`; generalises across
  work types, distinct from `:Album` (a release). CQ-16 browses it.
- **Curated ≠ derived:** a `:WorkCollection` is an identity-bearing individual; "works related to
  a seed" stays a query (CQ-4/8/13), nothing stored. Reify a collection only when a human would
  name it as *that one*.
- **Deferred by design — L2/L3 triggers** (the act/state reifications discussed but not built):
  - **L2 (time-indexed membership** — a reified `:CollectionMembership` state with a
    `gist:TimeInterval`): add **when a CQ needs collection *history*** (works entering/leaving over
    time, "what did C contain in year Y"). Until then `:collects` is the current-membership view.
  - **L3 (act of collecting** — a `:CompilationEvent ⊑ gist:Event` with curator + date that
    *establishes* memberships): add **when the provenance waiver is lifted for production**. At that
    point `:collects` becomes derived from open memberships (single source of truth), not asserted.

## Known issues / decisions pending

- CQ-8 (producer lineage) and CQ-11 (member crossover) need richer instance data (Artefact 5).
- **Vocalist instrument gap:** with `:SoloArtist ⊑ :Musician`, vocalists trip the soft
  "a musician should play an instrument" warning (voice isn't modelled). Resolve by modelling
  `:Voice` or relaxing the expectation to "sings or plays."
- Annotation style is still mixed `rdfs:label`/`rdfs:comment` + SKOS; the style guide targets
  SKOS-only `skos:prefLabel`/`skos:definition` — a separate cleanup, not yet scheduled.
- `:locatedIn` is left domain-open (permissive) to span orgs, venues, events, and places.
- **CQ-15 documented approximations** (accepted, not fixed): `:originatesFrom` (birthplace) is a
  *proxy* for formative residence — lossy for emigrant artists; event boundary dates are sourced
  editorial claims, not exact facts; the 15–25 "coming-of-age" window is a culturally-loaded
  query parameter on an Anglo-American-skewed corpus. Revisit with a residence-during-period
  link + provenance before production.
- **`:activeFrom` vs `:startsCareerIn`:** both now express career onset. `:activeFrom` is
  canonical; consider deprecating `:startsCareerIn` or formally subordinating it in a later pass.
- **`:locatedIn` acyclicity:** transitive roll-up assumes a DAG; non-tree geography (metro across
  two states, disputed regions) would break it. A SHACL/`scripts/` acyclicity guard is deferred.
- **SHACL without RDFS inference:** `check_shacl` runs `inference='none'`, so class-targeted
  shapes only match explicitly-typed nodes (subclass instances slip superclass shapes). Pre-
  existing; revisit if constraint coverage needs to follow the hierarchy.

> Living document — update before completing each feature/development task.
