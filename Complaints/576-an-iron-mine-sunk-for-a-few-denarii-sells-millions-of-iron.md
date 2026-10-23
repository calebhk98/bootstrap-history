# An iron mine sunk for a few denarii sells millions of iron

**Status:** open

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md`, Rome, seed 11, around 109 AD). `buy mine iron 100` cost a few denarii to sink and
tens a year to stand; the founder's iron then sold at thousands of denarii a tonne, so a few thousand tonnes raised
millions. The player made and sold something, so it is not an exploit by the rules, but the margin is not plausible.

Measured: Measured 2026-10-21 on main 3cb9c9a0, an opened Rome game with the full spin-up: from a checkout root, `from sim.tests import harness; import os; os.environ.pop("ROME_SPIN_UP_YEARS", None); game = harness.sim(capital=1e7)`, then the reads named below. A `quote mine iron 100` costs a little to sink and more each year to stand; per kilogram of ore a year that is about the median iron-ore price across tiles, so at the median the mine earns about its cost. But iron-ore prices spread across tiles by several hundredfold (read `record.memory.prices` for `iron_ore_kg|<tile>`), so a sale read at one tile's ask can be far above the mine's cost. How the founder's mine output reaches a buyer was not traced here: if it is valued at the home sellers' ask with no check that buyers exist, as a founder concern's output is (668), the fix is 668's (the founder sells into the year's clearing); the price spread itself is 473's. Trace the mine output's sale path (`sim/engine/economy_mining.py` and the material stock it adds to) before closing. Earlier reading: iron opened far above its making cost on the branch of the playtest. 519 (now narrowed to precious ores; its common-ores check passes) records the cause as a year of inputs stocked at the opening and the fix of opening producers with a working stock instead, held back until the spin-up settles (473). Measure the founder's mine cost per tonne against the shown iron price at the opening, and check `sited_ore_price_over_cost` against the current red list in 558.

What it would take: iron near its cost at the opening (519, 473), and a test that a founder's mine output sells at
a bounded multiple of its cost per tonne.

## Trace of the mine output's sale path (founder-sells-into-clearing)

A mine does not sell anything by itself. `sim/engine/economy_mining.py` turns a tranche into a working
(`commission_mines`), whose yearly tonnes (`mine_yield_t_for`) are an own supply (`_own_material_supply("mine:<material>")`,
`sim/engine/economy_materials.py`) that the founder's works draw on as an input. Ore the founder sells goes through the
`sell` order (`GoodsMarket.sell`, `sim/engine/goods_market_api.py`), which is not the home-ask path of 668: it pays
`sale_proceeds` (the economy's price on the tile falling with the tonnes sold) at once, cut to `market_room_tonnes`, which was
the tonnes the sellers offered, not what buyers want. That cap is now `sale_room_tonnes`: no more than the buyers took
and still wanted last year (`market_record` sold plus unmet) where the economy trades the good, so a good no one bought
sells nothing (`sim/tests/test_sale_room_follows_buyers.py`). A concern the founder runs on the ore sells its product through
668's path. What is not fixed: the price spread across tiles (473), and `sell` still pays at once at the price the book last
showed, not from the year's clearing. Whether a founder's iron now sells at a bounded multiple of its cost was not measured
(no spin-up run here): measure with the commands in the 668 hand-off.
