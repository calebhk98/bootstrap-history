# Ink needs olive oil and tallow candles need cotton, so England cannot make either

**Status:** open

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
