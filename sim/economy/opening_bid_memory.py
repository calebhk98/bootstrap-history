"""What the opening's households' bids take from the market and the cohort's plan, and not from its income.

The opening settles income by asking, many times over, what the households buy at an income. Between those asks the
prices, the baskets and the stores' weights do not move; only the income does. A `BidMemory` kept for the asks
of one settlement holds the basket of each cohort, the priced needs of each basket and the store weights of each
(basket, tile), so each is worked out once. It must not outlive a change of prices or of the cohorts' plans."""
from typing import Dict, Tuple

from . import households
from .household_work_year import basket_key, cohort_basket


class BidMemory:
    def __init__(self) -> None:
        self._basket: Dict[str, object] = {}
        self._priced: Dict[Tuple, object] = {}
        self._stores: Dict[Tuple, dict] = {}

    def basket(self, setup, record, cohort):
        found = self._basket.get(cohort.agent_id)
        if found is None:
            found = self._basket[cohort.agent_id] = cohort_basket(setup, record, cohort)
        return found

    def priced(self, setup, record, view, cohort, basket):
        key = basket_key(record, cohort)
        found = self._priced.get(key)
        if found is None:
            found = self._priced[key] = households.need_prices(basket, view, cohort.tile)
        return found

    def stores(self, record, cohort) -> dict:
        """The store weights and prices shared by the cohorts of one basket (they see the same priced needs)."""
        return self._stores.setdefault(basket_key(record, cohort), {})
