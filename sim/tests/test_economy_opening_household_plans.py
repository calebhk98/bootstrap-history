"""Complaint 473: the opening is solved to a fixed point with the households' first-year choices. A year's households
hire household work and buy milled the grains whose milling costs less than their hours (`household_work_year.plans`);
an opening sized to final demand while its cohorts grind by hand and hire nothing sized the producers of a grain for
households that then buy flour, and no labour for the work they then hire. The rules, each on built inputs: the plans
are a pure reading of the cohorts' choice, the cohorts take them, the hired work is a use of hands that a tile's price
rations, the iteration stops where the choice stops moving, and a solved opening's final demand is what its households'
choice at its prices buys."""

QUICK_TOPIC = True

import dataclasses
import math
import types
import unittest

from sim.economy import (goods_market, household_grinding, household_work_year, households_work, labour_state, opening,
                         opening_plans)
from sim.economy.households_basket import Basket, NeedSpec, make_basket
from sim.economy.households_cohort import Cohort
from sim.economy.market_memory import YearView, market_key
from sim.economy.recipes import recipe_from_entry as recipes_from_entry
from sim.economy.setup import TradeSpec, labour_area
from sim.economy.types import GoodSpec, LabourOffer, Recipe
from sim.tests import economy_fixture as fixture
from sim.world.need_demand import NEED_SUBSTITUTION_ELASTICITY

DATA = {"days_per_year": 100, "tasks": {
    "grinding": {"needs_hearth": False, "scales_with_ground_grain": True, "hours_per_adult_woman_per_day": 2.0,
                 "adult_women_per_person": 0.25}}}
NEED_DATA = {"needs": {"food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 10.0},
                       "household_work": {"surplus_budget_share": 0.0, "subsistence_per_capita_per_year": 0.0}},
             "goods": {"wheat_kg": {"satisfies": {"food": 1.0}, "milled_as": "flour_kg"},
                       "flour_kg": {"satisfies": {"food": 1.0}},
                       "domestic_service_hour": {"satisfies": {"household_work": 1.0}}}}


class View:
    def __init__(self, wage, prices):
        self.wage_per_hour, self.prices = wage, prices

    def wage(self, _trade, _area):
        return self.wage_per_hour

    def price(self, good, _area):
        return self.prices.get(good)

    def area_of(self, _good, tile):
        return tile


def setup():
    return types.SimpleNamespace(
        household_work=DATA, working_hours_per_year=1000.0, servant_trade="servant", hunger_need="food", fuel_need="warmth",
        ready_to_eat=frozenset(), milled_as=household_grinding.milled_as_map(NEED_DATA),
        basket_for=lambda tile: make_basket(NEED_DATA, {}))


def record_and_offers(wage):
    worker = Cohort(agent_id="c", tile="t1", income_class=0, people=100.0, working_people=50.0, ownership_share=0.0)
    record = types.SimpleNamespace(titles={"t1": {"c": 1.0}}, tenancies={}, cohorts={"c": worker},
                                    sold_share_expected={market_key("labourer", labour_area("t1")): 1.0})
    return record, [LabourOffer("c", "labourer", labour_area("t1"), 500.0, wage)]


class PlansTests(unittest.TestCase):
    def test_a_cohort_whose_hours_are_dear_plans_to_buy_the_grain_milled(self):
        record, offers = record_and_offers(1.0)
        plans = household_work_year.plans(setup(), record, View(1.0, {"wheat_kg": 1.0, "flour_kg": 2.0}), offers, {})
        self.assertEqual(plans["c"][2], ("wheat_kg",))

    def test_a_cohort_whose_hours_are_cheap_plans_to_grind_by_hand(self):
        record, offers = record_and_offers(1.0)
        plans = household_work_year.plans(setup(), record, View(1.0, {"wheat_kg": 1.0, "flour_kg": 9.0}), offers, {})
        self.assertEqual(plans["c"][2], ())

    def test_reading_the_plans_changes_no_cohort(self):
        record, offers = record_and_offers(1.0)
        household_work_year.plans(setup(), record, View(1.0, {"wheat_kg": 1.0, "flour_kg": 2.0}), offers, {})
        self.assertEqual(record.cohorts["c"].milled_grains, ())

    def test_deciding_stores_what_the_plans_read(self):
        record, offers = record_and_offers(1.0)
        view = View(1.0, {"wheat_kg": 1.0, "flour_kg": 2.0})
        plans = household_work_year.plans(setup(), record, view, offers, {})
        household_work_year.decide(setup(), record, view, offers, {})
        self.assertEqual(record.cohorts["c"].milled_grains, plans["c"][2])
        self.assertEqual(record.cohorts["c"].hired_work_per_person, plans["c"][0])


