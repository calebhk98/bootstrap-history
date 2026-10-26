"""Complaint 598: a state's tariff and embargo on another country act in the markets. A tariff raises the delivered price
of an import and reaches the state's treasury; an embargo stops the crossing; merchants see the charge in their route
arithmetic so trade diverts to an untaxed source, and a change mid-game is seen at once. Small fixtures: stub games,
nothing builds a whole game."""

QUICK_TOPIC = True

import contextlib
import math
import types
import unittest

from sim.agents import relations
from sim.agents.trader import route_terms
from sim.economy.tariffs import duty_transfers
from sim.economy.types import EDGE_EXTERNAL
from sim.engine import trade_duty
from sim.engine.agents_port_trade import TradeView
from sim.engine.mod_stores import StoreBook
from sim.engine.state import FounderState, HouseholdState, ProjectsState, SimulationState
from sim.engine.state_seat import bind_seat, seat_from_template
from sim.ui.proto import command_registry
import sim.ui.proto.dispatch  # noqa: F401  (registers every command)
from sim.ui.proto.seat_address import run_as_seat

from .test_no_seller_no_price import _Offers, _fake_sim


def _stores():
    return StoreBook({})


def _priced_game():
    sim = _fake_sim(home_prices={}, partner_makes={"cassia_kg"}, partner_prices={"cassia_kg": 50.0})
    sim.stores, sim.civ = _stores(), {"id": "rome"}
    return sim


class TariffOnLandedPrice(unittest.TestCase):

    def test_a_tariff_adds_its_share_of_the_partners_cost_to_the_landed_price(self):
        sim = _priced_game()
        offers = _Offers(sim)
        before = offers.landed_price("cassia_kg", "partner", offers.route)
        relations.set_side(sim.stores, "rome", "partner", tariff=0.2)
        after = offers.landed_price("cassia_kg", "partner", offers.route)
        self.assertAlmostEqual(after - before, 0.2 * 50.0)
        self.assertAlmostEqual(offers.landed_price("cassia_kg", "partner", offers.route, with_duty=False), before)

    def test_the_partners_tariff_on_us_does_not_raise_what_we_pay(self):
        sim = _priced_game()
        offers = _Offers(sim)
        before = offers.landed_price("cassia_kg", "partner", offers.route)
        relations.set_side(sim.stores, "partner", "rome", tariff=0.5)
        self.assertAlmostEqual(offers.landed_price("cassia_kg", "partner", offers.route), before)

    def test_an_embargo_leaves_no_cross_border_offer(self):
        sim = _priced_game()
        offers = _Offers(sim)
        self.assertEqual(offers.offered_by("cassia_kg"), "partner")
        relations.set_side(sim.stores, "rome", "partner", embargo=True)
        self.assertIsNone(offers.landed_price("cassia_kg", "partner", offers.route))
        self.assertIsNone(offers.offered_by("cassia_kg"))
        self.assertIsNone(offers.unit_price("cassia_kg"))

    def test_a_change_mid_game_is_seen_without_a_stale_price(self):
        sim = _priced_game()
        offers = _Offers(sim)
        open_price = offers.household_prices()["cassia_kg"]
        relations.set_side(sim.stores, "rome", "partner", tariff=0.2)
        taxed_price = offers.household_prices()["cassia_kg"]
        self.assertAlmostEqual(taxed_price - open_price, 10.0)
        relations.set_side(sim.stores, "rome", "partner", tariff=None)
        self.assertAlmostEqual(offers.household_prices()["cassia_kg"], open_price)
        relations.set_side(sim.stores, "rome", "partner", embargo=True)
        self.assertNotIn("cassia_kg", offers.household_prices())
        relations.set_side(sim.stores, "rome", "partner", embargo=False)
        self.assertAlmostEqual(offers.household_prices()["cassia_kg"], open_price)


