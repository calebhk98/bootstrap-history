"""What households' bids take from the market and the cohort's plan, and not from its income (the opening's settlement and the year's orders use it).

The opening settles income by asking, many times over, what the households buy at an income. Between those asks the
prices, the baskets and the stores' weights do not move; only the income does. A `BidMemory` kept for the asks
of one settlement holds the basket of each cohort, the priced needs of each basket and the store weights of each
(basket, tile), so each is worked out once. It must not outlive a change of prices or of the cohorts' plans."""
from typing import Dict, Tuple

from . import cohort_prime
from .households_basket import cohort_need_prices
from .household_work_year import basket_key, kept_basket


class BidMemory:
    def __init__(self) -> None:
        self._key: Dict[str, tuple] = {}
        self._basket: Dict[str, object] = {}
        self._priced: Dict[Tuple, object] = {}
        self._stores: Dict[Tuple, dict] = {}

    def know(self, agent_ids, keys) -> None:
        """The `basket_key` of each cohort named, when the caller has worked them out in one pass."""
        self._key.update(zip(agent_ids, keys))

    def key(self, record, cohort) -> tuple:
        """The cohort's `basket_key`, worked out once (it needs the cohort's title to its land)."""
        found = self._key.get(cohort.agent_id)
        if found is None:
            found = self._key[cohort.agent_id] = basket_key(record, cohort)
        return found

    def basket(self, setup, record, cohort):
        found = self._basket.get(cohort.agent_id)
        if found is None:
            found = self._basket[cohort.agent_id] = kept_basket(setup, self.key(record, cohort))
        return found

    def priced(self, setup, record, view, cohort, basket):
        key = self.key(record, cohort)
        found = self._priced.get(key)
        if found is None:
            cohort_prime.prime_cohort_baskets(setup, record, view, True)
            found = self._priced[key] = cohort_need_prices(basket, view, cohort.tile, key)
        return found

    def stores(self, record, cohort) -> dict:
        """The store weights and prices shared by the cohorts of one basket (they see the same priced needs)."""
        return self._stores.setdefault(self.key(record, cohort), {})
