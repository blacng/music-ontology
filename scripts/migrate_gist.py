"""Migrate the gist alignment from the invalid `gistCore#` prefix to current gist v14.1.0.

The original ontology used `gist: = https://w3id.org/semanticarts/ontology/gistCore#`, which
matches no gist release, and referenced terms (Agent, Artifact, Concept, PhysicalThing, Place)
that exist in no gist version. This rewrites the alignment against current gist (v14.1.0):

- prefix  -> https://w3id.org/semanticarts/ns/ontology/gist/  (current gist term namespace)
- import  -> the gist ontology IRI, resolved locally via ontology/catalog-v001.xml
- re-parent classes whose old gist terms were dropped:
    Agent       -> Person (lyricist/producer) / Organization (band) / domain root (MusicalAgent)
    Artifact    -> Content (MusicalWork) / Collection (MusicChart) / domain root (MusicAward)
    Concept     -> Aspect (key/time-signature/tempo)
    PhysicalThing -> Equipment (instrument)
    Place       -> GeoRegion (:Place) ; Venue -> :Place
  Terms that still exist (Category, Collection, Event, Organization, isCategorizedBy) just
  follow the prefix change.

Run: uv run python scripts/migrate_gist.py
"""
import re
from pathlib import Path

TTL = Path("ontology/music_vocabulary_comprehensive.ttl")
t = TTL.read_text()

t = t.replace(
    "@prefix gist: <https://w3id.org/semanticarts/ontology/gistCore#> .",
    "@prefix gist: <https://w3id.org/semanticarts/ns/ontology/gist/> .",
)
t = t.replace(
    "owl:imports gist: .",
    "owl:imports <https://w3id.org/semanticarts/ontology/gistCore> .",
)

# Property domains that pointed at the dropped gist:Agent -> our :MusicalAgent umbrella.
t = t.replace("rdfs:domain gist:Agent", "rdfs:domain :MusicalAgent")
t = t.replace(
    '"A gist:Agent that creates or performs music; the common parent of musical artists and musicians."',
    '"Any person or group that creates or performs music; the common parent of musical artists and musicians."',
)

# subject -> (old gist parent term, new parent or None to drop the gist parent)
REPARENT = {
    ":MusicalAgent": ("gist:Agent", None),
    ":Lyricist": ("gist:Agent", "gist:Person"),
    ":MusicProducer": ("gist:Agent", "gist:Person"),
    ":MusicalWork": ("gist:Artifact", "gist:Content"),
    ":MusicAward": ("gist:Artifact", None),
    ":MusicChart": ("gist:Artifact", "gist:Collection"),
    ":MusicKey": ("gist:Concept", "gist:Aspect"),
    ":TimeSignature": ("gist:Concept", "gist:Aspect"),
    ":Tempo": ("gist:Concept", "gist:Aspect"),
    ":MusicalInstrument": ("gist:PhysicalThing", "gist:Equipment"),
    ":Venue": ("gist:Place", ":Place"),
    ":Place": ("gist:Place", "gist:GeoRegion"),
}
# subject -> extra gist parent to add (alongside the existing domain parent)
ADD = {":Band": "gist:Organization", ":Musician": "gist:Person"}


def subject_of(block):
    m = re.match(r"^(:[A-Za-z0-9_]+)\s+a\b", block)
    return m.group(1) if m else None


blocks = re.split(r"\n\s*\n", t)
out = []
for b in blocks:
    s = subject_of(b)
    if s in REPARENT:
        old, new = REPARENT[s]
        lines = []
        for ln in b.split("\n"):
            if f"rdfs:subClassOf {old}" in ln:
                if new is None:
                    continue  # drop the gist parent → domain root
                ln = ln.replace(old, new)
            lines.append(ln)
        b = "\n".join(lines)
    if s in ADD:
        lines, added = [], False
        for ln in b.split("\n"):
            lines.append(ln)
            if not added and "rdfs:subClassOf" in ln:
                indent = ln[: len(ln) - len(ln.lstrip())]
                lines.append(f"{indent}rdfs:subClassOf {ADD[s]} ;")
                added = True
        b = "\n".join(lines)
    out.append(b)

TTL.write_text("\n\n".join(out))
print("migrated gist alignment ->", TTL)
