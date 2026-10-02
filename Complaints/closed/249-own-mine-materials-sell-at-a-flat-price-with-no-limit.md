# Material stock sells at a flat 80% of the buy price with no volume limit, price impact or link to demand, so mine output can be sold for years of demand at once (coal about 108 a tonne, 7,000 t in one command)

**Status:** closed

The tester ran a 4,000 t/yr coal mine at about 10 a tonne, then `sell coal 7000` returned about 755 thousand (about 108 a tonne) while `materials` listed demand at 254.5 t/yr. Selling 28 years of demand barely moved the price.

Cause: `sell_material_stock` (`sim/engine/economy_materials.py`) pays `sold * sell_per_tonne`, and `material_trade_quote` sets `sell_per_tonne = buy * MATERIAL_TRADE_SELL_SHARE_OF_BUY` (0.8) with a flat buy price; it is capped only by stock on hand. The buy side is limited to `market_available_tonnes_per_year` and its price climbs as the order fills; the sell side has neither. Measured (harness, Rome 100 AD, 50,000 t of coal in stock): quote 134.76 buy, 107.81 sell; selling 1, 100, 7,000 and 20,000 t each returned 107.81 a tonne (754,647 for 7,000, 2,156,134 for 20,000) and the quote did not move. The 7,000 t case reproduces the tester's figure.

Why it matters: a mine is an unbounded money machine against a price the same calculation says is the long-run cost, at a time when the tester says money is scarce only for the first fifteen years. Geology bounds it (the tester noted regional caps) but nothing ties the sale to buyers. It conflicts with CLAUDE.md 4.3 (interventions pass through ordinary rules: a market is demand) and is a clean exploit for any player.

What it would take: a sell quote that falls with the volume sold against the year's demand (and recovers), limited to the tonnes the market absorbs per year like `buy_material_stock`; a test that selling ten years of demand in one command returns far less than linear. Related: 147, 174, 212, 103.


Found in the final blind playtests of this branch (Rome 100 AD fog, won 301 AD; balance and exploits; reproduced with the harness). Reports: `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.
