"""Complaint 106: a seat founds a bank when it holds a node declaring `deposit_banking` and has the capital; the capital
comes from outside the book into a bank the economy treats like any other. Rules on built inputs; the command on a game
is not tested through a game."""

QUICK_TOPIC = True

import unittest

from sim.economy import api as economy_api
from sim.economy.economy import Economy
from sim.engine import economy_port_bank, seat_bank
from sim.tests import economy_fixture as fixture
from sim.ui.proto import command_registry
from sim.ui.proto import dispatch_bank, typed  # noqa: F401  (registers the command and its parser)


class Refusals(unittest.TestCase):
    def test_a_seat_without_the_banking_node_is_refused_with_its_cause(self):
        refusal = seat_bank.refusal_for(False, 100.0, 1000.0)
        self.assertEqual(refusal.cause, "no_banking_institution")

    def test_the_capital_must_be_a_positive_amount(self):
        for capital in (0.0, -5.0, None, "lots", True):
            self.assertEqual(seat_bank.refusal_for(True, capital, 1000.0).cause, "capital_not_positive", capital)

    def test_the_capital_cannot_exceed_the_seats_money(self):
        refusal = seat_bank.refusal_for(True, 2000.0, 1000.0)
        self.assertEqual(refusal.cause, "capital_exceeds_cash")
        self.assertEqual(refusal.facts["cash"], 1000.0)

    def test_a_seat_that_knows_and_can_pay_is_not_refused(self):
        self.assertIsNone(seat_bank.refusal_for(True, 100.0, 1000.0))


class TheBank(unittest.TestCase):
    def setUp(self):
        self.economy = Economy(fixture.small_setup())
        self.record = self.economy.record
        self.money = self.economy.setup.currency_id
        self.supply = self.record.book.money_supply(self.money)

    def test_the_capital_comes_in_from_outside_and_is_the_banks_own_and_the_seat_is_its_founder(self):
        coin = self.economy.setup.coin_per_unit
        bank = economy_port_bank.found(self.economy, "seat:player", 500.0 * coin, 3)
        self.assertEqual(bank.founder, "seat:player")
        self.assertAlmostEqual(bank.paid_in, 500.0)
        self.assertAlmostEqual(self.record.book.balance(bank.agent_id, self.money), 500.0)
        self.assertIn(bank.agent_id, self.record.banks)
        self.assertAlmostEqual(self.record.book.money_supply(self.money) - self.supply, 500.0)

    def test_no_capital_founds_no_bank(self):
        self.assertIsNone(economy_api.found_bank_from_outside(self.economy, "seat:player", 0.0, 0, economy_api.EDGE_EXCHANGE))
        self.assertEqual(self.record.banks, {})


class TheCommand(unittest.TestCase):
    def test_the_found_command_is_registered_and_documented(self):
        entry = command_registry.COMMANDS["found"]
        self.assertTrue(entry["usage"] and entry["description"])

    def test_found_bank_with_a_capital_parses_to_the_command(self):
        parsed, error = typed.parse_typed("found bank 2,500")
        self.assertIsNone(error)
        self.assertEqual(parsed, {"cmd": "found", "what": "bank", "capital": 2500.0})

    def test_found_with_nothing_after_it_asks_what(self):
        parsed, error = typed.parse_typed("found")
        self.assertIsNone(parsed)
        self.assertTrue(error)


if __name__ == "__main__":
    unittest.main()
