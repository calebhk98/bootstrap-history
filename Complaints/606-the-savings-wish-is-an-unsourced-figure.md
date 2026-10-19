# The households' savings wish (two years of surplus income plus a cash buffer) is a labelled figure with no source

**Status:** open

Part of Complaint 526 (The opening's income leaks saving, so the economy opens at subsistence and its wage keeps falling).

**What is wrong.** The wish is many times what any household holds, and counting held wealth does not remove it. Its size drives how much of the opening's income is saved.

**Evidence.** `SAVINGS_RESPONSE_FLOOR` and the savings target in `households_orders.goods_orders`; measured on Rome in 526's notes.

**Why it matters.** An unsourced stored figure that moves the whole opening is a hardcoded outcome (CLAUDE.md 4.1, 4.4).

**What it would take.** Check the wish against sources on pre-modern household saving before building assets to match it. Keep or change the figure with the source recorded on the constant, and re-measure the settled ratio.

**Test.** The constant carries its source and, if still a heuristic, its `retire` entry (`python3 sim/constants.py --burndown`); a test pins the settled ratio band after the change.

**Progress.** Each number behind the wish (`SAVINGS_YEARS_OF_SURPLUS_INCOME`, `SAVINGS_RATE_RESPONSE_LIMIT`, `SAVINGS_RESPONSE_FLOOR`, `HOUSEHOLD_TIME_PREFERENCE`, `WEALTH_DRAWDOWN_LIMIT`, `SPENDING_CUT_LIMIT`) now records the literature it was checked against (recalled, not read; confidence D) and retires to 607. The literature gives months to a few years of income for a household buffer and nothing per household for a pre-modern society, so no value changed. Still open: a read source for years of surplus income (probate inventories, dowry records), and the cash buffer's `BASE_HOLDING_YEARS` (`sim/economy/currency.py`) is not yet checked. Test: `sim/tests/test_savings_wish_provenance.py`.
