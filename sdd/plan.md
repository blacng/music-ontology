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
| 7 | **Production Readiness** (Artefact 7) | ⏳ Next | 12-point gate |

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

Artefact 7 — Production Readiness (12-point gate): CQ tests pass ✅, reasoner check (consistency /
unsatisfiable classes), SHACL on canonical data, OWL profile declaration, `owl:versionIRI`,
change-log. Open follow-ups: (a) the 5 vocalist "no instrument" warnings (model `:Voice` or relax
to "sings or plays"); (b) completing the real catalog so its 19 SHACL completeness Warnings clear
(distinct from the synthetic test fixture).

> Living document — update before completing each feature/development task.
