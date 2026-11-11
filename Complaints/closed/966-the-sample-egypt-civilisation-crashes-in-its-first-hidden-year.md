# The sample Egypt civilisation crashes in its first hidden year

**Status:** closed - the setup kept recipes whose inputs have no price (nothing the society can run makes them); it now leaves them out until a technique prices them. The cold Egypt opening itself was not run here; the orchestrator re-runs it

`sample_egypt_100bc_e7k2:egypt` is a mod civilisation with no shipped opening, so a new game runs its own spin-up, and
the first hidden year raises `KeyError: 'meat_kg'` in `MarketAreaMap.area_of` (`sim/economy/market_areas.py`), reached
from `year_close.close_agents` through `expected_sales.market_capacities`. The good has no bucket in the area map, so
some producer or market names a good the map was not built for.

Reproduce (a cold opening, so it takes minutes):

    printf '{"cmd":"state"}\n{"cmd":"quit"}\n' | python3 sim/simulator.py agent --civ sample_egypt_100bc_e7k2:egypt --seed 1

**Why it matters.** A mod civilisation that cannot open is a scenario no player can start, and `civs` still lists it.

**What it would take.** Find which producer, recipe or market carries `meat_kg` into `market_capacities` without a
market-area bucket (the area map is built from the goods the setup declares), then a regression test on the smallest
setup that carries a good the map lacks.

**Cause (found by building Egypt's setup without a game, `build_setup` on an unopened game).** The market-area map is built
from the goods with an opening price; `makeable_prices` drops the price of a good no runnable recipe can make. Egypt holds
none of the herd techniques, so meat, milk, hide, fat and wool have no maker and no price, yet recipes with no
`requires_node` that consume them (salted meat, cheese, felt, glue, leather, ...) stayed in the setup's recipes: forty
recipes whose inputs or outputs had no area. A producer of such a recipe asked for `area_of(meat_kg, tile)` and got a
`KeyError`. Other civilisations hold the herd techniques, so every input is priced.

**Fix.** `port_closure.runnable_recipes` keeps only the recipes whose hard inputs are all priced; `build_setup` applies it
after `makeable_prices`, and `recipes_by_country` lists only recipes the setup holds. A technique gained later prices the
inputs and `admit_recipes` brings the recipe in. Test: `sim/tests/test_complaint_966_recipes_with_unpriced_inputs.py`.

**Not part of this.** Three recipes with priced inputs but an unpriced output (`cassia_kg`, `sugar_cane_sett_native_kg`,
`tea_plant_stock_native_kg`) are in every civilisation's setup, Rome's included, and do not crash there.

**Second path (output slot).** `runnable_recipes` also leaves out a recipe with an unpriced output, and
`opening_with_techniques` prices the goods of every entry the held techniques allow (not only the added ones), so a known
recipe (cheese, salted meat) whose input a late technique newly prices gets its output priced too. Every slot good of every
setup recipe then has a market area, checked on Egypt's setup with and without the herd techniques added.
