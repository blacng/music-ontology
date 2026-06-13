# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is an **ontology-engineering project**, not a conventional application. The `uv`/
`pyproject.toml` setup exists only to run the validation tooling — there is no application
code. The actual deliverables are:

1. **`ontology/music_vocabulary_comprehensive.ttl`** — a ~50-class, ~38-property OWL 2 ontology
   of music concepts (artists, works, instruments, genres, relationships), aligned to the
   **gist** upper ontology (`gist:` = `https://w3id.org/semanticarts/ontology/gistCore#`).
   Its own namespace is `:` = `https://www.somusicvocabulary.org/music#`.
   (`.bak` is the pre-Artefact-4 snapshot.)
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

- **Alignment:** Reuse gist classes by IRI (`rdfs:subClassOf gist:Agent`); never redefine
  upper-ontology classes. Check for an existing gist class before creating a new one.
- **Naming:** Classes = PascalCase singular nouns (`MusicalArtist`, `RockBand`).
  Properties = camelCase verbs/relationships.
- **Annotations:** Every class needs `skos:prefLabel` + `skos:definition`, written in
  Aristotelian form ("A `<Genus>` that `<differentia>`."). Note: the current `.ttl` mixes
  `rdfs:label`/`rdfs:comment` with SKOS — the style guide's target is SKOS-only.
- **Type discrimination:** prefer `gist:isCategorizedBy` over subclassing for type variation.
- **Genre (gist:Category pattern, set in Artefact 4):** genres are `gist:Category` instances;
  `:hasGenre rdfs:subPropertyOf gist:isCategorizedBy`; hierarchy via transitive
  `:hasBroaderGenre`; top-level genres typed `:TopLevelGenre`. Do **not** reintroduce
  `skos:broader` for genre hierarchy.
- **Geography:** `:originatesFrom` (agents → `:Place`) and transitive `:locatedIn`
  (orgs/venues/events/place-containment) over `:Place`/`:City`/`:Country`. Not free-text.
- **Time:** use `:bornOn` (`xsd:date`); never store `:hasAge` (time-varying).
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

- `ontology/` — the `*.ttl` files (model + instances, and SHACL shapes).
- `scripts/` — transform/validation scripts.
- `sdd/` — spec-driven-development control docs (`spec.md`, `plan.md`).
- `docs/` — engineering deliverables (`competency-questions.md`, `shacl-report.md`).
- `prompt_library/`, `docs/prompt-library-summary.md` — local-only (git-ignored).

## Commands

- Validate model (parse + SPARQL): `uv run python scripts/validate_fixes.py`
- Validate SHACL: `uv run pyshacl -s ontology/music_vocabulary_shapes.ttl -m -f human ontology/music_vocabulary_comprehensive.ttl`
- Add a dependency: `uv add <package>` · Sync: `uv sync`
- Python pinned to **3.14** (`.python-version`, `requires-python = ">=3.14"`)

## Working norms specific to this project

- **Adversarial-by-default:** after generating any artefact (CQs, SHACL, class defs, test
  data), run it through `adversarial_critique_skill.md` before considering it done.
- **LLMs are pair-modellers, not solvers:** ask clarifying questions before proposing fixes,
  offer ≥2 options with explicit trade-offs, and push back on weaker choices rather than
  agreeing. The `model_dialogue.md` prompt encodes this — follow it for fix discussions.
