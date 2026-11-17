"""The scalar figures a cohort's close changes, for every cohort at once: the rules of `households_close.closed_figures` written over columns,
each from the plain Python (`currency.update_expected_inflation`, `opening_resting.resting_household_purse`,
`households_buffer_stock.mean_net_income`, `durable_stock.update_expected_spending`). What the market view answers (price level, observed
inflation, equity, claims) is read by the caller, through the view, and handed in as columns."""
import numpy as np

from sim.jit import njit

# positions in the `constants` array: the declared numbers the rules read, taken by the caller when it calls
INFLATION_SPEED, SPENDING_SPEED, CASH_SHARE, WEALTH_TARGET_YEARS = 0, 1, 2, 3


@njit
def _expected_spending(expected, spent, planned, speed):
    spent = max(spent, planned)
    if expected <= 0.0:
        return spent
    return expected + speed * (spent - expected)


@njit
def _resting_purse(mean_income, share_wealth, claims, share, target_years):
    """`opening_resting.resting_household_purse`."""
    if share_wealth <= 0.0:
        return 0.0
    share_term = share * (share_wealth - target_years * mean_income)
    cash = max(mean_income, -share_term / share - claims)
    return cash - mean_income


@njit
def closed_scalars(constants, has_price_level, level_now, observed, equity, claims, income_received, spent, floor_cost_of_person, people,
                   expected_inflation, last_basket_price_level, cash_target, share_wealth, last_year_income, expected_spending,
                   planned_spending, expected_floor_cost, out):
    """`out[field, cohort]` for the eight fields in the order: expected_inflation, last_basket_price_level, cash_target, share_wealth,
    last_year_income, expected_spending, planned_spending, expected_floor_cost. `observed` is NaN where the view has no observed inflation.
    `share_wealth` is NaN where the cohort holds none; `has_price_level` is false where its basket names no good (price figures stay)."""
    for cohort in range(len(people)):
        expected, level, target, wealth = expected_inflation[cohort], last_basket_price_level[cohort], cash_target[cohort], share_wealth[cohort]
        if has_price_level[cohort]:
            level = level_now[cohort]
            seen = observed[cohort]
            if np.isnan(seen):
                seen = level / last_basket_price_level[cohort] - 1.0
            expected = expected_inflation[cohort] + constants[INFLATION_SPEED] * (seen - expected_inflation[cohort])
            wealth = equity[cohort]
            mean_income = income_received[cohort] if last_year_income[cohort] <= 0.0 else 0.5 * (income_received[cohort] + last_year_income[cohort])
            target = _resting_purse(mean_income, wealth, claims[cohort], constants[CASH_SHARE], constants[WEALTH_TARGET_YEARS])
        out[0, cohort], out[1, cohort], out[2, cohort], out[3, cohort] = expected, level, target, wealth
        out[4, cohort] = income_received[cohort]
        out[5, cohort] = _expected_spending(expected_spending[cohort], spent[cohort], planned_spending[cohort], constants[SPENDING_SPEED])
        out[6, cohort] = 0.0
        out[7, cohort] = _expected_spending(expected_floor_cost[cohort], floor_cost_of_person[cohort] * people[cohort], 0.0,
                                            constants[SPENDING_SPEED])
