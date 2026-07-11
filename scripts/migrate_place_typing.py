#!/usr/bin/env python3
"""Migrate place typing from subclasses to the gist:Category pattern.

Why: geography is moving off subclass-per-level (:City/:Nation ⊑ :Place) onto the
same gist:Category idiom already used for genres — a single :Place class whose
granularity is carried by `:hasPlaceType` (⊑ gist:isCategorizedBy) a :PlaceType
individual (:City, :Region, :Nation, :Continent). This scales to arbitrary
admin levels as *data* rather than schema, and matches the style-guide rule
"prefer gist:isCategorizedBy over subclassing for type variation."

How: a targeted, formatting-preserving text rewrite of the ABox files only —
every `a :City ;` / `a :Nation ;` (etc.) instance assertion becomes
`a :Place ; :hasPlaceType :City ;`. The TBox class declarations are handled
separately (by hand) and are NOT touched here. Idempotent: re-running finds no
remaining `a :<Level> ;` instance patterns and rewrites nothing.

Safe to re-run. Reports the count of rewrites per file.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files carrying place *instances* (never the TBox, whose class defs use the same
# `:City a owl:Class` token we must not rewrite).
TARGETS = [
    ROOT / "ontology" / "music_catalog_data.ttl",
    ROOT / "tests" / "test_data.ttl",
]

LEVELS = ["City", "Region", "Nation", "Continent"]


def migrate_text(text: str) -> tuple[str, int]:
    total = 0
    for level in LEVELS:
        # Match an instance type assertion `a :City ;` (surrounded by whitespace),
        # not `:hasPlaceType :City` (no preceding ` a `) nor `a owl:Class`.
        pattern = re.compile(r"(?<=\s)a :%s ;" % level)
        text, n = pattern.subn("a :Place ; :hasPlaceType :%s ;" % level, text)
        total += n
    return text, total


def main() -> int:
    grand = 0
    for path in TARGETS:
        original = path.read_text()
        migrated, n = migrate_text(original)
        if n:
            path.write_text(migrated)
        print(f"{path.relative_to(ROOT)}: {n} place-type assertions migrated")
        grand += n
    print(f"total: {grand}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
