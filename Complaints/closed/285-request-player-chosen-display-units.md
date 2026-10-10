# Request: let the player choose display units (area, mass, temperature, money), with one unit layer that mods can extend and a test that proves every screen goes through it

**Status:** closed - registry, formatters, options, JSON `_display` fields, compound units, sentences written by the engine, civilisation display units and units typed in commands are all in; see the third increment

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

## Third increment (closes the request)

- **Engine prose.** `sim/engine/units_prose.py` writes a quantity inside a sentence (`money_text`, `mass_text`, `area_text`, `temperature_text`, `mass_rate_text`, `mass_per_area_text`; `plain_number` for counts, hours and people). With nothing chosen the text is the one the game wrote before; otherwise the number is converted and the chosen unit's name (singular or `plural` from the registry) follows it. Every sentence found by the scan was converted: refusals, advice, log lines and notes in `sim/engine/`, `sim/labour/` (through `LabourWorld.money_text`), `sim/agents/` (through the world the petition is lodged with) and `sim/ui/proto/`.
- **The check.** `test_complaint_285_no_hand_units` (no game is built, a few seconds) fails on a string that puts a placeholder beside a unit word, on `{:,.0f}`-style separators written by hand, on a call for the currency word outside the formatters, on a sentence that prints a money source (capital, a price, an upkeep) without `money_text`, on a reply key that reads like a quantity but has no field rule, on a rounded reply field that is not ruled, tagged or listed as not a unit quantity, and on a text-screen line that prints a native unit beside a key with no rule. Files that may format by hand are listed in the test with a reason (text screens over an already converted reply, the developer analysis subcommands, model reprs, data-author messages).
- **The detector is data, not a private list.** `quantity_words` and `not_quantities` in `data/world/units.json` define what reads like a quantity (`units.looks_like_quantity`); the text-screens test and the static scans share it. A producer can also state a field's unit where it builds the reply: `units.tagged(reply, field="mass:tonne")` (a compound is `"money:civ_coin/area:hectare"`), carried in the reply's `field_units`. Field rules gained `within` (a rule that applies only inside a field of a given name, for `cost.total`). The scan found a good many money fields that had no rule (`to_buy_it`, `you_have`, `you_could_raise`, `per_unit`, `a_year_of_one` and others); they now have one.
- **`why`, `path`, `anatomy`.** `test_complaint_285_hand_screens` renders `why` and `path` from hand-written replies in the shape the dispatchers build (with a fake unit for money and mass) and checks the anatomy rows name no unit of a dimension a player can change.
- **Temperature.** No screen or reply shows a temperature: no string or key under `sim/ui/` mentions one (the production data keeps it in the engine). The item is moot; the test fails if a screen starts mentioning temperature without a rule (`furnace_temperature_c` style names already match one) and `temperature_text` is ready for the sentence.
- **Commands.** `buy`, `quote` and `sell` (farm, forest, nitre, mine, material), `bribe` and the `rush`/`pursue` caps take a `unit` (id, name, plural or symbol of a registry unit of the right dimension, or `shown`), or the typed form `buy farm 10 acre`, or `"n": "10 acre"`; the engine converts through the registry. Without a unit the quantity is the native one, so scripts never depend on a display choice. The table of which target takes which dimension is `TARGET_QUANTITY` in `sim/ui/proto/buy_targets.py`.
- **Civilisation units.** A civilisation file may name `display_units` (`{"area": "iugerum", "mass": "libra"}`); those are shown for any dimension the player has not chosen (`units.set_civ_defaults`, applied by the interactive front end and `agent --pretty`, not by JSON replies for scripts). `validate` checks the names against the registry. Rome names the iugerum and libra; Han China the mu and jin, added to the registry for it.

Not converted, on purpose: sentences in the developer analysis subcommands (`cli.py`, `cli_analysis.py`), model reprs and messages for data authors, and the carrier labels inside `sim/geography/` (audit labels, not shown). Localisation of the prose itself is Complaint 362.

Owner decision (2026-10-02): nice to have, longer and lower priority.
