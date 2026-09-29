# Nothing validates that a starting state agrees with itself

**Status:** open

**Source:** `reports/COMBINED_TECH_TREE_REALISM_REVIEW_part_01.md`, suggestion 6 (audit scenario grants for internal contradictions automatically).

## What is wrong

The review found its worst problems by hand: a start that owns iron and glass
but a low heat rung, a briefing that says "no iron" while the loaded state has
wrought iron and iron-tyred wheels. The existing check
(`sim/tests/test_civilisation_prerequisites.py`) covers missing prerequisites
only, and holds a known count (`Complaints/42`). Nothing compares a
civilisation's briefing, capability rungs and owned techs against each other.

## Evidence

- `sim/tests/test_civilisation_prerequisites.py` and
  `sim/tests/test_explicit_starting_techs.py` check prerequisites and the
  grant set, nothing about capability ceilings or briefing claims.
- `data/civilizations/_SCHEMA.md` lists the fields a start declares.

## Why it matters

Every new scenario and every mod that adds a start (`mods/`) can reintroduce
these contradictions silently; a validator catches the class instead of one
node at a time.

## What it would take

A `validate` step that, per civilisation, derives the highest capability rung
each owned technology implies from the tree's own capability nodes and flags a
lower declared rung, and checks declared "absent" facts (for example a
`needs_first` group) against owned techs. Data-driven, no civilisation ids in
code. Test with a deliberately broken fixture.
