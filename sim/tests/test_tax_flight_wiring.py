"""Complaint 657: the year's flight wiring. Each test builds the inputs and calls the rule the engine hands its numbers to:
the take by tile, the penalty on each route, the tenants who leave, the fugitives and their return."""
import unittest
from types import SimpleNamespace

from sim.agents import fiscal_flight, fiscal_response, flight, flight_inputs, liability, revenue
from sim.agents import government_levers_tax
from sim.agents.api import Government
from sim.agents.records import ActorRecord
from sim.economy import flight_routes, flight_year
from sim.economy.protocols import YearInputs
from sim.labour.api import MarketState, Route

QUICK_TOPIC = True

HARVEST_FORM = {"form": "grain_levy", "basis": "harvest", "rate": 0.2}


def bands(count):
	return [count / 5.0] * 5


class TakeByTile(unittest.TestCase):
	def test_the_take_is_the_rate_times_the_reach_on_the_tile(self):
		taken = flight_inputs.taxed_share_by_tile([HARVEST_FORM], {"a": 1.0, "b": 0.5}, liability.INDIVIDUAL, {"a": 10.0, "b": 10.0},
												  {"a": 10.0, "b": 10.0})
		self.assertAlmostEqual(taken["a"], 0.2)
		self.assertAlmostEqual(taken["b"], 0.1)

	def test_a_tile_the_form_does_not_cover_bears_none_of_it(self):
		form = dict(HARVEST_FORM, tiles=["a"])
		taken = flight_inputs.taxed_share_by_tile([form], {"a": 1.0, "b": 1.0}, liability.INDIVIDUAL, {}, {"a": 10.0, "b": 10.0})
		self.assertEqual(taken["b"], 0.0)

	def test_a_form_on_something_other_than_income_is_not_a_take_on_a_worker(self):
		form = {"form": "tariff", "basis": "imports_value", "rate": 0.3}
		self.assertEqual(flight_inputs.take_on_tile([form], "a", 1.0), 0.0)

	def test_under_collective_liability_those_who_stay_bear_the_take_of_those_who_left(self):
		args = ([HARVEST_FORM], {"a": 1.0})
		individual = flight_inputs.taxed_share_by_tile(*args, liability.INDIVIDUAL, {"a": 100.0}, {"a": 50.0})
		collective = flight_inputs.taxed_share_by_tile(*args, liability.COLLECTIVE, {"a": 100.0}, {"a": 50.0})
		self.assertAlmostEqual(collective["a"], 2.0 * individual["a"])


class PenaltyOnTheRoutes(unittest.TestCase):
	ROUTES = {"work@a": [Route("work@b", 1.0), Route("work@c", 1.0)]}

	def penalised(self, reach_b, reach_c, penalty=flight.expected_penalty_of_leaving):
		return flight_routes.with_recapture_penalty(self.ROUTES, {"work@a": 0.2}, {"b": reach_b, "c": reach_c},
													{"work@a": 100.0}, penalty)["work@a"]

	def test_a_destination_beyond_the_states_reach_carries_no_penalty(self):
		routes = self.penalised(0.0, 0.8)
		self.assertEqual(routes[0].expected_penalty, 0.0)
		self.assertGreater(routes[1].expected_penalty, 0.0)

	def test_the_penalty_follows_what_he_owes(self):
		owed = 0.2 * 100.0
		self.assertEqual(self.penalised(0.8, 0.8)[0].expected_penalty, flight.expected_penalty_of_leaving(owed, 0.8))

	def test_without_the_rule_or_a_take_the_routes_are_unchanged(self):
		self.assertEqual(self.penalised(0.8, 0.8, penalty=None), self.ROUTES["work@a"])
		none_taken = flight_routes.with_recapture_penalty(self.ROUTES, {}, {"b": 1.0}, {"work@a": 100.0}, flight.expected_penalty_of_leaving)
		self.assertEqual(none_taken, self.ROUTES)

	def test_the_inputs_carry_no_take_unless_the_engine_fills_it(self):
		inputs = YearInputs(1, {}, 0.5, {}, {})
		self.assertEqual((dict(inputs.taxed_share_by_tile), inputs.amnesty_share, inputs.immunity_years), ({}, 0.0, 0.0))


class Leavers(unittest.TestCase):
	def test_only_taxed_areas_with_people_leaving_flee(self):
		shares = flight_year.fleeing_shares({"x": -10.0, "y": -10.0, "z": 5.0}, {"x": 100.0, "y": 100.0, "z": 50.0}, {"x": 0.5, "z": 0.5})
		self.assertEqual(shares, {"x": 0.05})

	def test_tenants_of_a_fleeing_area_leave_the_land_and_the_title_goes_back_to_no_holder(self):
		record = SimpleNamespace(
			cohorts={"serf": SimpleNamespace(agent_id="serf", tile="a"), "other": SimpleNamespace(agent_id="other", tile="b")},
			titles={"t1": {"lord": 0.5}},
			tenancies={"t1": [{"tenant": "serf", "lessor": "lord", "share": 0.5, "arrears": 0.0}]})
		released = flight_year.tenants_flee(record, {"work@a": 1.0})
		self.assertEqual(released, {"t1": 0.5})
		self.assertEqual(record.titles["t1"], {})

	def test_each_year_away_adds_the_take_to_what_a_fugitive_owes(self):
		fugitives = {}
		flight_year.note_fugitives(fugitives, {"home": 0.1}, {"home": 100.0}, {"home": -10.0, "refuge": 10.0}, {"home": 0.2}, {"home": 50.0})
		self.assertEqual(fugitives["home"]["people"], 10.0)
		self.assertEqual(fugitives["home"]["refuge"], "refuge")
		flight_year.note_fugitives(fugitives, {}, {"home": 90.0}, {}, {"home": 0.2}, {"home": 50.0})
		self.assertAlmostEqual(fugitives["home"]["arrears_per_head"], 20.0)


