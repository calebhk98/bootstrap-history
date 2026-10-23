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


from sim.agents.business_founder_review import FounderReview
from sim.agents.tuning import EXIT_LOSS_YEARS


class _Founder(FounderReview):
    """The founder's household as the owner of a business, reviewed through a stand-in seat."""

    def __init__(self, business):
        self.business = business


def _founder_seat(business, auto_shed=True, capability=(), spared=(), capital=0.0):
    closed_works = []
    game = SimpleNamespace(
        state=SimpleNamespace(founder=SimpleNamespace(policy={"auto_shed": auto_shed}), scenario=SimpleNamespace(year=7),
                              household=SimpleNamespace(capital=capital),
                              projects=SimpleNamespace(granted=set(spared), business=business)),
        CAPABILITY_INSTITUTIONS=set(capability), never_abandon=lambda entry_key: False,
        close_work=lambda entry_key, reason, year: (closed_works.append((entry_key, reason, year)),
                                                    business.mothball(entry_key, year, reason)),
        revenue=lambda: 0.0, upkeep=lambda: 0.0, living_cost=lambda: 0.0, mine_operating_cost=lambda: 0.0)
    world = SimpleNamespace(_sim=game, concern_margin=lambda entry_key: -1.0)
    world.founder_review = lambda: SeatReview(world)
    return world, closed_works


def _years_of_loss(business, owner, world, entry_key, years):
    closed = []
    for _ in range(years):
        business.note_year(entry_key, -1.0)
        closed += business.review(owner, world, rules=(business_review.LOSS_MAKING,))
    return closed


class LossRuleOnTheSeat(unittest.TestCase):

    def test_a_seat_that_sheds_losses_shuts_a_plant_after_the_shared_run_of_loss_years_and_dates_it(self):
        business = Business.running(["shop"])
        world, closed_works = _founder_seat(business)
        closed = _years_of_loss(business, _Founder(business), world, "shop", EXIT_LOSS_YEARS)
        self.assertEqual([(closure.entry_key, closure.reason) for closure in closed], [("shop", business_review.LOSS_MAKING)])
        self.assertEqual(closed_works, [("shop", business_review.LOSS_MAKING, 7)])
        self.assertEqual(business.state_of("shop"), "mothballed")

    def test_one_year_short_of_the_run_shuts_nothing(self):
        business = Business.running(["shop"])
        world, closed_works = _founder_seat(business)
        self.assertEqual(_years_of_loss(business, _Founder(business), world, "shop", EXIT_LOSS_YEARS - 1), [])
        self.assertEqual(business.state_of("shop"), "operating")

    def test_a_seat_that_switched_auto_shed_off_keeps_its_plant(self):
        business = Business.running(["shop"])
        world, closed_works = _founder_seat(business, auto_shed=False)
        self.assertEqual(_years_of_loss(business, _Founder(business), world, "shop", 3 * EXIT_LOSS_YEARS), [])
        self.assertEqual(business.state_of("shop"), "operating")

    def test_a_capability_institution_is_not_shed_for_a_loss_nor_is_a_granted_one(self):
        business = Business.running(["school", "granted"])
        world, closed_works = _founder_seat(business, capability=("school",), spared=("granted",))
        for entry_key in ("school", "granted"):
            _years_of_loss(business, _Founder(business), world, entry_key, 2 * EXIT_LOSS_YEARS)
        self.assertEqual((business.state_of("school"), business.state_of("granted")), ("operating", "operating"))

    def test_the_books_cut_losses_only_in_arrears_with_a_yearly_deficit(self):
        business = Business.running(["shop"])
        world, _ = _founder_seat(business, capital=-10.0)
        world._sim.living_cost = lambda: 5.0
        self.assertTrue(SeatReview(world).cuts_losses_now())
        world._sim.state.household.capital = 10.0
        self.assertFalse(SeatReview(world).cuts_losses_now())
        world._sim.state.household.capital = -10.0
        world._sim.revenue = lambda: 50.0
        self.assertFalse(SeatReview(world).cuts_losses_now())


if __name__ == "__main__":
    unittest.main()
