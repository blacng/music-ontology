# SHACL Validation Report

**Artefact:** 3 (SHACL Generation) · GRL Workshop methodology
**Shapes:** `ontology/music_vocabulary_shapes.ttl`
**Data:** `ontology/music_catalog_data.ttl` (ABox) · **TBox** supplied as `ont_graph`
**Tool:** pyshacl 0.31.0 (`meta_shacl=True` — shapes themselves validate) · **`inference='rdfs'`**
**Result (v2.4.0):** **0 Violations, 0 Warnings** ✅ — now under RDFS inference

Reproduce: `make shacl` (or `uv run python scripts/check_shacl.py`).

> **v2.4.0 — inference is on.** Validation previously ran with pyshacl's default `inference='none'`,
> so `sh:targetClass` matched only *explicitly*-typed nodes: an instance asserted as `:SoloArtist`
> was never checked by `:MusicalArtistShape`. With `inference='rdfs'`, subclass and domain/range
> entailments are materialised first, so shapes see the types the model implies. Full `owlrl` closure
> is **not** used — it puns class IRIs as individuals and raised spurious Violations on `:City` and
> `:Region`. Enabling inference immediately exposed a real bug; see *The `rdfs:domain` trap* below.

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

## The `rdfs:domain` trap (v2.4.0)

Turning inference on immediately surfaced a bug that `inference='none'` had been hiding.

`:startsCareerIn`, `:activeFrom` and `:activeUntil` carried `rdfs:domain :MusicalArtist`. In RDFS a
domain is **not** a constraint ("only musical artists may have this property") — it is an *inference
rule*: **"anything with this property *is* a `:MusicalArtist`."** Producers, conductors and
non-artist musicians all have career years, so RDFS silently retyped them. `:GeorgeMartin`,
`:QuincyJones` and `:RickRubin` became musical artists and then tripped *"a musical artist should
have at least one genre"* — three Warnings whose real cause was a bad axiom, not missing data.

**The data was right; the axiom was wrong.** The three domains were dropped, and the constraint
reading now lives where constraints belong — in SHACL, as `:CareerOnsetShape`. Result: **0
Violations, 0 Warnings**, the Warnings gone because the cause was fixed rather than suppressed.

Four properties still carry `rdfs:domain :MusicalArtist` (`:isSignedTo`, `:speaksLanguage`,
`:nationalityOf`, `:performs`). None mistypes anything in the current ABox, so they were left alone —
but the trap is armed; see *Known issues* in `sdd/spec.md` before adding data that would trip it.

## Shape inventory

**15 NodeShapes** — MusicalArtist, Band, Musician, Song, Album, Composition, MusicGenre,
TopLevelGenre, Place, CityRollup, PlaceType, HistoricalEvent, WorkCollection, **CareerOnset** (new in
v2.4.0), ChartConsistency — plus **4 SHACL-SPARQL constraints** (incl. chart consistency, CQ-10).

Type-checks are `sh:Violation`; cardinality-completeness is `sh:Warning`. After the Artefact-4 fix,
`:collaboratesWith` checks against `:MusicalAgent`. All type/structural constraints pass.

`:CareerOnsetShape` targets `sh:targetSubjectsOf` the three career-onset properties: values must be a
single `xsd:gYear`, and the subject must be a `:MusicalAgent` or a `:MusicProducer`. Verified with a
negative test — a `:RecordLabel` claiming a career onset is rejected, as is a non-`gYear` `activeFrom`.
