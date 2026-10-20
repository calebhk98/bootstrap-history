"""A household's own plot: hours it keeps back from the labour market to grow what it could not get."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy.households_cohort import Cohort
from sim.economy import households_own, titles_worked
from sim.economy.households_own import hours_for_own_plan, next_own_plan, withhold_hours
from sim.economy.types import LabourOffer, Recipe

OPTIONS = {"food": [(2.0, "grow_grain", "grain", 1.0)]}     # two hours a need unit at fertility one


def cohort(plan=None):
    return Cohort("household:t:0", "t", 0, 100.0, 50.0, 0.3, own_plan_by_need=dict(plan or {}))


class PlotHectaresTests(unittest.TestCase):
    RECIPES = {"grow_grain": Recipe("grow_grain", {"grain": 10.0}, {}, {"hand": 4.0})}
    LAND = {"grow_grain": 2.0}

    def test_hectares_follow_the_hours_the_plan_needs(self):
        # ten need units at two hours each is twenty hours: five runs of four hours, two hectares a run
        self.assertAlmostEqual(households_own.plot_hectares({"food": 10.0}, OPTIONS, self.RECIPES, self.LAND, 1.0), 10.0)

    def test_poorer_soil_takes_more_land_for_the_same_food(self):
        self.assertAlmostEqual(households_own.plot_hectares({"food": 10.0}, OPTIONS, self.RECIPES, self.LAND, 0.5), 20.0)

    def test_a_need_it_cannot_grow_takes_no_land(self):
        self.assertEqual(households_own.plot_hectares({"tools": 10.0}, OPTIONS, self.RECIPES, self.LAND, 1.0), 0.0)


class OwnPlanTests(unittest.TestCase):
    def test_hours_grow_the_plan_at_this_tiles_fertility(self):
        self.assertAlmostEqual(hours_for_own_plan(cohort({"food": 10.0}), OPTIONS, 0.5), 40.0)

    def test_a_household_with_no_plan_keeps_nothing_back(self):
        self.assertEqual(hours_for_own_plan(cohort(), OPTIONS, 0.5), 0.0)

    def test_a_need_it_cannot_grow_keeps_nothing_back(self):
        self.assertEqual(hours_for_own_plan(cohort({"tools": 10.0}), OPTIONS, 0.5), 0.0)

    def test_the_plan_keeps_what_it_grew_and_adds_this_years_shortfall(self):
        # growing only last year's shortfall would leave it short again the year after
        plan = next_own_plan({"food": 60.0}, {"food": 20.0}, money_left=True)
        self.assertAlmostEqual(plan["food"], 60.0 * (1.0 - households_own.OWN_PLAN_RELEASE_SHARE_PER_YEAR) + 20.0)

    def test_a_household_short_because_it_is_poor_grows_no_plan(self):
        # it spent all it earned: more wage work, not fewer hours sold, is what feeds it
        plan = next_own_plan({}, {"food": 20.0}, money_left=False)
        self.assertEqual(plan, {})

    def test_with_markets_feeding_it_the_plan_fades(self):
        plan = {"food": 60.0}
        for _year in range(60):
            plan = next_own_plan(plan, {}, money_left=True)
        self.assertLess(plan.get("food", 0.0), 1.0)


class WithholdTests(unittest.TestCase):
    def test_offers_shrink_in_proportion_and_the_kept_hours_are_returned(self):
        offers = [LabourOffer("w", "smith", "a", 60.0, 1.0), LabourOffer("w", "miner", "a", 40.0, 1.0)]
        kept_offers, kept = withhold_hours(offers, {"w": 50.0})
        self.assertEqual([offer.hours for offer in kept_offers], [30.0, 20.0])
        self.assertEqual(kept, {"w": 50.0})

    def test_it_cannot_keep_more_than_it_has(self):
        kept_offers, kept = withhold_hours([LabourOffer("w", "smith", "a", 60.0, 1.0)], {"w": 500.0})
        self.assertEqual([offer.hours for offer in kept_offers], [0.0])
        self.assertEqual(kept, {"w": 60.0})


class LandHeldTests(unittest.TestCase):
    """Own-plot growing is limited to land the cohort holds or leases (Complaint 551)."""
    RECIPES = {"grow_grain": Recipe("grow_grain", {"grain": 10.0}, {}, {"hand": 4.0})}
    LAND = {"grow_grain": 2.0}
    BASKET = types.SimpleNamespace(needs=[types.SimpleNamespace(
        need_id="food", subsistence_per_person=1.0, goods=(("grain", 1.0),))])

    def _grow(self, hectares, fertility=1.0):
        # 100 people, 1000 idle hours; the food floor is 100 need units: 200 hours, 100 hectares
        options = households_own.own_production_options(self.RECIPES, self.LAND, self.BASKET)
        return households_own.own_production(cohort(), 1000.0, options, self.RECIPES, fertility, self.BASKET,
                                             self.LAND, hectares)

    def test_a_cohort_holding_no_land_grows_nothing(self):
        moves, grown, units = self._grow(0.0)
        self.assertEqual((moves, grown, units), ([], {}, {}))

    def test_a_cohort_grows_no_more_than_its_hectares_yield(self):
        # ten hectares: five runs of ten units, fifty need units, against a floor of one hundred
        _moves, grown, units = self._grow(10.0)
        self.assertAlmostEqual(units["food"], 50.0)
        self.assertAlmostEqual(grown["grain"], 50.0)

    def test_poorer_soil_yields_less_from_the_same_hectares(self):
        _moves, _grown, units = self._grow(10.0, fertility=0.5)
        self.assertAlmostEqual(units["food"], 25.0)

    def test_land_beyond_the_floor_is_not_farmed(self):
        _moves, _grown, units = self._grow(500.0)
        self.assertAlmostEqual(units["food"], 100.0)

    def test_hours_on_land_follow_hectares_and_run_size(self):
        self.assertAlmostEqual(households_own.hours_on_land(3.0, self.RECIPES["grow_grain"], 2.0), 6.0)
        self.assertEqual(households_own.hours_on_land(0.0, self.RECIPES["grow_grain"], 2.0), 0.0)

    def test_plan_hours_are_capped_by_land_held(self):
        plan = cohort({"food": 10.0})                      # twenty hours of plan
        self.assertAlmostEqual(hours_for_own_plan(plan, OPTIONS, 1.0), 20.0)
        self.assertEqual(hours_for_own_plan(plan, OPTIONS, 1.0, self.RECIPES, self.LAND, 0.0), 0.0)
        self.assertAlmostEqual(hours_for_own_plan(plan, OPTIONS, 1.0, self.RECIPES, self.LAND, 3.0), 6.0)

    def test_allocation_cuts_claims_to_the_tiles_arable_land(self):
        grant = titles_worked.allocate_hectares({"a": 30.0, "b": 10.0}, 20.0)
        self.assertAlmostEqual(sum(grant.values()), 20.0)
        self.assertAlmostEqual(grant["a"], 15.0)
        self.assertEqual(titles_worked.allocate_hectares({"a": 5.0}, 20.0), {"a": 5.0})

    def test_worked_share_is_title_less_let_out_plus_tenancy(self):
        record = types.SimpleNamespace(cohorts={}, titles={"t": {"lord": 0.6, "other": 0.4}},
                                       tenancies={"t": [{"tenant": "serf", "lessor": "lord", "share": 0.25,
                                                         "arrears": 0.0}]})
        self.assertAlmostEqual(titles_worked.worked_share(record, "t", "lord"), 0.35)
        self.assertAlmostEqual(titles_worked.worked_share(record, "t", "serf"), 0.25)
        self.assertEqual(titles_worked.worked_share(record, "t", "stranger"), 0.0)


if __name__ == "__main__":
    unittest.main()
