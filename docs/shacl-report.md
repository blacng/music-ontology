# SHACL Validation Report

**Artefact:** 3 (SHACL Generation) · GRL Workshop methodology
**Shapes:** `ontology/music_vocabulary_shapes.ttl`
**Data:** `ontology/music_vocabulary_comprehensive.ttl`
**Tool:** pyshacl 0.31.0 (`meta_shacl=True` — shapes themselves validate)
**Result:** `conforms=False` — 2 Violations, 14 Warnings

Reproduce: `uv run pyshacl -s ontology/music_vocabulary_shapes.ttl -m -f human ontology/music_vocabulary_comprehensive.ttl`

## Violations (must fix — genuine inconsistencies)

Both violations share **one root cause: the `:Musician` ↔ `:MusicalArtist` boundary is
incoherent.** The ontology models them as parallel branches of `gist:Agent`, but real
individuals span both.

| Focus | Path | Why |
|-------|------|-----|
| `:TheBeatles` | `:hasMember` | member `:PaulMcCartney` is typed `:SoloArtist`/`:Lyricist`, **not** `:Musician` (the declared range of `:hasMember`) |
| `:PaulMcCartney` | `:collaboratesWith` | value `:JohnLennon` is typed `:Musician`, **not** `:MusicalArtist` (the declared range of `:collaboratesWith`) |

→ **Requires a modelling decision (loop back to Artefact 4).** Candidate resolutions:
- **(C) Multi-type the individuals** — also type McCartney `:Musician`, Lennon `:SoloArtist`.
  Simplest; acknowledges these people genuinely are both. *(Recommended for a prototype.)*
- **(B) Common superclass / widen ranges** — introduce a shared `gist:Agent`-level person
  class as the range of `:hasMember`/`:collaboratesWith`. More invasive.
- **(A) Re-parent the hierarchy** — e.g. `:SoloArtist ⊑ :Musician`. Rejected: a `:Band` is a
  `:MusicalArtist` but is **not** a `:Musician` (a band is not a person), so this breaks bands.

## Warnings (completeness — test-data targets for Artefact 5)

These are not errors; they mark where sparse prototype data won't yet satisfy a recommender.

| # | Expectation (CQ) | Nodes |
|---|------------------|-------|
| 7 | A band should have ≥1 member (CQ-11) | BerlinPhilharmonic, Coldplay, LedZeppelin, LondonSymphonyOrchestra, Nirvana, Radiohead, TheRollingStones |
| 4 | A song should state its performer | BohemianRhapsody, CryMeARiver, ImagineSong, SmokeOnTheWater |
| 2 | A musician should play ≥1 instrument (CQ-5) | HerbertVonKarajan, LeonardBernstein |
| 1 | An album should state its performer | TheDarkSideOfTheMoon |

## Shape inventory

10 NodeShapes (MusicalArtist, Band, Musician, Song, Album, Composition, MusicGenre,
TopLevelGenre, City) + 1 SHACL-SPARQL constraint (chart consistency, CQ-10). Type-checks are
`sh:Violation`; cardinality-completeness is `sh:Warning`. The CQ-10 SPARQL constraint and all
genre/place type constraints currently pass.
