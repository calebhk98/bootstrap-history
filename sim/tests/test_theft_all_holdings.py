"""Complaint 273: theft, sack and banditry read the same exposure of everything a holder keeps (coin, goods, land,
loans, shares); stolen goods leave the holder's stock for the thieves' edge and stolen money lands with the thieves,
never destroyed. The coin module sends the ledger's commands for both (`DrawDownStock`, `HoldEdgeGoods`, `PayEdge`, `PayEdgeFrom`)."""

QUICK_TOPIC = True

import types
import unittest

from sim.agents.edges import EDGE_THIEVES
from sim.coin import exposure as exposures
from sim.coin import theft_exposure
from sim.coin.commands import ChargeActorsTheft, PlunderHousehold
from sim.actors.api import DrawDownActorStore, HoldEdgeGoods
from sim.demography.api import TakeFromGranary
from sim.coin.exposure import Exposure, GoodsLot, split_purse
from sim.coin.module import Coin
from sim.ledger.api import STORE_ACTOR, STORE_GRANARY, STORE_STOCK, DrawDownStock, PayEdge, PayEdgeFrom
from sim.tests import module_harness

CALM = dict(guard_hours_per_tonne_year={"coin": 0.0}, visible_scale=0.5, state_reach=0.0, protection=0.0)
EVENT = 0.5


def thief():
    return module_harness.build(Coin)


def exposure_of(purse, coin, goods_tonnes, price=10.0, land=500.0, loans=200.0):
    lots = [GoodsLot("iron", goods_tonnes, price, STORE_STOCK)]
    values = {"coin": coin, "goods": goods_tonnes * price, "land": land, "loans": loans}
    return Exposure(values=values, lots=lots, purse=purse)


def money_sent(module):
    return sum(command.amount for command in module_harness.sent(module) if isinstance(command, (PayEdge, PayEdgeFrom)))


def goods_sent(module):
    return {command.good: command.tonnes for command in module_harness.sent(module) if isinstance(command, HoldEdgeGoods)}


class EachStoreIsAskedByItsOwner(unittest.TestCase):

    def test_a_lot_in_an_actors_store_is_drawn_down_from_that_actor_then_held_by_the_edge(self):
        module = thief()
        module.take_goods(GoodsLot("grain", 50.0, 4.0, STORE_ACTOR, "state"), 7.0)
        self.assertEqual(module_harness.sent(module), [DrawDownActorStore("state", "grain", 7.0), HoldEdgeGoods(EDGE_THIEVES, "grain", 7.0)])

    def test_a_lot_in_the_stock_is_drawn_down_by_commodity_then_held_by_the_edge(self):
        module = thief()
        module.take_goods(GoodsLot("iron", 50.0, 4.0, STORE_STOCK), 7.0)
        self.assertEqual(module_harness.sent(module), [DrawDownStock("iron", 7.0), HoldEdgeGoods(EDGE_THIEVES, "iron", 7.0)])

    def test_a_lot_in_the_granary_is_taken_in_kilograms_then_held_by_the_edge(self):
        module = thief()
        module.take_goods(GoodsLot("wheat", 5.0, 4.0, STORE_GRANARY), 2.0)
        self.assertEqual(module_harness.sent(module), [TakeFromGranary(2000.0), HoldEdgeGoods(EDGE_THIEVES, "wheat", 2.0)])


