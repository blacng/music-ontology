# Production Readiness Report

**Artefact:** 7 (Production Readiness) · GRL Workshop methodology · 12-point gate
**Ontology:** `ontology/music_vocabulary_comprehensive.ttl` (`owl:versionInfo "2.0.0"`)
**Maturity:** research prototype (some items waived with documented reasons)

## Scorecard

| # | Check | Status |
|---|-------|--------|
| 1 | All CQs have passing SPARQL tests | ✅ pass |
| 2 | Reasoner: no inconsistency / unsatisfiable classes | ✅ pass (gist v14.1.0 imported) |
| 3 | Every NodeShape validates (pyshacl) | ✅ pass (0 Violations) |
| 4 | OWL 2 profile declared, no violations | ⚠ not strict DL (datatypes) — waived |
| 5 | No undeclared classes / properties / annotation props | ✅ pass (gist re-aligned) |
| 6 | Every class has `skos:prefLabel` + `skos:definition` | ✅ pass (53/53, SKOS-only) |
| 7 | `owl:versionIRI` set | ✅ fixed |
| 8 | Change-log | ✅ fixed (`CHANGELOG.md`) |
| 9 | Modelling decisions documented (Y-statements) | ✅ pass (`sdd/decisions.md`) |
| 10 | Downstream artefacts regenerated & tested | ✅ pass (N/A: JSON-LD/OpenAPI/SQL) |
| 11 | ≥3 adversarial perspectives critiqued & actioned | ✅ pass |
| 12 | Peer reviewer sign-off | ⏳ pending (human) |

**10 green, 1 waived (item 4), 1 human sign-off (item 12).**

---

## Detail

**1 — CQ tests ✅** `scripts/run_cq_tests.py` → 12/12 against `ontology/` + `tests/test_data.ttl`. (Tests run on the controlled synthetic fixture, per Artefact 5, not the illustrative catalog.)

**2 — Reasoner ✅** HermiT via `make reason` (containerized ROBOT) with **gist v14.1.0 imported
locally** (vendored at `ontology/imports/gistCore.ttl`, resolved via `ontology/catalog-v001.xml`):
**consistent, 0 unsatisfiable classes/properties**. The gist alignment was re-built against current
gist (see §5) — our gist parent terms now all resolve. The remaining reference-violation warnings
in the closure are gist v14's *own* internal module references, not ours.

**3 — SHACL ✅** `make shacl` → 0 Violations; 19 advisory completeness Warnings on the illustrative catalog (`docs/shacl-report.md`).

**4 — OWL 2 profile ⚠ (waived)** `robot validate-profile --profile DL` → **not in OWL 2 DL**. Fixed: `skos:related` declared as `owl:AnnotationProperty`. Remaining: `xsd:gYear` and `xsd:date` are **outside the OWL 2 datatype map** (`releasedIn`, `startsCareerIn`, `awardYear`, `bornOn`, `heldOn`). The ontology *is* valid OWL 2 Full. **Waived for the prototype**; production fix = migrate to `xsd:dateTime` / model years as `xsd:integer` (also touches CQ-4's decade logic).

**5 — Undeclared terms ✅** music# namespace: **0 undeclared classes**; `skos:related` declared.
The gist alignment was **migrated to current gist v14.1.0** — prefix → `…/ns/ontology/gist/`,
import → vendored `gistCore.ttl`, and classes re-parented to valid current-gist terms
(`gist:Person`/`gist:Organization` for agents, `gist:Content` for works, `gist:Equipment` for
instruments, `gist:Aspect` for musical features, `gist:GeoRegion` for places). All our gist refs
now resolve in the imports closure. Applied via `scripts/migrate_gist.py`.

**6 — Labels & definitions ✅** All 53 classes have `skos:prefLabel` + `skos:definition`. Migrated
classes & properties to **SKOS-only** (`rdfs:label`→`skos:prefLabel`, `rdfs:comment`→`skos:scopeNote`;
instances keep `rdfs:label` as data) via `scripts/migrate_skos_labels.py`. Also fixed a surfaced IRI
collision — `:Country` was both the geographic class and the Country-music genre; the class is now
`:Nation`. SKOS annotation properties declared (DL-clean).

**7 — versionIRI ✅** Added `owl:versionIRI <https://www.somusicvocabulary.org/music/2.0.0>` (`owl:versionInfo "2.0.0"`).

**8 — Change-log ✅** `CHANGELOG.md` created.

**9 — Decisions documented ✅** Nine formal **Y-statements** in `sdd/decisions.md` (RDF/OWL, single
upper ontology, gist migration, genre pattern, agent boundary, geography, prototype maturity,
tooling, SKOS labels), cross-linked to the informal `sdd/plan.md` log.

**10 — Downstream artefacts ✅** SHACL, CQ tests, and docs are regenerated at each step (the methodology's regeneration discipline). JSON-LD context / OpenAPI / SQL DDL are **N/A** — a research prototype has no serving layer.

**11 — Adversarial critique ✅** Artefact 2 ran **four** perspectives (sceptic, domain expert, regulator, first-principles); findings drove CQ v2/v3/v4 and the boundary fix.

**12 — Peer sign-off ⏳** Human gate; the PR review serves as it. Not yet signed off.

---

## Outstanding work (prioritized)

1. ~~Decide gist alignment~~ **DONE** — migrated to current gist **v14.1.0** (path (a)). Investigation
   showed the original alignment was never valid (`gistCore#` matched no release; Agent/Concept/
   PhysicalThing existed in no gist version), so this was a re-modelling, not a swap. gist is now
   vendored + imported locally and the ontology re-parents to real gist terms — **0 unsatisfiable
   classes**. BFO/DOLCE were considered and rejected (mixing upper ontologies is an anti-pattern;
   current gist covers every concept).
2. ~~`skos:prefLabel` migration~~ **DONE** (item 6) — classes & properties are SKOS-only.
3. ~~Y-statement formalization~~ **DONE** (item 9) — `sdd/decisions.md`.
4. **OWL 2 DL datatypes** (item 4) — **waived** for the prototype; production fix = `gYear`/`date` → `xsd:dateTime`/integer.
5. **Carried follow-ups:** vocalist `:Voice` (the 5 instrument Warnings); complete the real catalog so its 19 SHACL completeness Warnings clear.
6. **Peer sign-off** (item 12) — the PR review.

Reproduce the automated checks: `make check` (items 1, 3) · `make reason` (item 2, needs Docker) ·
`docker run --rm -v "$PWD":/work -w /work obolibrary/robot robot validate-profile --profile DL --input ontology/music_vocabulary_comprehensive.ttl` (item 4).
