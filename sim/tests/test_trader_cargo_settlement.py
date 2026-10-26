"""A trader's cargo is settled once, after the home market has cleared (Complaints/115).

The partner's side of a cargo goes through the foreign coin ledger and the route's carriers; the home side is what the
book gave (or, with no book, the quote). The trader's purse is trued up from what it was booked at the decision to what
the cargo really made. The foreign-trade module runs over plain views with its payment seams recorded, and the ledger's
commands it sends are read back.
"""

QUICK_TOPIC = True

import unittest

from sim.actors.api import NoteTraderMargin
from sim.agents import edges
from sim.actors.world_trade import TradeView
from sim.foreign_trade.api import NoteActorHomeTrade, NoteCargoLeg, SettleTraderCargo
from sim.foreign_trade.module import ForeignTrade
from sim.foreign_trade.state import ForeignTradeWorld
from sim.ledger.api import PayActorFromEdge, PayEdgeFrom
from sim.refusal import Refusal
from sim.tests import module_harness

PARTNER, OTHER, TRADER = "han_china_100ad", "norse_900ad", "trader:test"
SETTLEMENT = "edge:market settlement"


class Recording(ForeignTrade):
    """The module with its payment seams recorded."""

    def setup(self):
        super().setup()
        self.settled, self.lifts = [], []

    def partner_facts(self, _partner):
        return {"route": "route"}

    def settle_flow(self, partner, flow_tonnes, value, per_coin):
        self.settled.append((partner, flow_tonnes, value))

    def record_lift(self, partner, route, flow_tonnes, unmet_tonnes):
        self.lifts.append((partner, flow_tonnes))


def trade_module(trader_in_cast=True):
    answers = {} if trader_in_cast else {NoteTraderMargin: Refusal("no_such_actor", "none")}
    return module_harness.build(Recording, world=ForeignTradeWorld(), answers=answers, views={
        "legacy_agent_economy": {}, "home_unit_price": lambda material: 2.0,
        "civilisation_record": lambda partner: {"coin_standard": {"material": "silver_kg", "kg_per_unit": 1.0}}})


def note_leg(module, source, destination, tonnes=10.0, paid=100.0, received=160.0, duty=0.0):
    module.apply_note_cargo_leg(NoteCargoLeg(TRADER, "grain", tonnes, source, destination, paid, received, 5.0, "home", duty))


def landing(module, tonnes=10.0, paid=100.0, received=160.0):
    note_leg(module, PARTNER, "home", tonnes, paid, received)


def taking(module, tonnes=10.0, paid=100.0, received=160.0):
    note_leg(module, "home", PARTNER, tonnes, paid, received)


def settle(module, results):
    module.apply_settle_trader_cargo(SettleTraderCargo(results))


