# Engine code names civilisation ids

**Status:** closed - pinned by sim/tests/test_civilisation_independence.py (the guard scans engine, world and tool code for every civilisation id in data/civilizations)

CLAUDE.md section 4.7: the engine never special-cases content ids. These do.

## Evidence

Find them with:

    grep -rn '"rome_100ad"\|"han_china_100ad"\|"norse_900ad"\|"mexica_1500"\|"england_1300"' sim/engine sim/world --include=*.py

- `sim/engine/society_diffusion.py`, `_is_foreign_institution` and
  `_is_foreign_only`: a fast path returns "not foreign" when the civilisation
  id is Rome. The foreign-institution test matches name markers written from
  a Roman point of view, so Rome is exempted by id rather than by what the
  node is. A mod civilisation, or Rome renamed by a mod, gets the wrong answer.
- `sim/engine/cli.py`, `DICE_FREE_FLOOR_YEARS`: a hand-updated table of
  measured years keyed by civilisation id. It goes stale when the tree changes
  and says nothing for any other civilisation.
- `sim/engine/cli.py` fallbacks to `"rome_100ad"` when no civilisation is
  given, instead of the `default_civ` setting in `sim/engine/settings.py`.

## Why it matters

Mods can now patch, hide or add civilisations, and the game is heading to
multiplayer. Any behaviour keyed on an id silently diverges for every
civilisation that is not the one named.

## What it would take

- Tag institutions with the society that created them (data on the node) and
  compare against the civilisation's own society tag, so "foreign" follows
  from data for every civilisation.
- Compute the dice-free floor on demand (or cache it per tree version), or
  drop the number from the menu.
- Route every fallback through the `default_civ` setting.
- Add a guard test that fails when a civilisation id literal appears in
  `sim/engine` or `sim/world` outside settings.
