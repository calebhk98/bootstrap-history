# A state in deficit can only cut spending: it cannot borrow

**Status:** closed - pinned by sim/tests/test_state_borrowing_gate.py; a state borrows only once it holds a node declaring the `state_credit` mechanic (fin_public_debt), and before that a deficit cuts spending

`Government.pay_standing_need` (`sim/engine/actors/government.py`) pays the standing need from the purse and, when the purse is short, cuts every line by the same share (`budget.funded_share`). A real state in a bad year borrows, debases or sells office. The place to add credit is between the revenue being credited and `funded_share` being computed: the state would draw a loan up to what lenders will give against its revenue, and next year's `standing_lines` would carry interest on it as a line like any other (`budget_lines.py` shows the pattern: people at wages, goods at the market's price, or here money owed).

Until then the only responses to a deficit are a smaller army (at `ARMY_ADJUSTMENT_RATE`), unpaid lines, and the need-driven levy on the visible founder. Check: `python3 sim/budget_series.py norse_900ad 100 1` shows the unfunded share and the levy rate year by year.

Owner decision (2026-10-02): not realistic as built: early states did not borrow. State borrowing should require a technology (research) first, so this is reopened.

Done (owner decision 2026-10-02): `Government.credit_ceiling` is zero unless the state knows a `state_credit` node, its own or its society's baseline (`SimWorld.state_may_borrow`). The node is data (`data/branches/40_finance_institutions.json`, mechanic documented in `data/branches/MECHANICS.md`); no civilisation starts with it. A civilisation whose history had state borrowing at its start date (England 1300, with Italian bankers) would list the node in `starting_techs`, with its prerequisites; that is not done here. Interest on the debt is the existing `pay_interest` line.
