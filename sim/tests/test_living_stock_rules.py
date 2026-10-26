"""Living stock (Complaints/365, 366, 133): what is held, what a node's `holds` asks, the partner's quote and the charge,
and the year's breeding and loss. The living-stock module is built by `module_harness` with plain values for the views
it reads; each test calls one method of it (or one rule) and reads what it answered or sent. The whole-game checks were
test_living_stock_scenario and test_living_stock_trade_scenario."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import forward_living_stock
from sim.engine.foreign_economies import ForeignEconomiesMixin
from sim.engine.society_diffusion import DiffusionMixin
from sim.agents.api import edges
from sim.foreign_trade.api import SettleFlow
from sim.ledger.api import ChangeStock, PayEdge
from sim.living_stock import rules
from sim.living_stock.api import BuyStock, ChangeHeld, GrantOpeningStock
from sim.living_stock.module import LivingStock
from sim.living_stock.state import LivingStockWorld
from sim.living_stock import yearly
from sim.refusal import Refusal, cause_of
from sim.tests import module_harness
from sim.ui.proto import stock_purchases
from sim.world.material_units import tonnes_per_unit

EGGS, HERD = "eggs_kg", "herd_kg"


def _module(tonnes=None, nodes=None, civ=None, **views):
    """The module with `tonnes` held by commodity key (a material is its own key here), a node table and a civilisation."""
    tonnes = tonnes or {}
    plain = {"material_commodity": lambda material: material, "goods_stock": lambda key: tonnes.get(key, 0.0),
             "tree": (nodes or {}).get, "civilisation": civ or {}}
    plain.update(views)
    return module_harness.build(LivingStock, views=plain, world=LivingStockWorld())


class Held(unittest.TestCase):
    def test_stock_held_is_the_ledger_tonnes_counted_in_units(self):
        self.assertAlmostEqual(_module({EGGS: 0.0005}).stock_held(EGGS), 0.5)

    def test_rules_count_tonnes_in_units(self):
        self.assertAlmostEqual(rules.held_units(0.0005, 0.001), 0.5)

    def test_stock_status_names_the_units_short_of_what_a_node_holds_asks(self):
        module = _module({EGGS: 0.00001}, nodes={"silk": {"holds": {EGGS: 0.02}}, "plain": {}})
        (material, short), = module.stock_status("silk")["missing"]
        self.assertEqual(material, EGGS)
        self.assertAlmostEqual(short, 0.01)
        self.assertEqual(module.stock_status("plain")["missing"], [])

    def test_enough_held_leaves_nothing_missing(self):
        module = _module({EGGS: 0.001}, nodes={"silk": {"holds": {EGGS: 0.02}}})
        self.assertEqual(module.stock_status("silk")["missing"], [])

    def test_stock_holds_met_needs_every_material(self):
        module = _module({EGGS: 0.001})
        self.assertTrue(module.stock_holds_met({EGGS: 1.0}))
        self.assertFalse(module.stock_holds_met({EGGS: 1.0, HERD: 1.0}))

    def test_stock_gates_list_a_nodes_holds_and_a_civilisations_gate_on_it(self):
        module = _module({}, nodes={"collar": {"holds": {EGGS: 0.02}}}, civ={"needs_first": {
            "_note": "x", "draught": {"material": HERD, "units": 5.0, "ids": ["collar"], "node": "import"}}})
        self.assertEqual(module.stock_status("collar")["gates"], [
            {"material": EGGS, "needed": 0.02, "held": 0.0, "brought_by": None},
            {"material": HERD, "needed": 5.0, "held": 0.0, "brought_by": "import"}])

    def test_the_held_herds_are_those_held_rounded_for_the_screens(self):
        self.assertEqual(rules.held_herds({EGGS: 0.12345, HERD: 0.0}.get, [HERD, EGGS]), {EGGS: 0.123})

    def test_a_change_of_held_units_is_a_ledger_change_of_their_tonnes(self):
        module = _module()
        module.change_held(ChangeHeld(EGGS, 1.5))
        self.assertEqual(module_harness.sent(module),
                         [ChangeStock(EGGS, 1.5 * tonnes_per_unit(EGGS), legacy_snapshot_after_change=True)])

    def test_the_opening_holding_is_what_the_civilisation_held_at_its_date_notes_aside(self):
        module = _module(civ={"opening_stock": {"_note": "x", EGGS: 2.0, HERD: 7.0}})
        module.grant_opening_stock(GrantOpeningStock())
        self.assertEqual([(sent.commodity, sent.tonnes) for sent in module_harness.sent(module)],
                         [(EGGS, 2.0 * tonnes_per_unit(EGGS)), (HERD, 7.0 * tonnes_per_unit(HERD))])


class NeededRows(unittest.TestCase):
    def test_a_row_lists_only_the_stock_a_node_itself_holds_not_one_a_node_brings(self):
        gates = [{"material": EGGS, "needed": 0.02, "held": 0.5, "brought_by": None},
                 {"material": HERD, "needed": 5.0, "held": 0.0, "brought_by": "import"}]
        self.assertEqual(rules.needed_by(gates), [{"material": EGGS, "needed": 0.02, "held": 0.5}])


class UnheldStockBlocker(unittest.TestCase):
    def test_a_node_with_stock_short_is_refused_naming_the_stock(self):
        stand_in = types.SimpleNamespace(stock_missing=lambda node_id: [(EGGS, 0.02)])
        refused, why = forward_living_stock.check_unheld_stock(stand_in, "silk", {}, False, {}, True)
        self.assertFalse(refused)
        self.assertIn(EGGS, why)

    def test_a_node_with_nothing_short_is_not_blocked(self):
        stand_in = types.SimpleNamespace(stock_missing=lambda node_id: [])
        self.assertIsNone(forward_living_stock.check_unheld_stock(stand_in, "silk", {}, False, {}, True))


class NeedsFirst(unittest.TestCase):
    CIV = {"needs_first": {"draught": {"material": HERD, "units": 5.0, "ids": ["collar"], "node": "import"}}}

    def stand_in(self, met, done=()):
        return types.SimpleNamespace(civ=self.CIV, stock_holds_met=lambda stock: met,
                                     state=types.SimpleNamespace(projects=types.SimpleNamespace(done=set(done))))

    def test_a_gate_on_stock_not_held_names_the_node_that_lifts_it(self):
        self.assertEqual(DiffusionMixin.needs_first(self.stand_in(False), "collar")[0], "import")

    def test_holding_the_stock_lifts_the_gate_with_no_research(self):
        self.assertEqual(DiffusionMixin.needs_first(self.stand_in(True), "collar"), (None, None))

    def test_the_node_that_lifts_the_gate_done_lifts_it_too(self):
        self.assertEqual(DiffusionMixin.needs_first(self.stand_in(False, ["import"]), "collar"), (None, None))


class PartnerRefusal(unittest.TestCase):
    def stand_in(self, monopolies, government=None, gate=None):
        return types.SimpleNamespace(
            partner_gate_refusal=lambda partner: gate, partner_civ=lambda partner: {
                "name": "Han", "state_monopolies": monopolies},
            partner_government=lambda partner: government,
            goods_market=types.SimpleNamespace(acting_party_id="home"),
            state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=100)))

    def refusal(self, stand_in):
        return ForeignEconomiesMixin.partner_refusal(stand_in, "han", EGGS)

    def test_a_state_monopoly_on_the_good_holds_the_export_back(self):
        self.assertEqual(cause_of(self.refusal(self.stand_in([EGGS]))), "partner_export_held_back")

    def test_a_good_outside_the_monopolies_is_sold(self):
        self.assertIsNone(self.refusal(self.stand_in(["salt"])))

    def test_the_gate_refusal_comes_first(self):
        gate = Refusal("partner_not_reached", "not reached")
        self.assertEqual(cause_of(self.refusal(self.stand_in([], gate=gate))), "partner_not_reached")

    def test_markets_shut_to_the_buyer_refuse_with_the_reopening_year(self):
        government = types.SimpleNamespace(markets_closed_until=lambda party, year: 130, decision_policy=None,
                                           record=types.SimpleNamespace(state_monopolies=set()))
        self.assertEqual(cause_of(self.refusal(self.stand_in([], government))), "partner_market_shut")


class PurchaseQuote(unittest.TestCase):
    def module(self, refusal=None, per_tonne=2000.0, holds=1.0, trading=("han",), prices=None):
        def partner(civilization_id):
            return {"civ": {"opening_stock": {EGGS: holds}}, "stock_taken": {}, "has_government": True}
        return _module(partners=list(trading), partner=partner,
                       partner_refusal=lambda partner, material: refusal,
                       partner_landed_price=lambda partner, material: (prices or {}).get(partner, per_tonne))

    def quote(self, module, units=0.5, partner=None):
        return module.stock_purchase_quote(EGGS, units, partner)

    def test_the_cost_is_the_price_per_tonne_times_the_tonnes_bought(self):
        quote = self.quote(self.module(holds=1000.0), units=500.0)
        self.assertTrue(quote["ok"])
        self.assertAlmostEqual(quote["tonnes"], 0.5)
        self.assertAlmostEqual(quote["cost"], 1000.0)
        self.assertEqual(quote["partner"], "han")

    def test_a_refusing_partner_refuses_with_its_cause(self):
        quote = self.quote(self.module(refusal=Refusal("partner_export_held_back", "no")))
        self.assertEqual((quote["ok"], quote["cause"]), (False, "partner_export_held_back"))

    def test_buying_more_than_the_partner_holds_is_refused(self):
        quote = self.quote(self.module(holds=1.0), units=2.0)
        self.assertEqual((quote["ok"], quote["cause"]), (False, "partner_holds_less"))

    def test_what_smugglers_took_is_no_longer_for_sale(self):
        module = _module(partners=["han"], partner=lambda civilization_id: {
            "civ": {"opening_stock": {EGGS: 1.0}}, "stock_taken": {EGGS: 0.75}, "has_government": True},
            partner_refusal=lambda partner, material: None, partner_landed_price=lambda partner, material: 1.0)
        self.assertEqual(self.quote(module, units=0.5)["cause"], "partner_holds_less")

    def test_a_partner_not_trading_is_refused(self):
        self.assertEqual(self.quote(self.module(trading=()), partner="han")["cause"], "partner_not_trading")

    def test_an_amount_not_positive_is_refused(self):
        self.assertEqual(self.quote(self.module(), units=0)["cause"], "amount_not_positive")

    def test_with_two_sellers_the_cheaper_is_chosen(self):
        module = self.module(trading=("han", "india"), prices={"han": 3000.0, "india": 1000.0})
        self.assertEqual(self.quote(module)["partner"], "india")


class Settle(unittest.TestCase):
    QUOTE = BuyStock(EGGS, "han", 0.1, 5.0)

    def test_a_buyer_who_cannot_pay_is_charged_nothing_and_receives_nothing(self):
        module = _module(can_pay=lambda cost: False)
        self.assertEqual(cause_of(module.buy_stock(self.QUOTE)), "cannot_afford")
        self.assertEqual(module_harness.sent(module), [])

    def test_the_quoted_cost_is_paid_the_tonnes_delivered_and_the_partner_settled(self):
        module = _module(can_pay=lambda cost: True)
        self.assertIs(module.buy_stock(self.QUOTE), True)
        self.assertEqual(module_harness.sent(module), [
            PayEdge(edges.EDGE_MARKET, 5.0, "stock bought abroad"), ChangeStock(EGGS, 0.1), SettleFlow("han", 0.1, 5.0)])


class BuyCommand(unittest.TestCase):
    def test_a_refused_quote_is_answered_with_its_cause_and_charges_nothing(self):
        sent = []
        stand_in = _Capital(None, {"ok": False, "cause": "partner_holds_less", "error": "less"}, sent)
        reply = stock_purchases.buy_living_stock(stand_in, {"material": EGGS}, 1.0)
        self.assertEqual((reply["ok"], reply["cause"], sent), (False, "partner_holds_less", []))

    def test_a_good_quote_settles_and_reports_what_was_paid_and_held(self):
        purse = {"capital": 100.0}
        quote = {"ok": True, "material": EGGS, "units": 2.0, "partner": "han", "cost": 30.0, "tonnes": 0.002}
        reply = stock_purchases.buy_living_stock(_Capital(purse, quote, []), {"material": EGGS}, 2.0)
        self.assertEqual((reply["ok"], reply["paid"], reply["bought_units"], reply["held_now"]),
                         (True, 30.0, 2.0, 2.0))

    def test_a_buyer_who_cannot_pay_is_told_so_and_nothing_changes(self):
        purse = {"capital": 100.0}
        quote = {"ok": True, "material": EGGS, "units": 2.0, "partner": "han", "cost": 300.0, "tonnes": 0.002}
        stand_in = _Capital(purse, quote, [], answer=Refusal("cannot_afford", "no"))
        reply = stock_purchases.buy_living_stock(stand_in, {"material": EGGS}, 2.0)
        self.assertFalse(reply["ok"])
        self.assertEqual(purse["capital"], 100.0)

    def test_no_material_named_is_refused(self):
        self.assertFalse(stock_purchases.buy_living_stock(types.SimpleNamespace(), {}, 1.0)["ok"])


class _Capital:
    """A game as the purchase screen reads it: a purse, a quote view, a held view and a send that charges the quote."""

    def __init__(self, purse, quote, sent, answer=True):
        self.purse, self.quote, self.sent, self.answer = purse, quote, sent, answer

    @property
    def capital(self):
        return self.purse["capital"]

    def spending_power(self, kind):
        return 100.0

    def view(self, name):
        return (lambda *arguments: self.quote) if name == "stock_purchase_quote" else _Held()

    def send(self, command):
        self.sent.append(command)
        if self.answer is True:
            self.purse["capital"] -= command.cost
        return self.answer


class _Held:
    def __getitem__(self, material):
        return 2.0


class YearsTurn(unittest.TestCase):
    RATES = {HERD: {"natural_increase": 0.1, "annual_loss": 0.02, "breeding_minimum_units": 10.0},
             EGGS: {"natural_increase": 0.0, "annual_loss": 0.5, "breeding_minimum_units": 1.0}}

    def turn(self, held):
        tonnes = {material: units * tonnes_per_unit(material) for material, units in held.items()}
        module = _module(tonnes, stock_land={"place": None, "pasture_kg": 0.0},
                         endemic_stock_loss=lambda place, species: 0.0, nursery_room_units=lambda *arguments: None)
        with mock.patch.object(yearly, "stock_rates", lambda: self.RATES):
            module.step_living_stock("founder")
        changes = {}
        for sent in module_harness.sent(module):
            material = HERD if sent.commodity == HERD else EGGS
            changes[material] = changes.get(material, 0.0) + sent.tonnes / tonnes_per_unit(material)
        return changes

    def test_a_herd_above_its_minimum_gains_its_increase_less_its_loss(self):
        self.assertAlmostEqual(self.turn({HERD: 100.0})[HERD], 100.0 * (0.1 - 0.02))

    def test_a_herd_below_the_breeding_minimum_only_suffers_its_loss(self):
        self.assertAlmostEqual(self.turn({HERD: 5.0})[HERD], -5.0 * 0.02)

    def test_stored_eggs_are_lost_and_not_multiplied(self):
        self.assertAlmostEqual(self.turn({EGGS: 1.0})[EGGS], -0.5)

    def test_a_society_holding_no_stock_gains_none(self):
        self.assertEqual(self.turn({}), {})

    def test_the_societys_own_head_follows_the_herd_it_is_part_of(self):
        self.assertAlmostEqual(rules.society_herd_after(40.0, 100.0, 108.0), 43.2)
        self.assertAlmostEqual(rules.society_herd_after(500.0, 100.0, 108.0), 108.0)


if __name__ == "__main__":
    unittest.main()
