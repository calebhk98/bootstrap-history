"""Trade demand in the need shares (Complaint 434): a land carrier trade, water delivered by pipe, shaft work
for millwrights, the generic weight of goods no need names, and spending split inside a need by cost.
Pure functions on the recipe catalogue and small synthetic catalogues; no game is built."""
import json
import os
import unittest
from unittest import mock

from sim.engine import validate_production
from sim.engine.catalog import load_production_catalog
from sim.engine.solve_prices_core import techniques_available_to
from sim.labour import workforce_carriage, workforce_spinup
from sim.world import need_demand

QUICK_TOPIC = True

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PRODUCTION = load_production_catalog(_ROOT)


def _json(*parts):
    with open(os.path.join(_ROOT, *parts), encoding="utf-8") as handle:
        return json.load(handle)


def _starting_techs(civ_id):
    return set(_json("data", "civilizations", civ_id + ".json")["starting_techs"])


def _shares(reached, production=None, carriage=None):
    return workforce_spinup.need_shares_by_trade(
        production or _PRODUCTION, set(reached), techniques_available_to,
        carriage if carriage is not None else workforce_carriage.carriage_for(reached))


def _recipe(output, labour, inputs=None):
    return {"outputs": {output: 1.0}, "inputs": dict(inputs or {}), "labour_hours": dict(labour),
            "requires_node": None, "basis": "one", "yield_basis": "test", "conf": "C"}


def _zz_carriage(span=None):
    return workforce_carriage.Carriage((workforce_carriage.CarriageMode("zz_carrier", 1.0, 1.0),), span)


def _synthetic_shares(production, needs, carriage=None):
    with mock.patch.object(workforce_spinup, "_needs", return_value=needs):
        return workforce_spinup.need_shares_by_trade(production, set(), techniques_available_to, carriage)


class LandCarriersTests(unittest.TestCase):

    def test_land_modes_that_use_draught_or_pack_animals_name_a_carter(self):
        modes = {mode["id"]: mode for mode in _json("data", "world", "geography", "route_modes", "modes.json")["entries"]}
        trades = _json("data", "world", "trades.json")["trades"]
        self.assertIn("carter", trades)
        for mode_id in ("pack", "cart", "road"):
            self.assertEqual(modes[mode_id]["crew_trade"], "carter", mode_id)
        for mode in modes.values():
            self.assertIn(mode["crew_trade"], trades, mode["id"])

    def test_rome_carries_by_cart_so_carters_take_a_share_of_the_need(self):
        reached = _starting_techs("rome_100ad")
        self.assertIn("carter", workforce_carriage.carriage_for(reached).trades())
        self.assertGreater(_shares(reached).get("carter", 0.0), 0.0)

    def test_carters_are_drawn_from_the_same_pool_as_sailors(self):
        trades = _json("data", "world", "trades.json")["trades"]
        self.assertEqual(trades["carter"]["family"], trades["sailor"]["family"])
        self.assertGreater(trades["carter"]["training_years"], trades["labourer"]["training_years"])


class WaterNeedTests(unittest.TestCase):

    def test_water_is_a_household_need_with_a_stated_floor_and_ways_of_meeting_it(self):
        needs = _json("data", "world", "needs.json")
        water = needs["needs"]["water"]
        self.assertGreater(water["subsistence_per_capita_per_year"], 0.0)
        self.assertIn("Howard", water["subsistence_basis"])
        served_by = {good for good, attributes in needs["goods"].items() if "water" in attributes["satisfies"]}
        self.assertTrue({"water_kg", "water_piped_kg", "water_well_kg"} <= served_by)

    def test_a_civilisation_with_lead_plumbing_needs_plumbers_and_one_without_does_not(self):
        self.assertGreater(_shares(_starting_techs("rome_100ad")).get("plumber", 0.0), 0.0)
        self.assertEqual(_shares(_starting_techs("mexica_1500")).get("plumber", 0.0), 0.0)

    def test_piped_delivery_is_laid_in_lead_and_plumber_hours(self):
        piped = _PRODUCTION["water_piped_kg"]
        self.assertGreater(piped["labour_hours"]["plumber"], 0.0)
        capital = piped["capital"][0]
        self.assertIn("lead_kg", capital["build_materials"])
        self.assertGreater(capital["build_labour_hours"]["plumber"], 0.0)

    def test_water_drawn_at_the_point_of_use_is_not_hauled_a_mean_distance(self):
        for good in ("water_kg", "water_piped_kg", "water_well_kg"):
            self.assertEqual(_PRODUCTION[good]["carriage_km"], 0.0, good)

    def test_a_recipe_hauled_as_far_as_its_value_pays_for_costs_more_carriage_than_one_not_hauled(self):
        needs = {"needs": {"food": {"surplus_budget_share": 1.0}},
                 "goods": {"zz_food": {"satisfies": {"food": 1.0}}}}
        hauled = {"zz_food": _recipe("zz_food", {"zz_worker": 1.0})}
        at_hand = {"zz_food": dict(_recipe("zz_food", {"zz_worker": 1.0}), carriage_km=0.0)}
        with mock.patch.object(workforce_spinup.demand, "mass_in_kg_or_none", return_value=1000.0):
            carried = _synthetic_shares(hauled, needs, _zz_carriage())
            not_carried = _synthetic_shares(at_hand, needs, _zz_carriage())
        self.assertGreater(carried.get("zz_carrier", 0.0), 0.0)
        self.assertEqual(not_carried.get("zz_carrier", 0.0), 0.0)


