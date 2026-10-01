# A failed project charges the full book material bill, 26 to 100 times the `why` forecast once materials were bought or mined: blast furnace forecast about 32 thousand, lost about 847 thousand; industrial zinc forecast 119 thousand, lost 11.8 million

**Status:** closed

`why` prints "IF IT FAILS: N gone (40% of the money)"; a failure then subtracts a different number. The tester's blast furnace (133 AD) quoted 31,947 and took 846,998; industrial zinc (270 AD) quoted about 119 thousand and took 11.8 million; bulk steel took 6.2 million. Cash really fell by those amounts.

Mechanism (read from code and measured with `sim/tests/harness.sim("rome_100ad")`):

- Quote: `sim/engine/proto/techtree.py` (`failure_costs`) is `sim.project_cost(node_id) * 0.4`. `project_cost` returns the bill frozen at start: labour and capital plus only the materials NOT already held, priced at the market. Since complaint 147 the start also buys what the market can deliver into stock (`project_materials.settle_project_materials`, `buy_project_materials`) and that money is already paid, so the frozen bill shrinks by it, and owned stock or own-mine output shrinks the missing part further.
- Charge: `sim/engine/projects_completion.py` (`_complete`, `_lost`) is `node["_total_cost"] * FAILURE_RESET_SHARE * cost_money_factor()`. `_total_cost` is labour plus capital plus the static book `_material_cost` (`sim/engine/money_units.py`, `price_nodes`), the whole material bill at book prices whatever you hold, mined or already paid for at the start. The stock itself stays on hand, so the materials are paid twice.

Measured for Rome at arrival with nothing held: blast_furnace quote 365,587, charge 846,998 (the tester's exact charge); mat_bulk_steel quote 6.25 million, charge 6.24 million (they agree only while nothing is held); zinc_industry_scale quote 7.40 million, charge 11.80 million (the tester's 11.8 million). The gap therefore widens exactly as the player does the sensible thing the game rewards: sink a mine, buy the charcoal, or buy materials up front. With a coal mine the blast furnace forecast fell to about 32 thousand and the charge stayed 847 thousand.

This is the same two-call-site disagreement as complaint 214 (there the civilisation and opposition factors; here the materials), now a factor of tens. The tester avoided nothing: they could not price a retry, and lost 11.8 million where they expected 119 thousand.

What it would take (not done here): one function for "what a failure costs" used by the quote and by `_complete`, based on what the player actually paid in (bill as frozen plus up-front materials), and a regression test that, after `buy_project_materials` and with stock in hand, the charge equals the quote. Decide whether bought materials should be lost on failure at all (they are still in stock). Also: 218, 151, 241.


Found in the final blind playtests of this branch (Rome 100 AD fog, won 301 AD; tester bug 1; Rome, measured by harness). Reports: `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.
