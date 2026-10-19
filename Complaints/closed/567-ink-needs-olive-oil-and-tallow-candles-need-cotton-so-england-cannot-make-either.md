# Ink needs olive oil and tallow candles need cotton, so England cannot make either

**Status:** closed - iron-gall and gum-bound carbon ink recipes, linen and rush wick tallow candles; England prices all three

Found closing 566 (opening prices are now limited to goods a start can make). England 1300 loses `ink_kg`,
`written_page` and `light_tallow_candle` from its opening prices:

- `ink_kg` (`data/production/40_organics.json`) has one recipe, lamp-black in olive oil. Medieval England wrote with
  iron-gall ink (oak galls, iron sulphate, gum, water) and carbon ink bound with gum; neither is a recipe.
- `light_tallow_candle` (`data/production/99_lighting.json`) takes only `wick_cotton_m`. `wick_linen_m` and
  `wick_rush_m` exist but no tallow-candle recipe uses them.

Measure: `PYTHONPATH=. python3 -c "from sim.engine.economy_port_setup import build_setup; from sim.tests.harness import unopened_sim; s=build_setup(unopened_sim(civ='england_1300')); print({g: s.opening_prices.get(g) for g in ('ink_kg','written_page','light_tallow_candle')})"`.

What it would take: an iron-gall ink recipe and a gum-bound carbon ink recipe, each sourced, gated on the knowledge
that makes them; tallow-candle recipes with a linen and with a rush wick (or a wick input any of the three meets).
Test: England 1300 prices ink, a written page and a tallow candle at its opening; Rome still does.

## Resolution

`data/production/40_organics.json` gains `oak_gall_kg` and `gum_kg` (gathered, confidence D), `ink_iron_gall_kg`
(galls, green vitriol, gum, water; gated on `mat_vitriols`, the knowledge behind `if_iron_gall_ink`, which England's
start does not list) and `ink_carbon_gum_kg` (tallow lampblack bound with gum; gated on `prn_carbon_ink`). Both inks
output `ink_kg`. `data/production/99_lighting.json` gains `light_tallow_candle_linen` and `light_tallow_candle_rush`,
both outputting `light_tallow_candle`. Regression test: `sim/tests/test_ink_and_candle_recipes.py` (England and Rome
price all three; Norse prices them; Mexica prices none).
