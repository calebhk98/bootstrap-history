# `stuck` says "159 of them you could pay for" while `start` refuses with "you could raise 0"; the refusal does not state the rule or the number needed

**Status:** closed - `stuck`, `start`, `available` and the hire/train/commission refusals share one rule, and the refusal lists the cash-raising commands; selling plant or land is 320

B (109 AD, deep debt): `stuck` reported 159 payable things and recommended the cheapest; every start was refused "you could raise 0". Reproduced in Rome 100 AD, default poor_scholar kit, with `hire smith 3`, `hire scholar 2`, two steps (cash -7,245, credit limit 9,128): `stuck` prints "126 things you could begin, 69 of them you could pay for"; `start horse_collar` answers "REFUSED: cannot afford the materials this project needs bought now: it costs 1,177 denarii and you could raise 0 (cash -7,245, plus credit)".

Cause: `_stuck_startable_and_afford` (`sim/engine/proto/dispatch_inspection.py`) tests `project_cost <= spending_power("start")` (cash plus the whole credit line, net of arrears), while `start` also pays the materials that the market can deliver up front (`settle_project_materials`, `project_materials.py`, added with complaint 151) under `purchase_rule.can_pay`, which uses the "buy" budget: the ordinary share (`SPENDING_DRAW_SHARE_ORDINARY`, half) of the credit line. Two budgets and a third rule (`funding_capacity`, used for the warnings) for the same question.

Also from the tester: the true rule (about cash plus half the credit line plus a few years of spare income) is only explained inside a long credit note, and A's destitute mortal run hit the related case that replacement wages could not be financed under the credit that construction could. C: after smallpox, hiring is "refused past half your line", and the refusal should say exactly how much to pay down; there is no lever (sell assets, shrink the household) to climb out.

What it would take: one affordability function for `stuck`, `available`, `start` and `hire`; every refusal states the rule, the budget and the amount short (and, for debt, the pay-down that would allow it); a test that every start `stuck` calls payable is accepted by `start`. Related: 214, 220, 154 closed, 61 closed, 95.


Found in the final blind playtests of this branch (Rome 100 AD and Mexica 1500 fog runs; B bug 5 and annoyances; A destitute run; C design complaint on the debt trap). Reports: `Complaints/reports/playtest-rome-fog-fuzzy-demo.md`, `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.

**Fixed:** `_stuck_startable_and_afford` now asks `start_refusal`, the function `start` uses, so every start `stuck` calls payable is accepted (`sim/tests/test_stuck_matches_start.py`). `purchase_rule.refusal_text` states the rule, the cash and the credit share, the amount short, and that earning or paying down that amount allows the start.

**Also fixed:** the `available` AFFORD column and the `*` row marks ask `start_refusal` (rows carry `cannot_pay_now`); `hire`, `train` and `commission` refuse with `purchase_rule.refusal_text`.

**Also fixed:** `purchase_rule.refusal_text` ends with "To raise cash:" and the commands that do it, each with the amount the command itself uses (`sim/engine/cash_remedies.py`): `sell <material>` (`material_sale_offer`, the figure `sell` pays), `mothball <id>` (`venture_real_upkeep`), `close <material>` (`mine_operating_cost_for`) and `fire <trade>` (`annual_wage`). There is no loan command: credit is automatic and already counted in the budget. Test: `sim/tests/test_refusal_cash_remedies.py`.

**Remains (moved to 320):** selling a built concern or land to another actor.
