"""closure_reasons: a closed work records why and since when, and only its own cause clears it.

The rules are called on a business built here (`Business`, `business_review.reopen`); the staffing-closure age and the
closing of a work on the projects module over plain values, and the discounted reopening fee on the ventures module.
The loss-making and creditor-seizure closures (reasons "loss_making" and "creditor_seizure") are held by
test_business_review (LossRuleIsOneRule, the seizure tests)."""
QUICK_TOPIC = True

import types
import unittest

from sim.agents import business_review
from sim.agents.api import Business
from sim.agents.business_plant import MOTHBALLED, Plant
from sim.projects import closure_reasons, constants
from sim.reporting.api import NoteConcernChange
from sim.tests import module_harness, projects_host, ventures_host
from sim.ventures import constants as venture_constants

STAFF = business_review.STAFF_SHORT
MANUAL = closure_reasons.CLOSED_BY_CHOICE


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
		business = Business(plants=[Plant("mill", state=MOTHBALLED, since_year=40, reason=STAFF)])
		open_the_plant = Business.open_plant   # the function under test, called by name
		open_the_plant(business, "mill", 50)
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

	GRACE = constants.STAFF_CLOSURE_GRACE
	DISCOUNT = constants.STAFF_CLOSURE_DISCOUNT

	def game_with(self, reason, shut_year, year):
		business = a_business_running("mill")
		business.mothball("mill", shut_year, reason)
		projects = types.SimpleNamespace(mothballed=business.mothballed(), closures=business.closures())
		module = projects_host.build(projects_record=projects, year=year)
		# the build cost that makes opening the concern cost 1000
		ventures = ventures_host.build(
			tree_nodes={"mill": {"up": 0.0}}, project_cost=lambda _node: 1000.0 / venture_constants.VENTURE_CAPEX_SHARE_OF_BUILD_COST,
			staff_closure_age=module.staff_closure_age)
		return module, ventures

	def fee(self, reason, shut_year, year):
		return self.game_with(reason, shut_year, year)[1].reopen_fee("mill")

	def test_a_staffing_closure_has_an_age_and_a_manual_one_has_none(self):
		self.assertEqual(self.game_with(STAFF, 40, 43)[0].staff_closure_age("mill"), 3)
		self.assertIsNone(self.game_with(MANUAL, 40, 43)[0].staff_closure_age("mill"))

	def test_within_the_grace_window_reopening_costs_the_discounted_fraction(self):
		self.assertAlmostEqual(self.fee(STAFF, 40, 40 + self.GRACE), 1000.0 * self.DISCOUNT)

	def test_past_the_grace_window_reopening_costs_the_ordinary_fee(self):
		self.assertAlmostEqual(self.fee(STAFF, 40, 40 + self.GRACE + 1), 1000.0)

	def test_a_manual_closure_is_never_discounted_however_young(self):
		self.assertAlmostEqual(self.fee(MANUAL, 40, 41), 1000.0)


class CloseWorkRecordsTheReason(unittest.TestCase):
	"""The projects module's close_work: the business keeps the record, a staffing closure is remembered and told to the cause
	book, and a later manual closure is its own record."""

	def game(self, year):
		business = a_business_running("mill")
		projects = types.SimpleNamespace(business=business)
		module = projects_host.build(projects_record=projects, year=year, tree_nodes={"mill": {"rev": 40.0, "up": 15.0}})
		module.close_lapsed_dependents = lambda year: None
		return module, business

	def test_closing_for_staff_records_reason_and_year_and_remembers_it(self):
		module, business = self.game(40)
		module.close_work("mill", STAFF)
		self.assertEqual(business.closures()["mill"], {"reason": STAFF, "year": 40})
		self.assertEqual(module.seat.ever_closed_for_staff, {"mill"})
		self.assertIn(NoteConcernChange("closure", "mill", STAFF, 40.0, 15.0), module_harness.sent(module))

	def test_a_manual_closure_is_dated_with_the_year_given(self):
		module, business = self.game(40)
		module.close_work("mill", MANUAL, year=70)
		self.assertEqual(business.closures()["mill"], {"reason": MANUAL, "year": 70})
		self.assertEqual(module.seat.ever_closed_for_staff, set())


if __name__ == "__main__":
	unittest.main()