class HaulFollowsValueTests(unittest.TestCase):

    def test_a_dearer_tonne_is_carried_farther_and_dearer_carriage_shortens_the_haul(self):
        carriage = _zz_carriage()
        mode = carriage.modes[0]
        self.assertGreater(carriage.haul_km(mode, 200.0), carriage.haul_km(mode, 20.0))
        dear = workforce_carriage.CarriageMode("zz_carrier", 2.0, 2.0)
        self.assertLess(carriage.haul_km(dear, 20.0), carriage.haul_km(mode, 20.0))

    def test_no_haul_exceeds_the_span_between_the_realms_tiles(self):
        capped = _zz_carriage(span=3.0)
        self.assertAlmostEqual(capped.haul_km(capped.modes[0], 1.0e9), 3.0, places=9)
        self.assertLess(capped.haul_km(capped.modes[0], 1.0), 3.0)

    def test_the_realm_span_is_the_mean_distance_between_its_tiles(self):
        from sim.geography import api as geography
        ids = geography.tiles_held(_json("data", "civilizations", "rome_100ad.json"))
        span = geography.realm_span_km(ids)
        self.assertGreater(span, 100.0)
        self.assertIsNone(geography.realm_span_km(ids[:1]))

    def test_carriage_rates_cost_at_least_their_crew_hours(self):
        from sim.geography import api as geography
        for mode_id, rate in geography.carriage_rates(["cart", "sail", "foot"]).items():
            self.assertGreaterEqual(rate["cost_hours_per_tonne_km"], rate["crew_hours_per_tonne_km"], mode_id)

    def test_carters_are_a_minor_share_of_romes_need_not_a_quarter(self):
        reached = _starting_techs("rome_100ad")
        homes = _json("data", "civilizations", "rome_100ad.json")
        from sim.geography import api as geography
        carriage = workforce_carriage.carriage_for(reached, geography.tiles_held(homes))
        self.assertLess(_shares(reached, carriage=carriage)["carter"], 0.1)


class CarriageDistanceDataTests(unittest.TestCase):

    def test_the_validator_rejects_a_bad_carriage_distance(self):
        self.assertEqual(validate_production.check_carriage_km("water_kg", {"carriage_km": 0.0}), [])
        self.assertEqual(validate_production.check_carriage_km("water_kg", {}), [])
        for bad in (-1, "near", True, float("inf")):
            self.assertTrue(validate_production.check_carriage_km("water_kg", {"carriage_km": bad}), bad)


class MillwrightTests(unittest.TestCase):

    def test_a_water_wheel_charges_millwright_hours_to_build_and_to_run(self):
        self.assertGreater(_PRODUCTION["waterwheel_unit"]["labour_hours"]["millwright"], 0.0)
        self.assertGreater(_PRODUCTION["mechanical_mj_waterwheel"]["labour_hours"]["millwright"], 0.0)

    def test_millwright_need_follows_the_shaft_work_recipes_draw(self):
        # The wheel is the only supplier of shaft work here; the millwrights are needed exactly as far as a
        # good people want draws that work, and not at all when nothing does.
        wheel = {key: dict(_PRODUCTION[key], requires_node=None) for key in ("mechanical_mj_waterwheel", "waterwheel_unit")}
        needs = {"needs": {"food": {"surplus_budget_share": 1.0}},
                 "goods": {"zz_flour": {"satisfies": {"food": 1.0}}}}
        milled = dict(wheel, zz_flour=dict(_recipe("zz_flour", {"zz_baker": 1.0}), mechanical_mj=100.0))
        unmilled = dict(wheel, zz_flour=_recipe("zz_flour", {"zz_baker": 1.0}))
        self.assertGreater(_synthetic_shares(milled, needs).get("millwright", 0.0), 0.0)
        self.assertEqual(_synthetic_shares(unmilled, needs).get("millwright", 0.0), 0.0)

    def test_no_recipe_of_rome_draws_shaft_work_so_it_needs_no_millwrights(self):
        self.assertEqual(_shares(_starting_techs("rome_100ad")).get("millwright", 0.0), 0.0)