class CohortsTakePlansTests(unittest.TestCase):
    def cohorts(self):
        return {"c": Cohort(agent_id="c", tile="t1", income_class=0, people=100.0, working_people=50.0, ownership_share=0.0),
                "d": Cohort(agent_id="d", tile="t1", income_class=1, people=10.0, working_people=5.0, ownership_share=0.0)}

    def test_the_cohorts_hold_the_planned_hours_hired_and_grains_milled(self):
        held = opening_plans.with_plans(self.cohorts(), opening_plans.HouseholdPlans({"c": (0.4, 12.0, ("wheat_kg",))}))
        self.assertEqual(held["c"].milled_grains, ("wheat_kg",))
        self.assertEqual(held["c"].hired_work_per_person, 0.4)

    def test_a_cohort_with_no_plan_is_left_as_it_is(self):
        cohorts = self.cohorts()
        held = opening_plans.with_plans(cohorts, opening_plans.HouseholdPlans({"c": (0.4, 12.0, ())}))
        self.assertIs(held["d"], cohorts["d"])

    def test_plans_that_change_nothing_agree_with_an_opening_that_held_none(self):
        self.assertTrue(opening_plans.agree(self.cohorts(), opening_plans.HouseholdPlans({"c": (0.0, 5.0, ()), "d": (0.0, 1.0, ())})))

    def test_a_planned_milled_grain_or_hire_is_not_what_an_opening_held(self):
        self.assertFalse(opening_plans.agree(self.cohorts(), opening_plans.HouseholdPlans({"c": (0.0, 5.0, ("wheat_kg",))})))
        self.assertFalse(opening_plans.agree(self.cohorts(), opening_plans.HouseholdPlans({"d": (0.2, 5.0, ())})))

    def test_the_service_price_a_tile_calls_for_is_posted_where_a_market_for_it_exists(self):
        memory = types.SimpleNamespace(prices={market_key("service_hour", "t1"): 0.4, market_key("service_hour", "t2"): 0.4}, noted=[])
        memory.note_usual_price = memory.noted.append
        area_map = types.SimpleNamespace(area_of=lambda good, tile: tile)
        basket = Basket((NeedSpec(household_work_year.WORK_NEED, 0.0, 0.0, (("service_hour", 1.0),)),), 2.0, {})
        opening_plans.post_service_prices(memory, area_map, types.SimpleNamespace(basket_for=lambda tile: basket), {"t1": 1.5, "t2": 0.1})
        self.assertEqual(memory.prices, {market_key("service_hour", "t1"): 1.5, market_key("service_hour", "t2"): 0.4})     # a price never falls to the floor


