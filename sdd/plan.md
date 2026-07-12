# Plan — Ontology Engineering Lifecycle

Methodology: GRL Workshop (KGC 2026). Lifecycle arc:
**Review → Define → Critique → Assess → Validate → Conform → Release.**
Each generation step is followed by adversarial critique (Artefact 2) — not optional.

## Status

| # | Phase / Artefact | Status | Output |
|---|------------------|--------|--------|
| 1 | **CQ Generation** (Artefact 1) | ✅ Done | `docs/competency-questions.md` v1 |
| 2 | **Adversarial Critique** of CQs (Artefact 2) | ✅ Done | 5 ranked findings; 2 hard blockers |
| 3 | CQ revision per critique | ✅ Done | `docs/competency-questions.md` **v2** |
| 4 | **Modeller Dialogue** — structural fixes (Artefact 4) | ✅ Done | genre→gist:Category (`:hasBroaderGenre`+`:TopLevelGenre`); `:originatesFrom`→`:Place`+`:locatedIn` roll-up; `:hasAge`→`:bornOn`, drop `:hasHeight`. Applied via `scripts/apply_structural_fixes.py`, verified by `scripts/validate_fixes.py` |
| 5 | **SHACL Generation** (Artefact 3) | ✅ Done | `ontology/music_vocabulary_shapes.ttl` + `docs/shacl-report.md`; pyshacl-validated |
| 5b | **Modeller Dialogue loop-back** (Artefact 4) | ✅ Done | `:Musician`↔`:MusicalArtist` boundary fixed via `:MusicalAgent` superclass + `:SoloArtist ⊑ :Musician` + `:collaboratesWith`→`:MusicalAgent`; **0 Violations** |
| 6 | **Test Data + CQ Tests** (Artefact 5) | ✅ Done | `tests/test_data.ttl` + `tests/cq_test_manifest.json` + `scripts/run_cq_tests.py`; **12/12 CQs pass**. Caught & fixed CQ-2's non-standard `{1,2}` path quantifier |
| 7 | **Production Readiness** (Artefact 7) | 🔄 Near done | `docs/production-readiness.md` — **10 green**, 1 waived (item 4 datatypes), 1 sign-off (item 12). gist migrated; SKOS-only labels (item 6); Y-statements `sdd/decisions.md` (item 9); reasoner consistent |
| 8 | **v2.2 — Foundational time / geography / history** | ✅ Done | CQ-13 (activity-interval era overlap), CQ-14 (multi-level geography), CQ-15 (came-of-age during `:HistoricalEvent`, derived). Geography migrated to `gist:Category` place-typing (`scripts/migrate_place_typing.py`); new terms `:activeFrom`/`:activeUntil`, `:PlaceType`/`:hasPlaceType`/`:broaderPlaceType`, `:HistoricalEvent`; SHACL + tests + docs updated. Pressure-tested via `model_dialogue.md` + `adversarial_critique_skill.md`. **16/16 CQs pass, SHACL 0/0** |
| 9 | **v2.3 — Curated work collections (L1)** | ✅ Done | CQ-16 (browse a `:WorkCollection ⊑ gist:Collection` via plain relation `:collects`; kind via `:CollectionType` `gist:Category`). `:collects` mirrors `gist:isMemberOf` but is **not** its `owl:inverseOf` — that coupling leaked its domain onto the shared upper property and made 3 gist classes unsatisfiable (`make reason` caught it). Act/state reifications (event, time-indexed membership) deferred with triggers in `sdd/spec.md`. **17/17 CQs pass, SHACL 0/0, reasoner consistent** |

> **Sequencing rationale:** structural fixes precede SHACL and test data because both sit
> downstream of the schema (regeneration discipline) — fix the schema → constrain it →
> populate it. Expect one small loop back into the dialogue when SHACL generation surfaces
> additional cardinality constraints.

## Decisions log

- **Use case:** discovery / recommendation (drives CQ content; stays RDF/OWL, not LPG).
- **System maturity:** **research prototype** — rights/provenance/bias-audit CQs waived.
- **Testability stance:** full intended scope, each CQ has a measurable pass condition + flag.
- **Genre traversal:** top-level genre = depth-1 child of `:MusicGenre`; semantic fix
  (`skos:broaderTransitive` / `:TopLevelGenre` / `:hasSubgenre`) deferred to Artefact 4.
- **gist alignment (2026-06):** the original `gistCore#` alignment was **invalid** (matched no gist
  release; Agent/Concept/PhysicalThing exist in no gist version). **Migrated to current gist
  v14.1.0** (path (a)) — prefix `…/ns/ontology/gist/`, vendored + imported locally, classes
  re-parented (agents→Person/Organization, works→Content, instruments→Equipment, features→Aspect,
  places→GeoRegion; `:MusicalAgent`/`:MusicAward` are domain roots). **BFO/DOLCE rejected** — mixing
  upper ontologies is an anti-pattern and gist covers every concept. Stay single-upper.
- **Infrastructure (2026-06):** adopted a `Makefile` (thin task runner over `uv`) + GitHub
  Actions CI (`make check` on every push/PR) as the validation gate. **Docker deliberately
  deferred** — the stack is pure-Python with no deploy target, and `uv` + the lockfile already
  give reproducibility, so a container would be ceremony now. **Revisit Docker when Artefact 7
  introduces a Java reasoner (HermiT/Pellet/ELK)** or a triplestore (Fuseki/GraphDB) — that's
  where containerising the JVM toolchain solves a real problem.

## Next action

**v2.3** shipped and fully released: curated **work collections** (L1) — `:WorkCollection ⊑
gist:Collection` with the plain relation `:collects` (mirrors `gist:isMemberOf`, not its
`owl:inverseOf` — see the v2.3 row) and a `:CollectionType` `gist:Category` facet; CQ-16 browses it.
**17/17 CQs, SHACL 0/0, reasoner consistent**; tagged **v2.3.0** + GitHub release (Latest); CHANGELOG,
README, spec/plan all current. The act-of-collecting event and time-indexed membership are deferred
with explicit triggers in `sdd/spec.md`. Standing deferred follow-ups in `sdd/spec.md` →
Resolved-in-v2.3 + Known issues (work-collection L2/L3; CQ-15 residence-proxy + provenance;
`:locatedIn` acyclicity guard; `:startsCareerIn` deprecation).

## Release checklist

Lesson from v2.3.0: README and CHANGELOG trailed the feature PR and had to be backfilled (#20, #21).
**The doc surfaces are part of the feature, not a later chore — land them in the same PR.** For any
change that touches the model or the CQ set:

**In the feature PR (before merge):**
- [ ] `owl:versionInfo` + `owl:versionIRI` bumped in the TBox.
- [ ] `CHANGELOG.md` — new `[x.y.z]` entry (Added / Fixed / Scope-deferred).
- [ ] `README.md` — maturity line, release link, **class/property counts**, **CQ count** (+ `make test` line), journey + model-at-a-glance **mermaid diagrams** (validate them), Status table row + release chain.
- [ ] `docs/competency-questions.md` (new CQs + changelog), `sdd/spec.md` + `sdd/plan.md`.
- [ ] SHACL + `tests/` regenerated; `make check` **and** `make reason` green locally.

**After merge to `main` (release step):**
- [ ] Annotated tag `git tag -a vX.Y.Z` + push.
- [ ] `gh release create vX.Y.Z` with notes + `vPREV...vX.Y.Z` compare link; verify it shows **Latest**.
- [ ] Update the auto-memory lifecycle status note (released-through version).

> Living document — update before completing each feature/development task.
