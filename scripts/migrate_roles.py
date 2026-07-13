#!/usr/bin/env python3
"""Migrate musical roles from OWL classes to the gist:Category pattern.

Why: producer / conductor / lyricist / composer are things an agent DOES, not things it
IS. As classes they were rigid, so an agent could hold only the role you happened to type
them with. Quincy Jones — a trumpeter, arranger, conductor and producer, whose own
rdfs:comment in this catalogue says so — was typed :MusicProducer and nothing else, which
put him outside :MusicalAgent entirely: he could not hold :hasInstrument (domain
:Musician) nor be the :performedBy of a work (range :MusicalArtist). The model forbade
what the data already knew.

So roles become gist:Category instances reached by :hasRole, exactly as genres, place
granularity and collection types already work — the style guide's "prefer
gist:isCategorizedBy over subclassing for type variation". An agent may then hold any
number of roles, which is the entire point.

How: a targeted, formatting-preserving text rewrite of the ABox files only, in the idiom
of migrate_place_typing.py. An rdflib round-trip would re-serialize and destroy every
banner comment, provenance note and the block ordering split_tbox_abox.py depends on.
The TBox class deletions and the SHACL rewrites are handled separately (by hand) and are
NOT touched here.

Idempotent: re-running finds no remaining `a :<Role>` instance patterns and rewrites
nothing. Verifies its own output by parsing before writing, and refuses to write if the
post-conditions do not hold.

Safe to re-run. Reports the count of rewrites per file.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF

ROOT = Path(__file__).resolve().parent.parent
M = Namespace("https://www.somusicvocabulary.org/music#")

CATALOG = ROOT / "ontology" / "music_catalog_data.ttl"
FIXTURES = ROOT / "tests" / "test_data.ttl"
TBOX = ROOT / "ontology" / "music_vocabulary_comprehensive.ttl"

# Old role class -> new role individual.
ROLES = {
    "MusicProducer": "ProducerRole",
    "Conductor": "ConductorRole",
    "Lyricist": "LyricistRole",
    "Composer": "ComposerRole",
}

# The retype map. Each individual's OLD type list becomes a NEW type plus :hasRole values.
#
# Which class each lands in is decided by what the individual actually DOES in the
# catalogue, not by their most famous job:
#   * Karajan and Bernstein carry no :hasInstrument, so they are not :Musicians — they are
#     :MusicalPersons who conduct. This is what lets :MusicianShape drop its `sh:class
#     :Conductor` exemption: a conductor who plays nothing is simply not a musician, so the
#     shape never targets them. The exemption was compensating for a bad type assignment.
#   * Quincy Jones played trumpet — asserted here, and now finally assertable.
#   * The composers already carry instruments (piano/piano/organ) and are already
#     :SoloArtists, so they keep both and simply gain a role.
RETYPE = {
    # individual:              (new rdf:type, [roles], extra triples)
    "HerbertVonKarajan":       ("MusicalPerson", ["ConductorRole"], []),
    "LeonardBernstein":        ("MusicalPerson", ["ConductorRole"], []),
    "RickRubin":               ("MusicalPerson", ["ProducerRole"], []),
    "GeorgeMartin":            ("MusicalPerson", ["ProducerRole"], []),
    "QuincyJones":             ("Musician", ["ProducerRole", "ConductorRole", "ComposerRole"],
                                ["    :hasInstrument :Trumpet ;"]),
    "LudwigVanBeethoven":      ("SoloArtist", ["ComposerRole"], []),
    "WolfgangAmadeusMozart":   ("SoloArtist", ["ComposerRole"], []),
    "JohannSebastianBach":     ("SoloArtist", ["ComposerRole"], []),
    "BobDylan":                ("SoloArtist", ["ComposerRole", "LyricistRole"], []),
    "PaulMcCartney":           ("SoloArtist", ["LyricistRole"], []),
    "TaylorSwift":             ("SoloArtist", ["LyricistRole"], []),
    # Synthetic fixtures.
    "TST_Producer1":           ("MusicalPerson", ["ProducerRole"], []),
    "TST_Producer2":           ("MusicalPerson", ["ProducerRole"], []),
}

ROLE_INDIVIDUALS = """
###############################################################################
# INSTANCES — MUSICAL ROLES (gist:Category)
#
# What an agent DOES. An agent may hold several of these at once — :QuincyJones holds
# three — which is exactly what the old role-as-class model could not express.
###############################################################################

:ProducerRole a :MusicalRole ;
    rdfs:label "Producer"@en ;
    rdfs:comment "Oversees and manages the recording and production of music."@en ;
    skos:definition "The role of overseeing the recording, mixing and production of a musical work."@en ;
    :exampleInstance :GeorgeMartin, :QuincyJones, :RickRubin ;
    .

:ConductorRole a :MusicalRole ;
    rdfs:label "Conductor"@en ;
    rdfs:comment "Directs the performance of an orchestra or choir."@en ;
    skos:definition "The role of directing the performance of an orchestra, choir or other ensemble."@en ;
    :exampleInstance :HerbertVonKarajan, :LeonardBernstein ;
    .

