"""A cohort's household work in a year (Complaint 645): hiring by the worth of its hour, own hours kept out of the
labour offered, and the cooked food of a cohort with no hearth."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.tests.economy_view_defaults import ViewDefaults
from sim.economy import household_work_year, households_work
from sim.world.need_basket import make_basket
from sim.economy.households_cohort import Cohort
from sim.economy.market_memory import market_key
from sim.economy.setup import SetupTrade, labour_area
from sim.economy.types import LabourOffer
from sim.world import need_basket

DATA = {"days_per_year": 100, "tasks": {"carrying": {"needs_hearth": False, "hours_per_adult_woman_per_day": 2.0,
                                                    "adult_women_per_person": 0.25},
                                        "cooking": {"needs_hearth": True, "hours_per_person_per_day": 0.5}},
        "cooking_fuel_mj_per_person_per_day": 2.0}
NEED_DATA = {"needs": {"food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 10.0},
                       "warmth": {"surplus_budget_share": 0.1, "subsistence_per_capita_per_year": 300.0},
                       "household_work": {"surplus_budget_share": 0.0, "subsistence_per_capita_per_year": 0.0}},
             "goods": {"wheat_kg": {"satisfies": {"food": 1.0}},
                       "cooked_meal_kg": {"satisfies": {"food": 0.3}, "ready_to_eat": True},
                       "domestic_service_hour": {"satisfies": {"household_work": 1.0}},
                       "wood_kg": {"satisfies": {"warmth": 15.0}}}}


class View(ViewDefaults):
    def __init__(self, wages, prices=None):
        self.wages = wages
        self.prices = prices or {}

    def price(self, good, area):
        return self.prices.get(good)

    def price_of_good(self, good):
        return self.prices.get(good)

    def area_of(self, good, tile):
        return labour_area(tile)

    def wage(self, trade, area):
        return self.wages.get((trade, area))


def cohort(name, tile="t1", people=100.0):
    return Cohort(agent_id=name, tile=tile, income_class=0, people=people, working_people=people / 2,
                  ownership_share=0.0)


def setup():
    return types.SimpleNamespace(
        opening_wages={"labourer": 1.0, "servant": 1.0}, unskilled_trade="labourer", currency_id="coin",
        trades={"labourer": SetupTrade("labourer"), "servant": SetupTrade("servant")},
        household_work=DATA, working_hours_per_year=1000.0, servant_trade="servant", hunger_need="food", fuel_need="warmth", work_need="household_work",
        ready_to_eat=households_work.ready_to_eat_goods(NEED_DATA), milled_as={},
        basket_for=lambda tile: make_basket(NEED_DATA, {}))


def record(titles=None, tenancies=None, cohorts=()):
    expected = {market_key(trade, labour_area("t1")): 1.0 for trade in ("smith", "labourer", "servant")}
    return types.SimpleNamespace(labour=types.SimpleNamespace(sold_share_expected=expected), cohorts={each.agent_id: each for each in cohorts}, land=types.SimpleNamespace(titles=titles or {}, tenancies=tenancies or {}))


class EatenSignatureTests(unittest.TestCase):
    def test_it_is_the_signature_with_no_grains_left_out_and_the_same_hearth(self):
        buying = ("tile:a", True, 2.5, ("wheat_kg", "barley_kg"))
        self.assertEqual(household_work_year.eaten_signature(buying), ("tile:a", True, 2.5, ()))
        with mock.patch.object(household_work_year, "hearth_of", return_value=True):
            self.assertEqual(household_work_year.eaten_signature(buying),
                             household_work_year.signature_of(None, "tile:a", "household:a", 2.5, ("wheat_kg", "barley_kg"), False))


class SplitTests(unittest.TestCase):
    def test_a_cohort_whose_hour_is_worth_more_than_the_servants_price_hires(self):
        rich, area = cohort("rich"), labour_area("t1")
        rec = record({"t1": {"rich": 1.0}}, cohorts=[rich])
        offers = [LabourOffer("rich", "smith", area, 500.0, 1.0)]
        view = View({("smith", area): 3.0, ("servant", area): 1.0})
        hired, own, _milled = household_work_year.cohort_plan(setup(), rec, view, rich, offers)
        self.assertGreater(hired, 0.99 * households_work.hours_needed(100.0, DATA))
        self.assertAlmostEqual(hired + own, households_work.hours_needed(100.0, DATA))

    def test_a_cohort_whose_hour_is_worth_less_does_it_all_itself(self):
        poor, area = cohort("poor"), labour_area("t1")
        rec = record({"t1": {"poor": 1.0}}, cohorts=[poor])
        offers = [LabourOffer("poor", "labourer", area, 500.0, 0.5)]
        view = View({("labourer", area): 0.8, ("servant", area): 1.0})
        hired, own, _milled = household_work_year.cohort_plan(setup(), rec, view, poor, offers)
        self.assertLess(hired, 0.1 * households_work.hours_needed(100.0, DATA))
        self.assertAlmostEqual(hired + own, households_work.hours_needed(100.0, DATA))

    def test_a_cohort_does_its_own_work_when_the_service_costs_more_than_its_hour(self):
        # the servant's wage is low but the hour of service sells dear: the household pays the price, not the wage
        worker, area = cohort("worker"), labour_area("t1")
        rec = record({"t1": {"worker": 1.0}}, cohorts=[worker])
        offers = [LabourOffer("worker", "smith", area, 500.0, 1.0)]
        view = View({("smith", area): 3.0, ("servant", area): 1.0}, {"domestic_service_hour": 8.0})
        hired, own, _milled = household_work_year.cohort_plan(setup(), rec, view, worker, offers)
        self.assertLess(hired, 0.01 * households_work.hours_needed(100.0, DATA))
        self.assertAlmostEqual(hired + own, households_work.hours_needed(100.0, DATA))

    def test_a_cohort_hires_when_the_service_costs_less_than_its_hour(self):
        worker, area = cohort("worker"), labour_area("t1")
        rec = record({"t1": {"worker": 1.0}}, cohorts=[worker])
        offers = [LabourOffer("worker", "smith", area, 500.0, 1.0)]
        view = View({("smith", area): 3.0, ("servant", area): 5.0}, {"domestic_service_hour": 2.0})
        hired, _own, _milled = household_work_year.cohort_plan(setup(), rec, view, worker, offers)
        self.assertGreater(hired, 0.99 * households_work.hours_needed(100.0, DATA))

    def test_a_servant_nobody_has_paid_is_priced_at_the_unskilled_wage_not_the_workers_reservation(self):
        worker, area = cohort("worker"), labour_area("t1")
        rec = record({"t1": {"worker": 1.0}}, cohorts=[worker])
        offers = [LabourOffer("worker", "labourer", area, 500.0, 0.5)]
        _value, _needed, price, _milled = household_work_year.work_terms(setup(), rec, View({("labourer", area): 2.0}), worker, offers)
        self.assertAlmostEqual(price, 2.0)

    def test_a_landless_cohort_does_no_cooking_of_its_own(self):
        landless, area = cohort("landless"), labour_area("t1")
        rec = record({"t1": {}}, cohorts=[landless])
        offers = [LabourOffer("landless", "labourer", area, 500.0, 0.5)]
        _hired, own, _milled = household_work_year.cohort_plan(setup(), rec, View({("labourer", area): 0.1, ("servant", area): 1.0}),
                                                       landless, offers)
        self.assertAlmostEqual(own, households_work.hours_needed(100.0, DATA, has_hearth=False))

    def test_own_household_work_hours_reduce_the_hours_offered(self):
        poor, area = cohort("poor"), labour_area("t1")
        offers = [LabourOffer("poor", "labourer", area, 500.0, 0.5)]
        rec = record({"t1": {"poor": 1.0}}, cohorts=[poor])
        own = household_work_year.decide(setup(), rec, View({("labourer", area): 0.8, ("servant", area): 1.0}), offers)
        self.assertGreater(own["poor"], 0.0)

    def test_hired_hours_become_the_cohorts_floor_of_the_need(self):
        rich, area = cohort("rich"), labour_area("t1")
        rec = record({"t1": {"rich": 1.0}}, cohorts=[rich])
        offers = [LabourOffer("rich", "smith", area, 500.0, 1.0)]
        household_work_year.decide(setup(), rec, View({("smith", area): 3.0, ("servant", area): 1.0}), offers)
        hired_cohort = rec.cohorts["rich"]
        self.assertGreater(hired_cohort.hired_work_per_person, 0.99 * households_work.hours_per_person_per_year(DATA))
        spec = next(need for need in household_work_year.cohort_basket(setup(), rec, hired_cohort).needs
                    if need.need_id == "household_work")
        self.assertAlmostEqual(spec.subsistence_per_person, hired_cohort.hired_work_per_person)


class FullCostOfServiceTests(unittest.TestCase):
    """A household hires only where the hours it frees pay the service's full cost: the price, the hours spent directing
    the servant, and the freed hours finding a buyer."""

    def _hired(self, wage, price, supervision=0.0, sold=None):
        worker, area = cohort("worker"), labour_area("t1")
        rec = record({"t1": {"worker": 1.0}}, cohorts=[worker])
        if sold is not None:
            key = market_key("smith", area)
            rec.labour.sold_share_expected[key] = sold
        plan = setup()
        plan.household_work = dict(DATA, supervision_hours_per_hired_hour=supervision)
        offers = [LabourOffer("worker", "smith", area, 500.0, 0.1)]
        view = View({("smith", area): wage, ("servant", area): 1.0}, {"domestic_service_hour": price})
        hired, _own, _milled = household_work_year.cohort_plan(plan, rec, view, worker, offers)
        return hired

    def test_a_household_whose_freed_hours_would_go_unsold_does_not_hire(self):
        self.assertGreater(self._hired(3.0, 2.0), 0.99 * households_work.hours_needed(100.0, DATA))
        self.assertLess(self._hired(3.0, 2.0, sold=0.2), 0.01 * households_work.hours_needed(100.0, DATA))

    def test_a_household_whose_hour_is_worth_well_above_the_full_cost_hires(self):
        self.assertGreater(self._hired(10.0, 2.0, supervision=0.1, sold=0.9), 0.99 * households_work.hours_needed(100.0, DATA))

    def test_a_household_whose_hour_barely_beats_the_price_does_not_hire_once_directing_costs_hours(self):
        self.assertGreater(self._hired(2.1, 2.0), 0.5 * households_work.hours_needed(100.0, DATA))
        self.assertLess(self._hired(2.1, 2.0, supervision=0.2), 0.5 * households_work.hours_needed(100.0, DATA))

    def test_hiring_falls_as_the_full_cost_rises(self):
        wages = [1.5 + 0.5 * step for step in range(10)]

        def hirers(price, supervision):
            return sum(1 for wage in wages if self._hired(wage, price, supervision) > 0.5 * households_work.hours_needed(100.0, DATA))

        by_price = [hirers(price, 0.1) for price in (1.0, 2.0, 3.0, 4.0)]
        self.assertEqual(by_price, sorted(by_price, reverse=True))
        self.assertGreater(by_price[0], by_price[-1])
        by_supervision = [hirers(2.0, share) for share in (0.0, 0.2, 0.4, 0.6)]
        self.assertEqual(by_supervision, sorted(by_supervision, reverse=True))
        self.assertGreater(by_supervision[0], by_supervision[-1])

    def test_the_sold_share_counts_hours_with_a_buyer(self):
        self.assertAlmostEqual(households_work.sold_share(25.0, 75.0), 0.25)
        self.assertEqual(households_work.sold_share(0.0, 0.0), 1.0)


class ExpectedSoldShareTests(unittest.TestCase):
    def test_the_share_held_in_the_record_wins_over_the_openings_expectation(self):
        rec = types.SimpleNamespace(labour=types.SimpleNamespace(sold_share_expected={market_key("smith", "a1"): 0.3}))
        self.assertAlmostEqual(household_work_year.sold_share_at(rec, "smith", "a1", 0.9), 0.3)

    def test_a_market_with_no_year_behind_it_takes_the_openings_expectation(self):
        rec = types.SimpleNamespace(labour=types.SimpleNamespace(sold_share_expected={}))
        self.assertAlmostEqual(household_work_year.sold_share_at(rec, "smith", "a1", 0.6), 0.6)

    def test_a_record_lacks_history_for_a_market_it_holds_no_share_for(self):
        rec = types.SimpleNamespace(labour=types.SimpleNamespace(sold_share_expected={market_key("smith", "a1"): 0.3}))
        held = LabourOffer("w", "smith", "a1", 10.0, 1.0)
        new = LabourOffer("w", "smith", "a2", 10.0, 1.0)
        self.assertFalse(household_work_year.lacks_history(rec, [held]))
        self.assertTrue(household_work_year.lacks_history(rec, [held, new]))


class HearthTests(unittest.TestCase):
    def _foods(self, basket):
        priced = need_basket.need_prices(basket, {"wheat_kg": 1.0, "cooked_meal_kg": 1.0, "domestic_service_hour": 1.0}.get)
        return {good for need in priced if need.spec.need_id == "food" for good, _price, _effect, _share in need.goods}

    def test_a_landless_cohorts_food_is_served_by_cooked_food(self):
        landless = cohort("landless")
        rec = record({"t1": {}}, cohorts=[landless])
        self.assertFalse(household_work_year.has_hearth(rec, landless))
        self.assertEqual(self._foods(household_work_year.cohort_basket(setup(), rec, landless)), {"cooked_meal_kg"})

    def test_a_cohort_with_land_or_a_tenancy_has_a_hearth_and_keeps_its_basket(self):
        owner, tenant = cohort("owner"), cohort("tenant")
        rec = record({"t1": {"owner": 0.5}}, {"t1": [{"tenant": "tenant", "lessor": "owner", "share": 0.2}]}, [owner, tenant])
        self.assertTrue(household_work_year.has_hearth(rec, owner))
        self.assertTrue(household_work_year.has_hearth(rec, tenant))
        self.assertIn("wheat_kg", self._foods(household_work_year.cohort_basket(setup(), rec, owner)))

    def test_a_cohort_on_a_plot_in_a_tile_where_most_people_have_none_has_no_hearth(self):
        # the tile is urban: 300 of its 400 people work no land (household_urban.is_urban)
        owner, townsfolk = cohort("owner", people=100.0), cohort("townsfolk", people=300.0)
        rec = record({"t1": {"owner": 0.5}}, cohorts=[owner, townsfolk])
        self.assertFalse(household_work_year.has_hearth(rec, owner))
        self.assertEqual(household_work_year.hearths_of(rec, ["t1", "t1"], ["owner", "townsfolk"]), [False, False])

    def test_the_same_cohort_in_a_tile_where_most_people_hold_land_has_a_hearth(self):
        owner, other = cohort("owner", people=300.0), cohort("other", people=100.0)
        rec = record({"t1": {"owner": 0.5}}, cohorts=[owner, other])
        self.assertTrue(household_work_year.has_hearth(rec, owner))
        self.assertEqual(household_work_year.hearths_of(rec, ["t1", "t1"], ["owner", "other"]), [True, False])


class CookingFuelTests(unittest.TestCase):
    def _warmth_floor(self, basket):
        return next(need.subsistence_per_person for need in basket.needs if need.need_id == "warmth")

    def test_a_cohort_with_a_hearth_burns_cooking_fuel_on_top_of_the_warmth_floor(self):
        owner = cohort("owner")
        rec = record({"t1": {"owner": 1.0}}, cohorts=[owner])
        floor = self._warmth_floor(household_work_year.cohort_basket(setup(), rec, owner))
        self.assertAlmostEqual(floor, 300.0 + households_work.cooking_fuel_per_person_per_year(DATA, True))
        self.assertGreater(floor, 300.0)

    def test_a_cohort_with_no_hearth_burns_none(self):
        landless = cohort("landless")
        rec = record({"t1": {}}, cohorts=[landless])
        self.assertAlmostEqual(self._warmth_floor(household_work_year.cohort_basket(setup(), rec, landless)), 300.0)


class SubsistenceCostTests(unittest.TestCase):
    def test_the_wage_floor_counts_the_cooking_fuel_of_a_cohort_with_a_hearth(self):
        from sim.economy import year_labour
        from sim.world.need_basket import subsistence_cost_per_person
        owner = cohort("owner", "t1")
        rec = record({"t1": {"owner": 1.0}}, cohorts=[owner])
        view = View({}, {"wheat_kg": 1.0, "cooked_meal_kg": 1.0, "domestic_service_hour": 1.0, "wood_kg": 2.0})
        plain = subsistence_cost_per_person(need_basket.need_prices(setup().basket_for("t1"), view.price_of_good))
        fuel = households_work.cooking_fuel_per_person_per_year(DATA, True)
        cost = year_labour.subsistence_cost_by_tile(setup(), rec, view)["t1"]
        self.assertAlmostEqual(cost - plain, fuel * 2.0 / 15.0)    # wood serves warmth at 15 per kg


if __name__ == "__main__":
    unittest.main()
