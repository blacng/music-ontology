# Music Ontology

[![CI](https://github.com/blacng/music-ontology/actions/workflows/ci.yml/badge.svg)](https://github.com/blacng/music-ontology/actions/workflows/ci.yml)

A **gist-aligned OWL 2 ontology** of the popular- and classical-music domain, built to power a
**music discovery / recommendation** application — and, just as importantly, a worked example of
the **GRL Workshop methodology** (Graph Research Labs, KGC 2026) for engineering ontologies with
LLMs as disciplined pair-modellers.

- **Namespace:** `:` → `https://www.somusicvocabulary.org/music#`
- **Upper ontology:** **gist v14.1.0** — `gist:` → `https://w3id.org/semanticarts/ns/ontology/gist/` (vendored at `ontology/imports/`, reasoner-validated)
- **Scope:** content-based candidate generation (no user/interaction/rating is modelled)
- **Maturity:** research prototype · **released v2.1.0** (SHACL fully conforms)

---

## The approach

Rather than hand-authoring the ontology and hoping it's right, the model is driven through a
disciplined lifecycle: **every requirement is a testable competency question, every generated
artefact is adversarially critiqued, every fix enumerates its downstream regenerations, and the
result is validated by machine (`rdflib`, `pyshacl`, and a HermiT reasoner) rather than by assertion.**

### High-level — the methodology arc

```mermaid
flowchart LR
  CQ[CQ Generation] --> CRIT[Adversarial Critique]
  CRIT --> FIX[Modeller Dialogue / Fixes]
  FIX --> SHACL[SHACL Generation]
  SHACL --> TEST[Test Data + CQ Tests]
  TEST --> REL[Production Readiness]
  CRIT -. run after every generation .-> CQ
```

### Detailed — the journey so far

```mermaid
flowchart TB
  cq1[CQ v1 · 12 discovery CQs] --> crit[Critique · 5 findings, 2 blockers]
  crit --> cq2[CQ v2/v3 · measurable + genre-root fix]
  cq2 --> dlg{Modeller Dialogue · structural fixes}
  dlg -->|genre| g[gist:Category · hasBroaderGenre · TopLevelGenre]
  dlg -->|geography| pl[structured Place · locatedIn roll-up]
  dlg -->|time| bd[bornOn replaces hasAge]
  g --> ttl[(ontology · post-fix)]
  pl --> ttl
  bd --> ttl
  ttl --> shacl[SHACL shapes]
  shacl --> rep[pyshacl · 2 Violations surfaced]
  rep --> dlg2[loop-back · MusicalAgent superclass · 0 Violations]
  dlg2 --> td[Test Data · 12/12 CQ tests]
  td --> gist[gist v14.1.0 re-align · reasoner-validated]
  gist --> skos[SKOS-only labels · Y-statements]
  skos --> pr[Production Readiness · 10/12 green]
  pr --> rel([Released v2.0.0])
```

Key decision points along the way:
- **RDF over LPG** — the discovery use case shapes *which questions* we ask, not the storage tech;
  the model stays RDF/OWL (reasoning, SHACL, SPARQL, interoperability).
- **Genres as `gist:Category`, not OWL subclasses** — genre is a cross-cutting facet over artists,
  albums, and songs; subclassing it wouldn't deliver transitivity through `:hasGenre` and would
  fight the team style guide. The chosen pattern gives sound transitive traversal via the
  `owl:TransitiveProperty` `:hasBroaderGenre`, with top genres marked `:TopLevelGenre`.
- **Structure beats free text** — geography became a `:Place`/`:City`/`:Nation` graph with
  transitive `:locatedIn` (enabling "artists from England"), and the time-varying `:hasAge` became
  a stable `:bornOn` date.

---

## The model at a glance

```mermaid
graph LR
  MusicalArtist & Musician -->|subClassOf| MusicalAgent
  SoloArtist -->|subClassOf| MusicalArtist
  SoloArtist -->|subClassOf| Musician
  Band -->|subClassOf| MusicalArtist
  MusicalArtist -->|hasGenre| MusicGenre
  MusicGenre -->|hasBroaderGenre*| MusicGenre
  TopLevelGenre -->|subClassOf| MusicGenre
  Band -->|hasMember| Musician
  Musician -->|hasInstrument| MusicalInstrument
  MusicalArtist -->|isSignedTo| RecordLabel
  MusicalAgent -->|collaboratesWith| MusicalAgent
  MusicalArtist -->|originatesFrom| Place
  City -->|locatedIn*| Nation
  Song & Album -->|performedBy| MusicalArtist
  Album -->|producedBy| MusicProducer
  Album -->|hasTrack| Song
  Song -->|writtenBy| Lyricist
  Song -->|chartedIn| MusicChart
  Composition -->|composedBy| Composer
```

~53 classes / ~38 properties across agents, works, a genre taxonomy, instruments,
events/venues, awards/charts, places, and musical features (key, tempo, time signature). Agents
re-parent to `gist:Person`/`gist:Organization`, works to `gist:Content`, instruments to
`gist:Equipment`, features to `gist:Aspect`, places to `gist:GeoRegion`.

---

## Repository layout

| Path | Contents |
|------|----------|
| `ontology/` | `music_vocabulary_comprehensive.ttl` (model + instances), `music_vocabulary_shapes.ttl` (SHACL), `imports/gistCore.ttl` (vendored gist v14.1.0) + `catalog-v001.xml` |
| `scripts/` | transform + validation scripts (`validate_fixes`, `run_cq_tests`, `check_shacl`, `migrate_*`) |
| `tests/` | CQ regression suite: `test_data.ttl` (synthetic fixtures) + `cq_test_manifest.json` |
| `sdd/` | spec-driven-development control docs: `spec.md`, `plan.md`, `decisions.md` (Y-statements) |
| `docs/` | engineering deliverables: `competency-questions.md`, `shacl-report.md`, `production-readiness.md` |
| `CHANGELOG.md`, `CLAUDE.md` | release notes; guidance for Claude Code in this repo |
| `prompt_library/` *(local-only)* | the seven GRL Workshop prompts — git-ignored |

---

## Running the validation

Requires [`uv`](https://docs.astral.sh/uv/) (Python pinned to 3.14) and `make`.

```bash
make install   # uv sync
make check     # the full gate: model checks + CQ tests + SHACL (run by CI on every PR)

# or individually:
make validate  # parse + SPARQL (genre traversal, place roll-up, …)
make test      # CQ regression suite (12/12)
make shacl     # SHACL conformance — fails only on Violations; Warnings are advisory
make reason    # HermiT consistency check, gist imported (needs Docker; not in the CI gate)
```

`make check` is exactly what GitHub Actions runs on every push and pull request. The one-shot
transforms that produced the current model are preserved and re-runnable in `scripts/`
(`apply_structural_fixes.py`, `migrate_gist.py`, `migrate_skos_labels.py`).

---

## Status

Lifecycle complete — **released [v2.0.0](https://github.com/blacng/music-ontology/releases/tag/v2.0.0)**.

| Phase | State |
|-------|-------|
| CQ generation → critique → revision (v4) | ✅ done |
| Modeller Dialogue — structural fixes + `:MusicalAgent` boundary | ✅ done — **0 Violations** |
| SHACL generation | ✅ done — `docs/shacl-report.md` |
| Test data + CQ tests | ✅ done — **12/12 CQs pass** |
| gist v14.1.0 re-alignment | ✅ done — vendored, reasoner-validated |
| SKOS-only labels + Y-statements | ✅ done — `sdd/decisions.md` |
| Production readiness (12-pt gate) | ✅ **10/12 green** (item 4 waived, item 12 = PR sign-off) |
| Vocals + catalog completeness (v2.1) | ✅ done — SHACL **fully conforms (0/0)** |
| **Release** | ✅ **v2.0.0** → **v2.1.0** |

See [`sdd/plan.md`](sdd/plan.md) for the live lifecycle tracker and [`sdd/spec.md`](sdd/spec.md)
for the specification.
