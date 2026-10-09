"""A trader's cargo is settled once, after the home market has cleared (Complaints/115).

The partner's side of a cargo goes through the foreign coin ledger and the route's carriers; the home side is what the
book gave (or, with no book, the quote). The trader's purse is trued up from what it was booked at the decision to what
the cargo really made. Run on a stub with the mixin's own seams recorded.
"""

QUICK_TOPIC = True

import unittest

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.engine.agents_port_trade import TradeView
from sim.engine.trader_cargo import TraderCargoMixin

PARTNER, OTHER, TRADER = "han_china_100ad", "norse_900ad", "trader:test"


class Stub(TraderCargoMixin):
    """The seams the mixin reads, recording what it settles."""

    def __init__(self):
        self.state = type("State", (), {})()
        self.state.economy = type("Economy", (), {"agent_economy": {}})()
        self.state.actors = ActorsState(home_country="home")
        self.registry = ActorRegistry(self.state.actors)
        self.registry.add(TRADER, ActorRecord(kind="trader", location="town", money=1000.0, founded_year=90))
        self.settled, self.lifts, self.tallies = [], [], []

    @property
    def actors(self):
        return self.registry

    def edge(self, name):
        return self.state.actors.edge(name)

    def _coin_metal_price(self, _material):
        return 2.0

    def _foreign_economy_facts(self, _partner):
        return {"route": "route"}

    def _settle_flow(self, partner, flow_tonnes, value, per_coin):
        self.settled.append((partner, flow_tonnes, value))

    def _record_lift(self, partner, route, flow_tonnes, unmet_tonnes, capital_tied=0.0):
        self.lifts.append((partner, flow_tonnes))

    def note_actor_trade(self, partner, material, tonnes, to_partner):
        self.tallies.append((partner, material, tonnes, to_partner))

    @property
    def purse(self):
        return self.registry.get(TRADER).money


class ShippingWorld(TradeView):
    """A trader's view of the world with prices fixed and its market seams recorded."""

    def __init__(self, on_book):
        self.on_book = on_book
        self.notes, self._memo = [], {}
        self.game = Stub()
        self._sim = self.game
        self.game.note_actor_home_trade = lambda *args: self.notes.append(("home", args))

    def runs_agent_economy(self):
        return self.on_book

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


def landing(game, tonnes=10.0, paid=100.0, received=160.0):
    game.note_cargo_leg(TRADER, "grain", tonnes, PARTNER, "home", paid, received, 5.0, home="home")


def taking(game, tonnes=10.0, paid=100.0, received=160.0):
    game.note_cargo_leg(TRADER, "grain", tonnes, "home", PARTNER, paid, received, 5.0, home="home")


class CargoSettlement(unittest.TestCase):
    def test_one_route_shipped_twice_in_a_year_is_one_leg(self):
        game = Stub()
        landing(game, 10.0, 100.0, 160.0)
        landing(game, 5.0, 50.0, 80.0)
        legs = game.cargo_legs()
        self.assertEqual(len(legs), 1)
        self.assertEqual((legs[0]["tonnes"], legs[0]["paid"], legs[0]["received"], legs[0]["kind"]), (15.0, 150.0, 240.0, "in"))

    def test_a_landing_cargo_pays_the_partner_in_coin_and_trues_up_to_what_the_book_gave(self):
        game = Stub()
        landing(game)
        (leg,) = game.cargo_legs()
        game.settle_trader_cargo({leg["id"]: {"tonnes": 8.0, "money": 120.0}})
        self.assertEqual(game.settled, [(PARTNER, 10.0, 100.0)])
        self.assertEqual(game.lifts, [(PARTNER, 10.0)])
        self.assertAlmostEqual(game.purse, 1000.0 + (120.0 - 160.0))   # fetched less than booked at the decision
        self.assertEqual(game.cargo_legs(), [])

    def test_a_taking_cargo_the_book_part_filled_is_paid_for_by_the_partner_only_in_part(self):
        game = Stub()
        taking(game)
        (leg,) = game.cargo_legs()
        game.settle_trader_cargo({leg["id"]: {"tonnes": 6.0, "money": 30.0}})   # 6 tonnes bought, 30 of 100 funds unspent
        (partner, flow, value), = game.settled
        self.assertEqual((partner, flow), (PARTNER, -6.0))
        self.assertAlmostEqual(value, 160.0 * 0.6)
        self.assertEqual(game.tallies, [(PARTNER, "grain", -4.0, True)])   # the partner's book closes on what really went
        self.assertAlmostEqual(game.purse, 1000.0 + (160.0 * 0.6 - 160.0) + 30.0)

    def test_with_no_book_the_cargo_is_settled_at_its_quote(self):
        game = Stub()
        landing(game)
        taking(game)
        game.settle_trader_cargo(None)
        self.assertEqual(sorted(game.settled), [(PARTNER, -10.0, 160.0), (PARTNER, 10.0, 100.0)])
        self.assertAlmostEqual(game.purse, 1000.0)
        self.assertEqual(game.tallies, [])

    def test_a_cargo_between_two_partners_settles_both_sides_and_touches_no_purse(self):
        game = Stub()
        game.note_cargo_leg(TRADER, "grain", 10.0, PARTNER, OTHER, 100.0, 160.0, 5.0, home="home")
        game.settle_trader_cargo({})
        self.assertEqual(sorted(game.settled), sorted([(OTHER, -10.0, 160.0), (PARTNER, 10.0, 100.0)]))
        self.assertAlmostEqual(game.purse, 1000.0)

    def test_the_trader_margin_follows_what_the_cargo_really_made(self):
        game = Stub()
        game.registry.get(TRADER).record.last_margin = 50.0
        landing(game)
        (leg,) = game.cargo_legs()
        game.settle_trader_cargo({leg["id"]: {"tonnes": 8.0, "money": 120.0}})
        self.assertAlmostEqual(game.registry.get(TRADER).record.last_margin, 50.0 - 40.0)


class ShippingNotesTheLeg(unittest.TestCase):
    def test_on_the_agent_economy_the_home_side_is_left_to_the_book(self):
        world = ShippingWorld(on_book=True)
        self.assertEqual(world.ship(TRADER, "grain", 5.0, PARTNER, "home"), (20.0, 50.0))
        self.assertEqual([note for note in world.notes if note[0] in ("sale", "purchase")], [])
        (leg,) = world.game.cargo_legs()
        self.assertEqual((leg["kind"], leg["tonnes"], leg["paid"], leg["received"], leg["carriage"]), ("in", 5.0, 20.0, 50.0, 10.0))

    def test_with_the_agent_economy_off_the_engines_own_market_still_takes_the_home_side(self):
        world = ShippingWorld(on_book=False)
        world.ship(TRADER, "grain", 5.0, "home", PARTNER)
        world.ship(TRADER, "grain", 3.0, PARTNER, "home")
        self.assertEqual([note for note in world.notes if note[0] in ("sale", "purchase")], [("purchase", 5.0), ("sale", 3.0)])
        self.assertEqual(sorted(leg["kind"] for leg in world.game.cargo_legs()), ["in", "out"])


if __name__ == "__main__":
    unittest.main()
