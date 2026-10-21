"""Complaint 657: a payer weighs staying under the state's take against leaving to a tile it reaches less (the migration
rule), a state chooses who answers for those who left, and amnesty, immunity and remission are levers any state pulls.
Each test builds the inputs and calls the rule."""
import unittest
from types import SimpleNamespace

from sim.agents import evasion, flight, government_levers, government_levers_tax, liability
from sim.agents.api import Government
from sim.agents.records import ActorRecord
from sim.economy.titles_flight import tenant_flees
from sim.labour.market.migration import migrate, move_shares
from sim.labour.market.records import Clearing, MarketState, Route, YearInputs, YearReport
from sim.refusal import Refusal

QUICK_TOPIC = True

BANDS = 5


def clearing(area, wage):
	hours = 1000.0
	return Clearing(trade="digger", area=area, wage=wage, hours_offered=hours, hours_wanted=hours, hours_hired=hours,
					hired_by_employer={}, paid_by_employer={}, average_wage=wage)


def leavers_from_home(home_take=0.0, away_take=0.0, penalty=0.0):
	"""People of the home area who leave in a year: equal wages, a moving cost, the state's take and a recapture penalty."""
	state = MarketState(workers={"home": {"digger": [100.0] * BANDS}, "away": {"digger": [0.0] * BANDS}})
	inputs = YearInputs(trades={}, bids=[], subsistence_per_worker_year={"home": 50.0, "away": 50.0},
						hours_per_worker_year=100.0, discount_rate=0.05, career_years=30.0,
						routes={"home": [Route("away", 10.0, expected_penalty=penalty)]},
						taxed_share={"home": home_take, "away": away_take})
	report = YearReport()
	migrate(state, inputs, {("home", "digger"): clearing("home", 1.0), ("away", "digger"): clearing("away", 1.0)}, report)
	return -report.migrated.get("home", 0.0)


class FlightThroughTheMigrationRule(unittest.TestCase):
	def test_a_heavier_take_at_home_sends_more_people_out(self):
		flows = [leavers_from_home(home_take=take) for take in (0.0, 0.1, 0.3)]
		self.assertEqual(flows, sorted(flows))
		self.assertGreater(flows[-1], flows[0])

	def test_a_lighter_take_where_they_go_sends_more_people_out(self):
		self.assertGreater(leavers_from_home(home_take=0.3, away_take=0.0), leavers_from_home(home_take=0.3, away_take=0.3))

	def test_the_expected_penalty_of_recapture_keeps_people_in(self):
		self.assertLess(leavers_from_home(home_take=0.3, penalty=40.0), leavers_from_home(home_take=0.3, penalty=0.0))


class PenaltyByReach(unittest.TestCase):
	def test_a_leaver_beyond_the_states_reach_expects_no_penalty(self):
		self.assertEqual(flight.expected_penalty_of_leaving(100.0, 0.0), 0.0)

	def test_the_chance_of_recapture_rises_with_reach(self):
		chances = [flight.recapture_chance(reach) for reach in (0.0, 0.3, 0.6, 1.0)]
		self.assertEqual(chances, sorted(chances))
		self.assertEqual(chances[0], 0.0)

	def test_the_penalty_rises_with_reach_and_with_what_is_owed(self):
		self.assertLess(flight.expected_penalty_of_leaving(100.0, 0.3), flight.expected_penalty_of_leaving(100.0, 0.7))
		self.assertLess(flight.expected_penalty_of_leaving(50.0, 0.7), flight.expected_penalty_of_leaving(100.0, 0.7))

	def test_an_amnesty_lowers_what_a_fugitive_owes_on_coming_home(self):
		self.assertEqual(flight.arrears_owed_by_fugitive(100.0, 0.0), 100.0)
		self.assertEqual(flight.arrears_owed_by_fugitive(100.0, 1.0), 0.0)

	def test_a_fugitive_returns_sooner_when_arrears_are_waived(self):
		owed_without, owed_with = flight.arrears_owed_by_fugitive(30.0, 0.0), flight.arrears_owed_by_fugitive(30.0, 1.0)
		without = move_shares(1.0, [(1.0, owed_without / 50.0)])
		waived = move_shares(1.0, [(1.0, owed_with / 50.0)])
		self.assertGreater(waived[0], without[0])


