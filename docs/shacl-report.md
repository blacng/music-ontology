# SHACL Validation Report

**Artefact:** 3 (SHACL Generation) · GRL Workshop methodology
**Shapes:** `music_ontology/ontology/music_vocabulary_shapes.ttl`
**Data:** `music_ontology/ontology/music_vocabulary_comprehensive.ttl`
**Tool:** pyshacl 0.31.0 (`meta_shacl=True` — shapes themselves validate)
**Result:** `conforms=False` — **0 Violations, 19 Warnings** (Warnings are completeness only)

Reproduce: `uv run pyshacl -s music_ontology/ontology/music_vocabulary_shapes.ttl -m -f human music_ontology/ontology/music_vocabulary_comprehensive.ttl`

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

## Warnings (completeness — test-data targets for Artefact 5)

Not errors; they mark where sparse prototype data won't yet satisfy a recommender.

| # | Expectation (CQ) | Nodes |
|---|------------------|-------|
| 7 | A band should have ≥1 member (CQ-11) | BerlinPhilharmonic, Coldplay, LedZeppelin, LondonSymphonyOrchestra, Nirvana, Radiohead, TheRollingStones |
| 7 | A musician should play ≥1 instrument (CQ-5) | BeyonceKnowles, DavidBowie, HerbertVonKarajan, KanyeWest, LeonardBernstein, MichaelJackson, SadeAdu |
| 4 | A song should state its performer | BohemianRhapsody, CryMeARiver, ImagineSong, SmokeOnTheWater |
| 1 | An album should state its performer | TheDarkSideOfTheMoon |

**Note on the instrument warnings:** 5 of the 7 (Beyoncé, Bowie, Kanye, Jackson, Sade) are new
— a *consequence* of `:SoloArtist ⊑ :Musician`. They're vocalists, and voice isn't modelled as
an instrument. Two clean ways to clear them later: model a `:Voice` (the `:MusicalInstrument`
definition — "a device constructed for making music" — doesn't fit voice well, so this needs
thought), or relax the expectation to "sings **or** plays." Left as a documented follow-up.

## Shape inventory

10 NodeShapes (MusicalArtist, Band, Musician, Song, Album, Composition, MusicGenre,
TopLevelGenre, City) + 1 SHACL-SPARQL constraint (chart consistency, CQ-10). Type-checks are
`sh:Violation`; cardinality-completeness is `sh:Warning`. After the Artefact-4 fix,
`:collaboratesWith` checks against `:MusicalAgent`. All type/structural constraints pass.