class ServiceRoomTests(unittest.TestCase):
    """The hours a tile's households hire are one more use of its hands: where they would take more than the other
    producers leave, the price of an hour hired rises until hiring falls."""

    def test_households_that_all_fit_leave_the_price_where_it_is(self):
        self.assertEqual(households_work.service_price_that_fits([(3.0, 10.0, 1.0), (2.0, 10.0, 1.0)], 25.0), 0.0)

    def test_the_household_whose_hour_is_worth_least_stops_hiring_first(self):
        floor = households_work.service_price_that_fits([(3.0, 10.0, 1.0), (2.0, 10.0, 1.0), (1.5, 10.0, 1.0)], 25.0)
        self.assertEqual(floor, 1.5)       # at 1.5 only the first two hire, which the room covers

    def test_a_price_that_stops_the_dearest_hour_hiring_leaves_no_hiring(self):
        self.assertEqual(households_work.service_price_that_fits([(3.0, 10.0, 1.0)], 5.0), 3.0)

    def test_a_household_that_would_not_hire_anyway_takes_no_room(self):
        self.assertEqual(households_work.service_price_that_fits([(0.5, 10.0, 1.0), (3.0, 10.0, 1.0)], 10.0), 0.0)

    def test_a_cohort_hires_nothing_at_a_floor_its_hour_is_not_worth(self):
        record, offers = record_and_offers(1.0)
        view = View(1.0, {"wheat_kg": 1.0, "flour_kg": 9.0, "domestic_service_hour": 0.5})   # it grinds by hand, so it has work to hire
        hired = household_work_year.plans(setup(), record, view, offers, {})["c"][0]
        floor_hired = household_work_year.plans(setup(), record, view, offers, {}, {"t1": 1.5})["c"][0]
        self.assertGreater(hired, 0.0)
        self.assertLess(floor_hired, 0.01 * hired)


GRAIN, FLOUR, SERVICE, MILLER, SERVANT, MILL, SERVE = "grain_kg", "flour_kg", "service_hour", "miller", "servant", "mill_flour", "serve_hour"
WORK = {"days_per_year": 100, "tasks": dict(DATA["tasks"], water_and_fuel={
    "needs_hearth": False, "hours_per_adult_woman_per_day": 0.5, "adult_women_per_person": 0.25})}   # a fixed load beside the grinding


def household_work_setup(flour_price=0.4, hours_per_worker=2000.0):
    """The fixture economy with a mill and a servant: a household grinds its grain by hand (50 hours a person at its food
    floor) or buys flour, and does its work itself or hires it (12.5 hours a person of the fixed load either way)."""
    base = fixture.small_setup()
    specs = dict(base.specs)
    specs[FLOUR] = GoodSpec(FLOUR, 1.0, 0.1, 0.0, "food")
    specs[SERVICE] = GoodSpec(SERVICE, math.inf, 0.0, 0.0, "service")
    recipes = dict(base.recipes)
    recipes[MILL] = Recipe(MILL, {FLOUR: 1000.0}, {GRAIN: 1000.0}, {MILLER: 20.0})
    recipes[SERVE] = Recipe(SERVE, {SERVICE: 1.0}, {}, {SERVANT: 1.0})
    needs = (NeedSpec(fixture.FOOD, 250.0, 0.6, ((GRAIN, 1.0), (FLOUR, 1.0))),
             NeedSpec(fixture.ORNAMENT, 0.0, 0.05, ((fixture.METAL, 1.0),)),
             NeedSpec(household_work_year.WORK_NEED, 0.0, 0.0, ((SERVICE, 1.0),)))
    need_data = {fixture.FOOD: {"surplus_budget_share": 0.6}, fixture.ORNAMENT: {"surplus_budget_share": 0.05},
                 household_work_year.WORK_NEED: {"surplus_budget_share": 0.0}}
    wages = dict(base.opening_wages, **{MILLER: 1.2, SERVANT: 0.4})
    return dataclasses.replace(
        base, specs=specs, recipes=recipes, basket=Basket(needs, NEED_SUBSTITUTION_ELASTICITY, need_data),
        trades={trade: TradeSpec(trade) for trade in wages}, opening_wages=wages,
        opening_prices=dict(base.opening_prices, **{FLOUR: flour_price, SERVICE: 0.4}), household_work=WORK,
        milled_as={GRAIN: FLOUR}, servant_trade=SERVANT, working_hours_per_year=hours_per_worker)


def bought_by_households(setup, record, area_map):
    view = YearView(record.memory, record.book, area_map, setup.currency_id, labour_area)
    bought = {GRAIN: 0.0, FLOUR: 0.0}
    for _cohort, bid, price in opening._opening_bids(setup, record, view):
        if bid.good in bought:
            bought[bid.good] += goods_market.quantity_at(bid, price)
    return bought


