"""SHACL conformance gate for CI.

pyshacl's exit code is driven by `conforms`, which is False whenever there is any
result — including advisory Warnings. This repo intentionally carries completeness
Warnings on the illustrative catalog, so the meaningful gate is: **fail only on
Violations**; report Warnings without failing.

Run: uv run python scripts/check_shacl.py
"""
import sys
from rdflib import Graph, RDF
from rdflib.namespace import SH
from pyshacl import validate

DATA = "ontology/music_vocabulary_comprehensive.ttl"
SHAPES = "ontology/music_vocabulary_shapes.ttl"


def main():
    data = Graph().parse(DATA, format="turtle")
    shapes = Graph().parse(SHAPES, format="turtle")
    _, report, _ = validate(data, shacl_graph=shapes, meta_shacl=True)

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
