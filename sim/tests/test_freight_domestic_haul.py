"""Complaints/326: rivers from the tiles, a domestic flow ledger, droving of live animals, on built inputs. The haul as a game
prices it (dues, the opposite flow, driven stock) is in test_foreign_freight_wiring_rules."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.geography import api as geography
from sim.geography import droving, flow_ledger, freight_cost, routes_graph
from sim.geography.api import dues_hours_per_tonne


# A tile outside the default civilisation's ground that only carts join to it.
LAND_ONLY_TILE = "chad_08"


def _inputs(mode="drove"):
    return geography.droving_carrier(mode)["inputs"]


class FlowLedger(unittest.TestCase):

    def test_an_empty_ledger_returns_every_carrier_empty(self):
        self.assertEqual(flow_ledger.overall_imbalance({}), 1.0)

    def test_opposite_flows_fill_the_return(self):
        ledger = {}
        flow_ledger.record_flow(ledger, "a", "b", 100.0)
        self.assertEqual(flow_ledger.pair_imbalance(ledger, "a", "b"), 1.0)
        flow_ledger.record_flow(ledger, "b", "a", 50.0)
        self.assertAlmostEqual(flow_ledger.return_fill_share(ledger, "a", "b"), 0.5)
        self.assertAlmostEqual(flow_ledger.pair_imbalance(ledger, "a", "b"), 50.0 / 150.0)
        flow_ledger.record_flow(ledger, "b", "a", 50.0)
        self.assertEqual(flow_ledger.overall_imbalance(ledger), 0.0)

    def test_the_overall_imbalance_weights_pairs_by_tonnes(self):
        ledger = {}
        flow_ledger.record_flow(ledger, "a", "b", 100.0)
        flow_ledger.record_flow(ledger, "b", "a", 100.0)
        flow_ledger.record_flow(ledger, "c", "d", 100.0)
        self.assertAlmostEqual(flow_ledger.overall_imbalance(ledger), 100.0 / 300.0)

    def test_a_stay_or_a_negative_amount_records_nothing(self):
        ledger = {}
        flow_ledger.record_flow(ledger, "a", "a", 5.0)
        flow_ledger.record_flow(ledger, "a", "b", -5.0)
        self.assertEqual(ledger, {})


class DuesAndWalkingCargo(unittest.TestCase):

    def test_dues_are_added_once_to_the_cargo_that_arrives(self):
        inputs = _inputs()
        plain = freight_cost.leg_money_per_tonne(1.0, inputs, 100.0)
        self.assertAlmostEqual(freight_cost.leg_money_per_tonne(1.0, inputs, 100.0, dues_per_tonne=3.0) - plain, 3.0)

    def test_a_herds_feed_is_eaten_on_the_loaded_leg_only(self):
        inputs = _inputs()
        prices = freight_cost.CarrierPrices(0.0)
        args = (inputs, 1.0, 1.0, prices, 0.05, 250.0)
        walking_empty = freight_cost.freight_money_per_tonne_km(*args, 1.0, cargo_walks=True)
        walking_full = freight_cost.freight_money_per_tonne_km(*args, 0.0, cargo_walks=True)
        carried_empty = freight_cost.freight_money_per_tonne_km(*args, 1.0)
        self.assertAlmostEqual(walking_empty - walking_full, inputs.driver_hours_per_tonne_km)
        self.assertAlmostEqual(carried_empty - walking_empty, inputs.feed_kg_per_tonne_km)
        self.assertAlmostEqual(walking_full, inputs.feed_kg_per_tonne_km + inputs.driver_hours_per_tonne_km)


class Droving(unittest.TestCase):

    def test_the_herd_is_the_carrier_and_has_no_vehicle(self):
        inputs = _inputs()
        self.assertEqual(inputs.vehicle_wear_fraction_per_tonne_km, 0.0)
        self.assertGreater(inputs.feed_kg_per_tonne_km, 0.0)
        self.assertGreater(inputs.driver_hours_per_tonne_km, 0.0)
        self.assertAlmostEqual(inputs.feed_kg_per_tonne_km * inputs.tonne_km_per_day, inputs.feed_kg_per_day)

    def test_a_drove_walks_at_most_the_animals_day(self):
        carrier = {"animal": "ox", "head_per_drover": 10, "km_per_day": 1000, "drover_hours_per_day": 10}
        fast = droving.freight_physical_inputs(carrier)
        self.assertLess(fast.distance_per_day_km, 100.0)

    def test_feed_rises_with_the_work_of_walking(self):
        carrier = {"animal": "ox", "head_per_drover": 10, "km_per_day": 10, "drover_hours_per_day": 10}
        short = droving.freight_physical_inputs(carrier).feed_kg_per_day
        longer = droving.freight_physical_inputs(dict(carrier, km_per_day=20)).feed_kg_per_day
        self.assertGreater(longer, short)

    def test_goods_never_go_by_drove_and_stock_does_not_go_by_cart(self):
        everything = [["lnd_mule_transport", "lnd_two_wheel_cart", "sea_square_sail", "lnd_ox_transport"]]
        goods = geography.usable_modes(everything)
        stock = geography.usable_modes(everything, cargo="living_stock")
        self.assertNotIn("drove", goods)
        self.assertIn("drove", stock)
        for mode in ("foot", "pack", "cart", "road"):
            self.assertNotIn(mode, stock)
        self.assertIn("river_boat", stock)
        self.assertIn("sail", stock)
        self.assertNotIn("drove", geography.modes_carrying("goods"))

    def test_only_stock_marked_walks_goes_by_drove(self):
        from sim.engine.domestic_haul import DomesticHaulMixin
        from sim.engine.living_stock_yearly import stock_rates
        classes = {material: DomesticHaulMixin._cargo_class(None, material) for material in stock_rates()}
        walking = {material for material, cargo in classes.items() if cargo == "living_stock"}
        self.assertTrue(walking)
        self.assertEqual(walking, {material for material, row in stock_rates().items() if row.get("walks")})
        self.assertLess(len(walking), len(classes))     # seed and cuttings are carried as goods

    def test_the_daily_loss_is_stated_with_its_basis(self):
        entry = geography.open_map().catalogue("route_modes")["drove"]
        self.assertGreater(entry["cargo_loss_per_day"], 0.0)
        self.assertIn(entry["cargo_loss_conf"], ("A", "B", "C", "D"))
        self.assertTrue(entry["cargo_loss_source"])
        self.assertEqual(geography.cargo_loss_per_day()["drove"], entry["cargo_loss_per_day"])

    def test_a_herd_on_the_road_loses_its_daily_share(self):
        from sim.geography import cargo_cost
        self.assertAlmostEqual(cargo_cost.daily_loss_share(0.01, 1.0), 0.01)
        self.assertAlmostEqual(cargo_cost.daily_loss_share(0.01, 10.0), 1.0 - 0.99 ** 10)
        self.assertEqual(cargo_cost.daily_loss_share(0.0, 50.0), 0.0)

    def test_labour_counts_no_droving_as_goods_carriage(self):
        from sim.labour import workforce_carriage
        carriage = workforce_carriage.carriage_for(["lnd_two_wheel_cart"])
        self.assertTrue(carriage.modes)
        rates = geography.carriage_rates(geography.usable_modes([["lnd_two_wheel_cart"]]))
        self.assertNotIn("drove", rates)

    def test_the_route_search_walks_a_herd_over_land(self):
        tiles = geography.tile_ids()
        origin = next(tile for tile in tiles if geography.tile_facts(tile)["neighbours"])
        reached = geography.route_costs([origin], ["drove"], mode_costs={"drove": 1.0})
        self.assertGreater(len(reached), 1)


class HaulArithmetic(unittest.TestCase):
    """The class, mode and unjoined-haul rules (`haul_route`) and the herd's loss on the road, on given inputs."""

    def test_stock_that_walks_is_living_stock_and_anything_else_is_goods(self):
        from sim.engine.haul_route import cargo_class_of
        self.assertEqual(cargo_class_of({"walks": True}), "living_stock")
        self.assertEqual(cargo_class_of({"walks": False}), "goods")
        self.assertEqual(cargo_class_of({}), "goods")
        self.assertEqual(cargo_class_of(None), "goods")

    def test_goods_go_by_the_cart_and_stock_by_the_first_walking_mode_else_the_cart(self):
        from sim.engine.haul_route import domestic_haul_mode
        self.assertEqual(domestic_haul_mode("goods", ["drove"], "cart"), "cart")
        self.assertEqual(domestic_haul_mode("living_stock", ["drove", "foot"], "cart"), "drove")
        self.assertEqual(domestic_haul_mode("living_stock", [], "cart"), "cart")

    def test_an_unjoined_haul_is_one_leg_at_the_rate_plus_the_dues_once(self):
        from sim.engine.haul_route import unjoined_haul_cost
        self.assertAlmostEqual(unjoined_haul_cost(0.5, 200.0, 7.0), 107.0)
        self.assertAlmostEqual(unjoined_haul_cost(0.5, 0.0, 7.0), 7.0)

    def test_the_cargo_share_counts_a_herds_loss_on_the_road_over_interest_alone(self):
        from sim.engine.haul_route import Leg, Route, domestic_cargo_cost_share
        route = Route((Leg("a", "b", "drove", 400.0, 0.0, 20.0),))
        interest_only = domestic_cargo_cost_share(0.0, {}, route, 0.05)
        with_loss = domestic_cargo_cost_share(0.0, {"drove": 0.01}, route, 0.05)
        self.assertGreater(with_loss, interest_only)
        self.assertGreater(interest_only, 0.0)


