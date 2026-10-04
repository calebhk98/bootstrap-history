"""Foreign trade on the agent economy: partners buy and sell through edge:external at the port, the money
they pay in or take out shows in the coin stock and the balance of payments (Complaint 389). Engine-free
fixture; each test states a direction, not a figure."""
import unittest

from sim.economy import foreign
from sim.economy.economy import Economy
from sim.economy.types import EDGE_EXTERNAL
from sim.tests import economy_fixture as fixture

COIN = "coin"
GRAIN_OUTPUT_SCALE = 3.0e6      # the order of a year of the fixture's grain, so a partner is felt in the market


def partner_year(setup, economy, exports=None, imports=None, export_budget=None):
    """One year with a partner at the port: it buys `exports` {good: (price, quantity)} and sells `imports`."""
    exports, imports = exports or {}, imports or {}
    orders = foreign.external_orders(
        {good: price for good, (price, _quantity) in imports.items()},
        {good: price for good, (price, _quantity) in exports.items()},
        {good: quantity for good, (_price, quantity) in imports.items()},
        {good: quantity for good, (_price, quantity) in exports.items()},
        economy.view().area_of, setup.port_tile, export_budget=export_budget)
    return economy.step(fixture.quiet_year(setup, engine_orders={EDGE_EXTERNAL: orders}))


def first_year(**trade):
    setup = fixture.small_setup()
    economy = Economy(setup)
    supply = economy.record.book.money_supply(COIN)
    outcome = partner_year(setup, economy, **trade)
    return economy, outcome, outcome.money_supply - supply


class ExportTests(unittest.TestCase):
    def test_a_foreign_buyers_payment_raises_the_coin_stock(self):
        _economy, _outcome, control = first_year()
        economy, outcome, change = first_year(exports={fixture.GRAIN: (0.5, GRAIN_OUTPUT_SCALE)})
        paid = foreign.balance_of_payments(economy.record.book, COIN)
        self.assertGreater(paid.exports_received, 0.0)
        self.assertGreater(outcome.money_audit.edge_net[EDGE_EXTERNAL][COIN], 0.0)
        self.assertGreater(change, control)

    def test_the_balance_of_payments_shows_money_flowing_in(self):
        economy, _outcome, _change = first_year(exports={fixture.GRAIN: (0.5, GRAIN_OUTPUT_SCALE)})
        paid = foreign.balance_of_payments(economy.record.book, COIN)
        self.assertEqual(paid.imports_paid, 0.0)
        self.assertLess(paid.net_outflow, 0.0)

    def test_the_coin_stock_grows_by_what_the_partner_paid(self):
        _economy, outcome, change = first_year(exports={fixture.GRAIN: (0.5, GRAIN_OUTPUT_SCALE)})
        self.assertAlmostEqual(change - other_edges(outcome), outcome.money_audit.edge_net[EDGE_EXTERNAL][COIN],
                               delta=1e-6 * outcome.money_supply)

    def test_a_partners_budget_bounds_what_it_can_pay(self):
        economy, outcome, _change = first_year(exports={fixture.GRAIN: (0.5, GRAIN_OUTPUT_SCALE)}, export_budget=100.0)
        paid = foreign.balance_of_payments(economy.record.book, COIN)
        self.assertLessEqual(paid.exports_received, 100.0 + 1e-6)

    def test_a_partner_that_will_not_pay_the_price_buys_nothing(self):
        economy, _outcome, _change = first_year(exports={fixture.GRAIN: (0.0001, GRAIN_OUTPUT_SCALE)})
        self.assertEqual(foreign.balance_of_payments(economy.record.book, COIN).exports_received, 0.0)

    def test_the_year_stays_conserved_and_audited(self):
        economy, outcome, _change = first_year(exports={fixture.GRAIN: (0.5, GRAIN_OUTPUT_SCALE)})
        self.assertTrue(outcome.money_audit.ok)
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())


class ImportTests(unittest.TestCase):
    def test_paying_for_imports_lowers_the_coin_stock_and_is_a_net_outflow(self):
        _economy, _outcome, control = first_year()
        economy, outcome, change = first_year(imports={fixture.GRAIN: (0.05, GRAIN_OUTPUT_SCALE)})
        paid = foreign.balance_of_payments(economy.record.book, COIN)
        self.assertGreater(paid.imports_paid, 0.0)
        self.assertGreater(paid.net_outflow, 0.0)
        self.assertLess(outcome.money_audit.edge_net[EDGE_EXTERNAL][COIN], 0.0)
        self.assertLess(change, control)

    def test_cheap_imports_lower_the_domestic_price_of_the_good(self):
        _economy, control, _change = first_year()
        _economy, flooded, _change = first_year(imports={fixture.GRAIN: (0.02, 7 * GRAIN_OUTPUT_SCALE)})
        self.assertLess(flooded.prices[fixture.GRAIN], control.prices[fixture.GRAIN])

    def test_a_partner_paying_well_for_our_grain_pays_sellers_more_than_the_home_price(self):
        economy, control, _change = first_year()
        economy, bought, _change = first_year(exports={fixture.GRAIN: (3.0, 7 * GRAIN_OUTPUT_SCALE)})
        paid = foreign.balance_of_payments(economy.record.book, COIN).exports_received
        self.assertGreater(paid / bought.output[fixture.GRAIN], control.prices[fixture.GRAIN])

    @unittest.expectedFailure   # finding: with a partner bidding far above home, the recorded grain price falls to the opening seed instead of rising
    def test_a_partner_buying_exports_does_not_lower_the_domestic_price_of_the_good(self):
        _economy, control, _change = first_year()
        _economy, bought, _change = first_year(exports={fixture.GRAIN: (3.0, 7 * GRAIN_OUTPUT_SCALE)})
        self.assertGreaterEqual(bought.prices[fixture.GRAIN], control.prices[fixture.GRAIN])


class BalanceTests(unittest.TestCase):
    def test_imports_and_exports_together_net_to_the_difference(self):
        economy, outcome, change = first_year(exports={fixture.GRAIN: (0.5, GRAIN_OUTPUT_SCALE)},
                                              imports={fixture.METAL: (95.0, 500.0)})
        paid = foreign.balance_of_payments(economy.record.book, COIN)
        self.assertAlmostEqual(paid.net_outflow, paid.imports_paid - paid.exports_received)
        self.assertAlmostEqual(change, -paid.net_outflow + other_edges(outcome), delta=1e-6 * outcome.money_supply)


def other_edges(outcome):
    return sum(nets.get(COIN, 0.0) for edge, nets in outcome.money_audit.edge_net.items() if edge != EDGE_EXTERNAL)


if __name__ == "__main__":
    unittest.main()
