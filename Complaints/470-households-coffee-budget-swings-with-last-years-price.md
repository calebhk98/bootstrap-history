# A need's budget follows last year's price, so a falling price alternates up and down

**Status:** open

In the innovator scenario (`sim/tests/economy_innovator_scenario.py`, `python3 -m sim.tests --only economy_innovator_pricing`) the coffee price falls over the years but alternates between a high and a low year after entry (print the rows with `python3 -c "from sim.tests import economy_innovator_scenario as s; [print(r['year'], round(r['price'], 2)) for r in s.run_scenario()]"`). The sellers' asks are nearly the same in a high and a low year; the swing is in the buyers' side. A cohort's coffee budget is a share of its surplus set from last year's price (`households_orders.goods_orders`, `need_units`), and across needs that share rises as the price falls (`NEED_SUBSTITUTION_ELASTICITY` is above one). Budget and price therefore chase each other: a low price one year doubles or triples the next year's budget, the price jumps, the budget falls back. The two-year mean falls steadily, which is what `test_the_price_path_falls_steadily_without_a_swing_between_years` checks; a year-to-year bound does not hold.

What it would take: smooth the split of surplus across needs the way total spending is smoothed (`SPENDING_CUT_LIMIT`, `expected_spending`), or let the budget follow an expected price rather than last year's. Tighten the scenario test to a year-to-year bound once it holds. Do not make sellers hold back to hide it: their asks are not the cause.

Related: 336, 468.