def hired_hours(record):
    return sum(cohort.hired_work_per_person * cohort.people for cohort in record.cohorts.values())


class SolvedOpeningTests(unittest.TestCase):
    def test_the_opening_demands_the_grain_its_households_buy_at_the_solved_prices(self):
        for flour_price, buys_milled in ((0.2, True), (30.0, False)):
            with self.subTest(flour_price=flour_price):
                setup = household_work_setup(flour_price)
                record, area_map, _carriage = opening.open_economy(setup)
                bought = bought_by_households(setup, record, area_map)
                self.assertAlmostEqual(record.opening_demand.get(GRAIN, 0.0), bought[GRAIN], delta=1e-6 * max(1.0, bought[GRAIN]))
                self.assertEqual(bought[GRAIN] == 0.0, buys_milled)
                if buys_milled:
                    self.assertGreater(bought[FLOUR], 0.0)

    def test_the_households_of_the_solved_opening_choose_what_it_holds(self):
        setup = household_work_setup()
        record, area_map, _carriage = opening.open_economy(setup)
        chosen = opening_plans.household_plans(setup, record, area_map).by_cohort
        for cohort_id, cohort in record.cohorts.items():
            self.assertAlmostEqual(cohort.hired_work_per_person, chosen[cohort_id][0], delta=1e-6 * max(chosen[cohort_id][0], 1e-3))
            self.assertEqual(tuple(cohort.milled_grains), chosen[cohort_id][2])
        self.assertGreater(hired_hours(record), 0.0)

    def test_the_hired_household_work_is_sized_as_hours_the_solve_covers(self):
        setup = household_work_setup()
        record, _area_map, _carriage = opening.open_economy(setup)
        hired = hired_hours(record)
        self.assertGreater(hired, 0.0)
        self.assertAlmostEqual(record.opening_demand[SERVICE], hired, delta=1e-6 * hired)
        servants = sum(by_trade.get(SERVANT, 0.0) for by_trade in labour_state.producers_hours_needed(setup, record).values())
        self.assertAlmostEqual(servants, hired, delta=1e-6 * hired)
        people = sum(labour_state.people_by_trade(record.workforce, labour_area(tile)).get(SERVANT, 0.0) for tile in setup.tiles)
        self.assertGreaterEqual(people * setup.working_hours_per_year, hired * (1.0 - 1e-9))

    def test_where_hands_are_short_the_service_price_rises_but_no_producer_is_dropped(self):
        roomy = opening.open_economy(household_work_setup())[0]
        scarce_setup = household_work_setup(hours_per_worker=150.0)
        scarce = opening.open_economy(scarce_setup)[0]
        posted = [price for key, price in scarce.memory.prices.items() if key.startswith(SERVICE)]
        self.assertGreater(max(posted), scarce_setup.opening_prices[SERVICE])
        self.assertEqual({producer.recipe_id for producer in roomy.producers.values()} - {SERVE},
                         {producer.recipe_id for producer in scarce.producers.values()} - {SERVE})


class PlacementTests(unittest.TestCase):
    def test_a_service_made_from_hours_alone_is_placed_after_the_producers_that_need_a_place(self):
        setup = household_work_setup()
        recipes = {recipe_id: setup.recipes[recipe_id] for recipe_id in (fixture.FARM, MILL, SERVE, fixture.MINE)}
        order = opening._placement_order({recipe_id: 1.0 for recipe_id in recipes}, recipes, setup)
        self.assertEqual(order[-1], SERVE)

    def test_a_service_flagged_in_data_is_placed_last_though_its_unit_has_a_mass(self):
        setup = household_work_setup()
        specs = dict(setup.specs)
        specs[SERVICE] = GoodSpec(SERVICE, 1.0, 0.0, 0.0, "service")
        flagged = dataclasses.replace(setup.recipes[SERVE], service=True)
        recipes = {recipe_id: setup.recipes[recipe_id] for recipe_id in (fixture.FARM, MILL, fixture.MINE)}
        recipes[SERVE] = flagged
        order = opening._placement_order({recipe_id: 1.0 for recipe_id in recipes},
                                         recipes, dataclasses.replace(setup, specs=specs))
        self.assertEqual(order[-1], SERVE)

    def test_a_recipe_entry_marked_service_in_data_is_a_service_recipe(self):
        entry = {"outputs": {SERVICE: 1.0}, "labour_hours": {SERVANT: 1.0}, "service": True}
        self.assertTrue(recipes_from_entry(SERVE, entry).service)
        self.assertFalse(recipes_from_entry(SERVE, {"outputs": {SERVICE: 1.0}, "labour_hours": {SERVANT: 1.0}}).service)


