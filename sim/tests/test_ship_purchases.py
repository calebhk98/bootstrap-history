"""Complaint 617: the navy buys durable ships made by shipwrights."""
QUICK_TOPIC = True

import dataclasses
import unittest
from types import SimpleNamespace

from sim.agents import budget_lines
from sim.economy import api as economy_api
from sim.economy import labour_state, producers
from sim.economy.recipes import recipe_from_entry
from sim.economy.types import GoodSpec
from sim.engine import economy_port_actors as actors_port
from sim.engine.economy_port import EconomyPort
from sim.tests import economy_fixture
from sim.tests.economy_fixture import FARMS, METAL
from sim.world import demand


class ShipPurchases(unittest.TestCase):
    def test_fleet_planning_does_not_open_an_unopened_economy(self):
        world = SimpleNamespace(state=SimpleNamespace(
            projects=SimpleNamespace(granted={"sea_mortise_tenon"})))
        port = EconomyPort(world)
        port._opening = True
        goods = port.fleet_goods("state:a")
        self.assertEqual([good["material"] for good in goods], ["warship"])
        self.assertEqual(goods[0]["held"], 0.0)
        self.assertGreater(goods[0]["life"], 0.0)

    def test_a_new_good_without_a_curated_commodity_group_can_be_bought(self):
        world = SimpleNamespace(_material_commodity_map=lambda: {"iron_bar_kg": "iron"})
        port = EconomyPort(world)
        self.assertEqual(port.materials_in("warship"), ["warship"])
        self.assertEqual(port.materials_in("iron"), ["iron_bar_kg"])

    def test_state_hull_bid_is_filled_by_shipwright_production(self):
        entry = demand.production_data()["warship"]
        recipe = recipe_from_entry("warship", entry)
        base = economy_fixture.small_setup()
        specs = dict(base.specs)
        specs.update({good: GoodSpec(good, 1.0, 0.0, 0.0, "input") for good in recipe.inputs})
        specs["warship"] = GoodSpec("warship", entry["unit_mass_kg"], 0.0, 20.0, "ship", capital_asset=True)
        setup = dataclasses.replace(base, specs=specs, recipes=dict(base.recipes, warship=recipe),
                                    trades=dict(base.trades, shipwright=economy_api.TradeSpec("shipwright")),
                                    opening_wages=dict(base.opening_wages, shipwright=1.5),
                                    opening_prices=dict(base.opening_prices, warship=100000.0,
                                                        **{good: 0.1 for good in recipe.inputs}))
        economy = economy_api.blank_economy(setup)
        owner = sorted(economy.record.cohorts)[0]
        builder = producers.Producer("shipyard", owner, "warship", FARMS, 1.0, expected_sales=1.0)
        economy.record.producers[builder.agent_id] = builder
        economy.record.workforce = labour_state.opening_workforce(setup, economy.record)
        economy_api.post_transfers(economy, [economy_api.Transfer(
            economy_api.EDGE_LEGACY, builder.agent_id, setup.currency_id, 1000000.0, "workshop capital")])
        economy_api.move_goods(economy, [economy_api.GoodsMove(
            economy_api.EDGE_LEGACY, builder.agent_id, good, FARMS, quantity, "workshop inputs")
            for good, quantity in recipe.inputs.items()])
        purchases = []
        world = SimpleNamespace(
            territory=lambda: SimpleNamespace(coast_km=100.0),
            fleet_goods=lambda: [{"material": "warship", "life": 20.0,
                                  "held": 0.0, "crew": entry["naval_crew"]}],
            trade_exists=lambda trade: True, national_people=lambda trade: 100000.0,
            pay_per_person_year=lambda trade: 10.0,
            commodity_of=lambda material: material,
            material_cost=lambda material, tonnes: tonnes * 100000000.0)
        line, = budget_lines.navy_line(world)
        for commodity, quantity in line.materials.items():
            actors_port.note_purchase(purchases, "state:a", commodity, quantity, line.material_cost)
        orders, funding = actors_port.purchase_orders(
            economy, purchases, lambda good: 0.001, lambda actor: FARMS,
            lambda commodity: [commodity], setup.coin_per_unit)
        actors_port.fund(economy, funding)
        outcome = economy.step(economy_fixture.quiet_year(setup, engine_orders=orders))
        actors_port.close(economy, [], purchases)
        self.assertGreater(outcome.output.get("warship", 0.0), 0.0,
                           (outcome.output, economy.record.hours_hired, economy.record.workforce))
        self.assertGreater(actors_port.held_units(economy, "state:a", "warship"), 0.0)
        hired = sum(hours for key, hours in economy.record.hours_hired.items() if key.startswith("shipwright|"))
        self.assertGreater(hired, 0.0)
        self.assertEqual(economy_api.economy_book(economy).check_conservation(1e-6).breaches, ())

    def test_navy_buys_missing_hulls_and_keeps_only_the_crew_on_payroll(self):
        world = SimpleNamespace(
            territory=lambda: SimpleNamespace(coast_km=100.0),
            fleet_goods=lambda: [{"material": "test_hull", "life": 20.0,
                                  "held": 0.0, "crew": {"sailor": 60.0}}],
            trade_exists=lambda trade: True, national_people=lambda trade: 100000.0,
            pay_per_person_year=lambda trade: 10.0,
            commodity_of=lambda material: material,
            material_cost=lambda material, tonnes: tonnes * 1000000.0)
        line, = budget_lines.navy_line(world)
        self.assertEqual(line.labour, {"sailor": 60.0})
        self.assertAlmostEqual(line.materials.get("test_hull", 0.0), 0.001)
        self.assertGreater(line.material_cost, 0.0)
        world.fleet_goods = lambda: [{"material": "test_hull", "life": 20.0,
                                     "held": 1.0, "crew": {"sailor": 60.0}}]
        replacement, = budget_lines.navy_line(world)
        self.assertAlmostEqual(replacement.materials["test_hull"], 0.001 / 20.0)
        world.territory = lambda: SimpleNamespace(coast_km=0.0)
        self.assertEqual(budget_lines.navy_line(world), [])

    def test_bought_durables_are_retained_and_wear_even_without_another_purchase(self):
        specs = economy_fixture.specs({METAL: 20.0})
        specs[METAL] = dataclasses.replace(specs[METAL], capital_asset=True)
        setup = economy_fixture.small_setup(specs=specs)
        economy = economy_api.blank_economy(setup)
        book = economy_api.economy_book(economy)
        economy_api.move_goods(economy, [economy_api.GoodsMove(
            economy_api.EDGE_LEGACY, actors_port.buy_account("state:a"), METAL, FARMS, 2.0, "test purchase")])
        purchases = [{"buyer": "state:a"}]
        actors_port.close(economy, [], purchases)
        self.assertAlmostEqual(actors_port.held_units(economy, "state:a", METAL), 2.0)
        outcome = economy.step(economy_fixture.quiet_year(
            setup, durable_users=(actors_port.held_account("state:a"),)))
        self.assertAlmostEqual(actors_port.held_units(economy, "state:a", METAL), 1.9)
        self.assertAlmostEqual(outcome.accounts.goods[METAL].durable_wear, 0.1)
        self.assertEqual(book.check_conservation(1e-6).breaches, ())
        restored = economy_api.economy_from_record(setup, economy_api.export_record(economy))
        self.assertAlmostEqual(actors_port.held_units(restored, "state:a", METAL), 1.9)

    def test_materials_bought_for_immediate_use_are_consumed_even_if_durable(self):
        setup = economy_fixture.small_setup(specs=economy_fixture.specs({METAL: 20.0}))
        economy = economy_api.blank_economy(setup)
        economy_api.move_goods(economy, [economy_api.GoodsMove(
            economy_api.EDGE_LEGACY, actors_port.buy_account("state:a"), METAL, FARMS, 2.0, "test purchase")])
        actors_port.close(economy, [], [{"buyer": "state:a"}])
        self.assertEqual(actors_port.held_units(economy, "state:a", METAL), 0.0)
        self.assertEqual(economy_api.economy_book(economy).stock(actors_port.buy_account("state:a"), METAL, FARMS), 0.0)

    def test_ship_recipes_take_shipwright_work_and_make_counted_goods(self):
        production = demand.production_data()
        for good in ("merchant_ship", "warship"):
            with self.subTest(good=good):
                entry = production.get(good, {})
                self.assertEqual(entry.get("unit_dimension"), "count")
                self.assertGreater(entry.get("unit_mass_kg", 0.0), 0.0)
                self.assertGreater(entry.get("labour_hours", {}).get("shipwright", 0.0), 0.0)
                self.assertEqual(entry.get("outputs"), {good: 1.0})


if __name__ == "__main__":
    unittest.main()