class WhatTheTakeAccountsFor(unittest.TestCase):
	ROUTES = {"work@a": [Route("work@b", 5.0)]}
	INCOME = {"work@a": 100.0, "work@b": 100.0}
	FLOOR = {"work@a": 50.0, "work@b": 50.0}

	def fraction(self, home_take, away_take=0.0, routes=None):
		taxed = {"work@a": home_take, "work@b": away_take}
		return flight_year.tax_attributable_fractions(routes or self.ROUTES, taxed, self.INCOME, self.FLOOR).get("work@a", 0.0)

	def test_a_heavier_take_accounts_for_more_of_the_flow(self):
		self.assertGreater(self.fraction(0.4), self.fraction(0.1))
		self.assertGreater(self.fraction(0.1), 0.0)

	def test_where_the_take_is_the_same_at_both_ends_it_accounts_for_less_than_where_only_home_is_taxed(self):
		self.assertGreater(self.fraction(0.3, 0.0), self.fraction(0.3, 0.3))

	def test_a_recapture_penalty_on_the_route_lowers_the_share_of_the_flow_the_take_accounts_for(self):
		with_penalty = {"work@a": [Route("work@b", 5.0, expected_penalty=40.0)]}
		self.assertLess(self.fraction(0.3, routes=with_penalty), self.fraction(0.3))

	def test_an_area_the_state_takes_nothing_from_has_no_flight_to_account_for(self):
		self.assertEqual(self.fraction(0.0), 0.0)


class ReturnOfFugitives(unittest.TestCase):
	def share(self, home=1.0, away=1.0, arrears=0.0):
		return flight_year.returning_share(away, home, arrears, 50.0, 5.0)

	def test_a_better_home_brings_more_people_back(self):
		self.assertGreater(self.share(home=1.5), self.share(home=1.0))

	def test_what_he_owes_on_coming_home_keeps_him_away(self):
		self.assertLess(self.share(arrears=100.0), self.share(arrears=0.0))

	def test_an_amnesty_lowers_what_he_owes_and_so_brings_him_back(self):
		owed = [flight.arrears_owed_by_fugitive(100.0, amnesty) for amnesty in (0.0, 0.5, 1.0)]
		shares = [self.share(arrears=amount) for amount in owed]
		self.assertEqual(shares, sorted(shares))
		self.assertGreater(shares[-1], shares[0])

	def test_an_income_that_cannot_be_weighed_brings_nobody(self):
		self.assertEqual(self.share(home=0.0), 0.0)

	def test_people_who_return_are_taken_from_the_refuge_and_put_home(self):
		workforce = MarketState(workers={"refuge": {"digger": bands(100.0)}, "home": {"digger": bands(10.0)}})
		moved = flight_year.move_back(workforce, "refuge", "home", 30.0)
		self.assertAlmostEqual(moved, 30.0)
		self.assertAlmostEqual(sum(workforce.workers["refuge"]["digger"]), 70.0)
		self.assertAlmostEqual(sum(workforce.workers["home"]["digger"]), 40.0)

	def run_return(self, take=0.4, amnesty=0.0, immunity=0.0, arrears=0.0, income_home=100.0, income_refuge=100.0):
		workforce = MarketState(workers={"refuge": {"digger": bands(100.0)}, "home": {"digger": bands(10.0)}})
		fugitives = {"home": {"people": 40.0, "arrears_per_head": arrears, "refuge": "refuge"}}
		came = flight_year.return_fugitives(
			workforce, fugitives, {"home": take}, {"home": 50.0, "refuge": 50.0}, {"home": income_home, "refuge": income_refuge},
			amnesty, immunity, lambda refuge, home: 5.0, flight.arrears_owed_by_fugitive, flight.share_after_immunity)
		return came.get("home", 0.0), fugitives

	def test_a_state_that_takes_less_at_home_gets_more_of_its_fugitives_back(self):
		self.assertGreater(self.run_return(take=0.0)[0], self.run_return(take=0.4)[0])

	def test_immunity_on_the_land_taken_up_again_brings_more_back_than_none(self):
		self.assertGreater(self.run_return(immunity=5.0)[0], self.run_return(immunity=0.0)[0])

	def test_an_amnesty_brings_more_back_where_arrears_are_owed(self):
		self.assertGreater(self.run_return(amnesty=1.0, arrears=200.0)[0], self.run_return(amnesty=0.0, arrears=200.0)[0])

	def test_people_who_came_home_are_no_longer_fugitives(self):
		came, fugitives = self.run_return(take=0.0, income_home=300.0)
		self.assertAlmostEqual(fugitives["home"]["people"], 40.0 - came)


