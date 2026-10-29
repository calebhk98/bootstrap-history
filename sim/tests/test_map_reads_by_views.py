"""Modules that used to read the game's map object now ask the land module's views. Each test gives one view a value that no
default could stand for and requires the module's answer to carry it: a read that kept answering its default after the move
would fail here. Plain views; no game."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.disease.module import Disease
from sim.disease.state import DiseaseWorld
from sim.foreign_trade.module import ForeignTrade
from sim.foreign_trade.state import ForeignTradeWorld
from sim.freight import routes
from sim.freight.module import Freight
from sim.markets import household_needs
from sim.tests import materials_stand_in, module_harness, resources_stand_in


class DiseaseReadsTests(unittest.TestCase):
    def test_the_endemic_death_rates_are_those_of_the_tiles_the_nation_holds(self):
        asked = []
        module = module_harness.build(Disease, world=DiseaseWorld(), views={
            "home_tiles_held": lambda: ["t1", "t2", "conquered"],
            "endemic_people_loss": lambda tiles: asked.append(list(tiles)) or {"working_age": 0.5}})
        self.assertEqual(module.endemic_death_rates(), {"working_age": 0.5})
        self.assertEqual(asked, [["t1", "t2", "conquered"]])

    def test_a_tiles_area_is_the_one_the_land_module_describes(self):
        module = module_harness.build(Disease, world=DiseaseWorld(), views={
            "home_tiles_held": lambda: ["t1"], "tile_description": lambda tile: {"land_area_km2": 321.5}})
        self.assertEqual(module.area_by_tile(), {"t1": 321.5})


class FreightReadsTests(unittest.TestCase):
    def test_livestock_goes_by_the_first_mode_whose_cargo_walks_and_goods_by_cart(self):
        module = module_harness.build(Freight, views={
            "carriage_facts": lambda: {"walking_modes": ["drove"], "loss_per_day": {}, "dues_hours_per_tonne": {}}})
        self.assertEqual(module.domestic_haul_mode("living_stock"), "drove")
        self.assertEqual(module.domestic_haul_mode("goods"), "cart")

    def test_handling_is_charged_from_the_dues_hours_the_land_module_states(self):
        module = module_harness.build(Freight, views={
            "wage": lambda trade: 2.0, "carriage_facts": lambda: {
                "walking_modes": [], "loss_per_day": {}, "dues_hours_per_tonne": {"cart": 3.0}}})
        self.assertEqual(module.freight_handling_costs()["cart"], 6.0)

    def test_the_destination_tiles_of_a_haul_are_the_tiles_held_by_this_society(self):
        asked = {}

        class Asked(Freight):
            def freight_mode_costs(self, imbalance=1.0, modes=None, cargo=None):
                return {"cart": 1.0}

            def freight_handling_costs(self):
                return {}

        module = module_harness.build(Asked, views={
            "civilisation": lambda: {"id": "home"}, "held_techniques": lambda include_starting: frozenset(),
            "tiles_listed_by": lambda civilisation: ["held_tile"], "modes_usable": lambda parties, cargo="goods": ["cart"],
            "cheapest_route": lambda origins, destinations, modes, *rest, **keywords: asked.update(destinations=destinations) or None})
        with mock.patch.object(routes, "choose_route", side_effect=lambda search, cost, mode_costs, share: search(mode_costs)):
            module.haul_route(["origin"], 0.0, "goods")
        self.assertEqual(asked, {"destinations": ["held_tile"]})


class ResourcesReadsTests(unittest.TestCase):
    CATALOGUE = {"mechanisms": {"gold": "mineral_deposit", "cattle": "herd_animal"}, "metals": ("gold",), "ore_goods": {},
                 "works_priced_materials": ("gold",), "demand_goods": {"gold": ("gold_kg", "gold_leaf_kg")},
                 "mining_trade": "assayer"}

    def module(self):
        return resources_stand_in.build(views={"deposit_catalogue": lambda: self.CATALOGUE})

    def test_a_material_is_a_deposit_resource_when_the_catalogue_gives_it_a_deposit_mechanism(self):
        module = self.module()
        self.assertEqual(module.mine_resource_id("gold_kg"), "gold")
        self.assertIsNone(module.mine_resource_id("cattle"))
        self.assertIsNone(module.mine_resource_id("unknown"))

    def test_the_goods_a_mine_supplies_and_its_trade_come_from_the_catalogue(self):
        module = self.module()
        self.assertEqual(module.mine_demand_goods("gold"), ("gold_kg", "gold_leaf_kg"))
        self.assertEqual(module.mine_demand_goods("tin"), ("tin",))
        self.assertEqual(module.mine_trade(), "assayer")
        self.assertEqual(module.works_materials(), ("gold",))

    def test_the_home_land_area_is_the_land_modules_area_of_the_tiles_held(self):
        module = resources_stand_in.build(views={
            "tiles_listed_by": lambda civilisation: ["t1"], "land_area_of": lambda tiles: 12.5 if list(tiles) == ["t1"] else -1.0})
        self.assertEqual(module.home_land_area_km2(), 12.5)


class MaterialsReadsTests(unittest.TestCase):
    def test_a_hectare_of_coppice_yields_the_forests_increment_over_the_wood_to_charcoal_ratio(self):
        module = materials_stand_in.build(
            tiles_listed_by=lambda civilisation: ["t1"], forest_increment=lambda tiles: 8.0 if tuple(tiles) == ("t1",) else -1.0)
        self.assertEqual(module.charcoal_per_hectare(), 2.0)


class ForeignTradeReadsTests(unittest.TestCase):
    def test_the_mineral_share_of_a_partner_is_asked_of_the_tiles_its_file_lists(self):
        asked = []
        module = module_harness.build(ForeignTrade, world=ForeignTradeWorld(), views={
            "civilisation_record": lambda partner_id: {"id": partner_id}, "tiles_listed_by": lambda civilisation: ["p1", "p2"],
            "mineral_share_of_tiles": lambda tiles, commodity: asked.append((list(tiles), commodity)) or 0.25})
        self.assertEqual(module._mineral_share("partner", "tin"), 0.25)
        self.assertEqual(asked, [(["p1", "p2"], "tin")])


class HouseholdBasketTests(unittest.TestCase):
    def test_each_tile_is_weighted_by_its_share_of_the_people_in_the_order_given(self):
        tiles = ["afghanistan_01", "afghanistan_02"]
        records = household_needs.climate_records(tiles, [{"lat": 1.0}, {"lat": 2.0}])
        self.assertEqual([record[0] for record in records], [{"lat": 1.0}, {"lat": 2.0}])
        self.assertAlmostEqual(sum(record[1] for record in records), 1.0)

    def test_a_basket_built_for_a_civilisation_and_model_is_kept(self):
        model = type("Model", (), {"basket": object()})()
        built, remembered = [], {}
        with mock.patch.object(household_needs.need_basket, "mean_climate_basket",
                               lambda basket, records: built.append(records) or ("basket", len(built))):
            first = household_needs.civilisation_basket(model, "rome", remembered, lambda: ["rome records"])
            again = household_needs.civilisation_basket(model, "rome", remembered, lambda: self.fail("rebuilt"))
        self.assertEqual((first, again, built), (("basket", 1), ("basket", 1), [["rome records"]]))


if __name__ == "__main__":
    unittest.main()
