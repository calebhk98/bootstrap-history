"""SCENARIO (Complaints 497, 645): the opening solved for its households' plans is cut in cost without changing what it
solves. The memory of what a bid takes from the market and the plan (opening_bid_memory.py) gives the same bids, the same
households' plans and the same quantities and prices as working everything out again, on a small built economy whose
households' choice cycles."""
import dataclasses
import unittest
from unittest import mock

from sim.economy import household_work_year, households, opening, opening_bid_memory, opening_income, opening_plans
from sim.economy.household_work_year import basket_key, cohort_basket
from sim.economy.market_memory import YearView
from sim.economy.setup import labour_area
from sim.tests.test_economy_opening_household_plans import household_work_setup

HIRED_HOURS = 0.5


class NoMemory:
    """Everything worked out again at every ask, as before the memory existed."""
    def basket(self, setup, record, cohort):
        return cohort_basket(setup, record, cohort)

    def priced(self, setup, record, view, cohort, basket):
        return households.need_prices(basket, view, cohort.tile)

    def stores(self, record, cohort):
        return None


def solved_without_memory(setup):
    """The opening as solved with nothing remembered between asks for bids."""
    with mock.patch.object(opening_bid_memory, "BidMemory", NoMemory):
        return opening.open_economy(setup)


def cycling_choice(real_household_plans):
    """The households' choice, made to cycle: each hires while the hours a household gains from hiring exceed the number
    of households hiring, so all hiring leaves none hiring and none hiring leaves all."""
    def choose(setup, record, area_map, room_by_tile=None):
        real = real_household_plans(setup, record, area_map, room_by_tile)
        names = sorted(real.by_cohort)
        margins = {name: float(len(names) - index) - 0.5 for index, name in enumerate(names)}
        hiring = sum(1 for cohort in record.cohorts.values() if cohort.hired_work_per_person > 0.0)
        by_cohort = {name: ((HIRED_HOURS if margins[name] - hiring > 0.0 else 0.0),) + tuple(plan[1:])
                     for name, plan in real.by_cohort.items()}
        return opening_plans.HouseholdPlans(by_cohort, real.service_price_by_tile, margins)
    return choose


def summary(solved):
    record = solved[0]
    return ({name: (cohort.hired_work_per_person, tuple(cohort.milled_grains)) for name, cohort in record.cohorts.items()},
            dict(record.opening_demand), dict(record.memory.prices),
            {key: dataclasses.asdict(producer) for key, producer in record.producers.items()})


class BidMemoryTests(unittest.TestCase):
    def test_bids_asked_again_at_other_incomes_are_the_bids_of_working_everything_out_again(self):
        setup = household_work_setup()
        record, area_map, _carriage = opening.open_economy(setup)
        view = YearView(record.memory, record.book, area_map, setup.currency_id, labour_area)
        memory = opening_bid_memory.BidMemory()
        for per_head in (900.0, 600.0, 450.0, 300.0):
            record.cohorts.update(opening_income.with_income(record.cohorts, per_head, 0.9))
            remembered = [(cohort.agent_id, bid) for cohort, bid, _price in opening._opening_bids(setup, record, view, memory)]
            fresh = [(cohort.agent_id, bid) for cohort, bid, _price in opening._opening_bids(setup, record, view)]
            self.assertEqual(remembered, fresh)
            self.assertTrue(remembered)

    def test_cohorts_of_one_basket_share_what_the_memory_holds_and_others_do_not(self):
        setup = household_work_setup()
        record, _area_map, _carriage = opening.open_economy(setup)
        memory = opening_bid_memory.BidMemory()
        cohorts = sorted(record.cohorts.values(), key=lambda cohort: cohort.agent_id)
        for cohort in cohorts:
            self.assertIs(memory.stores(record, cohort), memory.stores(record, cohort))
        distinct = {id(memory.stores(record, cohort)) for cohort in cohorts}
        self.assertEqual(len(distinct), len({basket_key(record, cohort) for cohort in cohorts}))


class FastPathEqualsFullPathTests(unittest.TestCase):
    def test_an_opening_whose_choice_settles_has_the_same_plans_quantities_and_prices(self):
        setup = household_work_setup()
        self.assertEqual(summary(opening.open_economy(setup)), summary(solved_without_memory(setup)))

    def test_an_opening_whose_choice_cycles_has_the_same_plans_quantities_and_prices(self):
        setup = household_work_setup()
        cycling = cycling_choice(opening_plans.household_plans)
        with mock.patch.object(opening_plans, "household_plans", cycling):
            fast = summary(opening.open_economy(setup))
        with mock.patch.object(opening_plans, "household_plans", cycling):
            full = summary(solved_without_memory(setup))
        self.assertEqual(fast, full)
        hiring = sum(1 for hired, _grains in fast[0].values() if hired > 0.0)
        self.assertTrue(0 < hiring < len(fast[0]))      # settled between all hiring and none: the bisection ran


if __name__ == "__main__":
    unittest.main()