class LiabilitySpiral(unittest.TestCase):
	def years_of_flight(self, rule, years=8, registered=100.0, shock_share=0.1, rate=0.2):
		"""(take on a stayer, payers remaining) each year after a shock removes some; the stayers answer the take with the
		migration rule, a place to go taking nothing."""
		remaining = registered * (1.0 - shock_share)
		history = []
		for _ in range(years):
			take = liability.stayers_share_taken(rule, rate, registered, remaining)
			history.append((take, remaining))
			share = move_shares(1.0 - take, [(1.0, 0.05)])[0]
			remaining -= remaining * share
		return history

	def test_under_a_collective_rule_a_shock_raises_the_burden_and_drives_more_out(self):
		history = self.years_of_flight(liability.COLLECTIVE)
		takes = [take for take, _ in history]
		self.assertEqual(takes, sorted(takes))
		self.assertGreater(takes[-1], takes[0])
		fractions_lost = [1.0 - after[1] / before[1] for before, after in zip(history, history[1:])]
		self.assertEqual(fractions_lost, sorted(fractions_lost))
		self.assertGreater(fractions_lost[-1], fractions_lost[0])

	def test_under_an_individual_rule_the_burden_does_not_rise_and_the_same_share_leaves_each_year(self):
		history = self.years_of_flight(liability.INDIVIDUAL)
		self.assertEqual({take for take, _ in history}, {0.2})
		fractions_lost = [1.0 - after[1] / before[1] for before, after in zip(history, history[1:])]
		for fraction in fractions_lost:
			self.assertAlmostEqual(fraction, fractions_lost[0])

	def test_a_shock_leaves_fewer_payers_under_the_collective_rule(self):
		collective = self.years_of_flight(liability.COLLECTIVE)[-1][1]
		individual = self.years_of_flight(liability.INDIVIDUAL)[-1][1]
		self.assertLess(collective, individual)

	def test_nothing_is_owed_by_a_unit_nobody_remains_in(self):
		self.assertIsNone(liability.stayers_share_taken(liability.COLLECTIVE, 0.2, 100.0, 0.0))
		self.assertEqual(liability.shares_by_unit(liability.COLLECTIVE, 0.2, {"a": 10.0, "b": 10.0}, {"a": 5.0, "b": 0.0}),
						 {"a": 0.4})

	def test_remission_lowers_the_stayers_take_under_either_rule(self):
		for rule in liability.RULES:
			self.assertLess(liability.stayers_share_taken(rule, 0.2, 100.0, 80.0, 0.5),
							liability.stayers_share_taken(rule, 0.2, 100.0, 80.0, 0.0))

	def test_the_collective_take_is_capped_at_everything_the_payer_has(self):
		self.assertEqual(liability.stayers_share_taken(liability.COLLECTIVE, 0.5, 100.0, 10.0), 1.0)


def record_with_tenancy():
	return SimpleNamespace(cohorts={}, titles={"t1": {"lord": 0.5}},
						   tenancies={"t1": [{"tenant": "serf", "lessor": "lord", "share": 0.5, "arrears": 0.0}]})


class LandLeftByFlight(unittest.TestCase):
	def test_the_land_a_fleeing_tenant_worked_goes_back_to_no_holder(self):
		record = record_with_tenancy()
		self.assertEqual(tenant_flees(record, "serf", 1.0), {"t1": 0.5})
		self.assertEqual(record.titles["t1"], {})
		self.assertEqual(record.tenancies, {})

	def test_a_part_of_the_household_leaving_releases_that_part(self):
		record = record_with_tenancy()
		tenant_flees(record, "serf", 0.4)
		self.assertAlmostEqual(record.tenancies["t1"][0]["share"], 0.3)
		self.assertAlmostEqual(record.titles["t1"]["lord"], 0.3)