class FixedPointTests(unittest.TestCase):
    def cohorts(self):
        return {"c": Cohort(agent_id="c", tile="t1", income_class=0, people=100.0, working_people=50.0, ownership_share=0.0)}

    def test_the_solve_stops_at_the_first_opening_that_holds_what_its_households_plan(self):
        plan = opening_plans.HouseholdPlans({"c": (0.4, 12.0, ("wheat_kg",))})
        opened_with = []

        def open_with(plans):
            opened_with.append(plans)
            return opening_plans.with_plans(self.cohorts(), plans) if plans is not None else self.cohorts()
        result = opening_plans.settle(open_with, lambda cohorts: plan, lambda cohorts: cohorts)
        self.assertEqual(opened_with, [None, plan])
        self.assertEqual(result["c"].milled_grains, ("wheat_kg",))

    def test_a_choice_that_depends_on_the_opening_is_followed_until_it_stops_moving(self):
        steps = [("a",), ("a", "b"), ("a", "b")]      # what the households plan once they hold none, one, two grains milled

        def open_with(plans):
            return opening_plans.with_plans(self.cohorts(), plans) if plans is not None else self.cohorts()

        def choose(cohorts):
            return opening_plans.HouseholdPlans({"c": (0.0, 0.0, steps[len(cohorts["c"].milled_grains)])})
        result = opening_plans.settle(open_with, choose, lambda cohorts: cohorts)
        self.assertEqual(result["c"].milled_grains, ("a", "b"))

    def test_a_choice_that_cycles_ends_at_the_pass_bound(self):
        opened = []

        def open_with(plans):
            opened.append(plans)
            return plans

        def choose(_opened):
            return opening_plans.HouseholdPlans({"c": (float(len(opened) % 2), 0.0, ())})
        held = lambda plans: opening_plans.with_plans(self.cohorts(), plans) if plans is not None else self.cohorts()
        opening_plans.settle(open_with, choose, held, passes=4)
        self.assertEqual(len(opened), 5)


    def test_a_choice_that_cycles_between_all_hiring_and_none_settles_on_those_who_gain_most(self):
        margins = {"a": 3.5, "b": 2.5, "c": 1.5, "d": 0.5}      # what an hour hired gains each household when none else hires

        def cohorts(plans):
            return {name: Cohort(agent_id=name, tile="t1", income_class=0, people=100.0, working_people=50.0,
                                 ownership_share=0.0, hired_work_per_person=plans.by_cohort[name][0] if plans else 0.0)
                    for name in margins}

        def choose(opened):
            hiring = sum(1 for cohort in opened.values() if cohort.hired_work_per_person > 0.0)
            # each extra household hiring takes an hour's worth of the gain from all: hiring is dearer the more there are
            return opening_plans.HouseholdPlans({name: (1.0 if gain - hiring > 0.0 else 0.0, 0.0, ()) for name, gain in margins.items()},
                                                margin_by_cohort=margins)
        result = opening_plans.settle(cohorts, choose, lambda opened: opened)
        self.assertEqual(sorted(name for name, cohort in result.items() if cohort.hired_work_per_person > 0.0), ["a", "b"])
        self.assertTrue(opening_plans.agree(result, choose(result)))


if __name__ == "__main__":
    unittest.main()
