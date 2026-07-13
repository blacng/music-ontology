# Negative SHACL fixtures

Each `.ttl` here is **deliberately broken**: it is crafted to violate exactly one shape.
`scripts/check_shacl_negative.py` asserts that each one **actually fires the expected shape**,
and fails the build if a fixture *conforms*.

## Why this exists

A SHACL gate reporting `0 Violations` proves nothing on its own. A shape that targets zero
nodes, a shape whose constraint has been neutered, and a shape that genuinely passes are all
indistinguishable from the outside — they all report zero. `make shacl` was **vacuously green**:
it could not tell you whether the shapes were working or merely silent.

This bit us concretely. A previous release claimed `:CareerOnsetShape` was *"verified with a
negative test — a `:RecordLabel` claiming a career onset is rejected."* No such fixture existed.
The test lived in a throwaway shell heredoc, was never committed, never ran in CI, and passed
only because the one input chosen could not have revealed the shape was broken. The claim then
propagated into four files.

So: **if a shape is worth having, its negative case is worth committing.**

## Rules

1. **One fixture, one shape.** A fixture that trips two shapes tells you nothing precise.
2. **Fire for the right reason.** The gate matches on `(focusNode, constraintComponent, path,
   severity)` plus a message substring — not merely `conforms == False`. A typo'd IRI that trips
   a *different* shape is a failure, not a pass.
3. **Not all expectations are Violations.** `:MusicianShape` carries node-level
   `sh:severity sh:Warning`. A gate keyed on Violation *count* would silently pass its fixture.
   Expected severity is declared per-fixture in `manifest.json`.
4. **Validated standalone** — own data graph + TBox + shapes. Never merged with the catalogue,
   so a fixture cannot be masked by, or accidentally repair, real data.
5. **Adversarial construction.** Build the fixture trying to make the shape *pass* when it should
   fail. Add one ordinary extra triple and check the guard still holds.

## Proving the gate itself works

A negative harness that has never been *observed failing* has proved nothing. Mutate a shape
(delete a `sh:minCount`, revert the taxonomy-only `ont_graph` strip) and confirm the gate goes
red. That mutation test is the only thing that establishes this directory is not decoration.
