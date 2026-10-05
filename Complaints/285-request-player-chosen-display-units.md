# Request: let the player choose display units (area, mass, temperature, money), with one unit layer that mods can extend and a test that proves every screen goes through it

**Status:** partly - registry, formatters, options, JSON `_display` fields and the compound-unit rule are in, and every read-only text screen passes `sim/tests/test_complaint_285_text_screens.py`; the remains below are open

Stakeholder request. Screens show quantities in whatever unit each piece of code happened to use: land in iugera or hectares, mass in kg or tonnes, temperatures in Celsius, money in the civilisation's coin. A player should be able to pick preferred units in the options (for example square kilometres, hectares or the civilisation's own land unit; Celsius, Fahrenheit or kelvin; kilograms, pounds or a civilisation's own weight; the civilisation's coin, labour hours, or another currency). The default stays exactly what the game shows now.

## What it needs

- **One internal unit per dimension.** The engine already works in physical units in most places (hectares since the physical-units work, kilograms or tonnes, labour hours; see `Complaints/132`, `140`, `278`). Each dimension gets one declared base unit, and every quantity that reaches a player is tagged with its dimension where it is produced, not formatted ad hoc where it is printed.
- **A unit registry in data.** Units are data: a name, a symbol, a dimension, and a conversion to the base unit (a factor, or a factor and offset for temperature). Civilisation units (iugerum, mu, acre; the civilisation's coin from `currency_words`) are entries in the same registry, so a civilisation or a mod adds a unit by adding data, never engine code (CLAUDE.md 4.7).
- **A preference per dimension** in the options and settings (`sim/engine/settings.py`), saved like the other game options, defaulting to the current display.
- **One formatting path.** Every screen and every JSON reply converts through the registry. The JSON protocol keeps base-unit numbers alongside the converted display value, or states its unit explicitly, so agents reading JSON never have to guess.

## The test that proves it

A test registers a fake unit per dimension (for example `blob` = 0.0015 km² for area, and likewise for mass, temperature and money), selects them, then renders every screen and JSON reply that shows that dimension. It checks that:

1. every displayed quantity of that dimension is labelled `blob`;
2. no quantity is still labelled in the base unit or any other unit, which catches formatting that bypasses the layer;
3. the numbers equal the base values converted by the fake factor, and are therefore not equal to the base values.

The same test, with a mod supplying the fake unit, proves mods can add units.

## Why it matters

It removes a whole class of unit mix-ups (the iugerum and hectare split in `282`, money in book denarii in `144`), makes the game readable for players who think in other units, and gives mods a supported way to add a civilisation's own measures.

## Related

`136` (the game assumes Rome's units), `144` (money in physical units), `207` (what the currency unit means), `282` (production data names land in iugera), `122` (the mod system).

## Done (first increment)

Registry `data/world/units.json` (mods add `<mod_id>:<name>` units the same way they add other world data), `sim/engine/units.py` (one `format_<dimension>`), `sim/ui/units_text.py`, a `display_units` setting and the options entry (main menu 5, in-game `u`). The default shows exactly what the game showed. Test: `sim/tests/test_complaint_285_display_units.py` (fake `blob` unit per dimension, in memory and from a mod).

Covered: every JSON reply (any field the registry's `field_rules` match gets a `_display` sibling); text screens `buy` (farm, forest), `materials`, `state`, `money`, the `why` materials heading and the coin hoard line; money labels on every screen through `render_pretty`. Mass-per-year fields have no field rule yet (424).

## Second increment

Compound units: a field rule with `per_dimension` and `per_native` (money per mass: `buy_per_tonne` and its siblings) converts both parts by the player's choices, and `units_text.per_mass_heading` writes the `BUY`/`SELL` column headings of the `materials` and `market` screens. Money rules now cover the wage, cost, interest, debt and revenue fields the screens show. The policy description no longer embeds a sum.

Test `complaint_285_text_screens`: plays a short game, chooses a non-default unit for every dimension, renders every read-only text screen plus `quote` and `buy`, and fails on a native label (tonne, hectare, den, `/T`) or on a quantity-like numeric reply field with no field rule (`QUANTITY_KEY` in the test; counts and ratios are listed in `NOT_A_QUANTITY`).

## Remains

- Prose built inside the engine (event log lines such as the patron-heir sentence naming denarii, refusal and advice sentences with a quantity) is not converted; the test renders only the structured screens.
- The detector is a name heuristic: a quantity field named outside `QUANTITY_KEY` is not noticed. Tagging at the point a quantity is produced is still to do.
- Screens that need a technology or a deposit argument (`why`, `path`, `anatomy`) are not in the test's game.
- Temperature: the formatter and field rule exist, but no screen shows a temperature yet.
- Commands accept native units (hectares, tonnes) whatever is displayed.
- Civilisation units are listed in the registry with a `civilisations` limit; civ data does not yet reference its own units, and only Rome has any.

Owner decision (2026-10-02): nice to have, longer and lower priority.
