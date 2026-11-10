"""The cohorts' scalar close figures in one kernel call (`households_close_figures_kernel`): the view is asked for each cohort's price
level, observed inflation, equity and claims (a mod's adjusted view is read here), the rules run over the columns.

`closed_scalars_of(...)` -> {field: values by cohort} for the eight fields `households_close.closed_figures` changes, equal to it per cohort."""
from typing import Dict, Mapping, Sequence

import numpy as np

from . import currency, durable_stock, households_buffer_stock
from .households_close_figures_kernel import CASH_SHARE, INFLATION_SPEED, SPENDING_SPEED, WEALTH_TARGET_YEARS, closed_scalars

FIELDS = ("expected_inflation", "last_basket_price_level", "cash_target", "share_wealth", "last_year_income", "expected_spending",
          "planned_spending", "expected_floor_cost")


def first_good_of(basket):
    """The first good of the basket's first need that names one, or None: the good whose area gives the cohort its currency."""
    return next((need.goods[0][0] for need in basket.needs if need.goods), None)


def closed_scalars_of(view, agent_ids: Sequence[str], tiles: Sequence[str], baskets: Sequence, columns: Mapping[str, np.ndarray],
                      people: np.ndarray, income_received: np.ndarray, spent: np.ndarray, floor_cost_of_person: np.ndarray) -> Dict[str, np.ndarray]:
    """`columns` holds the cohorts' current values of the fields in FIELDS (share_wealth NaN for none); `baskets` is each cohort's basket."""
    count = len(agent_ids)
    constants = np.zeros(4)
    constants[INFLATION_SPEED] = currency.EXPECTATION_ADJUSTMENT_SPEED
    constants[SPENDING_SPEED] = durable_stock.EXPECTED_SPENDING_ADJUSTMENT
    constants[CASH_SHARE] = households_buffer_stock.yearly_cash_share()
    constants[WEALTH_TARGET_YEARS] = households_buffer_stock.WEALTH_INCOME_RATIO_TARGET / households_buffer_stock.MONTHS_PER_YEAR
    has_level = np.zeros(count, dtype=np.bool_)
    level, observed = np.zeros(count), np.full(count, np.nan)
    equity, claims = np.zeros(count), np.zeros(count)
    seen: Dict = {}
    first_of_basket: Dict = {}
    for position in range(count):
        basket = baskets[position]
        if id(basket) not in first_of_basket:
            first_of_basket[id(basket)] = first_good_of(basket)
        first_good = first_of_basket[id(basket)]
        if first_good is None:
            continue
        key = (first_good, tiles[position])
        if key not in seen:
            money = view.currency_of(view.area_of(first_good, tiles[position]))
            inflation = view.observed_inflation(money)
            seen[key] = (money, view.basket_price_level(money), np.nan if inflation is None else inflation)
        money, level[position], observed[position] = seen[key]
        has_level[position] = True
        equity[position] = view.equity(agent_ids[position])
        claims[position] = view.claims(agent_ids[position], money)
    out = np.zeros((len(FIELDS), count))
    closed_scalars(constants, has_level, level, observed, equity, claims, income_received, spent, floor_cost_of_person, people,
                   columns["expected_inflation"], columns["last_basket_price_level"], columns["cash_target"],
                   columns["share_wealth"], columns["last_year_income"], columns["expected_spending"], columns["planned_spending"],
                   columns["expected_floor_cost"], out)
    return dict(zip(FIELDS, out))
