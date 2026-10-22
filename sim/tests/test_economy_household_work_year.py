"""A cohort's household work in a year (Complaint 645): hiring by the worth of its hour, own hours kept out of the
labour offered, and the cooked food of a cohort with no hearth."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import household_work_year, households_work
from sim.economy.households_basket import make_basket
from sim.economy.households_cohort import Cohort
from sim.economy.households_own import withhold_hours
from sim.economy.setup import labour_area
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


class View:
    def __init__(self, wages):
        self.wages = wages

    def wage(self, trade, area):
        return self.wages.get((trade, area))


def cohort(name, tile="t1", people=100.0):
    return Cohort(agent_id=name, tile=tile, income_class=0, people=people, working_people=people / 2,
                  ownership_share=0.0)


def setup():
    return types.SimpleNamespace(
        household_work=DATA, working_hours_per_year=1000.0, servant_trade="servant", hunger_need="food", fuel_need="warmth",
        ready_to_eat=households_work.ready_to_eat_goods(NEED_DATA), milled_as={},
        basket_for=lambda tile: make_basket(NEED_DATA, {}))


def record(titles=None, tenancies=None, cohorts=()):
    return types.SimpleNamespace(titles=titles or {}, tenancies=tenancies or {},
                                 cohorts={each.agent_id: each for each in cohorts})


class SplitTests(unittest.TestCase):
    def test_a_cohort_whose_hour_is_worth_more_than_the_servants_price_hires(self):
        rich, area = cohort("rich"), labour_area("t1")
        rec = record({"t1": {"rich": 1.0}}, cohorts=[rich])
        offers = [LabourOffer("rich", "smith", area, 500.0, 1.0)]
        view = View({("smith", area): 3.0, ("servant", area): 1.0})
        hired, own = household_work_year.cohort_split(setup(), rec, view, rich, offers, 0.0)
        self.assertAlmostEqual(hired, households_work.hours_needed(100.0, DATA))
        self.assertEqual(own, 0.0)

    def test_a_cohort_whose_hour_is_worth_less_does_it_all_itself(self):
        poor, area = cohort("poor"), labour_area("t1")
        rec = record({"t1": {"poor": 1.0}}, cohorts=[poor])
        offers = [LabourOffer("poor", "labourer", area, 500.0, 0.5)]
        view = View({("labourer", area): 0.8, ("servant", area): 1.0})
        hired, own = household_work_year.cohort_split(setup(), rec, view, poor, offers, 0.0)
        self.assertEqual(hired, 0.0)
        self.assertAlmostEqual(own, households_work.hours_needed(100.0, DATA))

    def test_the_servants_price_falls_back_when_no_servant_has_been_paid(self):
        worker, area = cohort("worker"), labour_area("t1")
        rec = record({"t1": {"worker": 1.0}}, cohorts=[worker])
        offers = [LabourOffer("worker", "labourer", area, 500.0, 0.5)]
        hired, _own = household_work_year.cohort_split(setup(), rec, View({("labourer", area): 2.0}), worker, offers, 1.0)
        self.assertGreater(hired, 0.0)

    def test_a_landless_cohort_does_no_cooking_of_its_own(self):
        landless, area = cohort("landless"), labour_area("t1")
        rec = record({"t1": {}}, cohorts=[landless])
        offers = [LabourOffer("landless", "labourer", area, 500.0, 0.5)]
        _hired, own = household_work_year.cohort_split(setup(), rec, View({("labourer", area): 0.1, ("servant", area): 1.0}),
                                                       landless, offers, 0.0)
        self.assertAlmostEqual(own, households_work.hours_needed(100.0, DATA, has_hearth=False))

    def test_own_household_work_hours_reduce_the_hours_offered(self):
        poor, area = cohort("poor"), labour_area("t1")
        offers = [LabourOffer("poor", "labourer", area, 500.0, 0.5)]
        rec = record({"t1": {"poor": 1.0}}, cohorts=[poor])
        own = household_work_year.decide(setup(), rec, View({("labourer", area): 0.8, ("servant", area): 1.0}), offers, {})
        cut, kept = withhold_hours(offers, own)
        self.assertGreater(kept["poor"], 0.0)
        self.assertAlmostEqual(kept["poor"], min(own["poor"], 500.0))
        self.assertAlmostEqual(sum(offer.hours for offer in cut), 500.0 - kept["poor"])

    def test_hired_hours_become_the_cohorts_floor_of_the_need(self):
        rich, area = cohort("rich"), labour_area("t1")
        rec = record({"t1": {"rich": 1.0}}, cohorts=[rich])
        offers = [LabourOffer("rich", "smith", area, 500.0, 1.0)]
        household_work_year.decide(setup(), rec, View({("smith", area): 3.0, ("servant", area): 1.0}), offers, {})
        hired_cohort = rec.cohorts["rich"]
        self.assertAlmostEqual(hired_cohort.hired_work_per_person, households_work.hours_per_person_per_year(DATA))
        spec = next(need for need in household_work_year.cohort_basket(setup(), rec, hired_cohort).needs
                    if need.need_id == "household_work")
        self.assertAlmostEqual(spec.subsistence_per_person, hired_cohort.hired_work_per_person)


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


if __name__ == "__main__":
    unittest.main()
