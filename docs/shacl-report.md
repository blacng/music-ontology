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
| 7 | A musician should play ≥1 instrument (CQ-5) | 5 vocalists (Beyoncé, Bowie, Kanye, Jackson, Sade) → `:hasInstrument :Voice`. **v3.0.0: no conductor exemption.** Karajan and Bernstein are `:MusicalPerson`s who hold `:ConductorRole`, not `:Musician`s — a conductor who plays nothing is not a musician — so the shape simply never targets them |
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


---

## v3.0.0 — the gate stops being vacuously green

**26 NodeShapes.** SHACL: **0 Violations / 0 Warnings** on the catalogue.

That sentence used to mean nothing, and it is worth being precise about why.

### 1. The shapes were not reaching subclass instances at all

`check_shacl.py` ran with pyshacl's default `inference='none'`. `ont_graph` merges the TBox in but
computes **no entailment**, so a node asserted `:SoloArtist` slipped straight past
`sh:targetClass :MusicalArtist`. The shape hierarchy did not apply. Turning on `inference='rdfs'` fixed
targeting — and immediately surfaced 10 advisory Warnings on `tests/test_data.ttl`, which had never been
shape-checked by anything.

### 2. But naive RDFS inference makes shapes unfalsifiable

RDFS materialises `rdfs:domain`, and **a domain is an inference rule, not a constraint**. It does not
say "only agents may have a career onset"; it says "anything with a career onset **is** an agent". Hand
the full TBox to the closure and every `sh:class` check on that property's subject becomes
**unfalsifiable** — the closure manufactures the very type the shape is looking for.

Proven, not asserted:

```
ont_graph = FULL TBox        -> :RecordLabel with :startsCareerIn  CONFORMS   (shape is vacuous)
ont_graph = TAXONOMY-ONLY    -> :RecordLabel with :startsCareerIn  VIOLATION  (shape works)
```

So pyshacl gets a **taxonomy-only** view: `subClassOf`/`subPropertyOf` kept (targeting works),
`domain`/`range` dropped (property usage cannot manufacture types). The TBox *file* keeps its axioms.

### 3. "0 Violations" still proves nothing without negative fixtures

A shape targeting zero nodes, a shape whose constraint has been neutered, and a shape that genuinely
passes all report exactly the same thing. `tests/negative/` (17 fixtures, `make shacl-negative`) asserts
each one **fires for the expected reason** — matched on `(focus node, constraint component, path,
severity)` plus a message substring, not merely `conforms == False`. Keying on Violation *count* would
have silently passed the `:MusicianShape` fixture, which reports a **Warning**.

**Mutation-tested.** Revert the taxonomy-only strip → `record_label_career_onset.ttl` conforms and the
gate goes red. Delete `:MusicianShape`'s `sh:minCount` → the gate goes red. A harness never *observed*
failing has proved nothing.

**Coverage is reported, not claimed: 12 of 22 targeting shapes have a fixture.** The other 10 are named
in the gate's own output. Their green still means nothing yet.

### 4. `make reason` was vacuously green too — the same bug, one level up

The domain TBox carried **zero** `owl:disjointWith` axioms, so HermiT had nothing to contradict and
could not fail on **any** input. "Consistent, no unsatisfiable classes" certified only that the file
parsed. v3.0.0 adds the disjointness the domain actually has, and `make reason-negative` (in CI) requires
HermiT to reject a group that is also a person.

### 5. What the shapes still cannot do

`:HoldsProducerRoleShape` checks that a credited producer holds `:ProducerRole` — **anywhere, ever**. It
catches an agent who produces nothing at all; it **cannot catch a wrong credit**. The role is on the
agent, not the credit. See `sdd/decisions.md` AD-14.
