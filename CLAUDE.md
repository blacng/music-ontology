# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is an **ontology-engineering project**, not a conventional application. The `uv`/
`pyproject.toml` setup exists only to run the validation tooling — there is no application
code. The actual deliverables are:

1. **`ontology/music_vocabulary_comprehensive.ttl`** — a ~50-class, ~38-property OWL 2 ontology
   of music concepts (artists, works, instruments, genres, relationships), aligned to the
   **gist** upper ontology (`gist:` = `https://w3id.org/semanticarts/ns/ontology/gist/`, current
   v14.1.0, vendored at `ontology/imports/gistCore.ttl` + `ontology/catalog-v001.xml`).
   Its own namespace is `:` = `https://www.somusicvocabulary.org/music#`.
   (`.bak` is the pre-Artefact-4 snapshot.) **This file is the TBox** (model only) since the
   TBox/ABox split — the instance catalogue lives in **`ontology/music_catalog_data.ttl`** (the
   ABox). The split is destined for named graphs in a triplestore (`:…/music/tbox`, `:…/music/abox`,
   `:…/music/shapes`, gist); `scripts/split_tbox_abox.py` performs the split and
   `scripts/load_graphs.py` (`make dataset`) assembles the named-graph dataset for ingest.
2. **`prompt_library/`** — seven reusable LLM prompts implementing the **GRL Workshop**
   methodology (Graph Research Labs, KGC 2026) for using LLMs as pair-modellers in ontology
   engineering. `docs/prompt-library-summary.md` is the canonical index of all seven.

The methodology lifecycle is: **Review → Define → Critique → Assess → Validate → Conform → Release.**

## The prompt library (the core asset)

Each file in `prompt_library/` is a copy-paste-ready, cross-model prompt. When asked to
generate or modify ontology artefacts, **use these prompts as the operating procedure**
rather than improvising:

| File | Role |
|------|------|
| `CQ_generator.md` | Generate 10–12 competency questions (CQs) — the testable contract between ontology and application. Run first, before class definitions. |
| `adversarial_critique_skill.md` | Four-perspective antagonistic critique (sceptic / domain expert / regulator / first-principles). **Run after every generation step — not optional.** |
| `shacl_generator.md` | Generate SHACL NodeShapes/PropertyShapes from class defs + CQs. NodeShapes first. |
| `model_dialogue.md` | LLM as sceptical pair-modeller for fixing a specific audit finding. Always ≥2 fix options with trade-offs; ends with the list of downstream artefacts to regenerate. |
| `test_data_cq_generation.md` | Generate 25–40 synthetic instances + one SPARQL test per CQ + JSON expected-results manifest. |
| `style_guide_system_prompt.md` | The team conventions, meant to be set as the **system prompt** for every ontology-touching conversation. |
| (Production Readiness Checklist) | 12-point release gate — documented in `docs/prompt-library-summary.md` §7. |

## Modelling conventions (enforce these in any TTL change)

These come from `style_guide_system_prompt.md` and are reflected in the existing `.ttl`:

- **Alignment:** Aligned to **current gist v14.1.0** (`gist:` = `…/ns/ontology/gist/`), reused by
  IRI; never redefine upper classes. Current gist has **no** Agent/Concept/PhysicalThing/Place/
  Artifact — use: agents → `gist:Person` (people) / `gist:Organization` (bands); works →
  `gist:Content`; instruments → `gist:Equipment`; key/tempo/time-sig → `gist:Aspect`; places →
  `gist:GeoRegion`. `:MusicalAgent` and `:MusicAward` are domain roots (no gist parent — fine).
  Do **not** reintroduce the old `gistCore#` namespace. Stay single-upper (no BFO/DOLCE mixing).
- **Naming:** Classes = PascalCase singular nouns (`MusicalArtist`, `RockBand`).
  Properties = camelCase verbs/relationships.
