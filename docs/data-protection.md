# Data protection

`ontology/music_catalog_data.ttl` contains biographical facts about **real, named, living people**.
That makes parts of this repository personal data, and it should be treated as such rather than as
"just an illustrative catalogue".

## What personal data is held

| Predicate | Held for | Notes |
|---|---|---|
| `:bornOn` | 9 individuals | **Year only** (`xsd:gYear`) since v3.0.0 — see minimisation below |
| `:originatesFrom` | most agents | City/place of origin |
| `:speaksLanguage` | declared in the TBox | **no ABox assertions** |
| `:nationalityOf` | declared in the TBox | **no ABox assertions** |

Living individuals in the catalogue include Bob Dylan, Paul McCartney, Beyoncé Knowles, Taylor Swift,
Kanye West, Sade Adu and Rick Rubin.

## Data minimisation (GDPR Art. 5(1)(c))

`:bornOn` was `xsd:date` — nine **full birth dates**. Exactly one consumer in the entire repository
reads it: **CQ-15**, and it only ever took `YEAR(?b)`.

Nine exact dates of birth were being stored to satisfy a requirement for nine integers. As of v3.0.0
`:bornOn` is **`xsd:gYear`**, and `:BornOnShape`/`:MusicalArtistShape`/`:MusicalPersonShape` enforce
it. CQ-15 reads the year with `xsd:integer(STR(?b))` (SPARQL's `YEAR()` accepts only
`xsd:date`/`xsd:dateTime`).

**Do not widen `:bornOn` back to a date.** No competency question needs one. The `skos:scopeNote` on
the property says so, and the SHACL shape will reject it.

## What is missing, and what that means

This catalogue has **no statement-level provenance**. There is no `dct:source`, no
`prov:wasDerivedFrom`, no assertion date, no asserter, no confidence. If a fact here is wrong, there
is no mechanism to determine where it came from.

Consequences, stated plainly:

- **Do not use this to make decisions about a person.**
- **Do not use this for rights or royalty administration.** A credit that misroutes a payment cannot
  be traced to a source. The credit properties (`:producedBy`, `:writtenBy`, `:composedBy`,
  `:performedBy`) are the ones money moves on, and they are exactly the ones with no provenance.
- There is no Art. 30 record of processing, no documented lawful basis, no retention period, and no
  erasure procedure.

These are **known, accepted gaps** for a demonstration ontology, disclosed rather than hidden. They
are also precisely what would block certification for any regulated use. See `sdd/decisions.md` AD-7
and AD-14.

## If this catalogue ever leaves demonstration use

The minimum to close before it does:

1. **Provenance.** Per-graph `prov:wasDerivedFrom` / `dct:source` / `prov:generatedAtTime` at
   minimum; reified credits with per-statement sources for anything rights-bearing.
2. **Lawful basis.** A legitimate-interest assessment for biographical facts about public figures,
   plus a controller, a retention period, and an erasure path.
3. **Erasure.** A mechanism to remove an individual on request — today that is a hand-edit.
