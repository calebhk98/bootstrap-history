"""Which staff a state's reach reads: the guards' reach goes to theft, the inspectors' to the mine ceiling, the foresters' to the
forest ceiling, each by its own line's unfunded share and no other (Complaint 660). Each method is called on a stand-in `self`
that carries only the reach it should read, so a read of any other reach fails the test."""

QUICK_TOPIC = True

from types import SimpleNamespace
import unittest
from unittest import mock

from sim.engine.agents_port_budget import BudgetView
from sim.engine.economy_mining import MiningMixin
from sim.engine.legitimacy import LegitimacyMixin
from sim.engine.bridge_living_stock import partner_catch_chance
from sim.engine.theft_charge import TheftChargeMixin
from sim.engine.theft_exposure import visibility_factor
from sim.world import stock_dynamics


def reach_stand_in(unfunded, shares, year=100):
    """A game whose government record holds `unfunded` by line, and whose SimWorld answers `shares` by share name."""
    calls = []
    world_shares = {name: (lambda value=value, name=name: calls.append(name) or value) for name, value in shares.items()}
    world = SimpleNamespace(government=lambda: SimpleNamespace(record=SimpleNamespace(unfunded=unfunded)), **world_shares)
    game = SimpleNamespace(year=year, household=SimpleNamespace(done_version=1, operating_version=1),
                           population=SimpleNamespace(total=1000.0))
    return game, world, calls


class StaffReach(unittest.TestCase):
    def reach(self, game, world, line, share):
        with mock.patch("sim.engine.agents_port.SimWorld", lambda sim: world):
            return LegitimacyMixin._staff_reach(game, line, share)

    def test_the_line_reads_its_own_share_from_the_world(self):
        game, world, calls = reach_stand_in({}, {"order_share": 0.6, "inspection_share": 0.2})
        self.assertEqual(self.reach(game, world, "guards", "order_share"), 0.6)
        self.assertEqual(self.reach(game, world, "inspectors", "inspection_share"), 0.2)
        self.assertEqual(calls, ["order_share", "inspection_share"])

    def test_a_repeat_with_nothing_changed_is_remembered(self):
        game, world, calls = reach_stand_in({"guards": 0.1}, {"order_share": 0.6})
        self.reach(game, world, "guards", "order_share")
        self.reach(game, world, "guards", "order_share")
        self.assertEqual(calls, ["order_share"])

    def test_more_of_the_lines_pay_left_unpaid_is_read_again(self):
        game, world, calls = reach_stand_in({"guards": 0.1}, {"order_share": 0.6})
        self.reach(game, world, "guards", "order_share")
        world.government().record.unfunded["guards"] = 0.5
        self.reach(game, world, "guards", "order_share")
        self.assertEqual(calls, ["order_share", "order_share"])

    def test_another_lines_unpaid_pay_does_not_make_it_read_again(self):
        game, world, calls = reach_stand_in({"guards": 0.1}, {"order_share": 0.6})
        record = world.government().record
        self.reach(game, world, "guards", "order_share")
        record.unfunded["inspectors"] = 0.9
        self.reach(game, world, "guards", "order_share")
        self.assertEqual(calls, ["order_share"])

    def test_each_reach_names_its_line_and_share(self):
        asked = []
        stand_in = SimpleNamespace(_staff_reach=lambda line, share: asked.append((line, share)))
        LegitimacyMixin.order_reach(stand_in)
        LegitimacyMixin.inspection_reach(stand_in)
        LegitimacyMixin.forest_reach(stand_in)
        self.assertEqual(asked, [("guards", "order_share"), ("inspectors", "inspection_share"), ("foresters", "forest_share")])


