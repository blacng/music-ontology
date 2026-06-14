# Production Readiness Report

**Artefact:** 7 (Production Readiness) · GRL Workshop methodology · 12-point gate
**Ontology:** `ontology/music_vocabulary_comprehensive.ttl` (`owl:versionInfo "2.0.0"`)
**Maturity:** research prototype (some items waived with documented reasons)

## Scorecard

| # | Check | Status |
|---|-------|--------|
| 1 | All CQs have passing SPARQL tests | ✅ pass |
| 2 | Reasoner: no inconsistency / unsatisfiable classes | ✅ pass — ⚠ gist alignment dangling |
| 3 | Every NodeShape validates (pyshacl) | ✅ pass (0 Violations) |
| 4 | OWL 2 profile declared, no violations | ⚠ not strict DL (datatypes) — waived |
| 5 | No undeclared classes / properties / annotation props | ⚠ music# clean; gist refs dangling |
| 6 | Every class has `skos:prefLabel` + `skos:definition` | 🔧 fix-needed (no prefLabel) |
| 7 | `owl:versionIRI` set | ✅ fixed |
| 8 | Change-log | ✅ fixed (`CHANGELOG.md`) |
| 9 | Modelling decisions documented (Y-statements) | ⚠ partial |
| 10 | Downstream artefacts regenerated & tested | ✅ pass (N/A: JSON-LD/OpenAPI/SQL) |
| 11 | ≥3 adversarial perspectives critiqued & actioned | ✅ pass |
| 12 | Peer reviewer sign-off | ⏳ pending (human) |

**6 green, 4 partial/fix-needed, 1 decision, 1 human sign-off.**

---

## Detail

**1 — CQ tests ✅** `scripts/run_cq_tests.py` → 12/12 against `ontology/` + `tests/test_data.ttl`. (Tests run on the controlled synthetic fixture, per Artefact 5, not the illustrative catalog.)

**2 — Reasoner ✅ (with finding)** HermiT via `make reason` (containerized ROBOT): **consistent, 0 unsatisfiable classes**.
⚠ **Finding — gist namespace drift.** The reasoner reported **133 dangling reference violations**. Our `gist:` prefix is the legacy `…/semanticarts/ontology/gistCore#`, but `owl:imports` now resolves to current gist under `…/semanticarts/ns/ontology/gist/`. So `gist:Agent`, `gist:Category`, `gist:isCategorizedBy`, `gist:Place`, etc. are **not actually defined by the import** — the alignment is cosmetic at the IRI level and reasoning over gist axioms is incomplete. **Needs a decision** (see Outstanding).

**3 — SHACL ✅** `make shacl` → 0 Violations; 19 advisory completeness Warnings on the illustrative catalog (`docs/shacl-report.md`).

**4 — OWL 2 profile ⚠ (waived)** `robot validate-profile --profile DL` → **not in OWL 2 DL**. Fixed: `skos:related` declared as `owl:AnnotationProperty`. Remaining: `xsd:gYear` and `xsd:date` are **outside the OWL 2 datatype map** (`releasedIn`, `startsCareerIn`, `awardYear`, `bornOn`, `heldOn`). The ontology *is* valid OWL 2 Full. **Waived for the prototype**; production fix = migrate to `xsd:dateTime` / model years as `xsd:integer` (also touches CQ-4's decade logic).

**5 — Undeclared terms ⚠** music# namespace: **0 undeclared classes** (53/53 declared); `skos:related` now declared. Outstanding: the dangling gist refs from item 2.

**6 — Labels & definitions 🔧** `skos:definition` 53/53 ✅; **`skos:prefLabel` 0/53** (classes use `rdfs:label`). Mechanical migration pending (add `skos:prefLabel`, retire `rdfs:label`/`rdfs:comment` per the style guide's SKOS-only target).

**7 — versionIRI ✅** Added `owl:versionIRI <https://www.somusicvocabulary.org/music/2.0.0>` (`owl:versionInfo "2.0.0"`).

**8 — Change-log ✅** `CHANGELOG.md` created.

**9 — Decisions documented ⚠** Captured in `sdd/plan.md` → Decisions log (use case, maturity, genre pattern, agent boundary, infra/Docker). Not yet in the formal **Y-statement** template ("In the context of… facing… we decided… to achieve… accepting…"). Light doc work to formalize.

**10 — Downstream artefacts ✅** SHACL, CQ tests, and docs are regenerated at each step (the methodology's regeneration discipline). JSON-LD context / OpenAPI / SQL DDL are **N/A** — a research prototype has no serving layer.

**11 — Adversarial critique ✅** Artefact 2 ran **four** perspectives (sceptic, domain expert, regulator, first-principles); findings drove CQ v2/v3/v4 and the boundary fix.

**12 — Peer sign-off ⏳** Human gate; the PR review serves as it. Not yet signed off.

---

## Outstanding work (prioritized)

1. **gist alignment — DEFERRED (decided 2026-06-13, path (b) "for now").** Investigation showed the
   alignment was **never valid**: our `gist:` prefix (`…/ontology/gistCore#`) matches no gist release,
   and `Agent`/`Concept`/`PhysicalThing` exist in **no** gist version (FOAF/SKOS/BFO terms mis-prefixed).
   Current gist (v14) also dropped Agent/Place/Artifact/Concept/PhysicalThing. So "pin the matching
   version" is impossible — no single version resolves all 10 references. **Holding state:** documented
   and deferred as tech debt; the ontology remains consistent (the 133 dangling refs are warnings, not
   errors). The proper **re-alignment to current gist** (with a class mapping) is tracked in
   `sdd/plan.md` → *Deferred / tech debt*. *Open sub-question: whether to also drop the misleading
   `owl:imports` now (it redirect-resolves to the wrong gist) or leave it until the re-alignment.*
2. **`skos:prefLabel` migration** (item 6) — mechanical.
3. **OWL 2 DL datatypes** (item 4) — waive (prototype) or migrate `gYear`/`date` (production).
4. **Y-statement formalization** (item 9).
5. **Carried follow-ups:** vocalist `:Voice` (the 5 instrument Warnings); complete the real catalog so its 19 SHACL completeness Warnings clear.
6. **Peer sign-off** (item 12).

Reproduce the automated checks: `make check` (items 1, 3) · `make reason` (item 2, needs Docker) ·
`docker run --rm -v "$PWD":/work -w /work obolibrary/robot robot validate-profile --profile DL --input ontology/music_vocabulary_comprehensive.ttl` (item 4).
