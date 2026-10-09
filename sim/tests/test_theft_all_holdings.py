"""Complaint 273: theft, sack and banditry read the same exposure of everything an actor keeps (coin, goods, land,
loans, shares); stolen goods leave the holder's stock for the thieves' edge and stolen money lands with the thieves,
never destroyed."""

QUICK_TOPIC = True

import types
import unittest

from sim.agents.edges import Edge, EDGE_THIEVES
from sim.engine import theft_exposure
from sim.engine.holdings_exposure import Exposure, GoodsLot, HoldingsExposureMixin, split_purse
from sim.engine.theft_charge import TheftChargeMixin

CALM = dict(guard_hours_per_tonne_year={"coin": 0.0}, visible_scale=0.5, state_capacity=0.0, protection=0.0)
EVENT = 0.5


class Purse:
    def __init__(self, money):
        self.money = money

    def credit(self, amount, purpose):
        self.money += amount

    def debit(self, amount, purpose):
        self.money -= amount


def world_with_thieves():
    balances, goods = {}, {}
    thieves = Edge(EDGE_THIEVES, balances, {}, goods)
    return types.SimpleNamespace(edge=lambda name: thieves), thieves, balances


def exposure_of(purse, coin, goods_tonnes, price=10.0, land=500.0, loans=200.0):
    stock = {"iron": goods_tonnes}

    def take(tonnes):
        stock["iron"] -= tonnes

    lots = [GoodsLot("iron", goods_tonnes, price, take)]
    values = {"coin": coin, "goods": goods_tonnes * price, "land": land, "loans": loans}
    return Exposure(values=values, lots=lots, purse=purse.money), stock


class StolenGoodsLeaveTheStock(unittest.TestCase):

    def test_goods_taken_leave_the_stock_and_reach_the_thieves_edge(self):
        world, thieves, balances = world_with_thieves()
        purse = Purse(1000.0)
        exposure, stock = exposure_of(purse, coin=1000.0, goods_tonnes=100.0)
        TheftChargeMixin.steal_from(world, purse, exposure, EVENT, **CALM)
        taken = thieves.goods_held()["iron"]
        self.assertGreater(taken, 0.0)
        self.assertAlmostEqual(stock["iron"] + taken, 100.0)

    def test_land_is_never_lifted_and_money_is_conserved(self):
        world, thieves, balances = world_with_thieves()
        purse = Purse(1000.0)
        exposure, stock = exposure_of(purse, coin=1000.0, goods_tonnes=0.0, land=1e6, loans=0.0)
        taken = TheftChargeMixin.steal_from(world, purse, exposure, EVENT, **CALM)
        self.assertGreater(taken, 0.0)
        self.assertAlmostEqual(purse.money + balances[EDGE_THIEVES], 1000.0)
        self.assertAlmostEqual(taken, 1000.0 * theft_exposure.share_taken("coin", EVENT, **CALM))

    def test_goods_lose_a_smaller_share_than_coin(self):
        world, thieves, _ = world_with_thieves()
        purse = Purse(1000.0)
        exposure, stock = exposure_of(purse, coin=1000.0, goods_tonnes=100.0, loans=0.0)
        TheftChargeMixin.steal_from(world, purse, exposure, EVENT, **CALM)
        self.assertLess(thieves.goods_held()["iron"] / 100.0, (1000.0 - purse.money) / 1000.0)

    def test_claims_are_paid_from_the_purse_and_never_beyond_it(self):
        world, thieves, balances = world_with_thieves()
        purse = Purse(30.0)
        exposure = Exposure(values={"loans": 1e9}, lots=[], purse=purse.money)
        taken = TheftChargeMixin.steal_from(world, purse, exposure, 1.0, **CALM)
        self.assertLessEqual(taken, 30.0)
        self.assertGreaterEqual(purse.money, 0.0)
        self.assertAlmostEqual(purse.money + balances[EDGE_THIEVES], 30.0)

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
        sim = types.SimpleNamespace(lent_share=lambda: 0.0)
        state = types.SimpleNamespace(money=100.0, record=types.SimpleNamespace(stores={"grain": 50.0}, holdings={}),
                                      kind="government")
        firm = types.SimpleNamespace(money=100.0, record=types.SimpleNamespace(stores={}, holdings={}), kind="firm")
        state_view = HoldingsExposureMixin.actor_exposure(sim, state, lambda material: 4.0, lambda issuer_id: None)
        firm_view = HoldingsExposureMixin.actor_exposure(sim, firm, lambda material: 4.0, lambda issuer_id: None)
        self.assertAlmostEqual(state_view.values["goods"], 200.0)
        self.assertNotIn("goods", firm_view.values)
        self.assertNotIn("land", firm_view.values)
        state_view.lots[0].take(10.0)
        self.assertAlmostEqual(state.record.stores["grain"], 40.0)

    def test_a_firm_holds_shares_as_claims(self):
        sim = types.SimpleNamespace(lent_share=lambda: 0.0)
        issuer = types.SimpleNamespace(record=types.SimpleNamespace(last_margin=10.0))
        firm = types.SimpleNamespace(money=0.0, kind="firm",
                                     record=types.SimpleNamespace(stores={}, holdings={"other": 0.5}))
        view = HoldingsExposureMixin.actor_exposure(sim, firm, lambda material: 1.0, lambda issuer_id: issuer)
        self.assertGreater(view.values["shares"], 0.0)


