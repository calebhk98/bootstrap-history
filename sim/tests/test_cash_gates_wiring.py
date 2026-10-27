"""Complaint 640: each cash gate of the labour market (hire, commission, the automatic commission) asks the world's
spending_power('buy') and refuses with the cause cash_short when the fee is over it, and a stalled project's waiting_on
reads the same figure to tell the calendar's pace from a want of money. The rules on built numbers are in
test_affordability_and_credit; these are the callers, over stand-ins."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour_training import TrainingMixin
from sim.refusal import Refusal, cause_of
from sim.ui.proto.state_waiting import _waiting_on
from sim.tests.ui_stand_in import Game


class World:
    """The parts of the game a labour gate reads: the trade table, one household and a spending power it records."""

    def __init__(self, power):
        self.power = power
        self.asked = []
        self.wages = {"smith": 1.0}
        self.trades_absent = {"smith"}
        self.trade_notes = {}
        self.workforce = Game(contract_hours={})
        self.state = Game(household=self.workforce,
                                           projects=Game(done=set(), active={}))

    def spending_power(self, kind):
        self.asked.append(kind)
        return self.power

    def refusal_text(self, what, fee):
        return "cannot afford %s at %s" % (what, fee)


class Gate(TrainingMixin):
    LITERATE_TRADES = ()

    def __init__(self, power, fee):
        self._world = World(power)
        self.labour_market = Game(
            price_factor=lambda trade: 1.0, whole_recruits=lambda trade, asked, premium: asked,
            hire_cost=lambda trade, count, premium=0.0: fee)
        self.fee = fee

    def trade_available(self, trade):
        return True

    def household_room(self):
        return 10.0

    def market_supply(self, trade):
        return 1e9

    def commission_fee(self, trade, hours):
        return self.fee


class HireCheck(unittest.TestCase):
    def test_a_fee_over_the_purchase_budget_is_refused_cash_short_and_the_gate_asked_for_a_purchase(self):
        gate = Gate(power=99.0, fee=100.0)
        count, fee, refusal = gate.hire_check("smith", 2)
        self.assertEqual((count, fee), (None, None))
        self.assertEqual(cause_of(refusal), "cash_short")
        self.assertEqual(gate._world.asked, ["buy"])

    def test_a_fee_the_budget_covers_goes_through_with_its_cost(self):
        count, fee, refusal = Gate(power=100.0, fee=100.0).hire_check("smith", 2)
        self.assertEqual((count, fee, refusal), (2.0, 100.0, None))


class CommissionCheck(unittest.TestCase):
    def test_a_fee_over_the_purchase_budget_is_refused_cash_short(self):
        gate = Gate(power=0.0, fee=50.0)
        fee, refusal = gate.commission_check("smith", 10.0)
        self.assertIsNone(fee)
        self.assertEqual(cause_of(refusal), "cash_short")
        self.assertEqual(gate._world.asked, ["buy"])

    def test_a_fee_the_budget_covers_is_quoted(self):
        self.assertEqual(Gate(power=500.0, fee=50.0).commission_check("smith", 10.0), (50.0, None))


class CashInHandRefusal(unittest.TestCase):
    def test_it_is_a_cash_short_refusal(self):
        self.assertIsInstance(Gate(0.0, 1.0)._cash_in_hand_refusal("a fee", 5.0), Refusal)
        self.assertEqual(cause_of(Gate(0.0, 1.0)._cash_in_hand_refusal("a fee", 5.0)), "cash_short")


class AutoCommission(unittest.TestCase):
    def test_nothing_is_bought_when_nothing_can_be_raised_and_the_gate_asked_for_a_purchase(self):
        gate = Gate(power=0.0, fee=1.0)
        self.assertIsNone(gate.auto_commission_for_blocked())
        self.assertEqual(gate._world.asked, ["buy"])


class WaitingOn(unittest.TestCase):
    def _cause(self, power):
        world = Game(
            trade_demand_vs_supply=lambda: {}, project_cost=lambda node_id: 9000.0,
            spending_power=lambda kind: power if kind == "buy" else None, civ={})
        nodes = {"academy": {"yrs": 4.0, "lab": {}}}
        return cause_of(_waiting_on(world, nodes, "academy", {"ph_left": 0.0}, 9000.0))

    def test_room_to_spend_more_than_a_years_instalment_means_the_calendar_pace_holds_it_up(self):
        self.assertEqual(self._cause(50000.0), "money_pace")

    def test_nothing_to_raise_means_money_blocks_it(self):
        self.assertEqual(self._cause(0.0), "money_blocked")

    def test_some_money_short_of_an_instalment_means_it_is_unfunded(self):
        self.assertEqual(self._cause(100.0), "money_unfunded")


if __name__ == "__main__":
    unittest.main()
