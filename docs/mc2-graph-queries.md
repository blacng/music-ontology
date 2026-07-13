# MC-2 — Graph Queries: inserts, updates, and a write gate

> **Generated** by `scripts/demo_updates.py --report` (`make report`). Every result set below was captured from a real run — do not hand-edit.

The 18 read queries live in `docs/competency-questions.md`. This file covers the *write* side: each update names the graph it targets, so the ABox can be modified while the TBox and shapes graphs stay out of scope.

## Scenario 1 — INSERT DATA — add an artist to the ABox graph

The update names its target graph, so the TBox and shapes graphs are never in scope.

```sparql
INSERT DATA {
  GRAPH <https://www.somusicvocabulary.org/music/abox> {
    :JeffBuckley a :SoloArtist ;
        rdfs:label "Jeff Buckley"@en ;
        :bornOn "1994"^^xsd:gYear ;
        :hasGenre :Rock ;
        :hasInstrument :Guitar, :Voice ;
        :originatesFrom :UnitedStates ;
        :collaboratesWith :BobDylan .
  }
}
```


**Before — :SoloArtist count**


| artist |
|---|
| 15 artists |


**After — :SoloArtist count**


| artist |
|---|
| 16 artists |


✅ **INSERT DATA added exactly one :SoloArtist** — 15 → 16


**Which named graph holds the new triples?**


| graph |
|---|
| abox |


✅ **New triples live in the ABox graph only** — found in ['abox']


## Scenario 2 — DELETE/INSERT — correct a wrong value in place

`WITH` scopes an entire DELETE/INSERT/WHERE modify operation to one graph. 1994 was Buckley's *debut album* year, not his birth year — a plausible data error.

```sparql
WITH <https://www.somusicvocabulary.org/music/abox>
DELETE { :JeffBuckley :bornOn ?old }
INSERT { :JeffBuckley :bornOn "1966"^^xsd:gYear }
WHERE  { :JeffBuckley :bornOn ?old }
```


**Before**


| bornOn |
|---|
| 1994 |


**After**


| bornOn |
|---|
| 1966 |


✅ **bornOn corrected 1994 → 1966** — now [('1966',)]


✅ **still exactly one bornOn value (no duplicate left behind)**


## Scenario 3 — A write the shapes REJECT — validation as a write gate

`:EMI` is a `:RecordLabel`. It is not a `:MusicalAgent` and holds no `:LyricistRole`. `:WrittenByShape` is anchored on the **property** (`sh:targetSubjectsOf :writtenBy`), not on the work's class — which is exactly why this cannot slip through.

```sparql
INSERT DATA {
  GRAPH <https://www.somusicvocabulary.org/music/abox> {
    :HeyJude :writtenBy :EMI .
  }
}
```


**Before the bad write**


| Violations | Warnings |
|---|---|
| 0 | 0 |


✅ **Graph conforms before the bad write (0 Violations)**


**After the bad write**


| Violations | Warnings |
|---|---|
| 3 | 0 |


✅ **SHACL REJECTS the write (Violations > 0)** — 3 Violation(s) — the write gate is not vacuous


**Violation messages**


| message |
|---|
| This agent does not hold :LyricistRole. |
| writtenBy must point to a :MusicalAgent. |
| writtenBy must point to an agent who holds :LyricistRole. |


✅ **Graph conforms again after rollback** — 0 Violations


## Scenario 4 — DELETE WHERE — and why subject-position-only is not a deletion

Note the form first: `DELETE WHERE` is its own production in the SPARQL 1.1 grammar and takes **no `WITH` clause** — only the `Modify` form (scenario 2) does, so the target graph is named with an inner `GRAPH` block. Rewriting this as `WITH <…> DELETE WHERE {…}` is a parse error, not a style preference.

Now the substance. The delete pattern binds the artist as a **subject**, so anything pointing *at* him survives it. The inbound edge here is asserted by this demo (shown above) — the artist is new, so nothing in the catalogue points at him yet. In a real catalogue it is the normal case, not the exception.

It also gets strictly worse under a reasoner: `:collaboratesWith` is declared `owl:SymmetricProperty`, so a store doing OWL entailment would *derive* an inbound edge from the artist's own outbound one — and a subject-only delete would leave that behind too. rdflib does no OWL reasoning, so this run only sees the asserted edge.

```sparql
# Setup: another agent asserts an edge that points AT our artist.
INSERT DATA {
  GRAPH <https://www.somusicvocabulary.org/music/abox> { :DavidBowie :collaboratesWith :JeffBuckley . }
} ;

# The retraction — note it binds the artist in the SUBJECT position only.
DELETE WHERE {
  GRAPH <https://www.somusicvocabulary.org/music/abox> { :JeffBuckley ?p ?o }
}
```


**Before — triples with the artist as SUBJECT**


| predicate | object |
|---|---|
| label | Jeff Buckley |
| bornOn | 1966 |
| type | SoloArtist |
| collaboratesWith | BobDylan |
| hasGenre | Rock |
| hasInstrument | Guitar |
| hasInstrument | Voice |
| originatesFrom | UnitedStates |


**Before — triples with the artist as OBJECT**


| subject |
|---|
| DavidBowie |


✅ **Subject-position triples are gone** — 8 → 0


**After — the inbound edge SURVIVED**


| subject |
|---|
| DavidBowie |


✅ **The naive delete leaves a dangling inbound edge** — 1 edge(s) still point at a node that no longer exists


## Scenario 5 — The complete retraction — sweep the object position too

The companion to scenario 4's delete: same form, but the artist is bound in the **object** position. Only with both halves run is the node genuinely gone. In production these two would be issued as one request, separated by `;`.

```sparql
DELETE WHERE {
  GRAPH <https://www.somusicvocabulary.org/music/abox> { ?s ?p :JeffBuckley }
}
```


**After — inbound edges**


_(empty result set)_


✅ **No dangling edges remain**


✅ **ABox restored to its original :SoloArtist count** — 15 (started at 15)

