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

## Next action

Finish Artefact 7 outstanding items (`docs/production-readiness.md`). The blocking **decision**
is the **gist namespace drift** (our `gistCore#` IRIs don't resolve against current gist at
`…/ns/ontology/gist/` — 133 dangling refs): migrate / pin a version / drop the import. Then the
mechanical items: `skos:prefLabel` migration, Y-statement formalization, and the carried
follow-ups (vocalist `:Voice`; real-catalog completeness). DL-datatype deviation (`gYear`/`date`)
is waived for the prototype.

> Living document — update before completing each feature/development task.