def income_form(rate, reach, base=1000.0):
	return revenue.Assessment("levy", "harvest", base, rate, reach * rate * base, collectible=reach)


class TheMenuNetsTheBaseLostToFlight(unittest.TestCase):
	def world(self, reach, rate=0.2, away=0.0):
		return SimpleNamespace(revenue_assessments=lambda: [income_form(rate, reach)], fugitive_share=lambda: away)

	def test_a_raise_beyond_the_officials_reach_yields_less_than_the_extra_rate_on_the_base(self):
		naive = (fiscal_response.new_rate_of(0.2) - 0.2) * 1000.0 * 0.4
		self.assertLess(fiscal_response.rate_raise_yield(self.world(0.4)), naive)

	def test_where_the_officials_reach_everyone_nobody_can_leave_untaxed(self):
		self.assertAlmostEqual(fiscal_response.rate_raise_yield(self.world(1.0)), (fiscal_response.new_rate_of(0.2) - 0.2) * 1000.0)

	def test_the_share_who_leave_rises_with_the_take_and_falls_with_the_reach(self):
		self.assertGreater(fiscal_flight.flight_share(0.4, 0.3), fiscal_flight.flight_share(0.2, 0.3))
		self.assertGreater(fiscal_flight.flight_share(0.4, 0.3), fiscal_flight.flight_share(0.4, 0.8))
		self.assertEqual(fiscal_flight.flight_share(0.0, 0.3), 0.0)

	def test_a_state_past_the_rate_that_yields_most_is_offered_a_remission_and_one_below_it_is_not(self):
		low = fiscal_response.rate_cut_yield(self.world(0.3, rate=0.02))
		high = fiscal_response.rate_cut_yield(self.world(0.3, rate=0.9))
		self.assertEqual(low, 0.0)
		self.assertGreaterEqual(high, 0.0)

	def test_an_amnesty_is_offered_only_where_people_have_fled(self):
		forms = [income_form(0.2, 0.4)]
		self.assertEqual(fiscal_response.amnesty_yield(forms, 0.0), 0.0)
		self.assertGreaterEqual(fiscal_response.amnesty_yield(forms, 0.3), 0.0)

	def test_collective_liability_recovers_the_leavers_assessment_only_where_people_have_fled(self):
		self.assertEqual(fiscal_flight.collective_yield(self.world(0.4), [income_form(0.2, 0.4)]), (0.0, 0.0))
		recovered, lost = fiscal_flight.collective_yield(self.world(0.4, away=0.3), [income_form(0.2, 0.4)])
		self.assertGreater(recovered, 0.0)
		self.assertGreaterEqual(lost, 0.0)


class FlightOptionsInTheMenu(unittest.TestCase):
	def state_and_world(self, away):
		form = {"form": "levy", "basis": "harvest", "rate": 0.3}
		state = Government("government:home", ActorRecord(kind="government", money=0.0, revenue_forms=[form]))
		world = SimpleNamespace(revenue_assessments=lambda: [income_form(0.3, 0.4)], fugitive_share=lambda: away,
								revenue_forms=lambda: [form])
		return state, world

	def offered(self, away):
		state, world = self.state_and_world(away)
		options = fiscal_response.flight_options(state, world, 1000.0, 400.0, {})
		return {option.subject for option in options}

	def test_an_amnesty_and_collective_liability_are_offered_only_where_people_have_fled(self):
		self.assertEqual(self.offered(0.0), set())
		self.assertEqual(self.offered(0.3), {fiscal_response.AMNESTY, fiscal_response.LIABILITY})

	def test_a_state_already_collective_is_not_offered_it_again(self):
		state, world = self.state_and_world(0.3)
		state.record.levers[government_levers_tax.LIABILITY] = liability.COLLECTIVE
		names = {option.subject for option in fiscal_response.flight_options(state, world, 1000.0, 400.0, {})}
		self.assertNotIn(fiscal_response.LIABILITY, names)

	def test_the_levers_a_choice_covered_money_with_are_set_the_way_a_player_sets_them(self):
		state, world = self.state_and_world(0.3)
		pulled = state.pull_tax_response_levers({fiscal_response.LIABILITY: 5.0, fiscal_response.AMNESTY: 5.0}, world)
		self.assertEqual(pulled, {fiscal_response.LIABILITY: liability.COLLECTIVE, fiscal_response.AMNESTY: 1.0})
		self.assertEqual(government_levers_tax.liability_rule(state.record), liability.COLLECTIVE)
		self.assertEqual(government_levers_tax.amnesty_share(state.record), 1.0)

	def test_a_choice_that_covered_nothing_with_them_sets_none(self):
		state, world = self.state_and_world(0.3)
		self.assertEqual(state.pull_tax_response_levers({fiscal_response.RATE: 5.0}, world), {})


if __name__ == "__main__":
	unittest.main()
