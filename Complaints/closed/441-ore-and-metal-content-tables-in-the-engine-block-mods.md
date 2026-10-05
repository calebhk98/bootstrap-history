# Ore-to-deposit and mine tables in the engine name content ids, so mods cannot add a mineral

**Status:** closed - the three tables are catalogue data; `ore_and_mine_tables_from_data` (sim/tests/test_ore_and_mine_tables_from_data.py) pins the derived tables to the old literals and adds an ore from a mod

CLAUDE.md 4.7: the engine never special-cases content ids. Three tables do:
- `RENT_BEARING_ORE_MATERIALS` in `sim/engine/solve_prices_core.py` maps eight ore goods to a deposit
  metal and the goods smelted from them (`"iron_ore_kg": ("iron", ("pig_iron_kg", "iron_bloom_kg"))`);
- `METALS` in `sim/world/deposits.py` fixes the seven metals a deposit may hold;
- `MINE_OPEX_MATERIALS` and `MINE_TRADE = "miner"` in `sim/engine/economy_mining.py`.

A mod adding an ore, a deposit or a mining trade must edit engine code. The link belongs in data: each
deposit entry (`data/world/deposits.json`) can name the extraction recipe or good it feeds, and the
smelting link is already in the production data (a recipe's inputs).

What it would take: a `feeds` (or `ore_good`) field on deposit entries, read by geography; the
solver and the founder's mines read the link from data; the three tables go. The agent economy
needs none of this: it takes site limits per recipe (Complaint 440).

## Done

- `ore_goods` and `works_priced_from_deposits` fields on the resource rows in `data/world/geography/resources/`
  (minerals.json, energy.json); `mining_trade` in `parameters/resources.json` (still a labelled heuristic).
  `sim/geography/resource_links.py` reads them; `deposits.metals()` and `deposits.rent_bearing_ore_materials()`
  (and `MiningMixin.MINE_OPEX_MATERIALS` / `MINE_TRADE`, now properties of the game's map) take them from there.
- The literals in `solve_prices_core.py`, `deposits.py` and `economy_mining.py` are gone. The deposit loader
  (`load_deposits`) and the solver's rent function still read the base map; passing a mod's map through them is
  the follow-up for a mod that adds deposits, not only the link.
