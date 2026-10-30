"""A coin is a fixed weight of its metal, so it is worth what that metal is worth on the market.

Each year's close records the market's price ratio of every coin metal (the home society's and each partner's). A glut
of the metal (ratio below one) makes a unit of coin buy less of everything, so the price level rises with it; a
shortage lowers it. Holders of coin and of debts written in coin bear the change: nothing is indexed or compensated.
The society's coin stock is its opening stock plus what trade has brought in (the partners' ledgers are foreign
trade's); a partner's is its opening stock plus what the ledger says it gained or paid out."""
from sim.labour.api import people_fed_per_worker
from sim.unit_conversions import HOURS_PER_PERSON_YEAR
from sim.world import balance_of_payments, coin_metal

from .constants import REVALUATION_YEARLY_CAP, REVALUATION_YEARLY_SHARE

RATIOS = "ratios"


class Prices:
    """The phase `coin_revaluation` and the stock and price-level views (needs: civilisation, opening_population,
    opening_money_per_labour_hour, foreign_coin_home_units, foreign_coin_partner_units, partner_coin_standard,
    partner_opening_facts, foreign_economies, coin_value_ratio)."""

    def home_coin_metal(self):
        return self.needs.civilisation()["coin_standard"]["material"]

    def partner_coin_metal(self, civilization_id):
        return self.needs.partner_coin_standard[civilization_id]["material"]

    def metal_ratio(self, material):
        """The market's price over the incumbents' cost for a coin metal, as of the last year's close."""
        return self.world.metal_ratios.get(material, 1.0)

    def revalue_coin_metals(self, seats):
        """Record the market ratio of the home coin metal and of each partner's."""
        metals = {self.home_coin_metal()}
        metals.update(self.partner_coin_metal(partner) for partner in self.needs.foreign_economies())
        ratios = self.world.metal_ratios
        for metal in sorted(metals):
            ratios[metal] = coin_metal.revalued_ratio(
                ratios.get(metal, 1.0), self.needs.coin_value_ratio[metal], REVALUATION_YEARLY_SHARE, REVALUATION_YEARLY_CAP)
        self.bump(RATIOS)

    def opening_units(self, wage_per_year):
        workers = self.needs.opening_population() / people_fed_per_worker()
        return balance_of_payments.opening_stock_units(workers, wage_per_year)

    def home_opening_units(self):
        """Coin the society opened with, at the opening's money (not today's price level)."""
        if self._home_opening is None:
            self._home_opening = self.opening_units(self.needs.opening_money_per_labour_hour() * HOURS_PER_PERSON_YEAR)
        return self._home_opening

    def home_coin_stock(self):
        """Coin this society holds: its opening stock plus what trade has brought in."""
        return self.home_opening_units() + self.needs.foreign_coin_home_units()

    def home_price_level(self):
        """Price level of this society against its opening one: its coin stock against the opening's, the level of
        every good and wage in the home money, traded or not. This is the one price level the engine reads (wages,
        caches, clearing); the agent economy's `basket_price_level` is its own index of its own prices."""
        opening = self._home_opening or self.home_opening_units()
        stock = opening + self.needs.foreign_coin_home_units()
        return (balance_of_payments.money_stock_price_level(stock, opening)
                / self.metal_ratio(self.home_coin_metal()))

    def partner_coin_opening(self, civilization_id):
        """Coin a partner opened with."""
        if civilization_id not in self._partner_openings:
            facts = self.needs.partner_opening_facts[civilization_id]
            workers = float(facts["population"] or 0.0) / people_fed_per_worker()
            self._partner_openings[civilization_id] = balance_of_payments.opening_stock_units(
                workers, facts["money_per_labour_hour"] * HOURS_PER_PERSON_YEAR)
        return self._partner_openings[civilization_id]

    def partner_price_level(self, civilization_id):
        gained = self.needs.foreign_coin_partner_units[civilization_id]
        opening = self.partner_coin_opening(civilization_id)
        return (balance_of_payments.money_stock_price_level(opening + gained, opening)
                / self.metal_ratio(self.partner_coin_metal(civilization_id)))
