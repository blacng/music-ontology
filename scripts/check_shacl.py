"""SHACL conformance gate for CI.

pyshacl's exit code is driven by `conforms`, which is False whenever there is any
result — including advisory Warnings. This repo intentionally carries completeness
Warnings on the illustrative catalog, so the meaningful gate is: **fail only on
Violations**; report Warnings without failing.

Since the TBox/ABox split, this mirrors the intended triplestore layout: the
**ABox** (instance catalogue) is the data graph under validation, the **shapes**
are the SHACL graph, and the **TBox** is supplied as `ont_graph` so class-hierarchy
axioms (e.g. :SoloArtist rdfs:subClassOf :MusicalArtist) let `sh:targetClass`
reach subclass instances — without the model polluting the data being validated.

Run: uv run python scripts/check_shacl.py
"""
import sys
from rdflib import Graph, RDF
from rdflib.namespace import SH
from pyshacl import validate

DATA = "ontology/music_catalog_data.ttl"                 # ABox — the graph under validation
ONTOLOGY = "ontology/music_vocabulary_comprehensive.ttl"  # TBox — supplies the class hierarchy
SHAPES = "ontology/music_vocabulary_shapes.ttl"


def main():
    data = Graph().parse(DATA, format="turtle")
    ontology = Graph().parse(ONTOLOGY, format="turtle")
    shapes = Graph().parse(SHAPES, format="turtle")
    _, report, _ = validate(data, shacl_graph=shapes, ont_graph=ontology, meta_shacl=True)

    violations = warnings = 0
    for res in report.subjects(RDF.type, SH.ValidationResult):
        sev = str(report.value(res, SH.resultSeverity))
        if sev.endswith("Violation"):
            violations += 1
        elif sev.endswith("Warning"):
            warnings += 1

    print(f"SHACL: {violations} Violation(s), {warnings} Warning(s)")
    if violations:
        print("FAIL — Violations must be zero. See docs/shacl-report.md.")
        sys.exit(1)
    print("OK — no Violations (Warnings are advisory completeness signals).")


if __name__ == "__main__":
    main()
