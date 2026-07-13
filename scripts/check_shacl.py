"""SHACL conformance gate for CI.

pyshacl's exit code is driven by `conforms`, which is False whenever there is any
result — including advisory Warnings. This repo intentionally carries completeness
Warnings on the illustrative catalog, so the meaningful gate is: **fail only on
Violations**; report Warnings without failing.

Since the TBox/ABox split, this mirrors the intended triplestore layout: the
**ABox** (instance catalogue) is the data graph under validation, the **shapes**
are the SHACL graph, and the **TBox** is supplied as `ont_graph` — without the
model polluting the data being validated.

Why `inference="rdfs"` with a **taxonomy-only** ont_graph
---------------------------------------------------------
Two separate things were wrong before, and they pull in opposite directions:

1. `ont_graph` alone computes **no entailment** — it only merges the TBox triples in.
   With pyshacl's default (`inference="none"`) a node asserted `:SoloArtist` slipped
   straight past `sh:targetClass :MusicalArtist`: the shape hierarchy simply did not
   apply. `inference="rdfs"` is what actually makes targeting reach subclass instances.

2. But RDFS closure also materialises `rdfs:domain`/`rdfs:range`, and **a domain axiom
   is an inference rule, not a constraint**. It does not say "only agents may have a
   career onset"; it says "anything with a career onset **is** an agent". Feed the full
   TBox to the closure and every `sh:class` check on that property's subject becomes
   **vacuous** — the closure manufactures the very type the shape is looking for. A
   `:RecordLabel` asserting `:startsCareerIn` gets retyped `:MusicalAgent` and conforms.

So we hand pyshacl a **taxonomy-only** view: subClassOf/subPropertyOf kept (targeting
works), domain/range dropped (property usage cannot manufacture types). The TBox *file*
keeps its domain/range axioms — they are true, and HermiT (`make reason`) still sees
them. This strip is only how the validator *views* the model.

`tests/negative/` proves these shapes are not vacuous; `scripts/check_shacl_negative.py`
imports `validate_data` from here so both gates share one configuration. If they ever
drift, the negative gate stops proving anything about this one.

Run: uv run python scripts/check_shacl.py
"""
import sys
from rdflib import Graph, RDF, RDFS
from rdflib.namespace import SH
from pyshacl import validate

DATA = "ontology/music_catalog_data.ttl"                  # ABox — the graph under validation
ONTOLOGY = "ontology/music_vocabulary_comprehensive.ttl"  # TBox — supplies the class hierarchy
SHAPES = "ontology/music_vocabulary_shapes.ttl"
FIXTURES = "tests/test_data.ttl"                          # :TST_* synthetic fixtures


def taxonomy_only(tbox: Graph) -> Graph:
    """The TBox as the validator should see it: hierarchy without domain/range.

    See the module docstring — leaving domain/range in makes every sh:class check on
    an affected property's subject unfalsifiable.
    """
    view = Graph()
    for triple in tbox:
        if triple[1] not in (RDFS.domain, RDFS.range):
            view.add(triple)
    return view


def validate_data(data: Graph, shapes: Graph, tbox: Graph):
    """The one validation configuration. Both gates call this."""
    return validate(
        data,
        shacl_graph=shapes,
        ont_graph=taxonomy_only(tbox),
        meta_shacl=True,
        inference="rdfs",
    )


def tally(report: Graph) -> tuple[int, int]:
    violations = warnings = 0
    for res in report.subjects(RDF.type, SH.ValidationResult):
        sev = str(report.value(res, SH.resultSeverity))
        if sev.endswith("Violation"):
            violations += 1
        elif sev.endswith("Warning"):
            warnings += 1
    return violations, warnings


def main():
    tbox = Graph().parse(ONTOLOGY, format="turtle")
    shapes = Graph().parse(SHAPES, format="turtle")

    failed = False

    # The catalogue (ABox) — the release gate.
    _, report, _ = validate_data(Graph().parse(DATA, format="turtle"), shapes, tbox)
    violations, warnings = tally(report)
    print(f"SHACL  catalogue: {violations} Violation(s), {warnings} Warning(s)")
    if violations:
        print(report.serialize(format="turtle") if violations < 6 else "")
        failed = True

    # The synthetic fixtures. Nothing used to shape-check these, so a fixture could be
    # typed to a class that no longer exists and the CQ suite would stay green.
    fx = Graph().parse(DATA, format="turtle") + Graph().parse(FIXTURES, format="turtle")
    _, fx_report, _ = validate_data(fx, shapes, tbox)
    fx_violations, fx_warnings = tally(fx_report)
    print(f"SHACL  fixtures + catalogue: {fx_violations} Violation(s), {fx_warnings} Warning(s)")
    if fx_violations:
        print(fx_report.serialize(format="turtle") if fx_violations < 6 else "")
        failed = True

    if failed:
        print("FAIL — Violations must be zero. See docs/shacl-report.md.")
        sys.exit(1)
    print("OK — no Violations (Warnings are advisory completeness signals).")


if __name__ == "__main__":
    main()
