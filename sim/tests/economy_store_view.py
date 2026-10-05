"""A stub market view and cohort for the store-of-value tests, on the fixture's goods with a durable metal."""
import dataclasses

from sim.economy import households
from sim.tests import economy_fixture as fixture

SPECS = fixture.specs({fixture.METAL: 20})
BASKET = fixture.basket()
TILE = fixture.TOWN


class View:
    year = 1

    def __init__(self, prices=None, stocks=None, inflation=0.0):
        self.prices = {fixture.GRAIN: 0.3, fixture.ORE: 0.05, fixture.METAL: 95.0}
        self.prices.update(prices or {})
        self.stocks = stocks or {}
        self.inflation = inflation

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return 1.0

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area:" + good

    def currency_of(self, area):
        return "coin"

    def basket_price_level(self, currency):
        return 1.0

    def expected_inflation(self, currency):
        return self.inflation

    def cash(self, agent, currency):
        return 0.0

    def stock(self, agent, good, tile):
        return self.stocks.get((agent, good, tile), 0.0)


def cohort(people=100.0, **changes):
    base = households.Cohort("household:t:0", TILE, 0, people, people / 2, 0.3)
    return dataclasses.replace(base, **changes)


def orders(view=None, cash=20000.0, income=2000.0, specs=None, **cohort_changes):
    the_cohort = cohort(**cohort_changes)
    return households.goods_orders(the_cohort, view or View(), cash, income, BASKET,
                                   SPECS if specs is None else specs)


def metal_held(kilograms):
    return {("household:t:0", fixture.METAL, TILE): kilograms}