class TaxResponseLevers(unittest.TestCase):
	def government(self):
		return Government("government:home", ActorRecord(kind="government", money=0.0, revenue_forms=[
			{"form": "land_tax", "basis": "harvest", "rate": 0.1}]))

	def set(self, government, **request):
		context = government_levers.LeverContext(list(government.record.revenue_forms), {"wheat_kg"}, 1000.0)
		return government_levers.set_lever(government.record, request, context)

	def test_a_state_defaults_to_individual_liability_and_no_amnesty(self):
		record = self.government().record
		self.assertEqual(government_levers_tax.liability_rule(record), liability.INDIVIDUAL)
		self.assertEqual((government_levers_tax.amnesty_share(record), government_levers_tax.immunity_years(record),
						  government_levers_tax.remission_share(record)), (0.0, 0.0, 0.0))

	def test_each_lever_changes_the_field_the_rules_read(self):
		government = self.government()
		self.set(government, lever="liability", value="collective")
		self.set(government, lever="amnesty", value=0.8)
		self.set(government, lever="immunity", value=3)
		self.set(government, lever="remission", value=0.25)
		record = government.record
		self.assertEqual(government_levers_tax.liability_rule(record), "collective")
		self.assertEqual(government_levers_tax.amnesty_share(record), 0.8)
		self.assertEqual(government_levers_tax.immunity_years(record), 3.0)
		self.assertEqual(government_levers_tax.remission_share(record), 0.25)
		self.assertEqual(government_levers.current(record)["liability"], "collective")

	def test_remission_lowers_the_rates_every_reader_sees(self):
		government = self.government()
		self.set(government, lever="remission", value=0.5)
		self.assertAlmostEqual(government_levers.revenue_forms(government.record)[0]["rate"], 0.05)

	def test_a_bad_request_is_a_refusal_with_a_cause_and_changes_nothing(self):
		government = self.government()
		for request, cause in ((dict(lever="liability", value="tribal"), "unknown_rule"),
							   (dict(lever="amnesty", value=1.5), "value_out_of_range"),
							   (dict(lever="remission", value="much"), "value_not_number")):
			result = self.set(government, **request)
			self.assertIsInstance(result, Refusal)
			self.assertEqual(result.cause, cause)
		self.assertEqual(government.record.levers, {})

	def test_a_lever_is_cleared_with_a_null_value(self):
		government = self.government()
		self.set(government, lever="amnesty", value=0.5)
		self.set(government, lever="amnesty", value=None)
		self.assertEqual(government_levers_tax.amnesty_share(government.record), 0.0)

	def test_land_taken_up_from_desertion_owes_nothing_in_the_immunity_years(self):
		self.assertEqual(flight.share_after_immunity(0.2, 2.0, 3.0), 0.0)
		self.assertEqual(flight.share_after_immunity(0.2, 3.0, 3.0), 0.2)


class HidingAndTheRate(unittest.TestCase):
	def test_with_a_cost_that_scales_with_the_rate_the_rate_alone_changes_nothing_hidden(self):
		# Yitzhaki: a penalty in proportion to the tax leaves the rate out of the choice
		shares = [evasion.hidden_share_at_cost(rate, 0.4, rate) for rate in (0.05, 0.1, 0.2)]
		for share in shares:
			self.assertAlmostEqual(share, shares[0])

	def test_the_rate_response_of_the_built_rule_comes_only_from_the_fixed_cost_curve(self):
		self.assertLess(evasion.hidden_share(0.05, 0.4), evasion.hidden_share(0.1, 0.4))


if __name__ == "__main__":
	unittest.main()