class FounderSeat(types.SimpleNamespace):
    """The parts of `Sim` the founder's exposure and plunder read."""


def founder_seat(farm_hectares=10.0):
    stock = {"iron": 40.0}
    balances, goods = {}, {}
    thieves = Edge(EDGE_THIEVES, balances, {}, goods)
    household = Purse(2000.0)
    household.capital = 0.0
    household.protection = 0.0
    seat = FounderSeat(
        state=types.SimpleNamespace(household=household, holdings=types.SimpleNamespace(farm_hectares=farm_hectares)),
        civ={"staple": "wheat"}, price_index=1.0, farm_stock_kg=20000.0, forest_ha=2.0, FOREST_COST_PER_HA=100.0, state_capacity=0.0,
        lent_share=lambda: 0.1, farm_price_per_hectare=lambda: 50.0, _material_stock=lambda: stock,
        goods_market=types.SimpleNamespace(quote=lambda material: {"sell_per_tonne": 5.0}),
        edge=lambda name: thieves, visible_scale=lambda *args: 0.5, labour=types.SimpleNamespace(headcount=lambda: 3),
        thieves=thieves, balances=balances, stock=stock)
    household.capital = household.money
    household.eminence = 0.0
    seat.founder_visible_scale = lambda: 0.5
    seat.steal_from = lambda *args, **kwargs: TheftChargeMixin.steal_from(seat, *args, **kwargs)
    seat.founder_exposure = lambda: HoldingsExposureMixin.founder_exposure(seat)
    return seat


class FounderHoldings(unittest.TestCase):

    def test_the_founder_exposes_coin_loans_goods_and_land(self):
        view = HoldingsExposureMixin.founder_exposure(founder_seat())
        self.assertAlmostEqual(view.values["coin"], 1800.0)
        self.assertAlmostEqual(view.values["loans"], 200.0)
        self.assertAlmostEqual(view.values["goods"], (40.0 + 20.0) * 5.0)
        self.assertAlmostEqual(view.values["land"], 10.0 * 50.0 + 2.0 * 100.0)
        self.assertEqual({lot.name for lot in view.lots}, {"iron", "wheat"})

    def test_a_founder_with_no_farm_yet_exposes_only_the_forest_as_land(self):
        view = HoldingsExposureMixin.founder_exposure(founder_seat(farm_hectares=None))
        self.assertAlmostEqual(view.values["land"], 2.0 * 100.0)

    def test_a_sack_takes_money_and_stock_by_the_same_exposure_and_destroys_nothing(self):
        seat = founder_seat()
        household = seat.state.household
        taken = TheftChargeMixin.plunder_founder(seat, 0.6, "sack and plunder", order_holds=False)
        self.assertGreater(taken, 0.0)
        self.assertAlmostEqual(household.money + seat.balances[EDGE_THIEVES], 2000.0)
        self.assertLess(seat.stock["iron"], 40.0)
        self.assertLess(seat.farm_stock_kg, 20000.0)
        self.assertAlmostEqual(seat.thieves.goods_held()["iron"], 40.0 - seat.stock["iron"])
        self.assertEqual(seat.state.holdings.farm_hectares, 10.0)

    def test_an_ordered_state_makes_banditry_cost_less_than_a_sack_of_equal_strength(self):
        orderly, fallen = founder_seat(), founder_seat()
        orderly.state_capacity = 0.8
        kept = TheftChargeMixin.plunder_founder(orderly, 0.3, "banditry", order_holds=True)
        lost = TheftChargeMixin.plunder_founder(fallen, 0.3, "sack and plunder", order_holds=False)
        self.assertLess(kept, lost)


if __name__ == "__main__":
    unittest.main()
