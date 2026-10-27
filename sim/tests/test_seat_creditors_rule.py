"""The founder's seat as a debtor: its creditors press when the purse is past the credit line, take the plant that loses
most and repay themselves its proceeds, and leave a plant that pays. Each rule is called on a stand-in seat."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents import business_review
from sim.agents.api import Business
from sim.finance.api import constants as finance_constants
from sim.ledger.api import ReceiveFromEdge
from sim.projects.review import SeatReview
from sim.tests import module_harness, projects_host


def _seat(capital, limit, upkeep=100.0, size=2.0):
    module = projects_host.build(
        acting_balance=capital, credit_limit=lambda *arguments: limit, year=1,
        legacy_projects=SimpleNamespace(business=SimpleNamespace(size_of=lambda entry_key: size)))
    world = SimpleNamespace(upkeep=lambda entry_key, plant_size: upkeep * plant_size)
    received = [command for command in module_harness.sent(module) if isinstance(command, ReceiveFromEdge)]
    return SeatReview(module, world), module


class CreditorsPress(unittest.TestCase):

    def test_creditors_press_only_when_the_purse_is_past_the_line(self):
        self.assertTrue(_seat(-1001.0, 1000.0)[0].creditors_press())
        self.assertFalse(_seat(-1000.0, 1000.0)[0].creditors_press())
        self.assertFalse(_seat(500.0, 1000.0)[0].creditors_press())

    def test_the_proceeds_are_the_upkeep_of_the_plant_at_its_size_times_the_multiple(self):
        seat, module = _seat(-5000.0, 1000.0, upkeep=100.0, size=2.0)
        proceeds = seat.proceeds_of_seizure("shop")
        self.assertEqual(proceeds, 200.0 * finance_constants.CREDITOR_SEIZURE_VALUE_MULTIPLE)
        seat.receive_seizure("shop", proceeds)
        self.assertEqual([command.amount for command in module_harness.sent(module) if isinstance(command, ReceiveFromEdge)], [proceeds])


class _Seat(business_review.Reviewable):
    """A seat whose creditors press while its debt lasts; a seizure repays 100 of it."""

    def __init__(self, business, margins, debt):
        self.business, self.margins, self.debt, self.taken = business, margins, debt, []

    def creditors_press(self, world):
        return self.debt > 0.0

    def standing_margin(self, entry_key, world):
        return self.margins[entry_key]

    def receive_seizure(self, entry_key, proceeds, world):
        self.taken.append(entry_key)
        self.debt -= 100.0

    def shut(self, entry_key, reason, world):
        self.business.mothball(entry_key, 1, reason)


class SeizureTakesWhatLosesMoney(unittest.TestCase):

    def test_a_plant_that_pays_is_left_however_hard_the_creditors_press(self):
        business = Business.running(["paying"])
        seat = _Seat(business, {"paying": 5.0}, debt=1000.0)
        closed = business.review(seat, None, (business_review.CREDITOR_SEIZURE,))
        self.assertEqual((closed, seat.taken, business.state_of("paying")), ([], [], "operating"))

    def test_a_plant_that_loses_is_taken_while_the_creditors_press_and_the_one_that_pays_stays(self):
        business = Business.running(["losing", "paying"])
        seat = _Seat(business, {"losing": -5.0, "paying": 5.0}, debt=50.0)
        closed = business.review(seat, None, (business_review.CREDITOR_SEIZURE,))
        self.assertEqual([(closure.entry_key, closure.reason) for closure in closed],
                         [("losing", business_review.CREDITOR_SEIZURE)])
        self.assertEqual(business.state_of("paying"), "operating")


def _seat_game(auto_shed=True, capability=(), spared=(), never_abandon=(), capital=0.0, revenue=0.0, living=0.0, limit=0.0):
    """The projects module over what SeatReview reads, with `close_work` recording."""
    closed_works = []
    module = projects_host.build(
        founder={"alive": True, "life_left": 10.0, "dead_reason": None, "policy": {"auto_shed": auto_shed}}, year=7,
        capability_sets=(frozenset(capability), frozenset(), {}), never_abandon=lambda entry_key: entry_key in never_abandon,
        acting_balance=capital, revenue_estimate=revenue, upkeep=0.0, living_cost=lambda *arguments: living, mine_operating_cost=0.0,
        credit_limit=lambda *arguments: limit, legacy_projects=SimpleNamespace(granted=set(spared)))
    module.close_work = lambda entry_key, reason, year: closed_works.append((entry_key, reason, year))
    return SeatReview(module, SimpleNamespace()), closed_works


class SeatHooksOfTheLossRule(unittest.TestCase):

    def test_a_seat_sheds_losses_unless_auto_shed_is_off(self):
        self.assertTrue(_seat_game(auto_shed=True)[0].sheds_losses())
        self.assertFalse(_seat_game(auto_shed=False)[0].sheds_losses())

    def test_a_granted_plant_or_one_never_abandoned_is_spared(self):
        seat, _ = _seat_game(spared=("granted",), never_abandon=("kept",))
        self.assertEqual([seat.spares_plant(key) for key in ("granted", "kept", "shop")], [True, True, False])

    def test_a_capability_institution_is_worth_running_at_a_loss(self):
        seat, _ = _seat_game(capability=("school",))
        self.assertEqual([seat.serves_beyond_takings(key) for key in ("school", "shop")], [True, False])

    def test_the_books_cut_losses_in_arrears_with_a_yearly_deficit(self):
        self.assertTrue(_seat_game(capital=-10.0, living=5.0)[0].cuts_losses_now())

    def test_the_books_do_not_cut_losses_with_cash_in_hand(self):
        self.assertFalse(_seat_game(capital=10.0, living=5.0)[0].cuts_losses_now())

    def test_the_books_do_not_cut_losses_in_arrears_when_takings_cover_the_costs(self):
        self.assertFalse(_seat_game(capital=-10.0, living=5.0, revenue=50.0)[0].cuts_losses_now())

    def test_shutting_a_plant_closes_the_work_with_its_reason_in_the_scenarios_year(self):
        seat, closed_works = _seat_game()
        seat.shut("shop", business_review.LOSS_MAKING)
        self.assertEqual(closed_works, [("shop", business_review.LOSS_MAKING, 7)])


if __name__ == "__main__":
    unittest.main()
