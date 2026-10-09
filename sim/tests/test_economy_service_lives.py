"""A durable good households buy is held, wears by one service life's share a year, and is not
bought again in full."""

QUICK_TOPIC = True

import unittest

from sim.economy.economy import Economy
from sim.tests import economy_fixture as fixture

SERVICE_LIFE_YEARS = 20.0


def durable_setup():
    return fixture.small_setup(specs=fixture.specs({fixture.METAL: SERVICE_LIFE_YEARS}))


def household_stock(economy):
    book = economy.record.book
    return sum(quantity for agent in book.holders_of(fixture.METAL) if agent.startswith("household")
               for quantity in book.holdings(agent)["goods"][fixture.METAL].values())


def years_of(setup, years):
    """(household stock after the year, wear that year, units sold that year, households' income that
    year) for each year."""
    economy = Economy(setup)
    rows = []
    for _year in range(years):
        economy.step(fixture.quiet_year(setup))
        flow = economy.record.book.goods_flow(fixture.METAL)
        income = sum(cohort.last_year_income for cohort in economy.record.cohorts.values())
        rows.append((household_stock(economy), flow.get("wear", 0.0), flow["output"], income))
    return rows


class ServiceLifeTests(unittest.TestCase):
    def test_a_durable_bought_is_held_into_the_next_year(self):
        rows = years_of(durable_setup(), 3)
        self.assertGreater(rows[1][0], 0.0)
        self.assertGreater(rows[2][0], 0.0)

    def test_it_wears_by_one_service_life_share_of_what_is_in_use(self):
        stock, wear, _sold, _income = years_of(durable_setup(), 3)[2]
        self.assertAlmostEqual(wear, (stock + wear) / SERVICE_LIFE_YEARS, delta=1e-6 * (stock + wear))

    def test_a_good_without_a_service_life_is_not_held(self):
        rows = years_of(fixture.small_setup(), 3)
        self.assertEqual(rows[2][0], 0.0)

    def test_it_is_not_bought_again_in_full(self):
        # households fill the stock over years of income, then buy the wear plus the growth of the
        # stock they want, which follows their income (the fixture's income keeps growing)
        rows = years_of(durable_setup(), 13)
        bought = [rows[year][0] - rows[year - 1][0] + rows[year][1] for year in range(1, 13)]
        self.assertGreater(bought[0], 8.0 * rows[1][1])
        late = range(10, 13)
        late_bought = sum(rows[year][0] - rows[year - 1][0] + rows[year][1] for year in late) / 3.0
        late_wear = sum(rows[year][1] for year in late) / 3.0
        late_stock = sum(rows[year - 1][0] for year in late) / 3.0
        income_growth = (rows[12][3] / rows[9][3]) ** (1.0 / 3.0) - 1.0
        self.assertGreater(income_growth, 0.0, "the fixture's income should still be growing")
        self.assertLess(late_bought, late_wear + late_stock * income_growth * 1.5)

    def test_late_holdings_grow_smoothly_with_income_without_selling_out(self):
        # the fixture's income grows, so the wanted stock grows and the holding rises; the premise of
        # a flat income (stock change within one year's wear) does not hold
        rows = years_of(durable_setup(), 13)
        late = range(10, 13)
        bought = [rows[year][0] - rows[year - 1][0] + rows[year][1] for year in late]
        for year in late:
            self.assertGreaterEqual(rows[year][0], rows[year - 1][0], "households sell their stock down in year %d" % year)
        self.assertGreaterEqual(min(bought), 0.0)
        self.assertLess(max(bought), 2.0 * min(bought), "purchases swing from year to year")


if __name__ == "__main__":
    unittest.main()