class TheStateCollects(unittest.TestCase):

    def test_the_duty_inside_what_was_paid_goes_from_the_border_to_the_treasury(self):
        transfers = duty_transfers({"cassia_kg": 0.25}, {("merchant", "cassia_kg"): 80.0, ("house", "cassia_kg"): 20.0,
                                                         ("merchant", "wheat_kg"): 40.0}, "state:rome", "denarius")
        self.assertEqual([(each.payer, each.payee, each.amount) for each in transfers],
                         [(EDGE_EXTERNAL, "state:rome", 25.0)])

    def test_a_good_with_no_tariff_carries_no_duty(self):
        self.assertEqual(duty_transfers({}, {("merchant", "wheat_kg"): 40.0}, "state:rome", "denarius"), [])


class LedgerTalliesTheBorder(unittest.TestCase):

    def test_only_money_paid_straight_to_the_border_carries_the_tariff(self):
        from sim.economy.types import Transfer
        from sim.economy.year_ledger import YearLedger
        ledger = YearLedger(import_accounts=frozenset({"importer"}))
        ledger.note_postings([Transfer("house", EDGE_EXTERNAL, "coin", 30.0, "sale of silk"),
                              Transfer("house", "importer", "coin", 12.0, "sale of silk")], "sales")
        self.assertEqual(ledger.border_imports_paid, {("house", "silk"): 30.0})
        self.assertEqual(sum(ledger.imports_paid.values()), 42.0)


class _Sim:
    """The home state, its stores and the partners' prices a trader view asks about."""

    def __init__(self, prices):
        self.stores, self.civ = _stores(), {"id": "rome"}
        self.prices = prices

    def foreign_economies(self):
        return [place for place in self.prices if place != "rome"]

    def _foreign_economy_facts(self, partner):
        return {"freight_per_tonne": 3.0}


class _View(TradeView):
    def __init__(self, sim):
        self._sim = sim

    def price_at(self, material, place):
        return self._sim.prices[place]


class MerchantsSeeTheCharge(unittest.TestCase):

    def setUp(self):
        # two partners sell the same good; the cheaper one is taxed enough to be the dearer to bring home
        self.sim = _Sim({"rome": 20.0, "han": 8.0, "parthia": 9.0})
        self.view = _View(self.sim)

    def test_a_tariff_is_part_of_what_a_cargo_costs_to_bring_in(self):
        before = self.view.freight_between("han", "rome", "cassia_kg", 2.0)
        relations.set_side(self.sim.stores, "rome", "han", tariff=0.5)
        after = self.view.freight_between("han", "rome", "cassia_kg", 2.0)
        self.assertAlmostEqual(after - before, 0.5 * 8.0 * 2.0)
        self.assertAlmostEqual(self.view.duty_between("han", "rome", "cassia_kg", 2.0), 8.0)

    def test_an_embargoed_crossing_costs_without_limit_and_ships_nothing(self):
        relations.set_side(self.sim.stores, "rome", "han", embargo=True)
        self.assertEqual(self.view.freight_between("han", "rome", "cassia_kg", 1.0), math.inf)
        self.assertEqual(self.view.ship("trader", "cassia_kg", 1.0, "han", "rome"), (0.0, 0.0))

    def test_trade_diverts_to_the_untaxed_source(self):
        world = self.view
        gains = lambda source: world.price_at("cassia_kg", "rome") - world.price_at("cassia_kg", source) - world.freight_between(source, "rome", "cassia_kg", 1.0)   # noqa: E731
        self.assertGreater(gains("han"), gains("parthia"))
        relations.set_side(self.sim.stores, "rome", "han", tariff=0.5)
        self.assertLess(gains("han"), gains("parthia"))

    def test_the_traders_route_terms_carry_the_duty(self):
        terms = route_terms(self.view, "han", "rome", "cassia_kg")
        relations.set_side(self.sim.stores, "rome", "han", tariff=0.5)
        taxed = route_terms(self.view, "han", "rome", "cassia_kg")
        self.assertAlmostEqual(taxed["freight"] - terms["freight"], 0.5 * 8.0)
        self.assertLess(taxed["gain"], terms["gain"])
        relations.set_side(self.sim.stores, "rome", "han", embargo=True)
        embargoed = route_terms(self.view, "han", "rome", "cassia_kg")
        self.assertLessEqual(embargoed["gain"], -math.inf)

    def test_the_other_way_round_it_is_the_partners_state_that_charges(self):
        relations.set_side(self.sim.stores, "han", "rome", tariff=0.25)
        self.assertAlmostEqual(self.view.duty_between("rome", "han", "cassia_kg", 1.0), 0.25 * 20.0)
        self.assertEqual(self.view.duty_between("han", "rome", "cassia_kg", 1.0), 0.0)


