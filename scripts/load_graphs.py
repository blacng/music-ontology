#!/usr/bin/env python3
"""Assemble the named-graph dataset for triplestore ingest.

The source of truth stays as per-layer Turtle files (git-friendly, and what the
file-based validation gate consumes). This script is the *load-time mapping* half
of the design: it assigns each file to its named graph and emits ingest artifacts.

Outputs (into dist/):
  - music_dataset.trig  — the whole dataset as quads (universal quad-store input)
  - load.ru             — SPARQL `LOAD ... INTO GRAPH ...` update (endpoint ingest)
  - graph_manifest.json — the file -> graph-IRI map (documentation / other tooling)

The default graph carries a SPARQL Service Description (sd:) naming the graphs —
this is the "Default graph" box in the KGCMart layout.

Verifies the TriG round-trips (every source triple survives, in the right graph)
before the artifacts are considered good.

Run: uv run python scripts/load_graphs.py   (or: make dataset)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rdflib import Dataset, Graph, Literal, URIRef, RDFS
from rdflib.compare import isomorphic
from rdflib.namespace import Namespace

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BASE = "https://www.somusicvocabulary.org/music"
SD = Namespace("http://www.w3.org/ns/sparql-service-description#")

# The canonical file -> named-graph mapping. Order = ingest order.
GRAPHS = [
    ("ontology/music_vocabulary_comprehensive.ttl", f"{BASE}/tbox",   "TBox — classes, properties, ontology header"),
    ("ontology/music_catalog_data.ttl",             f"{BASE}/abox",   "ABox — instance catalogue"),
    ("ontology/music_vocabulary_shapes.ttl",        f"{BASE}/shapes", "SHACL shapes"),
    ("ontology/imports/gistCore.ttl",               "https://w3id.org/semanticarts/ontology/gistCore", "gist v14.1.0 (imported upper ontology)"),
]
DATASET_IRI = URIRef(f"{BASE}/dataset")


def build_dataset() -> tuple[Dataset, dict[str, Graph]]:
    ds = Dataset()
    ds.bind("sd", SD)
    per_graph: dict[str, Graph] = {}

    # Default graph: a Service Description naming the dataset's graphs.
    ds.add((DATASET_IRI, SD.name, DATASET_IRI))
    ds.add((DATASET_IRI, RDFS.label, Literal("SoMusic Vocabulary — named-graph dataset")))

    for rel, giri, role in GRAPHS:
        path = ROOT / rel
        if not path.exists():
            print(f"  skip (missing): {rel}", file=sys.stderr)
            continue
        g = ds.graph(URIRef(giri))
        g.parse(path, format="turtle")
        per_graph[giri] = g
        ng = URIRef(giri + "#named")  # a blank-node-free node describing this named graph
        ds.add((DATASET_IRI, SD.namedGraph, ng))
        ds.add((ng, SD.name, URIRef(giri)))
        ds.add((ng, RDFS.label, Literal(role)))
    return ds, per_graph


def main() -> int:
    DIST.mkdir(exist_ok=True)
    ds, per_graph = build_dataset()

    # --- TriG artifact ---
    trig_path = DIST / "music_dataset.trig"
    ds.serialize(destination=trig_path, format="trig")

    # --- Verify round-trip: reload and compare each named graph to its source. ---
    # Both sides are pushed through the TriG serializer first so that lexical
    # canonicalisation (e.g. xsd:decimal "312" -> "312.0", same value) applies
    # equally and the isomorphism check compares meaning, not spelling.
    def canon(triples) -> Graph:
        d = Dataset()
        gg = d.graph(URIRef("urn:x-canon"))
        for t in triples:
            gg.add(t)
        out = Dataset()
        out.parse(data=d.serialize(format="trig"), format="trig")
        return out.graph(URIRef("urn:x-canon"))

    reloaded = Dataset()
    reloaded.parse(trig_path, format="trig")
    for _, giri, _ in GRAPHS:
        src = per_graph.get(giri)
        if src is None:
            continue
        rt = reloaded.graph(URIRef(giri))
        if not isomorphic(canon(src), canon(rt)):
            print(f"ROUND-TRIP FAILED for graph <{giri}> "
                  f"(src {len(src)} vs reloaded {len(rt)} triples)", file=sys.stderr)
            return 1

    # --- SPARQL LOAD script (endpoint ingest) ---
    ru = ["# SPARQL Update — load each layer into its named graph.",
          "# Replace {BASE} with a URL/path your store can resolve (e.g. file:///abs/repo",
          "# or an HTTP mirror). Run against the store's update endpoint.", ""]
    for rel, giri, role in GRAPHS:
        if (ROOT / rel).exists():
            ru.append(f"# {role}")
            ru.append(f"LOAD <{{BASE}}/{rel}> INTO GRAPH <{giri}> ;")
    (DIST / "load.ru").write_text("\n".join(ru) + "\n")

    # --- JSON manifest (documentation / other tooling) ---
    manifest = {
        "dataset": str(DATASET_IRI),
        "defaultGraph": "SPARQL Service Description (sd:) naming the graphs below",
        "graphs": [
            {"file": rel, "graph": giri, "role": role}
            for rel, giri, role in GRAPHS if (ROOT / rel).exists()
        ],
    }
    (DIST / "graph_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    total = sum(len(g) for g in per_graph.values())
    print(f"Dataset assembled OK (round-trip verified): {total} triples across "
          f"{len(per_graph)} named graphs")
    for _, giri, _ in GRAPHS:
        if giri in per_graph:
            print(f"  <{giri}>: {len(per_graph[giri])} triples")
    print(f"\nArtifacts in {DIST.relative_to(ROOT)}/: "
          "music_dataset.trig, load.ru, graph_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
