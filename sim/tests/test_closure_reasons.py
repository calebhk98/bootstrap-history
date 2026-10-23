"""closure_reasons: a closed work records why and since when, and only its own cause clears it.

The rules are called on a business built here (`Business`, `business_review.reopen`) and on a stub game for the
staffing-closure age and the discounted reopening fee. The staffing closure kept through a save is test_closure_reasons_scenario.
The loss-making and creditor-seizure closures (reasons "loss_making" and "creditor_seizure") are held by
test_business_review (LossRuleIsOneRule, the seizure tests)."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.agents import business_review
from sim.engine import cause_book
from sim.agents.api import Business
from sim.engine.projects import ProjectsMixin
from sim.engine.projects_staffing import StaffingMixin
from sim.engine.projects_venture_quotes import VentureQuotesMixin

STAFF = business_review.STAFF_SHORT
MANUAL = StaffingMixin.CLOSED_BY_CHOICE


def a_business_running(*entry_keys):
	return Business.running(entry_keys, opened_year=0)


class ClosureRecord(unittest.TestCase):

	def test_a_closure_records_its_reason_and_year(self):
		business = a_business_running("mill")
		business.mothball("mill", 40, STAFF)
		self.assertEqual(business.closures()["mill"], {"reason": STAFF, "year": 40})

	def test_restoring_clears_the_record_so_a_later_manual_closure_has_its_own_year(self):
		business = a_business_running("mill")
		business.mothball("mill", 40, STAFF)
		business.restore("mill")
		self.assertNotIn("mill", business.closures())
		business.mothball("mill", 70, MANUAL)
		self.assertEqual(business.closures()["mill"], {"reason": MANUAL, "year": 70})

	def test_only_the_reason_that_resolves_a_closure_clears_it(self):
		business = a_business_running("mill")
		business.mothball("mill", 40, MANUAL)
		self.assertFalse(business.forget_reason("mill", STAFF))
		self.assertEqual(business.closures()["mill"]["reason"], MANUAL)
		self.assertTrue(business.forget_reason("mill", MANUAL))
		self.assertNotIn("mill", business.closures())

	def test_clearing_with_no_reason_removes_whatever_closure_there_is(self):
		business = a_business_running("mill")
		business.mothball("mill", 40, STAFF)
		self.assertTrue(business.forget_reason("mill"))
		self.assertNotIn("mill", business.closures())

	def test_a_running_plant_has_no_closure_record(self):
		business = a_business_running("mill")
		self.assertFalse(business.forget_reason("mill"))
		self.assertNotIn("mill", business.closures())

	def test_opening_a_shut_plant_brings_it_back_and_clears_its_record(self):
		business = a_business_running("mill")
		business.mothball("mill", 40, STAFF)
		business.open_plant("mill", 50)
		self.assertEqual(business.state_of("mill"), "operating")
		self.assertNotIn("mill", business.closures())


class ReopeningAnswersOnlyStaffingClosures(unittest.TestCase):

	class Owner:
		"""An owner that can staff whatever it is asked about."""

		def reopening_order(self, entry_keys, _world):
			return sorted(entry_keys)

		def reopens_staffed_plant(self, _entry_key, _world):
			return True

	def test_a_work_shut_for_want_of_staff_is_reopened(self):
		business = a_business_running("mill")
		business.mothball("mill", 40, STAFF)
		self.assertEqual(business_review.reopen(business, self.Owner(), None), ["mill"])

	def test_a_work_the_player_shut_on_purpose_is_never_reopened_on_its_own(self):
		business = a_business_running("mill")
		business.mothball("mill", 40, MANUAL)
		self.assertEqual(business_review.reopen(business, self.Owner(), None), [])


class StaffingClosureDiscount(unittest.TestCase):
	"""A concern the staffing rule shut within the grace window keeps its premises and costs a fraction to reopen."""

	GRACE = ProjectsMixin.STAFF_CLOSURE_GRACE
	DISCOUNT = ProjectsMixin.STAFF_CLOSURE_DISCOUNT

	def game_with(self, reason, shut_year, year):
		business = a_business_running("mill")
		business.mothball("mill", shut_year, reason)
		game = types.SimpleNamespace(
			state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=year),
			                            projects=types.SimpleNamespace(mothballed=business.mothballed(), closures=business.closures())),
			CLOSED_FOR_STAFF=StaffingMixin.CLOSED_FOR_STAFF, STAFF_CLOSURE_GRACE=self.GRACE,
			STAFF_CLOSURE_DISCOUNT=self.DISCOUNT, is_venture=lambda _node: True, venture_capex=lambda _node: 1000.0)
		game.closure_of = lambda node: StaffingMixin.closure_of(game, node)
		game.staff_closure_age = lambda node: StaffingMixin.staff_closure_age(game, node)
		return game

	def fee(self, reason, shut_year, year):
		game = self.game_with(reason, shut_year, year)
		return VentureQuotesMixin.reopen_fee(game, "mill")

	def test_a_staffing_closure_has_an_age_and_a_manual_one_has_none(self):
		self.assertEqual(StaffingMixin.staff_closure_age(self.game_with(STAFF, 40, 43), "mill"), 3)
		self.assertIsNone(StaffingMixin.staff_closure_age(self.game_with(MANUAL, 40, 43), "mill"))

	def test_within_the_grace_window_reopening_costs_the_discounted_fraction(self):
		self.assertAlmostEqual(self.fee(STAFF, 40, 40 + self.GRACE), 1000.0 * self.DISCOUNT)

	def test_past_the_grace_window_reopening_costs_the_ordinary_fee(self):
		self.assertAlmostEqual(self.fee(STAFF, 40, 40 + self.GRACE + 1), 1000.0)

	def test_a_manual_closure_is_never_discounted_however_young(self):
		self.assertAlmostEqual(self.fee(MANUAL, 40, 41), 1000.0)


class CloseWorkRecordsTheReason(unittest.TestCase):
	"""StaffingMixin.close_work on a stub game: the business keeps the record, a staffing closure is remembered, and a
	later manual closure is its own record."""

	def game(self, year):
		business = a_business_running("mill")
		projects = types.SimpleNamespace(business=business, ever_closed_for_staff=set())
		game = types.SimpleNamespace(state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=year), projects=projects),
		                             CLOSED_FOR_STAFF=StaffingMixin.CLOSED_FOR_STAFF, close_lapsed_dependents=lambda year: None)
		return game, business

	def test_closing_for_staff_records_reason_and_year_and_remembers_it(self):
		game, business = self.game(40)
		with mock.patch.object(cause_book, "record_concern"):
			StaffingMixin.close_work(game, "mill", STAFF)
		self.assertEqual(business.closures()["mill"], {"reason": STAFF, "year": 40})
		self.assertEqual(game.state.projects.ever_closed_for_staff, {"mill"})

	def test_a_manual_closure_after_a_restored_staffing_one_is_dated_afresh(self):
		game, business = self.game(40)
		with mock.patch.object(cause_book, "record_concern"):
			StaffingMixin.close_work(game, "mill", STAFF)
			business.restore("mill")
			StaffingMixin.close_work(game, "mill", MANUAL, year=70)
		self.assertEqual(business.closures()["mill"], {"reason": MANUAL, "year": 70})


if __name__ == "__main__":
	unittest.main()