class TradeDutyReads(unittest.TestCase):

    def test_a_game_without_stores_charges_nothing(self):
        self.assertEqual(trade_duty.terms(types.SimpleNamespace(), "rome", "han"), (0.0, False))

    def test_a_country_charges_nothing_on_itself(self):
        sim = _Sim({})
        relations.set_side(sim.stores, "rome", "rome", tariff=0.5)
        self.assertEqual(trade_duty.terms(sim, "rome", "rome"), (0.0, False))


class Game:
    """The root state with the real seat rebinding, as in the relations store topic."""

    def __init__(self):
        self.state = SimulationState(household=HouseholdState(capital=100.0), projects=ProjectsState(), founder=FounderState())
        self.state.seats["northern"] = seat_from_template({"country": "han"}, 50.0, {})
        self.session_seat = None
        self.year = 100
        self.civ = {"id": "rome"}

    @property
    def stores(self):
        return StoreBook(self.state.stores)

    def partner_countries(self):
        return ["han", "parthia"]

    @contextlib.contextmanager
    def act_as(self, seat_id):
        previous = self.state.acting_seat
        bind_seat(self.state, seat_id)
        try:
            yield self
        finally:
            bind_seat(self.state, previous)


class SettingThem(unittest.TestCase):

    def setUp(self):
        self.game = Game()
        self.handlers = command_registry.handlers()

    def send(self, cmd):
        return run_as_seat(self.game, cmd, lambda command: self.handlers[command["cmd"]](self.game, {}, command, None))

    def test_a_seat_sets_its_own_countrys_tariff_and_embargo(self):
        reply = self.send({"cmd": "set_relation", "text": "parthia term tariff 0.15"})
        self.assertTrue(reply["ok"])
        self.assertEqual(relations.tariff_on(self.game.stores, "rome", "parthia"), 0.15)
        self.assertTrue(self.send({"cmd": "set_relation", "text": "parthia embargo on"})["ok"])
        self.assertTrue(relations.embargoes(self.game.stores, "rome", "parthia"))
        self.assertTrue(self.send({"cmd": "set_relation", "text": "parthia embargo off"})["ok"])
        self.assertFalse(relations.embargoes(self.game.stores, "rome", "parthia"))
        self.assertTrue(self.send({"cmd": "set_relation", "with": "parthia", "term": "tariff", "value": 0})["ok"])
        self.assertEqual(relations.read(self.game.stores, "rome", "parthia")["tariff"], None)

    def test_another_seat_sets_only_its_own_side(self):
        reply = self.send({"cmd": "set_relation", "as": "northern", "text": "rome term tariff 0.3"})
        self.assertTrue(reply["ok"])
        self.assertEqual(relations.tariff_on(self.game.stores, "han", "rome"), 0.3)
        self.assertEqual(relations.tariff_on(self.game.stores, "rome", "han"), 0.0)

    def test_a_tariff_that_is_not_a_share_is_refused_with_a_cause(self):
        for value in (-0.1, 99, "high"):
            reply = self.send({"cmd": "set_relation", "with": "han", "term": "tariff", "value": value})
            self.assertFalse(reply["ok"])
            self.assertEqual(reply["cause"], "bad_tariff")
        self.assertEqual(relations.tariff_on(self.game.stores, "rome", "han"), 0.0)

    def test_an_embargo_word_that_is_neither_on_nor_off_is_refused_with_a_cause(self):
        reply = self.send({"cmd": "set_relation", "with": "han", "embargo": "maybe"})
        self.assertEqual(reply["cause"], "unknown_embargo")
        self.assertFalse(relations.embargoes(self.game.stores, "rome", "han"))


if __name__ == "__main__":
    unittest.main()