class StolenGoodsLeaveTheStock(unittest.TestCase):

    def test_goods_taken_are_asked_of_the_stock_for_the_thieves_edge(self):
        module = thief()
        module.steal_from(None, exposure_of(1000.0, coin=1000.0, goods_tonnes=100.0), EVENT, **CALM)
        (held,) = [sent for sent in module_harness.sent(module) if isinstance(sent, HoldEdgeGoods)]
        (drawn,) = [sent for sent in module_harness.sent(module) if isinstance(sent, DrawDownStock)]
        self.assertEqual((held.good, held.edge, drawn.commodity), ("iron", EDGE_THIEVES, "iron"))
        self.assertEqual(drawn.tonnes, held.tonnes)
        self.assertGreater(held.tonnes, 0.0)
        self.assertLess(held.tonnes, 100.0)

    def test_land_is_never_lifted_and_the_money_asked_is_the_coins_share(self):
        module = thief()
        taken = module.steal_from(None, exposure_of(1000.0, coin=1000.0, goods_tonnes=0.0, land=1e6, loans=0.0), EVENT, **CALM)
        self.assertGreater(taken, 0.0)
        self.assertEqual(goods_sent(module), {})
        self.assertAlmostEqual(taken, 1000.0 * theft_exposure.share_taken("coin", EVENT, **CALM))
        self.assertEqual(module_harness.sent(module), [PayEdge(EDGE_THIEVES, taken, "theft")])

    def test_goods_lose_a_smaller_share_than_coin(self):
        module = thief()
        taken = module.steal_from(None, exposure_of(1000.0, coin=1000.0, goods_tonnes=100.0, loans=0.0), EVENT, **CALM)
        self.assertLess(goods_sent(module)["iron"] / 100.0, taken / 1000.0)

    def test_claims_are_paid_from_the_purse_and_never_beyond_it(self):
        module = thief()
        taken = module.steal_from(None, Exposure(values={"loans": 1e9}, lots=[], purse=30.0), 1.0, **CALM)
        self.assertLessEqual(taken, 30.0)
        self.assertAlmostEqual(money_sent(module), taken)

    def test_an_actors_theft_is_paid_from_that_actor(self):
        module = thief()
        taken = module.steal_from("firm:1", Exposure(values={"coin": 100.0}, lots=[], purse=100.0), EVENT, **CALM)
        self.assertEqual(module_harness.sent(module), [PayEdgeFrom("firm:1", EDGE_THIEVES, taken, "theft")])

    def test_a_bigger_event_takes_proportionally_more_of_what_is_portable(self):
        for kind in ("coin", "goods", "loans"):
            self.assertAlmostEqual(theft_exposure.share_taken(kind, 0.4, **CALM)
                                   / theft_exposure.share_taken(kind, 0.2, **CALM), 2.0)
        self.assertGreater(theft_exposure.share_taken("coin", EVENT, **CALM),
                           theft_exposure.share_taken("goods", EVENT, **CALM))
        self.assertEqual(theft_exposure.share_taken("land", EVENT, **CALM), 0.0)


class WhatAnActorKeeps(unittest.TestCase):

    def test_lent_funds_are_loans_and_the_rest_is_coin(self):
        coin, loans = split_purse(1000.0, 0.25)
        self.assertAlmostEqual(coin, 750.0)
        self.assertAlmostEqual(loans, 250.0)
        self.assertEqual(split_purse(-5.0, 0.25), (0.0, 0.0))

    def test_a_state_holds_stores_as_goods_and_a_firm_holds_none(self):
        state_view = exposures.actor_exposure("state", 100.0, {"grain": 50.0}, lambda material: 4.0, lambda: 0.0, 0.0)
        firm_view = exposures.actor_exposure("firm", 100.0, {}, lambda material: 4.0, lambda: 0.0, 0.0)
        self.assertAlmostEqual(state_view.values["goods"], 200.0)
        self.assertNotIn("goods", firm_view.values)
        self.assertNotIn("land", firm_view.values)
        self.assertEqual(state_view.lots, [GoodsLot("grain", 50.0, 4.0, STORE_ACTOR, "state")])

    def test_a_firm_holds_shares_as_claims(self):
        view = exposures.actor_exposure("firm", 0.0, {}, lambda material: 1.0, lambda: 12.5, 0.0)
        self.assertEqual(view.values["shares"], 12.5)

    def test_every_actor_of_a_year_shares_one_reading_of_the_lent_share(self):
        reads = []
        record = types.SimpleNamespace(exited_year=None, stratum=None, country=None, stores={}, holdings={})
        actors = {name: types.SimpleNamespace(record=record, money=100.0, workforce={}, prominence=lambda: 0.0)
                  for name in ("a", "b", "c")}
        registry = types.SimpleNamespace(actors=actors, state=types.SimpleNamespace(home_country="home"), get=lambda _id: None)
        module = module_harness.build(Coin, views={
            "cast": registry, "actor_world": types.SimpleNamespace(material_price=lambda m: 1.0),
            "lent_share": lambda: reads.append(1) or 0.25, "visible_scale": lambda *call: 0.5, "order_reach": 0.0})
        module.charge_actors_theft(ChargeActorsTheft())
        self.assertEqual(len(reads), 1)
        self.assertEqual([command.actor for command in module_harness.sent(module)], ["a", "b", "c"])


