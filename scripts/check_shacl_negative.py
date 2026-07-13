"""Non-vacuity gate: prove the SHACL shapes can actually FAIL.

`make shacl` reporting "0 Violations" proves nothing on its own. A shape that targets zero
nodes, a shape whose constraint has been neutered, and a shape that genuinely passes all
report exactly the same thing: nothing. The green gate was **vacuously** green.

This ran real: a previous release claimed `:CareerOnsetShape` was "verified with a negative
test". No such fixture existed — it lived in a throwaway heredoc, never committed, never in
CI, and it passed only because the single input chosen could not have revealed the shape was
broken. The claim then propagated into four files.

So each fixture in `tests/negative/` is deliberately broken, and this gate asserts it **fires
the expected shape for the expected reason**. Three ways a lazier gate would lie:

  * Keying on `conforms == False` alone — a typo'd IRI tripping some *other* shape passes.
  * Keying on Violation COUNT — `:MusicianShape` reports a **Warning** (node-level
    `sh:severity sh:Warning`), so its fixture would sail through untested.
  * Matching `sh:sourceShape` by IRI — every inline `sh:property [ … ]` in the shapes file is
    a **blank node**. There is no IRI to match.

Hence the match tuple: (focus node, constraint component, path, severity) + message substring.

Configuration is imported from `check_shacl.py` — the same `validate_data()` the release gate
uses. If the two ever drift, this stops proving anything about that one.

Run: uv run python scripts/check_shacl_negative.py
"""
import json
import sys
from pathlib import Path

from rdflib import Graph
from rdflib.namespace import SH

from check_shacl import ONTOLOGY, SHAPES, validate_data

NEG_DIR = Path("tests/negative")
MANIFEST = NEG_DIR / "manifest.json"


def local(term) -> str:
    """Local name of an IRI — '…#Warning' -> 'Warning', '…/MaxCount…' -> 'MaxCount…'."""
    if term is None:
        return ""
    text = str(term)
    return text.split("#")[-1].split("/")[-1]


def results_of(report: Graph) -> list[dict]:
    out = []
    for node in report.subjects(SH.resultSeverity, None):
        out.append(
            {
                "focus": local(report.value(node, SH.focusNode)),
                "component": local(report.value(node, SH.sourceConstraintComponent)),
                "path": local(report.value(node, SH.resultPath)),
                "severity": local(report.value(node, SH.resultSeverity)),
                "message": str(report.value(node, SH.resultMessage) or ""),
            }
        )
    return out


def matches(result: dict, expect: dict) -> bool:
    if result["focus"] != expect["focus"]:
        return False
    if result["component"] != expect["component"]:
        return False
    if result["severity"] != expect["severity"]:
        return False
    if "path" in expect and result["path"] != expect["path"]:
        return False
    return expect["message_contains"].lower() in result["message"].lower()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    tbox = Graph().parse(ONTOLOGY, format="turtle")
    shapes = Graph().parse(SHAPES, format="turtle")

    failures: list[str] = []

    for entry in manifest["fixtures"]:
        name = entry["file"]
        # `expect` is a list: a fixture may legitimately break more than one thing at once.
        # A record label credited as producer is neither a :MusicalAgent nor a role-holder,
        # and BOTH failures are real. What must never happen is an *unexpected* Violation.
        expected = entry["expect"]
        if isinstance(expected, dict):
            expected = [expected]

        data = Graph().parse(NEG_DIR / name, format="turtle")
        conforms, report, _ = validate_data(data, shapes, tbox)
        results = results_of(report)

        if conforms:
            failures.append(
                f"{name}: CONFORMS. The fixture is supposed to be broken, so {entry['shape']} "
                f"is not firing — it is vacuous, mis-targeted, or has been neutered."
            )
            print(f"  [VACUOUS] {name:<42} {entry['shape']} did not fire")
            continue

        missing = [e for e in expected if not any(matches(r, e) for r in results)]
        if missing:
            got = "; ".join(
                f"{r['focus']}/{r['component']}/{r['path']}/{r['severity']}" for r in results
            ) or "nothing"
            want = "; ".join(
                f"{e['focus']}/{e['component']}/{e.get('path', '-')}/{e['severity']}"
                for e in missing
            )
            failures.append(
                f"{name}: fired, but for the WRONG REASON.\n"
                f"      missing:  {want}\n"
                f"      got:      {got}"
            )
            print(f"  [WRONG]   {name:<42} fired, but not as {entry['shape']}")
            continue

        # Anything else that fires is a Violation nobody asked for — a fixture tripping a
        # shape it was not written to test proves nothing precise, and can mask the signal.
        strays = [
            r
            for r in results
            if r["severity"] == "Violation" and not any(matches(r, e) for e in expected)
        ]
        if strays:
            detail = "; ".join(f"{r['focus']}/{r['component']}/{r['path']}" for r in strays)
            failures.append(
                f"{name}: fired correctly, but ALSO tripped unexpected Violation(s): {detail}. "
                f"Declare them in the manifest if they are intended, or make the fixture narrower."
            )
            print(f"  [NOISY]   {name:<42} extra violations: {detail}")
            continue

        fired = ", ".join(f"{e['component']} ({e['severity']})" for e in expected)
        print(f"  [FIRES]   {name:<42} {fired}")

    total = len(manifest["fixtures"])
    print(f"\nNegative fixtures: {total - len(failures)}/{total} fired as expected")

    if failures:
        print("\nFAIL — the shapes below are not doing what the gate claims:\n")
        for f in failures:
            print(f"  * {f}")
        return 1

    print("OK — every shape under test can actually fail. The green gate is not vacuous.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