class CargoSettlement(unittest.TestCase):
    def test_one_route_shipped_twice_in_a_year_is_one_leg(self):
        module = trade_module()
        landing(module, 10.0, 100.0, 160.0)
        landing(module, 5.0, 50.0, 80.0)
        legs = module.cargo_legs()
        self.assertEqual(len(legs), 1)
        self.assertEqual((legs[0]["tonnes"], legs[0]["paid"], legs[0]["received"], legs[0]["kind"]), (15.0, 150.0, 240.0, "in"))

    def test_a_landing_cargo_pays_the_partner_in_coin_and_trues_up_to_what_the_book_gave(self):
        module = trade_module()
        landing(module)
        (leg,) = module.cargo_legs()
        settle(module, {leg["id"]: {"tonnes": 8.0, "money": 120.0}})
        self.assertEqual(module.settled, [(PARTNER, 10.0, 100.0)])
        self.assertEqual(module.lifts, [(PARTNER, 10.0)])
        self.assertEqual(module_harness.sent(module), [   # fetched less than booked at the decision
            NoteTraderMargin(TRADER, 120.0 - 160.0), PayEdgeFrom(TRADER, edges.EDGE_MARKET, 160.0 - 120.0, SETTLEMENT)])
        self.assertEqual(module.cargo_legs(), [])

    def test_a_taking_cargo_the_book_part_filled_is_paid_for_by_the_partner_only_in_part(self):
        module = trade_module()
        taking(module)
        (leg,) = module.cargo_legs()
        settle(module, {leg["id"]: {"tonnes": 6.0, "money": 30.0}})   # 6 tonnes bought, 30 of 100 funds unspent
        (partner, flow, value), = module.settled
        self.assertEqual((partner, flow), (PARTNER, -6.0))
        self.assertAlmostEqual(value, 160.0 * 0.6)
        # the partner's book closes on what really went
        self.assertEqual(module.world.actor_trade[PARTNER]["grain"]["sold_tonnes"], -4.0)
        (margin, payment) = module_harness.sent(module)
        self.assertAlmostEqual(margin.amount, 160.0 * 0.6 - 160.0 + 30.0)
        self.assertAlmostEqual(payment.amount, -margin.amount)

    def test_with_no_book_the_cargo_is_settled_at_its_quote(self):
        module = trade_module()
        landing(module)
        taking(module)
        settle(module, None)
        self.assertEqual(sorted(module.settled), [(PARTNER, -10.0, 160.0), (PARTNER, 10.0, 100.0)])
        self.assertEqual(module_harness.sent(module), [])   # the trader keeps what it was booked at
        self.assertEqual(module.world.actor_trade, {})

    def test_a_cargo_between_two_partners_settles_both_sides_and_touches_no_purse(self):
        module = trade_module()
        note_leg(module, PARTNER, OTHER)
        settle(module, {})
        self.assertEqual(sorted(module.settled), sorted([(OTHER, -10.0, 160.0), (PARTNER, 10.0, 100.0)]))
        self.assertEqual(module_harness.sent(module), [])

    def test_the_trader_margin_follows_what_the_cargo_really_made(self):
        module = trade_module()
        landing(module)
        (leg,) = module.cargo_legs()
        settle(module, {leg["id"]: {"tonnes": 8.0, "money": 120.0}})
        self.assertIn(NoteTraderMargin(TRADER, -40.0), module_harness.sent(module))

    def test_a_trader_the_cast_does_not_hold_is_not_paid_or_charged(self):
        module = trade_module(trader_in_cast=False)
        landing(module)
        (leg,) = module.cargo_legs()
        settle(module, {leg["id"]: {"tonnes": 8.0, "money": 120.0}})
        self.assertEqual(module_harness.sent(module), [NoteTraderMargin(TRADER, -40.0)])

    def test_the_tariff_in_a_cargos_carriage_reaches_the_treasury_of_the_country_it_entered(self):
        module = trade_module()
        note_leg(module, "home", PARTNER, duty=3.0)
        settle(module, None)
        self.assertEqual(module_harness.sent(module),
                         [PayActorFromEdge(edges.EDGE_FREIGHT, "government:" + PARTNER, 3.0, "tax:tariff")])


class Shipping(TradeView):
    """A trader's view of the world with prices fixed and the module's leg book behind the game's seams."""

    def __init__(self):
        self.notes, self._memo = [], {}
        self.module = trade_module()
        module = self.module

        class Needs:
            """The views and the commands the trade view uses, with the cargo leg going to the module's leg book."""
            landed_cost = staticmethod(lambda paid, carriage: paid + carriage)
            border_duty_per_tonne = staticmethod(lambda source, destination, price: 0.0)

            @staticmethod
            def send(command):
                if isinstance(command, NoteCargoLeg):
                    module.apply_note_cargo_leg(command)
                else:
                    self_notes.append(("home" if isinstance(command, NoteActorHomeTrade) else "partner", command))
        self_notes = self.notes
        self.needs = Needs()

    def _home_place(self):
        return "home"

    def price_at(self, material, place):
        return 10.0 if place == "home" else 4.0

    def freight_between(self, source, destination, material, tonnes):
        return 2.0 * tonnes

    def commodity_of(self, material):
        return material

    def market_sale(self, seller_id, material, tonnes):
        self.notes.append(("sale", tonnes))

    def market_purchase(self, buyer_id, commodity, tonnes):
        self.notes.append(("purchase", tonnes))


class ShippingNotesTheLeg(unittest.TestCase):
    def test_the_home_side_is_left_to_the_book(self):
        world = Shipping()
        self.assertEqual(world.ship(TRADER, "grain", 5.0, PARTNER, "home"), (20.0, 50.0))
        self.assertEqual([note for note in world.notes if note[0] in ("sale", "purchase")], [])
        (leg,) = world.module.cargo_legs()
        self.assertEqual((leg["kind"], leg["tonnes"], leg["paid"], leg["received"], leg["carriage"]), ("in", 5.0, 20.0, 50.0, 10.0))

    def test_cargo_leaving_home_is_a_taking_leg_and_cargo_arriving_a_landing_leg(self):
        world = Shipping()
        world.ship(TRADER, "grain", 5.0, "home", PARTNER)
        world.ship(TRADER, "grain", 3.0, PARTNER, "home")
        self.assertEqual([note for note in world.notes if note[0] in ("sale", "purchase")], [])
        self.assertEqual(sorted(leg["kind"] for leg in world.module.cargo_legs()), ["in", "out"])


if __name__ == "__main__":
    unittest.main()