def household_module(farm_hectares=10.0, order_reach=0.0):
    """The coin module over a household of 2000 with iron in stock, a granary, a farm and a forest."""
    return module_harness.build(Coin, views={
        "civilisation": {"staple": "wheat"}, "acting_balance": 2000.0, "lent_share": 0.1, "held_goods": {"iron": 40.0},
        "goods_quote": lambda material: {"sell_per_tonne": 5.0}, "farm_holdings": {"hectares": farm_hectares, "stock_kg": 20000.0},
        "farm_land_price": 50.0, "forest_holding": {"hectares": 2.0, "base_cost_per_hectare": 100.0, "price_index": 1.0},
        "headcount": 3, "eminence": 0.0, "visible_scale": lambda *call: 0.5, "order_reach": order_reach,
        "standing": {"protection": 0.0}})


class HouseholdHoldings(unittest.TestCase):

    def test_the_household_exposes_coin_loans_goods_and_land(self):
        view = household_module().household_exposure()
        self.assertAlmostEqual(view.values["coin"], 1800.0)
        self.assertAlmostEqual(view.values["loans"], 200.0)
        self.assertAlmostEqual(view.values["goods"], (40.0 + 20.0) * 5.0)
        self.assertAlmostEqual(view.values["land"], 10.0 * 50.0 + 2.0 * 100.0)
        self.assertEqual({lot.name for lot in view.lots}, {"iron", "wheat"})
        self.assertEqual({lot.name: lot.store for lot in view.lots}, {"iron": STORE_STOCK, "wheat": STORE_GRANARY})

    def test_a_household_with_no_farm_yet_exposes_only_the_forest_as_land(self):
        view = household_module(farm_hectares=None).household_exposure()
        self.assertAlmostEqual(view.values["land"], 2.0 * 100.0)

    def test_a_sack_takes_money_and_stock_by_the_same_exposure_and_asks_for_both_from_the_thieves_edge(self):
        module = household_module()
        taken = module.plunder_household(PlunderHousehold(0.6, "sack and plunder", False))
        self.assertGreater(taken, 0.0)
        self.assertEqual([command for command in module_harness.sent(module) if isinstance(command, PayEdge)],
                         [PayEdge(EDGE_THIEVES, taken, "sack and plunder")])
        stolen = goods_sent(module)
        self.assertEqual(set(stolen), {"iron", "wheat"})
        self.assertLess(stolen["iron"], 40.0)
        self.assertLess(stolen["wheat"], 20.0)
        self.assertTrue(all(command.edge == EDGE_THIEVES for command in module_harness.sent(module)
                            if isinstance(command, HoldEdgeGoods)))

    def test_an_ordered_state_makes_banditry_cost_less_than_a_sack_of_equal_strength(self):
        kept = household_module(order_reach=0.8).plunder_household(PlunderHousehold(0.3, "banditry", True))
        lost = household_module().plunder_household(PlunderHousehold(0.3, "sack and plunder", False))
        self.assertLess(kept, lost)


if __name__ == "__main__":
    unittest.main()
