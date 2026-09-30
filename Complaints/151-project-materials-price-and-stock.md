# Projects price materials far above market, never draw owned stock, and paying does not deliver the flow

**Status:** open

Price: at 129 AD, buying 1 t showed charcoal_kg ~101 den/t and firewood_kg ~24 den/t; `materials` listed galena_kg at 73.5 den/t. `why lead_metallurgy` lists MATERIALS charcoal_kg 300,000 + galena_kg 280,000 (~30.5k + ~20.6k at those prices) but charges 532,296 for materials before the civ multiplier.

Stock: I bought 300 t of charcoal and held ~7,000 t of galena from my own mine, then `start lead_metallurgy`. The bill was unchanged; after `step 1` `money` showed the full amount spent and `materials` showed both stocks untouched. `buy material firewood_kg 400` likewise left `why charcoal_industrial` unchanged.

Flow: at 549 AD `start mat_bulk_steel` took the whole 14.8M bill, most of it "materials" (coal 38,400 t, iron ore 30,000 t), and the project then ran at 16% pace: "waiting on materials: this project consumes coal, whose shortage has it running at 16%". `capacity` showed coal 3,331 t/yr against 20,774 demanded. `buy material coal 5000` delivered only 3,331 t at ~408/t against a 134.8 book price. So the materials charge buys nothing physical.

What does work, undocumented: owning supply lowers the *scarcity* multiplier. `buy forest 500` cut `why zinc_industry_scale` from 63.0M to 26.7M (scarcity x2.511 -> x1.063).

Why it matters: this decided the run. The mid-game became a wall of 0.3-0.5M (later 15M, 63M) nodes, and `why zinc_industry_scale` needs 54,000 t of charcoal against ~425 t/yr of supply, which no screen flagged until the money was spent.

What it would take: one consistent material price between market and project; projects drawing owned stock/mine output first (or stop charging for materials that the flow must supply anyway); `why` showing "at today's supply this takes about N years" and the shortfall per material; `why` saying which owned supply lowers scarcity.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Related: 178 (market price information), 186 (the solver is off by default, so project costs come from the price book).
