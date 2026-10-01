# Request: let the player choose display units (area, mass, temperature, money), with one unit layer that mods can extend and a test that proves every screen goes through it

**Status:** open

Stakeholder request. Screens show quantities in whatever unit each piece of code happened to use: land in iugera or hectares, mass in kg or tonnes, temperatures in Celsius, money in the civilisation's coin. A player should be able to pick preferred units in the options (for example square kilometres, hectares or the civilisation's own land unit; Celsius, Fahrenheit or kelvin; kilograms, pounds or a civilisation's own weight; the civilisation's coin, labour hours, or another currency). The default stays exactly what the game shows now.

## What it needs

- **One internal unit per dimension.** The engine already works in physical units in most places (hectares since the physical-units work, kilograms or tonnes, labour hours; see `Complaints/136`, `144`, `282`). Each dimension gets one declared base unit, and every quantity that reaches a player is tagged with its dimension where it is produced, not formatted ad hoc where it is printed.
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
