"""Trader actors own the goods they carry between countries (Complaints/115, 405): a cargo is tallied per partner and
direction (`rules.note_actor_trade`, `rules.actors_carry`), the partner's book closes on the tally and clears it
(`ForeignTrade.apply_close_partner_books`), a cargo sold to a partner is extra supply that lowers its price
(`rules.clear_partner`), and the economy's stand-in external orders leave alone a good the actors carry in that direction
(`AgentEconomy._external_orders`). Each rule is called on plain values or on a stand-in that holds only what it reads."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.engine import economy_port_year
from sim.engine.agents_port_trade import TradeView
from sim.engine.economy_port_year import AgentEconomy
from sim.foreign_trade import rules
from sim.foreign_trade.commands import ClosePartnerBooks
from sim.foreign_trade.constants import BOUGHT, SOLD
from sim.foreign_trade.module import ForeignTrade
from sim.foreign_trade.state import ForeignTradeWorld
from sim.tests import module_harness

PARTNER = "partner"


class TallyTests(unittest.TestCase):
    def test_a_cargo_is_tallied_per_partner_material_and_direction(self):
        tally = {}
        rules.note_actor_trade(tally, PARTNER, "wheat", 3.0, True, landed_cost=6.0)
        rules.note_actor_trade(tally, PARTNER, "wheat", 1.0, False)
        flow = tally[PARTNER]["wheat"]
        self.assertEqual((flow[SOLD], flow[BOUGHT], flow["landed_cost_money"]), (3.0, 1.0, 6.0))

    def test_part_of_a_cargo_taken_back_takes_its_share_of_the_landed_cost_with_it(self):
        tally = {PARTNER: {"wheat": {SOLD: 4.0, BOUGHT: 0.0, "landed_cost_money": 8.0}}}
        rules.note_actor_trade(tally, PARTNER, "wheat", -1.0, True)
        flow = tally[PARTNER]["wheat"]
        self.assertEqual((flow[SOLD], flow["landed_cost_money"]), (3.0, 6.0))

    def test_actors_carry_a_good_only_in_the_direction_and_to_the_partner_it_was_tallied(self):
        tally = {PARTNER: {"wheat": {SOLD: 3.0, BOUGHT: 0.0}}}
        self.assertTrue(rules.actors_carry(tally, "wheat", True))
        self.assertTrue(rules.actors_carry(tally, "wheat", True, PARTNER))
        self.assertFalse(rules.actors_carry(tally, "wheat", False))
        self.assertFalse(rules.actors_carry(tally, "wheat", True, "elsewhere"))
        self.assertFalse(rules.actors_carry(tally, "iron", True))

    def test_the_landed_cost_is_the_purchase_plus_a_years_return_plus_carriage(self):
        self.assertAlmostEqual(rules.landed_cost(100.0, 7.0, 0.1), 117.0)


class CloseBooksTests(unittest.TestCase):
    ENTRY = {"capacity_tonnes": 10.0, "stock_tonnes": 5.0, "price_ratio": 1.0, "trade_tonnes": 0.0}

    def test_the_book_clears_on_the_years_cargo_records_the_outcome_and_empties_the_tally(self):
        cleared = []

        class Booked(ForeignTrade):
            def partner_facts(self, partner):
                return {}

            def _import_offers(self, partner, cargo):
                return {}, {"grain": sum(flow[SOLD] for flow in cargo.values())}

            def partner_entry(self, partner, commodity, facts):
                return entry

            def _partner_outcome(self, entry, commodity, sold, bought, imports=()):
                cleared.append((sold, bought))
                return SimpleNamespace(price_ratio=0.8)
        entry = dict(self.ENTRY)
        module = module_harness.build(Booked, views={"material_commodity": lambda material: "grain"}, world=ForeignTradeWorld(
            market_book={PARTNER: {"grain": entry}}, home_actor_trade={"wheat": {}}))
        rules.note_actor_trade(module.world.actor_trade, PARTNER, "wheat", 3.0, True)
        rules.note_actor_trade(module.world.actor_trade, PARTNER, "wheat", 1.0, False)
        with mock.patch("sim.foreign_trade.rules.market.adjusted_capacity", return_value=9.0), \
             mock.patch("sim.foreign_trade.rules.market.stock_after_year", return_value=4.0):
            module.apply_close_partner_books(ClosePartnerBooks())
        self.assertEqual(cleared, [(3.0, 1.0)])
        self.assertEqual(entry, {"capacity_tonnes": 9.0, "stock_tonnes": 4.0, "price_ratio": 0.8, "trade_tonnes": 2.0})
        self.assertEqual((module.world.actor_trade, module.world.home_actor_trade), ({}, {}))


class PartnerOutcomeTests(unittest.TestCase):
    def outcome(self, sold):
        entry = {"reference_tonnes": 100.0, "capacity_tonnes": 100.0, "stock_tonnes": 0.0}
        return rules.clear_partner(entry, 0.6, 6.0, sold, 0.0)

    def test_a_cargo_sold_to_the_partner_lowers_its_price_and_never_raises_it(self):
        base = self.outcome(0.0).price_ratio
        self.assertLess(self.outcome(50.0).price_ratio, base)
        self.assertLessEqual(self.outcome(10.0).price_ratio, base)


class ShipTests(unittest.TestCase):
    def ship(self, source, destination):
        calls = []
        sim = SimpleNamespace(
            note_actor_home_trade=lambda *args: calls.append(("home",) + args),
            note_actor_trade=lambda *args: calls.append(("partner",) + args),
            landed_cost=lambda paid, carriage: paid + carriage, note_cargo_leg=lambda *args, **kwargs: None)
        view = SimpleNamespace(
            duty_between=lambda *args: 0.0, price_at=lambda material, place: 2.0, _home_place=lambda: "home",
            freight_between=lambda *args: 1.0, _sim=sim, _delivered=lambda: {})
        paid_received = TradeView.ship(view, "trader", "wheat", 3.0, source, destination)
        return paid_received, calls

    def test_a_cargo_to_a_partner_is_tallied_there_with_its_landed_cost_and_taken_from_home(self):
        paid_received, calls = self.ship("home", PARTNER)
        self.assertEqual(paid_received, (6.0, 6.0))
        self.assertEqual(calls, [("home", "wheat", 3.0, False), ("partner", PARTNER, "wheat", 3.0, True, 7.0)])

    def test_a_cargo_from_a_partner_is_tallied_there_and_landed_at_home(self):
        _, calls = self.ship(PARTNER, "home")
        self.assertEqual(calls, [("home", "wheat", 3.0, True), ("partner", PARTNER, "wheat", 3.0, False)])

    def test_a_cargo_of_nothing_moves_nothing(self):
        self.assertEqual(self.ship("home", PARTNER)[0], (6.0, 6.0))
        self.assertEqual(TradeView.ship(SimpleNamespace(), "trader", "wheat", 0.0, "home", PARTNER), (0.0, 0.0))


class ExternalOrdersTests(unittest.TestCase):
    def orders(self, carried):
        recorded = {}
        sim = SimpleNamespace(
            foreign_economies=lambda: [PARTNER],
            goods_market=SimpleNamespace(_route_from=lambda partner: SimpleNamespace(cost_per_tonne=1.0),
                                         landed_price=lambda good, partner, route, with_duty=True: 10.0),
            actors_carry=lambda good, to_partner, partner=None: (good, to_partner) in carried,
            partner_price_per_unit=lambda partner, good: 20.0)
        economy = SimpleNamespace(
            setup=SimpleNamespace(import_duty_share={}, coin_per_unit=1.0, port_tile="port"),
            area_map=SimpleNamespace(goods=lambda: ["wheat", "iron"], area_of=None))
        game = SimpleNamespace(_sim=sim, _economy=economy, _partner_spending=lambda partners: 1.0)

        def record(landed, exports, available, wanted, area_of, port_tile, export_budget):
            recorded.update(landed=landed, exports=exports)
            return "orders"

        with mock.patch.object(economy_port_year.economy_api, "traded_volumes", return_value={"wheat": 5.0, "iron": 5.0}), \
             mock.patch.object(economy_port_year.economy_api, "opening_quantities", return_value={}), \
             mock.patch.object(economy_port_year.trade_duty, "export_terms", return_value=(0.0, False)), \
             mock.patch("sim.engine.material_units.tonnes_per_unit", return_value=1.0), \
             mock.patch.object(economy_port_year, "external_orders", record):
            AgentEconomy._external_orders(game)
        return recorded

    def test_with_no_cargo_both_goods_are_imported_and_exported(self):
        recorded = self.orders(set())
        self.assertEqual((sorted(recorded["landed"]), sorted(recorded["exports"])), (["iron", "wheat"], ["iron", "wheat"]))

    def test_a_good_the_actors_export_draws_no_export_bid_but_may_still_be_imported(self):
        recorded = self.orders({("wheat", True)})
        self.assertEqual((sorted(recorded["landed"]), sorted(recorded["exports"])), (["iron", "wheat"], ["iron"]))

    def test_a_good_the_actors_import_draws_no_import_offer_but_may_still_be_exported(self):
        recorded = self.orders({("wheat", False)})
        self.assertEqual((sorted(recorded["landed"]), sorted(recorded["exports"])), (["iron"], ["iron", "wheat"]))


if __name__ == "__main__":
    unittest.main()
