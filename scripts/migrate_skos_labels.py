"""Migrate vocabulary annotations to SKOS-only (style-guide target; Production Readiness item 6).

For every CLASS and PROPERTY stanza (not instances, not the ontology header):
  rdfs:label   -> skos:prefLabel
  rdfs:comment -> skos:scopeNote   (preserves the text without clobbering skos:definition)

Instances (genres, instruments, the catalog individuals) keep rdfs:label — they are data, not
vocabulary terms. The ontology header keeps its rdfs:label/comment metadata.

Run: uv run python scripts/migrate_skos_labels.py
"""
import re
from pathlib import Path

TTL = Path("ontology/music_vocabulary_comprehensive.ttl")
t = TTL.read_text()

VOCAB_TYPE = re.compile(
    r"^:\S+\s+a\s+(owl:Class|owl:ObjectProperty|owl:DatatypeProperty|owl:AnnotationProperty)\b"
)

out = []
converted = 0
for block in re.split(r"\n\s*\n", t):
    first = block.lstrip().split("\n", 1)[0]
    if VOCAB_TYPE.match(first):
        new = block.replace("rdfs:label ", "skos:prefLabel ").replace("rdfs:comment ", "skos:scopeNote ")
        if new != block:
            converted += 1
        block = new
    out.append(block)

TTL.write_text("\n\n".join(out))
print(f"converted {converted} class/property stanzas to SKOS labels -> {TTL}")