class StateReach(unittest.TestCase):
    def test_the_home_reach_is_the_share_the_paid_officials_collect_and_is_remembered(self):
        game, world, calls = reach_stand_in({"administration": 0.0}, {"collectible_share": 0.8})
        with mock.patch("sim.engine.agents_port.SimWorld", lambda sim: world):
            first = LegitimacyMixin.state_reach(game)
            second = LegitimacyMixin.state_reach(game)
        self.assertEqual((first, second, calls), (0.8, 0.8, ["collectible_share"]))

    def test_officials_left_unpaid_make_the_reach_be_read_again(self):
        game, world, calls = reach_stand_in({"administration": 0.0}, {"collectible_share": 0.8})
        with mock.patch("sim.engine.agents_port.SimWorld", lambda sim: world):
            LegitimacyMixin.state_reach(game)
            world.government().record.unfunded["administration"] = 100.0
            LegitimacyMixin.state_reach(game)
        self.assertEqual(calls, ["collectible_share", "collectible_share"])

    def test_the_agents_view_of_the_state_reads_the_games_authority(self):
        stand_in = SimpleNamespace(_sim=SimpleNamespace(state_authority=lambda: 0.42))
        self.assertEqual(BudgetView.state_reach(stand_in), 0.42)

    def test_a_partners_chance_to_catch_is_its_own_governments_reach_against_how_visible_the_bite_is(self):
        asked = []
        world = SimpleNamespace(state_reach=lambda: 1)
        actors = SimpleNamespace(world_for=lambda government, home: asked.append((government, home)) or world)
        stand_in = SimpleNamespace(actors=actors, partner_government=lambda civilization_id: "government:" + civilization_id)
        with mock.patch("sim.engine.agents_port_cast.seed_opening_cast"), \
                mock.patch("sim.engine.agents_port.SimWorld", lambda sim: "home world"):
            chance = partner_catch_chance(stand_in, "han_china_100ad", 0.5)
        self.assertEqual((chance, asked), (stock_dynamics.catch_chance(1.0, visibility_factor(0.5)),
                                           [("government:han_china_100ad", "home world")]))


class CeilingsReadOnlyTheirOwnStaff(unittest.TestCase):
    def mining_stand_in(self, **reaches):
        return SimpleNamespace(
            effect_best=lambda effect: None, MINE_CEILING_BASE_STRANGER=1000.0, MINE_CEILING_STATE_SCALE_STRANGER=5000.0,
            REVENUE_SCALE_DENARII=1.0e6, REVENUE_SCALE_CAP_MULTIPLE=4.0, revenue=lambda: 0.0,
            geography=SimpleNamespace(mineral_scale=lambda material: 1.0),
            FOREST_HA_PER_MILLION_KM2_BASE=100.0, FOREST_HA_PER_MILLION_KM2_PER_SC=400.0,
            home_land_area_km2=lambda: 1.0e6, **reaches)

    def test_the_mine_ceiling_rises_with_the_inspectors_reach_alone(self):
        low = MiningMixin.mine_land_ceiling(self.mining_stand_in(inspection_reach=lambda: 0.2), "iron")
        high = MiningMixin.mine_land_ceiling(self.mining_stand_in(inspection_reach=lambda: 0.8), "iron")
        self.assertEqual((low, high), (2000.0, 5000.0))

    def test_the_forest_ceiling_rises_with_the_foresters_reach_alone(self):
        low = MiningMixin.forest_land_ceiling(self.mining_stand_in(forest_reach=lambda: 0.0))
        high = MiningMixin.forest_land_ceiling(self.mining_stand_in(forest_reach=lambda: 0.5))
        self.assertEqual((low, high), (100.0, 300.0))


class PlunderReadsTheGuards(unittest.TestCase):
    def plunder(self, order_holds):
        taken = []
        household = SimpleNamespace(protection=0.3)
        stand_in = SimpleNamespace(
            state=SimpleNamespace(household=household), order_reach=lambda: 0.7, founder_exposure=lambda: "exposure",
            founder_visible_scale=lambda: 2.0,
            steal_from=lambda *arguments: taken.append(arguments) or 5.0)
        result = TheftChargeMixin.plunder_founder(stand_in, 0.2, "bandits", order_holds)
        return result, taken[0]

    def test_where_order_holds_the_guards_reach_and_the_households_protection_stand_against_the_thief(self):
        result, arguments = self.plunder(True)
        self.assertEqual(result, 5.0)
        self.assertEqual(arguments[5:8], (0.7, 0.3, "bandits"))

    def test_where_order_has_failed_neither_stands_against_the_thief(self):
        _result, arguments = self.plunder(False)
        self.assertEqual(arguments[5:8], (0.0, 0.0, "bandits"))


if __name__ == "__main__":
    unittest.main()