class GenericWeightTests(unittest.TestCase):

    _NEEDS = {"needs": {"food": {"surplus_budget_share": 1.0}},
              "goods": {"zz_grain": {"satisfies": {"food": 1.0}}}}

    def _catalogue(self):
        return {"zz_grain": _recipe("zz_grain", {"labourer": 1.0, "zz_baker": 1.0}),
                "zz_mica": _recipe("zz_mica", {"zz_miner": 5.0})}

    def test_a_mineral_no_need_names_and_no_recipe_uses_gets_no_demand(self):
        shares = _synthetic_shares(self._catalogue(), self._NEEDS)
        self.assertEqual(set(shares), {"zz_baker"})

    def test_a_recipe_that_uses_the_mineral_makes_its_miners_needed(self):
        catalogue = self._catalogue()
        catalogue["zz_grain"]["inputs"] = {"zz_mica": 0.5}
        shares = _synthetic_shares(catalogue, self._NEEDS)
        self.assertGreater(shares["zz_miner"], 0.0)

    def test_real_mining_no_longer_takes_half_of_rome_s_need(self):
        self.assertLess(_shares(_starting_techs("rome_100ad")).get("miner", 0.0), 0.4)

    def test_every_trade_in_the_shares_works_a_recipe_the_society_can_run(self):
        reached = _starting_techs("rome_100ad")
        available, _unreached, _unclassified = techniques_available_to(_PRODUCTION, reached)
        trades = set()
        for entry in available.values():
            trades.update(entry.get("labour_hours") or {})
            for capital in entry.get("capital") or ():
                trades.update(capital.get("build_labour_hours") or {})
        trades.update(workforce_carriage.carriage_for(reached).trades())
        self.assertLessEqual(set(_shares(reached)), trades)


class SpendingSplitTests(unittest.TestCase):

    _NEEDS = {"needs": {"food": {"surplus_budget_share": 1.0}},
              "goods": {"zz_cheap": {"satisfies": {"food": 1.0}}, "zz_dear": {"satisfies": {"food": 1.0}}}}

    def test_a_dearer_good_takes_a_smaller_share_of_the_need_s_spending(self):
        catalogue = {"zz_cheap": _recipe("zz_cheap", {"zz_cheap_trade": 1.0}),
                     "zz_dear": _recipe("zz_dear", {"zz_dear_trade": 2.0})}
        shares = _synthetic_shares(catalogue, self._NEEDS)
        self.assertGreater(shares["zz_cheap_trade"], shares["zz_dear_trade"])
        self.assertAlmostEqual(shares["zz_cheap_trade"], 2.0 / 3.0, places=9)

    def test_a_good_twice_as_effective_at_twice_the_cost_takes_an_equal_share(self):
        catalogue = {"zz_cheap": _recipe("zz_cheap", {"zz_cheap_trade": 1.0}),
                     "zz_dear": _recipe("zz_dear", {"zz_dear_trade": 2.0})}
        needs = {"needs": self._NEEDS["needs"],
                 "goods": {"zz_cheap": {"satisfies": {"food": 1.0}}, "zz_dear": {"satisfies": {"food": 2.0}}}}
        shares = _synthetic_shares(catalogue, needs)
        self.assertAlmostEqual(shares["zz_cheap_trade"], 0.5, places=9)

    def test_budget_weights_without_costs_stay_an_equal_split(self):
        weights = need_demand.budget_weights_by_good(self._NEEDS, {}, {"zz_cheap", "zz_dear"})
        self.assertAlmostEqual(weights["zz_cheap"], weights["zz_dear"], places=12)


if __name__ == "__main__":
    unittest.main()
