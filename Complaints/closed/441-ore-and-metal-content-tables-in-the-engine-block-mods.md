# Ore-to-deposit and mine tables in the engine name content ids, so mods cannot add a mineral

**Status:** open - outside `sim/economy/`

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