:LyricistRole a :MusicalRole ;
    rdfs:label "Lyricist"@en ;
    rdfs:comment "Writes the words (lyrics) for songs."@en ;
    skos:definition "The role of writing the words of a song."@en ;
    :exampleInstance :BobDylan, :PaulMcCartney, :TaylorSwift ;
    .

:ComposerRole a :MusicalRole ;
    rdfs:label "Composer"@en ;
    rdfs:comment "Writes original music."@en ;
    skos:definition "The role of creating an original musical work."@en ;
    :exampleInstance :LudwigVanBeethoven, :WolfgangAmadeusMozart, :JohannSebastianBach ;
    .

"""

# Insert the role individuals immediately before the agents that hold them.
ANCHOR = "###############################################################################\n# INSTANCES — MUSICIANS (band members / notable instrumentalists)"


def retype_block(text: str, name: str) -> tuple[str, int]:
    """Rewrite `:<name> a <old types> ;` into the new type + :hasRole lines.

    Idempotence hinges on the guard below. Matching the type line alone is not enough: after
    migration the line reads `a :MusicalPerson ;`, which matches just as happily, and a second
    run cheerfully appends a second :hasRole. So we rewrite ONLY a block whose type list still
    mentions one of the classes being retired. Every individual in RETYPE has one — that is
    why it is in RETYPE — so after one pass nothing matches and the migration is a no-op.
    """
    new_type, roles, extra = RETYPE[name]

    # Match the type line of this individual's block: ":Name a :A, :B ;"
    pattern = re.compile(r"^:%s a ([^;]+);" % re.escape(name), re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return text, 0

    old_types = match.group(1)
    if not any(re.search(r":%s\b" % old, old_types) for old in ROLES):
        return text, 0  # already migrated — leave it alone

    roles_line = "    :hasRole " + ", ".join(f":{r}" for r in roles) + " ;"
    replacement = "\n".join([f":{name} a :{new_type} ;", roles_line, *extra])
    return pattern.sub(lambda _: replacement, text, count=1), 1


def migrate_text(text: str, names: list[str]) -> tuple[str, int]:
    total = 0
    for name in names:
        text, n = retype_block(text, name)
        total += n
    return text, total


def check(graph: Graph, label: str) -> list[str]:
    """Post-conditions. Refuse to write if any of these fail."""
    problems = []
    for old in ROLES:
        leftover = list(graph.subjects(RDF.type, M[old]))
        if leftover:
            problems.append(f"{label}: {len(leftover)} individual(s) still typed :{old}")
    for subject, _, role in graph.triples((None, M.hasRole, None)):
        if str(role).split("#")[-1] not in ROLES.values():
            problems.append(f"{label}: {subject} has unknown role {role}")
    return problems


def main() -> int:
    grand = 0

    # 1. The catalogue: role individuals, then the retypes.
    catalog = CATALOG.read_text()
    if ":ProducerRole a :MusicalRole" not in catalog:
        if ANCHOR not in catalog:
            print(f"FAIL — anchor not found in {CATALOG.name}; refusing to guess placement.")
            return 1
        catalog = catalog.replace(ANCHOR, ROLE_INDIVIDUALS.lstrip("\n") + ANCHOR, 1)
        print(f"{CATALOG.relative_to(ROOT)}: 4 role individuals added")

    catalog_names = [n for n in RETYPE if not n.startswith("TST_")]
    catalog, n_cat = migrate_text(catalog, catalog_names)
    print(f"{CATALOG.relative_to(ROOT)}: {n_cat} individual(s) retyped")
    grand += n_cat

    # 2. The fixtures.
    fixtures = FIXTURES.read_text()
    fixture_names = [n for n in RETYPE if n.startswith("TST_")]
    fixtures, n_fix = migrate_text(fixtures, fixture_names)
    print(f"{FIXTURES.relative_to(ROOT)}: {n_fix} fixture(s) retyped")
    grand += n_fix

    # 3. Verify BEFORE writing. A migration that cannot check itself is a hand-edit in a
    #    trench coat.
    tbox = Graph().parse(TBOX, format="turtle")
    problems = []
    for label, text in ((CATALOG.name, catalog), (FIXTURES.name, fixtures)):
        try:
            graph = Graph().parse(data=text, format="turtle") + tbox
        except Exception as exc:  # noqa: BLE001 — surface the parse error verbatim
            problems.append(f"{label}: does not parse after migration — {exc}")
            continue
        problems.extend(check(graph, label))

    if problems:
        print("\nFAIL — post-conditions not met, nothing written:")
        for problem in problems:
            print(f"  * {problem}")
        return 1

    CATALOG.write_text(catalog)
    FIXTURES.write_text(fixtures)
    print(f"total: {grand} retyped (idempotent — re-run rewrites 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
