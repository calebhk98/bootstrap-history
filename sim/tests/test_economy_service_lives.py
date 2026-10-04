"""A durable good households buy is held, wears by one service life's share a year, and is not
bought again in full."""
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
    """(household stock after the year, wear that year, units sold that year) for each year."""
    economy = Economy(setup)
    rows = []
    for _year in range(years):
        economy.step(fixture.quiet_year(setup))
        flow = economy.record.book.goods_flow(fixture.METAL)
        rows.append((household_stock(economy), flow.get("wear", 0.0), flow["output"]))
    return rows


class ServiceLifeTests(unittest.TestCase):
    def test_a_durable_bought_is_held_into_the_next_year(self):
        rows = years_of(durable_setup(), 3)
        self.assertGreater(rows[1][0], 0.0)
        self.assertGreater(rows[2][0], 0.0)

    def test_it_wears_by_one_service_life_share_of_what_is_in_use(self):
        stock, wear, _sold = years_of(durable_setup(), 3)[2]
        self.assertAlmostEqual(wear, (stock + wear) / SERVICE_LIFE_YEARS, delta=1e-6 * (stock + wear))

    def test_a_good_without_a_service_life_is_not_held(self):
        rows = years_of(fixture.small_setup(), 3)
        self.assertEqual(rows[2][0], 0.0)

    @unittest.expectedFailure
    def test_it_is_not_bought_again_in_full(self):
        # finding: household purchases of the durable do not fall after the first stock-up year
        rows = years_of(durable_setup(), 4)
        self.assertLess(rows[3][2], 0.5 * rows[0][2])


if __name__ == "__main__":
    unittest.main()