class Rivers(unittest.TestCase):
    """Rivers are edges between tiles derived from the tile layers, not reaches authored inside regions."""

    def test_the_map_has_river_edges_from_its_layers(self):
        edges = [edge for edge in routes_graph.graph(geography.open_map()).edges if edge.edge_class == "river"]
        self.assertGreater(len(edges), 100)
        on_rivers = {edge.tile_a for edge in edges}
        self.assertTrue(all(geography.layer_value(tile, "river_km_navigable") for tile in on_rivers))

    def test_river_boats_haul_along_a_river_edge(self):
        world_map = geography.open_map()
        edge = next(edge for edge in routes_graph.graph(world_map).edges if edge.edge_class == "river")
        found = geography.route([edge.tile_a], [edge.tile_b], ["river_boat"], mode_costs={"river_boat": 1.0},
                                held_nodes={"lnd_ox_transport"})
        self.assertIsNotNone(found)
        self.assertEqual({leg["mode"] for leg in found["legs"]}, {"river_boat"})


class EconomyFlows(unittest.TestCase):

    def test_rates_lie_on_the_line_between_empty_and_full_returns(self):
        from . import economy_fixture
        setup = dataclasses.replace(economy_fixture.small_setup(),
                                    carriage_rates={"cart": 0.002}, carriage_rates_balanced={"cart": 0.0012})
        self.assertAlmostEqual(setup.carriage_rates_at(1.0)["cart"], 0.002)
        self.assertAlmostEqual(setup.carriage_rates_at(0.0)["cart"], 0.0012)
        self.assertAlmostEqual(setup.carriage_rates_at(0.5)["cart"], 0.0016)

    def test_merchants_record_what_they_carried_and_the_record_saves_it(self):
        from sim.economy.record import EconomyRecord
        from . import economy_fixture
        economy, _outcomes = economy_fixture.run(years=3)
        carried = economy.record.carried
        for origin, row in carried.items():
            for destination, tonnes in row.items():
                self.assertNotEqual(origin, destination)
                self.assertGreater(tonnes, 0.0)
        restored = EconomyRecord.from_record(economy.record.to_record())
        self.assertEqual(restored.carried, carried)

    def test_a_balanced_ledger_lowers_the_carriage_and_repartitions_once(self):
        from . import economy_fixture
        setup = dataclasses.replace(economy_fixture.small_setup(), carriage_rates_balanced={
            mode: rate * 0.5 for mode, rate in economy_fixture.small_setup().carriage_rates.items()})
        economy = economy_fixture.Economy(setup)
        full = economy.carriage.cost_per_tonne(economy_fixture.TOWN, economy_fixture.FARMS)
        economy.record.carried = {"town": {"farms": 5.0}, "farms": {"town": 5.0}}
        self.assertTrue(economy.follow_flows())
        self.assertEqual(economy.record.area_imbalance, 0.0)
        self.assertLess(economy.carriage.cost_per_tonne(economy_fixture.TOWN, economy_fixture.FARMS), full)
        self.assertFalse(economy.follow_flows())


if __name__ == "__main__":
    unittest.main()
