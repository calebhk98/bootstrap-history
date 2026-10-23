"""The founder's seat as a debtor: its creditors press when the purse is past the credit line, take the plant that loses
most and repay themselves its proceeds, and leave a plant that pays. Each rule is called on a stand-in seat."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents import business_review
from sim.agents.api import Business
from sim.engine.projects_review import SeatReview


def _seat(capital, limit, upkeep=100.0, multiple=3.0, size=2.0):
    received = []
    game = SimpleNamespace(
        state=SimpleNamespace(household=SimpleNamespace(capital=capital), scenario=SimpleNamespace(year=1),
                              projects=SimpleNamespace(business=SimpleNamespace(size_of=lambda entry_key: size))),
        credit_limit=lambda: limit, CREDITOR_SEIZURE_VALUE_MULTIPLE=multiple,
        receive_from_edge=lambda edge, proceeds, note: received.append(proceeds))
    world = SimpleNamespace(_sim=game, upkeep=lambda entry_key, plant_size: upkeep * plant_size)
    return SeatReview(world), received


class CreditorsPress(unittest.TestCase):

    def test_creditors_press_only_when_the_purse_is_past_the_line(self):
        self.assertTrue(_seat(-1001.0, 1000.0)[0].creditors_press())
        self.assertFalse(_seat(-1000.0, 1000.0)[0].creditors_press())
        self.assertFalse(_seat(500.0, 1000.0)[0].creditors_press())

    def test_the_proceeds_are_the_upkeep_of_the_plant_at_its_size_times_the_multiple(self):
        seat, received = _seat(-5000.0, 1000.0, upkeep=100.0, multiple=3.0, size=2.0)
        proceeds = seat.proceeds_of_seizure("shop")
        self.assertEqual(proceeds, 600.0)
        seat.receive_seizure("shop", proceeds)
        self.assertEqual(received, [600.0])


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


if __name__ == "__main__":
    unittest.main()
