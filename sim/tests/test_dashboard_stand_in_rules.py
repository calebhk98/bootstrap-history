"""The industrial dashboard's rows on stand-in games: material capacity arithmetic, the power ladder under fog, the
power figures and the short or full `economy` reply."""

QUICK_TOPIC = True

import types
import unittest

from sim.ui.proto import economy

POWER_NODES = {
    "cap_power_muscle": {"mechanics": {"power_tier": {"rank": 0, "label": "muscle", "scale": "muscle"}}},
    "cap_power_electric": {"mechanics": {"power_tier": {"rank": 1, "label": "kW scale", "scale": "workshop"}}},
    "cap_power_grid": {"mechanics": {"power_tier": {"rank": 2, "label": "MW scale", "scale": "grid"}}},
}


def material_game():
    return types.SimpleNamespace(
        annual_material_demand=lambda: {}, _demand_by_supply_tag=lambda demand: {},
        demand_and_own_supply_by_material=lambda by_tag: {"iron": (300.0, 500.0), "copper": (900.0, 100.0)},
        _material_market_tonnes=lambda material: 50.0, material_shortfall_t=lambda material, by_tag: 0.0,
        _own_material_supply=lambda tag: 70.0,
        view=lambda name: {"mine_capacity": lambda: {"coal": 1.0}, "mine_depletion_note": {"coal": None}}[name])


def power_game(visible, built=(), total_kw=0.0, demand_kw=0.0):
    return types.SimpleNamespace(
        installed_generation_kw_by_tier=lambda: {}, is_visible=lambda node_id: node_id in visible,
        has=lambda node_id: node_id in built, binding=None, throttle=1.0,
        generation_breakdown_kw=lambda: {"total_kw": total_kw, "local_kw": total_kw, "grid_kw": 0.0,
                                         "transmission_kw": 0.0, "mechanical_kw": {}},
        _electricity_demand_kw=lambda: demand_kw)


class MaterialCapacityRows(unittest.TestCase):

    def test_surplus_is_capacity_less_demand_and_capacity_is_own_plus_market(self):
        rows = {row["material"]: row for row in economy._material_capacity_rows(material_game())}
        iron = rows["iron"]
        self.assertEqual(iron["capacity_t_per_yr"], 550.0)
        self.assertEqual(iron["surplus_t_per_yr"], iron["capacity_t_per_yr"] - iron["demand_t_per_yr"])

    def test_the_worst_shortfall_comes_first(self):
        rows = economy._material_capacity_rows(material_game())
        self.assertEqual(rows[0]["material"], "copper")
        self.assertLess(rows[0]["surplus_t_per_yr"], 0.0)

    def test_owned_mine_capacity_with_no_demand_still_appears_with_zero_demand(self):
        rows = {row["material"]: row for row in economy._material_capacity_rows(material_game())}
        self.assertEqual(rows["coal"]["demand_t_per_yr"], 0.0)
        self.assertEqual(rows["coal"]["capacity_t_per_yr"], 120.0)


class PowerLadderUnderFog(unittest.TestCase):

    def test_only_visible_rungs_are_named(self):
        tiers, highest = economy._power_tiers(power_game({"cap_power_muscle"}, built={"cap_power_muscle"}), POWER_NODES)
        self.assertEqual([tier["id"] for tier in tiers], ["cap_power_muscle"])
        self.assertEqual(highest, "muscle")

    def test_with_nothing_visible_there_are_no_figures_and_no_waiting_lists(self):
        out = economy._power_status(power_game(set()), POWER_NODES)
        self.assertEqual(out["power_tiers_you_have_discovered"], "none yet")
        for key in ("generation_kw", "demand_kw", "waiting_on_workshop_scale_power", "waiting_on_grid_scale_power"):
            self.assertNotIn(key, out)

    def test_muscle_only_names_no_project_waiting_on_workshop_or_grid_power(self):
        out = economy._power_status(power_game({"cap_power_muscle"}, built={"cap_power_muscle"}), POWER_NODES)
        self.assertNotIn("waiting_on_workshop_scale_power", out)
        self.assertNotIn("waiting_on_grid_scale_power", out)


class PowerFigures(unittest.TestCase):

    def test_generation_demand_and_reserve_margin_are_the_engines_figures(self):
        block = economy._power_generation_block(power_game(set(), total_kw=150.0, demand_kw=100.0))
        self.assertEqual(block["generation_kw"]["total"], 150.0)
        self.assertEqual(block["demand_kw"], 100.0)
        self.assertAlmostEqual(block["reserve_margin"], 0.5)

    def test_no_demand_gives_no_reserve_margin_rather_than_a_ratio(self):
        block = economy._power_generation_block(power_game(set(), total_kw=150.0, demand_kw=0.0))
        self.assertIsNone(block["reserve_margin"])


class EconomyReply(unittest.TestCase):

    def test_economy_without_full_has_no_detail_tables(self):
        game = types.SimpleNamespace(
            year=100, price_index=1.0, wage_index=1.0, living_cost=lambda: 10.0, state=types.SimpleNamespace(),
            labour=types.SimpleNamespace(wage_bill=lambda: 4.0, headcount=lambda: 3.0, household_room=lambda: 2.0),
            literacy=lambda key: 0.1, revenue_sources=lambda: [], material_market_summary=lambda: None)
        game.state.dashboard_history = None
        out = economy._agent_economy(game)
        self.assertNotIn("wages_by_trade", out)
        self.assertNotIn("tracked_material_prices", out)
        self.assertEqual(out["cost_of_living_a_year"], 6.0)


if __name__ == "__main__":
    unittest.main()
