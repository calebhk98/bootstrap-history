"""A state keeps part of the cash it does not spend in the durable stores households use, by the same rule."""

QUICK_TOPIC = True

import unittest

from sim.economy.types import EDGE_PRODUCTION, GoodsMove
from sim.tests import economy_fixture as fixture


def run_years(years, service_lives=None):
    setup = fixture.small_setup(specs=fixture.specs(service_lives))
    economy, _outcomes = fixture.run(setup, years)
    return economy


def state_metal(economy):
    setup, book = economy.setup, economy.record.book
    return sum(book.holdings(setup.state_agent)["goods"].get(fixture.METAL, {}).values())


class StateStoreTests(unittest.TestCase):
    def test_a_state_with_cash_beyond_its_plan_buys_a_durable_store(self):
        economy = run_years(3, {fixture.METAL: 20})
        self.assertGreater(state_metal(economy), 0.0)
        self.assertTrue(economy.record.book.check_conservation(1e-9).ok)

    def test_a_state_holds_nothing_when_no_good_qualifies_as_a_store(self):
        self.assertEqual(state_metal(run_years(3)), 0.0)

    def test_the_store_is_not_used_up_as_a_purchase_for_the_lines(self):
        economy = run_years(3, {fixture.METAL: 20})
        self.assertGreater(state_metal(economy), 0.0)

    def test_a_state_holding_far_more_than_it_wants_offers_the_excess(self):
        economy = run_years(3, {fixture.METAL: 20})
        setup, record = economy.setup, economy.record
        before = state_metal(economy)
        record.book.move_many([GoodsMove(EDGE_PRODUCTION, setup.state_agent, fixture.METAL, setup.capital_tile,
                                         100.0 * max(before, 1.0), "test hoard")])
        hoard = state_metal(economy)
        economy.step(fixture.quiet_year(setup, year=3))
        self.assertLess(state_metal(economy), hoard)


if __name__ == "__main__":
    unittest.main()
