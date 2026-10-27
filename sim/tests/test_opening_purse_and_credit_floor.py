"""The founder's opening purse and the floor of the credit line (Complaint 665).

The purse is counted in hours of unskilled work (kit labourer-years times the opening wage) and repriced to the
economy's own wage when the economy first opens, so it must hold the same number of labour hours before and after.
The credit line never falls below the running costs, however little lenders hold beyond what others owe."""

QUICK_TOPIC = True

import contextlib
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.engine import opening_money
from sim.finance.rules import calculate_credit_ceiling
from sim.ledger.api import RescaleHouseholdMoney
from sim.markets.api import MarkMoneyPricedAtEconomy


def fake_sim(wage_after, seats):
    """A stand-in with the three things `reprice_opening_money` touches: the economy flag, the labour package's
    money per hour, and seats whose households are read through `act_as`."""
    households = {seat_id: SimpleNamespace(capital=capital, cash_mark=capital) for seat_id, capital in seats.items()}
    state = SimpleNamespace(seats=list(households), household=None)
    sent = []

    @contextlib.contextmanager
    def act_as(seat_id):
        state.household = households[seat_id]
        yield

    labour = SimpleNamespace(money_per_labour_hour=lambda: wage_after)
    return SimpleNamespace(state=state, labour=labour, act_as=act_as, sent=sent, send=sent.append), households


class OpeningPurseTests(unittest.TestCase):
    def reprice(self, wage_before, wage_after, seats):
        sim, households = fake_sim(wage_after, seats)
        with mock.patch.object(opening_money, "reprice_tree"):
            opening_money.reprice_opening_money(sim, wage_before)
        return sim, households

    def test_a_purse_holds_the_same_hours_of_unskilled_work_after_repricing(self):
        wage_before, wage_after, purse = 0.80, 0.08, 6000.0
        sim, _households = self.reprice(wage_before, wage_after, {"founder": purse})
        rescaling, = [command for command in sim.sent if isinstance(command, RescaleHouseholdMoney)]
        self.assertAlmostEqual(purse * rescaling.ratio / wage_after, purse / wage_before)

    def test_every_seat_is_sent_the_one_ratio_to_rescale_its_money_and_cash_mark_by(self):
        sim, _households = self.reprice(1.0, 0.25, {"founder": 400.0, "second": 40.0})
        self.assertEqual([command for command in sim.sent if isinstance(command, RescaleHouseholdMoney)],
                         [RescaleHouseholdMoney(0.25), RescaleHouseholdMoney(0.25)])

    def test_the_economy_is_marked_as_the_source_of_money_so_a_second_open_does_not_reprice_again(self):
        sim, _households = self.reprice(1.0, 0.5, {"founder": 10.0})
        self.assertEqual(sim.sent[0], MarkMoneyPricedAtEconomy())
        self.assertEqual(sim.sent.count(MarkMoneyPricedAtEconomy()), 1)


class CreditFloorTests(unittest.TestCase):
    def test_lenders_holding_nothing_leave_the_line_at_the_running_costs_not_at_the_name_or_the_income(self):
        floor = 107.0
        line = calculate_credit_ceiling(raw_credit=2000.0, running_cost_floor=floor, serviceable=750.0, market_cap=0.0)
        self.assertEqual(line, floor)

    def test_lenders_with_room_raise_the_line_to_the_least_of_name_income_and_room(self):
        self.assertEqual(calculate_credit_ceiling(2000.0, 107.0, 750.0, market_cap=500.0), 500.0)
        self.assertEqual(calculate_credit_ceiling(2000.0, 107.0, 750.0, market_cap=5000.0), 750.0)


if __name__ == "__main__":
    unittest.main()
