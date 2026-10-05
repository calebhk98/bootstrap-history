# Projects price materials far above market, never draw owned stock, and paying does not deliver the flow

**Status:** partly - projects price only the materials they lack at the current market quote (rising as the order fills), draw owned stock and own output first, and buy what the market can deliver at start into stock; `why` lists per-material need, held, missing and cost, and names owned output that lowers the scarcity premium (`scarcity_note`, test sim/tests/test_complaint_147_owned_supply_note.py). Remains: the part beyond what the market sells in a year is charged at the start price in instalments instead of bought year by year, and own output is counted per project without competition from other projects. `_material_cost` is not stale data: money_units.py derives it at load from the node's material hours, and `project_cost_without_materials` only uses it to subtract the book material share from the total, so it stays until 182 retires the book.

Price: at 129 AD, buying 1 t showed charcoal_kg ~101 den/t and firewood_kg ~24 den/t; `materials` listed galena_kg at 73.5 den/t. `why lead_metallurgy` lists MATERIALS charcoal_kg 300,000 + galena_kg 280,000 (~30.5k + ~20.6k at those prices) but charges 532,296 for materials before the civ multiplier.

Stock: I bought 300 t of charcoal and held ~7,000 t of galena from my own mine, then `start lead_metallurgy`. The bill was unchanged; after `step 1` `money` showed the full amount spent and `materials` showed both stocks untouched. `buy material firewood_kg 400` likewise left `why charcoal_industrial` unchanged.

Flow: at 549 AD `start mat_bulk_steel` took the whole 14.8M bill, most of it "materials" (coal 38,400 t, iron ore 30,000 t), and the project then ran at 16% pace: "waiting on materials: this project consumes coal, whose shortage has it running at 16%". `capacity` showed coal 3,331 t/yr against 20,774 demanded. `buy material coal 5000` delivered only 3,331 t at ~408/t against a 134.8 book price. So the materials charge buys nothing physical.

What does work, undocumented: owning supply lowers the *scarcity* multiplier. `buy forest 500` cut `why zinc_industry_scale` from 63.0M to 26.7M (scarcity x2.511 -> x1.063).

Why it matters: this decided the run. The mid-game became a wall of 0.3-0.5M (later 15M, 63M) nodes, and `why zinc_industry_scale` needs 54,000 t of charcoal against ~425 t/yr of supply, which no screen flagged until the money was spent.

What it would take: one consistent material price between market and project; projects drawing owned stock/mine output first (or stop charging for materials that the flow must supply anyway); `why` showing "at today's supply this takes about N years" and the shortfall per material; `why` saying which owned supply lowers scarcity.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Related: 174 (market price information), 182 (the solver is off by default, so project costs come from the price book).

## Stakeholder decisions

- One source of truth. A research node declares only physical needs: materials (quantities) and people (trades, hours). It never states a price. The economy links those quantities to the current market price and to demand automatically, so research authors never touch prices (this is also why `data/prices.json` is being deleted, see 182).
- Overview screens (`available`, `path`, the `why` headline) show what the whole project would cost if every missing material were bought now at current market prices.
- The detail view (`why <id>`) shows, per material: the quantity needed, how much you already hold (stock and own output), what is missing, and what the missing part costs at current market prices.
- Buying is demand: a project that needs a large quantity (e.g. copper for a nationwide power grid) raises that material's price as it is bought, through the normal market rules, not a special case.
- Projects draw owned stock and own output first; paying for a material delivers it (no separate "materials fee" on top of physical supply).

## What was built

- `sim/engine/project_materials.py`: the project side asks the economy for the price and availability of quantities. `project_material_bill(node)` returns rows (needed, held from stock and own output, missing, mean price, cost of the missing part). `material_purchase_cost` prices an order along the same capped quadratic scarcity curve as `material_price_factor`, adding the order to that material's yearly demand.
- `project_cost` (economy.py) is labour and capital (civ and price factors) plus the missing materials at market, times distance and opposition. An active project keeps the bill fixed at its start (`bill` in its record).
- `start` (projects_starting.py) buys the deliverable part of the missing materials into stock and refuses the start if that money cannot be raised; the rest is paid in instalments and the supply throttle still paces it.
- `buy material` and `quote material` use the same order pricing, and stock is kept under the commodity key the throttle reads, so buying `charcoal_kg` now feeds the throttle.
- Test: `sim/tests/test_complaint_147_project_materials.py`.

Also reported (England 1300 fog playtest): in 1373 the tester found `lead_metallurgy` quoted at about 7 million pence, which could not be financed even with credit, while their capital was about 3.5 million and recurring income about 700 thousand a year. On the current branch the same node in England 1300 quotes about 409 thousand pence at the start, mostly the "materials you do not hold" line, so the 1375 figure is more than an order of magnitude higher. The growth was not investigated (price index, scarcity premium on the material, or civ multiplier); measure it with `why lead_metallurgy` in a played-forward non-fog game. The tester read the quote as "late projects can still outrun the snowball", which fits the intent of 180 and 190. Report: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 72, 100, 157; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): the finery note cites 3 million kg of charcoal while `capacity` showed coal demand and no charcoal demand (coke substitution is allowed and works, which the tester later praised); bulk steel paid its whole 4.7 billion bill in the first year despite a two-year floor (materials are paid up front, `project_cost_now` splits `_up_front` from labour and capital, and nothing at start says which part is one-off); a 3 MW hydro station research bill was 5 million. Reproduces: untested (late game).

Also reported (final playtests, B; `Complaints/reports/final-playtests-triage.md`): the up-front material purchase interacts badly with failure: a failed project is charged 40% of the full book material bill in cash although the materials were already bought at the start and stay in stock (measured: blast_furnace charge 846,998 against a held-materials forecast of about 32 thousand). Filed as 247. B also praised the supply-chain effect the other way: a coal mine took the blast furnace from 1,003,716 to 105,072 (92% of the bill was coal at scarcity prices), 'the best moment of the run'. Do not lose that in fixing 251.
