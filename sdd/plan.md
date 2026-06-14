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
| 7 | **Production Readiness** (Artefact 7) | 🔄 In progress | `docs/production-readiness.md` — 6 green, 4 partial, 1 decision, 1 sign-off. Containerized HermiT (`make reason`): **consistent, 0 unsatisfiable**. Added `owl:versionIRI`, `CHANGELOG.md`, declared `skos:related` |

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
- **Infrastructure (2026-06):** adopted a `Makefile` (thin task runner over `uv`) + GitHub
  Actions CI (`make check` on every push/PR) as the validation gate. **Docker deliberately
  deferred** — the stack is pure-Python with no deploy target, and `uv` + the lockfile already
  give reproducibility, so a container would be ceremony now. **Revisit Docker when Artefact 7
  introduces a Java reasoner (HermiT/Pellet/ELK)** or a triplestore (Fuseki/GraphDB) — that's
  where containerising the JVM toolchain solves a real problem.

## Deferred / tech debt

- **gist re-alignment (deferred 2026-06-13; decision: path (b) "for now").** The reasoner audit
  showed the gist alignment was **never valid**, not merely outdated:
  - our `gist:` prefix `…/ontology/gistCore#` matches **no** gist release (v7–v11 use
    `…/ontologies.semanticarts.com/gist/`; v12+ use `…/ns/ontology/gist/`);
  - of our 10 referenced terms, **`Agent`, `Concept`, `PhysicalThing` exist in no gist version**
    (FOAF/SKOS/BFO terms mis-prefixed `gist:`); the other 7 exist in v11.1.0;
  - current gist (v14) **dropped** Agent/Place/Artifact/Concept/PhysicalThing, so moving forward is
    a re-modelling, not a swap.
  - So a clean "pin the matching version" is **impossible** — there is no single version that
    resolves all references. Holding state: documented + deferred (`owl:imports` left as-is unless
    decided otherwise; ontology stays consistent, dangling refs are known/accepted tech debt).
  - **Future task — re-align to current gist**, proposed mapping: `MusicalInstrument`→`gist:Equipment`,
    `MusicalWork`→`gist:Content`, `MusicChart`→`gist:Collection`, `MusicKey`/`TimeSignature`/`Tempo`→
    `gist:Aspect`, `Place`/`City`/`Country`→`gist:GeoRegion`, `Venue`→`gist:Building`, `MusicalAgent`
    (+`Lyricist`,`MusicProducer`)→domain root, `MusicAward`→domain root or `gist:Category`; keep 1:1:
    Category, Collection, Event, isCategorizedBy, Organization. See `docs/production-readiness.md` §2/§5.

## Next action

Finish the remaining Artefact 7 items that *are* actionable now: `skos:prefLabel` migration (item 6),
Y-statement formalization (item 9), and the carried follow-ups (vocalist `:Voice`; real-catalog
completeness). DL-datatype deviation (`gYear`/`date`) and the gist re-alignment are **deferred** (above).

> Living document — update before completing each feature/development task.