- **Annotations:** Classes & properties are **SKOS-only** — `skos:prefLabel` + `skos:definition`
  (Aristotelian form "A `<Genus>` that `<differentia>`."), `skos:scopeNote` for usage notes; do
  **not** add `rdfs:label`/`rdfs:comment` to vocabulary terms. Instances keep `rdfs:label` (data).
  Geographic country class is `:Nation` (`:Country` is the Country-music genre — don't conflate).
- **Type discrimination:** prefer `gist:isCategorizedBy` over subclassing for type variation.
- **Genre (gist:Category pattern, set in Artefact 4):** genres are `gist:Category` instances;
  `:hasGenre rdfs:subPropertyOf gist:isCategorizedBy`; hierarchy via transitive
  `:hasBroaderGenre`; top-level genres typed `:TopLevelGenre`. Do **not** reintroduce
  `skos:broader` for genre hierarchy.
- **Geography:** `:originatesFrom` (agents → `:Place`) and transitive `:locatedIn`
  (orgs/venues/events/place-containment) over `:Place`/`:City`/`:Country`. Not free-text.
- **Time:** use `:bornOn` (`xsd:date`); never store `:hasAge` (time-varying).
- **Vocals:** singing is modelled as `:hasInstrument :Voice` (`:Voice a :VocalInstrument ⊑ :MusicalInstrument`); `MusicianShape` exempts `:Conductor` from the play-an-instrument expectation.
- **Agent hierarchy:** `:MusicalAgent` (⊑ `gist:Agent`) is the shared parent of `:MusicalArtist`
  and `:Musician`; `:SoloArtist` is **both** (`⊑ :MusicalArtist` and `⊑ :Musician`); `:Band` is a
  `:MusicalArtist` only (a group, not a person). `:collaboratesWith` ranges over `:MusicalAgent`;
  `:hasMember` ranges over `:Musician`. Keep this when adding agents.
- **`:exampleInstance`** is a project-local annotation property used throughout the `.ttl` to
  attach illustrative individuals to classes.
- **Forbidden (≈5 ruthless rules):** no `owl:equivalentClass` without authorisation; no
  transitive properties on cyclic data; no annotation-as-object misuse; no untyped literals.
- Every fix must be **paired with a SHACL update** and must enumerate downstream artefacts
  (SHACL, CQs, JSON-LD context, OpenAPI, docs) to regenerate — the list is the deliverable.

## Validation / tooling expectations

No build pipeline exists yet. When validating ontology work, the methodology expects:
- **SHACL** validation via `pyshacl` or TopBraid before commit (never hand-regenerate
  curated SHACL with an LLM).
- **Reasoner** checks (HermiT / Pellet / ELK) for consistency and unsatisfiable classes.
- **SPARQL** CQ tests run against canonical synthetic data.

Both `rdflib` and `pyshacl` are installed. `scripts/validate_fixes.py` does
parse + SPARQL checks; SHACL is validated with `pyshacl`. The `scripts/` dir
holds reusable, reviewable ontology transforms — prefer a deterministic, validated script
over many hand-edits for bulk `.ttl` changes (see `apply_structural_fixes.py`).

## Repository layout

- `ontology/` — `music_vocabulary_comprehensive.ttl` (**TBox** — model), `music_catalog_data.ttl`
  (**ABox** — instances), `music_vocabulary_shapes.ttl` (SHACL), `imports/gistCore.ttl` (vendored gist).
- `scripts/` — transform/validation scripts (`split_tbox_abox.py` splits TBox/ABox; `load_graphs.py`
  assembles the named-graph dataset).
- `dist/` — generated triplestore-ingest artifacts (`music_dataset.trig`, `load.ru`, `graph_manifest.json`); git-ignored, rebuilt by `make dataset`.
- `tests/` — CQ regression suite: `test_data.ttl` (synthetic `:TST_*` fixtures) + `cq_test_manifest.json`; run via `scripts/run_cq_tests.py`.
- `sdd/` — spec-driven-development control docs (`spec.md`, `plan.md`).
- `docs/` — engineering deliverables (`competency-questions.md`, `shacl-report.md`).
- `docker-compose.yml` — two Docker services wired to `make`: `reasoner` (ROBOT/HermiT) and `fuseki` (SPARQL server).
- `prompt_library/`, `docs/prompt-library-summary.md` — local-only (git-ignored).

## Commands

- **Full gate (what CI runs):** `make check` — model checks + CQ tests + SHACL.
- Individually: `make validate` · `make test` · `make shacl` (or the underlying
  `uv run python scripts/{validate_fixes,run_cq_tests,check_shacl}.py`).
- SHACL gate fails only on **Violations**; completeness Warnings are advisory (currently 0/0).
- **ABox coverage (advisory, never fails):** `make coverage` — `make test` loads the synthetic
  `:TST_*` fixtures alongside the catalogue, so a CQ can be green while the real ABox holds nothing
  for it to find. `scripts/cq_coverage.py` re-runs each manifest query over TBox+ABox **only**, with
  the `?seed` left free, and counts how many real individuals can seed it. **Currently 17/17
  answerable** (CQ-15 and CQ-16 thin at one seed each). Run it whenever a CQ or the ABox changes.
- **Fixtures must model data the way the catalogue does.** `tests/test_data.ttl` once asserted *both*
  halves of an `owl:inverseOf` pair (`:performs` **and** `:performedBy`) where the catalogue asserts
  only `:performedBy` — so CQ-11 passed on fixtures and could never answer from real data. **Assert
  the direction the catalogue asserts; never restate an entailment in a fixture**, and never hardcode
  a `:TST_*` IRI back into a query (seeds are a `?seed` variable + a `fixture_seed` field).
- Assemble the named-graph dataset for triplestore ingest: `make dataset` → `dist/`.
- Reasoner consistency (HermiT via containerized ROBOT, needs Docker): `make reason` (merges TBox+ABox).
- Live SPARQL (Docker, needs `make dataset` first): `make serve` starts Fuseki at `http://localhost:3030`
  (dataset `music`); `make fuseki-load` (re)loads the 4 named graphs (idempotent — `DROP ALL` then load);
  `make down` stops it. Both Docker services live in `docker-compose.yml`.
- CI: `.github/workflows/ci.yml` runs two jobs on every push/PR — `make check` (`uv sync --locked`)
  and `make reason` (HermiT via Docker; catches OWL inconsistencies SHACL/SPARQL can't). Fuseki is a
  separate Docker target, not in the CI gate.
- Add a dependency: `uv add <package>` · Sync: `uv sync` · Python pinned to **3.14**.
- Docker (via `docker-compose.yml`) runs the **reasoner** (`make reason`) and **Fuseki** (`make serve`/
  `fuseki-load`); see `docs/production-readiness.md`.

## Working norms specific to this project

- **Adversarial-by-default:** after generating any artefact (CQs, SHACL, class defs, test
  data), run it through `adversarial_critique_skill.md` before considering it done.
- **LLMs are pair-modellers, not solvers:** ask clarifying questions before proposing fixes,
  offer ≥2 options with explicit trade-offs, and push back on weaker choices rather than
  agreeing. The `model_dialogue.md` prompt encodes this — follow it for fix discussions.
