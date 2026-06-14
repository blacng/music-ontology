# SHACL Validation Report

**Artefact:** 3 (SHACL Generation) · GRL Workshop methodology
**Shapes:** `ontology/music_vocabulary_shapes.ttl`
**Data:** `ontology/music_vocabulary_comprehensive.ttl`
**Tool:** pyshacl 0.31.0 (`meta_shacl=True` — shapes themselves validate)
**Result (v2.1.0):** `conforms=True` — **0 Violations, 0 Warnings** ✅ (the catalog was completed)

Reproduce: `uv run pyshacl -s ontology/music_vocabulary_shapes.ttl -m -f human ontology/music_vocabulary_comprehensive.ttl`

## Violations — resolved ✅

The initial run surfaced **2 Violations**, both tracing to one root cause: the
`:Musician` ↔ `:MusicalArtist` boundary was incoherent (parallel `gist:Agent` branches, but
individuals span both — McCartney is a solo artist *and* a Beatle; Lennon is a band musician
*and* a collaborator).

**Resolved structurally (Artefact 4 loop-back, option B):**
- introduced **`:MusicalAgent`** (⊑ `gist:Agent`) as the shared parent of `:MusicalArtist` and `:Musician`;
- **`:SoloArtist` ⊑ `:Musician`** (a solo performer is a person who sings/plays) — so a solo-artist band member satisfies `:hasMember`'s `:Musician` range;
- **`:collaboratesWith`** domain/range widened to `:MusicalAgent` — bands *and* individual musicians can collaborate.

This fixes the *cause* via the class hierarchy rather than patching individuals, so future band
members / collaborators won't re-break it. Re-validation: **0 Violations**.

## Completeness warnings — resolved in v2.1.0 ✅

The v2.0.0 run had **19 completeness Warnings** on the illustrative catalog (soft `sh:Warning`
expectations, not errors). All cleared in v2.1.0 by completing the catalog with **real data**:

| # (was) | Expectation (CQ) | How resolved |
|---------|------------------|--------------|
| 7 | A band should have ≥1 member (CQ-11) | added real line-ups for Coldplay, Nirvana, Led Zeppelin, Radiohead, the Rolling Stones, and a principal each for the two orchestras |
| 7 | A musician should play ≥1 instrument (CQ-5) | 5 vocalists (Beyoncé, Bowie, Kanye, Jackson, Sade) → `:hasInstrument :Voice`; the 2 conductors (Karajan, Bernstein) are exempted by the shape |
| 5 | A song/album should state its performer | added the performing bands — Queen, Deep Purple, Pink Floyd (+ members) — and John Lennon / Julie London |

**`:Voice` modelling (A3):** added `:VocalInstrument ⊑ :MusicalInstrument` and the `:Voice`
individual (with the `:MusicalInstrument` definition broadened to "a device, or the human voice");
the `MusicianShape` now reads "plays an instrument — singing counts via `:Voice` — **unless a
conductor**" (an `sh:or`).

## Shape inventory

10 NodeShapes (MusicalArtist, Band, Musician, Song, Album, Composition, MusicGenre,
TopLevelGenre, City) + 1 SHACL-SPARQL constraint (chart consistency, CQ-10). Type-checks are
`sh:Violation`; cardinality-completeness is `sh:Warning`. After the Artefact-4 fix,
`:collaboratesWith` checks against `:MusicalAgent`. All type/structural constraints pass.
