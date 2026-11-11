# An iron mine sunk for a few denarii sells millions of iron

**Status:** closed - sales of a pool are priced and cleared as the form its mines raise (`raised_material`), so mined ore can no longer be sold at the bar price; the whole-game re-measure is pending

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md`, Rome, seed 11, around 109 AD). `buy mine iron 100` cost a few denarii to sink and
tens a year to stand; the founder's iron then sold at thousands of denarii a tonne, so a few thousand tonnes raised
millions. The player made and sold something, so it is not an exploit by the rules, but the margin is not plausible.

Measured: Measured 2026-10-21 on main 3cb9c9a0, an opened Rome game with the full spin-up: from a checkout root, `from sim.tests import harness; import os; os.environ.pop("ROME_SPIN_UP_YEARS", None); game = harness.sim(capital=1e7)`, then the reads named below. A `quote mine iron 100` costs a little to sink and more each year to stand; per kilogram of ore a year that is about the median iron-ore price across tiles, so at the median the mine earns about its cost. But iron-ore prices spread across tiles by several hundredfold (read `record.memory.prices` for `iron_ore_kg|<tile>`), so a sale read at one tile's ask can be far above the mine's cost. How the founder's mine output reaches a buyer was not traced here: if it is valued at the home sellers' ask with no check that buyers exist, as a founder concern's output is (668), the fix is 668's (the founder sells into the year's clearing); the price spread itself is 473's. Trace the mine output's sale path (`sim/resources/workings.py` and `sim/resources/materials_phase.py` and the material stock it adds to) before closing. Earlier reading: iron opened far above its making cost on the branch of the playtest. 519 (now narrowed to precious ores; its common-ores check passes) records the cause as a year of inputs stocked at the opening and the fix of opening producers with a working stock instead, held back until the spin-up settles (473). Measure the founder's mine cost per tonne against the shown iron price at the opening, and check `sited_ore_price_over_cost` against the current red list in 558.

What it would take: iron near its cost at the opening (519, 473), and a test that a founder's mine output sells at
a bounded multiple of its cost per tonne.

## Trace of the mine output's sale path (founder-sells-into-clearing)

A mine does not sell anything by itself. `commission_mines` (`sim/resources/workings.py`) turns a tranche into a working, whose yearly tonnes (`mine_yield_t_for`) are an own supply (`_own_material_supply("mine:<material>")`, no longer in the code; grep `mine:` for the current reader) that the founder's works draw on as an input. Ore the founder sells goes through the
`sell` order (`GoodsMarket.sell`, `sim/markets/goods_market.py`), which is not the home-ask path of 668: it pays
`sale_proceeds` (the economy's price on the tile falling with the tonnes sold) at once, cut to `market_room_tonnes`, which was
the tonnes the sellers offered, not what buyers want. That cap is now `sale_room_tonnes`: no more than the buyers took
and still wanted last year (`market_record` sold plus unmet) where the economy trades the good, so a good no one bought
sells nothing (`sim/tests/test_sale_room_follows_buyers.py`). A concern the founder runs on the ore sells its product through
668's path. What is not fixed: the price spread across tiles (473), and `sell` still pays at once at the price the book last
showed, not from the year's clearing. Whether a founder's iron now sells at a bounded multiple of its cost was not measured
(no spin-up run here): measure with the commands in the 668 hand-off.

## Measurement on the rebuilt openings (commit 2094a71f, Rome, default start)

Commands (from the checkout root, `env -u ROME_SPIN_UP_YEARS python3 sim/simulator.py agent --civ rome_100ad`, JSON lines on stdin;
the CLI path loads from the shipped openings in about five seconds, whereas `harness.sim(capital=1e7)` misses the shipped key and
starts a cold spin-up): `buy mine iron 100`, four `step` years, `sell iron 99`, one `step`. Spread read after the run from the
economy's `record.memory.prices`.

- Mine cost: `quote mine iron 100` gives 24.9 coin to sink (three years to produce) and 391 a year to stand; the first standing
  year is charged 521.8 and the next 473.0 (wage and price index move). That is about 4.7 to 5.2 coin per tonne a year; the sinking cost
  annualised over any plausible life adds well under 0.1 coin per tonne a year.
- Sale: `sell iron 99` is posted at the quote of 1605 coin a tonne (limit 1584) and settles at the year's clearing. The founder's capital went
  from 1420.5 (same year, no sale) to 156692.9: 155272 coin for 99 tonnes, 1568 coin a tonne.
- Ratio: 1568 / 4.7 to 5.2 is about 300 to 330 times the mine's cost per tonne. This is far outside the opening check's band
  (`price_over_cost_sited_ores` reads 3.37 because it compares the ore price with the ore cost).
- Price spread, `iron_ore_kg|<tile>` over 157 tiles: min 0.00587, median 0.01494, max 0.01812 coin per kg (5.9, 14.9, 18.1 per
  tonne), a threefold spread, not hundredfold. At the median ore price the mine earns about 3 times its running cost.

Cause: the mine yields ore (`mine_labour_hours_per_tonne`, running hours per tonne of ore at the miner's wage), but the commodity `iron`
(`data/world/commodities.json`, `material_keys` bar, ore, bloom, sheet, cast iron; `price_material: iron_bar_kg`) is sold through
`GoodsMarket.post_order` -> `economy_good` -> `priced_key`, which prices the whole commodity pool as `iron_bar_kg`. The `iron_ore_kg`
good the economy trades at about 15 coin a tonne is not the one the sale is priced and cleared in. So 668's room cap (buyers took
the bar good, which is traded in volume) does not bind, and the ore is paid as bar iron. The same shape holds for any commodity whose
`price_material` is a worked form of what the mine raises.

## Fix

A held tonne of a commodity pool sells as the form its mines raise. `data/world/commodities.json` gives a commodity an optional
`raised_material` (iron: `iron_ore_kg`; copper: `copper_ore_kg`; documented in `data/world/COMMODITIES.md`). `prices.rules.sold_material`
returns it (else the material itself), and `GoodsMarket` prices, limits and clears every sale (`quote`, `quote_sell`, `post_order` on
the sell side, through `GoodsPricing.sold_as`) in that good, so `sell iron` and `sell iron_bar_kg` are both paid the ore good's price and
capped by what buyers of ore took (668). A buy is unchanged (a bought tonne is priced as the pool's `price_material`). A founder who wants
bar iron's price has to make bar from the ore, with the smelting concern, whose output is sold through the concern path (668), not the
mine's tonnes.

Regression test: `sim/tests/test_pool_sells_as_raised_form.py` (`sold_material`).

Known limit: the stock ledger holds one counter per commodity, so a tonne of bar the seat bought sells as ore too (a loss, not a gain).
Splitting the pool's stock by form is a wider change and is not made here; no engine code names iron.

Whole-game re-measure is pending (orchestrator): `buy mine iron 100`, four `step`, `sell iron 99`, `step` on `rome_100ad`; the
sale should now settle near the ore price (about 15 coin a tonne), a small multiple of the mine's cost per tonne.
