"""A trader's cargo at home is orders in the economy's book, so the home price moves with it (Complaints/115).

Each cargo leg that touches home gets an account in the book: a landing cargo arrives from the partner's edge and is
offered, a taking cargo is bought with funds the trader put in. After the clear the account is closed: money back to
the trader's purse, goods the market did not take back over the partner's edge. Run on the hand-built economy.
"""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import api as economy_api
from sim.economy import money_audit, taxes
from sim.engine import economy_port_cargo as cargo
from sim.tests import economy_fixture as fixture

PARTNER = "partner"
UNITS_PER_TONNE = 1000.0   # the fixture's grain is counted in kilograms


def tonnes_per_unit(_material):
    return 1.0 / UNITS_PER_TONNE


def warmed(years=3):
    economy, _outcomes = fixture.run(years=years)
    return economy


def copy_of(economy):
    return economy_api.economy_from_record(economy.setup, economy_api.export_record(economy))


def leg(kind, tonnes, paid=0.0, received=0.0):
    return {"id": "cargo:trader:test:%s:%s:%s" % (PARTNER, fixture.GRAIN, kind), "trader": "trader:test", "kind": kind,
            "source": PARTNER if kind == "in" else "home", "destination": "home" if kind == "in" else PARTNER,
            "partner": PARTNER, "material": fixture.GRAIN, "tonnes": tonnes, "paid": paid, "received": received}


def year_with(economy, legs):
    """Step one year with the legs' orders in the book; the results of closing their accounts."""
    moves, orders, fundings = cargo.cargo_orders(economy, legs, tonnes_per_unit)
    economy_api.move_goods(economy, moves)
    economy_api.post_transfers(economy, fundings)
    imports, exports = cargo.border_accounts(economy, legs)
    outcome = economy.step(dataclasses.replace(fixture.quiet_year(economy.setup, engine_orders=orders),
                                               import_accounts=imports, export_accounts=exports))
    return outcome, cargo.close_cargo_accounts(economy, legs, tonnes_per_unit)


class CargoInTheBook(unittest.TestCase):
    def test_a_landing_cargo_lowers_the_home_price_and_pays_the_trader_what_it_fetched(self):
        economy = warmed()
        control = copy_of(economy)
        quiet = control.step(fixture.quiet_year(control.setup))
        landing = leg("in", 400.0, paid=100.0, received=100.0)
        outcome, results = year_with(economy, [landing])
        self.assertLess(outcome.prices[fixture.GRAIN], quiet.prices[fixture.GRAIN])
        sold = results[landing["id"]]
        self.assertGreater(sold["tonnes"], 0.0)
        self.assertLessEqual(sold["tonnes"], 400.0 + 1e-9)
        book, currency = economy.record.book, economy.setup.currency_id
        self.assertAlmostEqual(sold["money"], -book.edge_net(economy_api.EDGE_CARGO, currency), places=6)
        self.assertEqual(book.holdings("cargo:trader:test:%s:%s:in" % (PARTNER, fixture.GRAIN)),
                         {"money": {}, "goods": {}})
        # the year's edge record starts at the step, so it shows only what came back: the cargo nobody bought
        unsold_units = (400.0 - sold["tonnes"]) * UNITS_PER_TONNE
        returned = -book.edge_goods_net(economy_api.external_edge(PARTNER), fixture.GRAIN)
        self.assertAlmostEqual(returned, unsold_units, delta=1e-3 * 400.0 * UNITS_PER_TONNE)

    def test_a_landing_cargo_pays_the_states_import_duty_out_of_its_takings(self):
        taxed, free = warmed(), warmed()
        taxed.setup = dataclasses.replace(taxed.setup, tax_forms=(taxes.TaxForm("customs", "imports_value", 0.1),),
                                          state_capacity=1.0)
        landing = leg("in", 400.0, paid=100.0, received=100.0)
        state, currency = taxed.setup.state_agent, taxed.setup.currency_id
        state_before = taxed.record.book.balance(state, currency)
        free_before = free.record.book.balance(state, currency)
        _outcome, with_duty = year_with(taxed, [landing])
        _outcome, without = year_with(free, [landing])
        duty = without[landing["id"]]["money"] - with_duty[landing["id"]]["money"]
        self.assertGreater(duty, 0.0)
        self.assertAlmostEqual(duty, 0.1 * without[landing["id"]]["money"], places=6 - 3)
        gained = taxed.record.book.balance(state, currency) - state_before
        self.assertAlmostEqual(gained - (free.record.book.balance(state, currency) - free_before), duty / taxed.setup.coin_per_unit,
                               delta=1e-6 * max(1.0, duty))

    def test_a_taking_cargo_raises_the_home_price_and_returns_what_it_did_not_spend(self):
        economy = warmed()
        control = copy_of(economy)
        quiet = control.step(fixture.quiet_year(control.setup))
        budget = 0.3 * 300.0 * UNITS_PER_TONNE
        taking = leg("out", 300.0, paid=budget, received=2.0 * budget)
        outcome, results = year_with(economy, [taking])
        self.assertGreater(outcome.prices[fixture.GRAIN], quiet.prices[fixture.GRAIN])
        bought = results[taking["id"]]
        self.assertGreater(bought["tonnes"], 0.0)
        self.assertLessEqual(bought["tonnes"], 300.0 + 1e-9)
        self.assertLessEqual(bought["money"], budget + 1e-6)   # what came back never exceeds what went in
        book = economy.record.book
        self.assertAlmostEqual(-book.edge_goods_net(economy_api.external_edge(PARTNER), fixture.GRAIN),
                               bought["tonnes"] * UNITS_PER_TONNE, delta=1e-3 * 300.0 * UNITS_PER_TONNE)

    def test_the_book_still_conserves_and_audits(self):
        economy = warmed()
        legs = [leg("in", 200.0), leg("out", 100.0, paid=0.3 * 100.0 * UNITS_PER_TONNE)]
        year_with(economy, legs)
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())
        audit = money_audit.year_report(economy.record)
        self.assertTrue(audit.ok, audit)

    def test_a_cargo_of_a_good_the_economy_does_not_trade_is_left_out_of_the_book(self):
        economy = warmed()
        outside = dict(leg("in", 50.0), material="unknown_good")
        moves, orders, fundings = cargo.cargo_orders(economy, [outside], tonnes_per_unit)
        self.assertEqual((moves, orders, fundings), ([], {}, []))
        self.assertEqual(cargo.close_cargo_accounts(economy, [outside], tonnes_per_unit), {})

    def test_a_cargo_between_two_partners_never_touches_the_home_book(self):
        economy = warmed()
        through = dict(leg("through", 50.0), source="a", destination="b")
        self.assertEqual(cargo.cargo_orders(economy, [through], tonnes_per_unit), ([], {}, []))


if __name__ == "__main__":
    unittest.main()
