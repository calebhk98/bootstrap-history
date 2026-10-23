"""Living stock (Complaints/365, 366, 133): what is held, what a node's `holds` asks, the partner's refusal and quote
charged, and the year's breeding and loss. Each test calls one method or function on a stand-in carrying only what it
reads; the whole-game checks were test_living_stock_scenario and test_living_stock_trade_scenario."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import living_stock, living_stock_yearly
from sim.engine.living_stock_trade import LivingStockTradeMixin
from sim.engine.living_stock_yearly import LivingStockYearlyMixin
from sim.engine.foreign_economies import ForeignEconomiesMixin
from sim.engine.society_diffusion import DiffusionMixin
from sim.refusal import Refusal, cause_of
from sim.ui.proto import stock_purchases

EGGS, HERD = "eggs_kg", "herd_kg"


class _Holder(living_stock.LivingStockMixin):
    """Held tonnes by key, a node table and a civilisation."""

    def __init__(self, tonnes=None, nodes=None, civ=None):
        self.tonnes, self.nodes, self.civ = tonnes or {}, nodes or {}, civ or {}
        self.changes = []

    def _stock_key(self, material):
        return material

    def material_stock_t(self, key):
        return self.tonnes.get(key, 0.0)

    def change_stock(self, material, units):
        self.changes.append((material, units))


class Held(unittest.TestCase):
    def test_stock_held_is_the_ledger_tonnes_counted_in_units(self):
        self.assertAlmostEqual(_Holder({EGGS: 0.0005}).stock_held(EGGS), 0.5)

    def test_stock_missing_names_the_units_short_of_what_a_node_holds_asks(self):
        holder = _Holder({EGGS: 0.00001}, nodes={"silk": {"holds": {EGGS: 0.02}}, "plain": {}})
        (material, short), = holder.stock_missing("silk")
        self.assertEqual(material, EGGS)
        self.assertAlmostEqual(short, 0.01)
        self.assertEqual(holder.stock_missing("plain"), [])

    def test_enough_held_leaves_nothing_missing(self):
        self.assertEqual(_Holder({EGGS: 0.001}, nodes={"silk": {"holds": {EGGS: 0.02}}}).stock_missing("silk"), [])

    def test_stock_holds_met_needs_every_material(self):
        holder = _Holder({EGGS: 0.001})
        self.assertTrue(holder.stock_holds_met({EGGS: 1.0}))
        self.assertFalse(holder.stock_holds_met({EGGS: 1.0, HERD: 1.0}))

    def test_stock_gates_list_a_nodes_holds_and_a_civilisations_gate_on_it(self):
        holder = _Holder({}, nodes={"collar": {"holds": {EGGS: 0.02}}}, civ={"needs_first": {
            "_note": "x", "draught": {"material": HERD, "units": 5.0, "ids": ["collar"], "node": "import"}}})
        self.assertEqual(holder.stock_gates("collar"), [
            {"material": EGGS, "needed": 0.02, "held": 0.0, "brought_by": None},
            {"material": HERD, "needed": 5.0, "held": 0.0, "brought_by": "import"}])

    def test_grant_stock_adds_the_units_to_the_ledger(self):
        holder = _Holder()
        holder.grant_stock(EGGS, 1.5)
        self.assertEqual(holder.changes, [(EGGS, 1.5)])

    def test_the_opening_holding_is_what_the_civilisation_held_at_its_date_notes_aside(self):
        holder = _Holder(civ={"opening_stock": {"_note": "x", EGGS: 2.0, HERD: 7.0}})
        holder.grant_opening_stock()
        self.assertEqual(holder.changes, [(EGGS, 2.0), (HERD, 7.0)])


class NeededRows(unittest.TestCase):
    def test_a_row_lists_only_the_stock_a_node_itself_holds_not_one_a_node_brings(self):
        gates = [{"material": EGGS, "needed": 0.02, "held": 0.5, "brought_by": None},
                 {"material": HERD, "needed": 5.0, "held": 0.0, "brought_by": "import"}]
        stand_in = types.SimpleNamespace(stock_gates=lambda node_id: gates)
        self.assertEqual(LivingStockYearlyMixin.stock_needed_by(stand_in, "n"),
                         [{"material": EGGS, "needed": 0.02, "held": 0.5}])


class UnheldStockBlocker(unittest.TestCase):
    def test_a_node_with_stock_short_is_refused_naming_the_stock(self):
        stand_in = types.SimpleNamespace(stock_missing=lambda node_id: [(EGGS, 0.02)])
        refused, why = living_stock.check_unheld_stock(stand_in, "silk", {}, False, {}, True)
        self.assertFalse(refused)
        self.assertIn(EGGS, why)

    def test_a_node_with_nothing_short_is_not_blocked(self):
        stand_in = types.SimpleNamespace(stock_missing=lambda node_id: [])
        self.assertIsNone(living_stock.check_unheld_stock(stand_in, "silk", {}, False, {}, True))


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
    def stand_in(self, refusal=None, per_tonne=2000.0, holds=1.0, trading=("han",)):
        return types.SimpleNamespace(
            partner_countries=lambda: list(trading), partner_refusal=lambda partner, material: refusal,
            partner_quote_per_tonne=lambda material, partner: per_tonne,
            _partner_holding=lambda partner, material: holds)

    def quote(self, stand_in, units=0.5, partner=None):
        return LivingStockTradeMixin.stock_purchase_quote(stand_in, EGGS, units, partner)

    def test_the_cost_is_the_price_per_tonne_times_the_tonnes_bought(self):
        quote = self.quote(self.stand_in(holds=1000.0), units=500.0)
        self.assertTrue(quote["ok"])
        self.assertAlmostEqual(quote["tonnes"], 0.5)
        self.assertAlmostEqual(quote["cost"], 1000.0)
        self.assertEqual(quote["partner"], "han")

    def test_a_refusing_partner_refuses_with_its_cause(self):
        quote = self.quote(self.stand_in(refusal=Refusal("partner_export_held_back", "no")))
        self.assertEqual((quote["ok"], quote["cause"]), (False, "partner_export_held_back"))

    def test_buying_more_than_the_partner_holds_is_refused(self):
        quote = self.quote(self.stand_in(holds=1.0), units=2.0)
        self.assertEqual((quote["ok"], quote["cause"]), (False, "partner_holds_less"))

    def test_a_partner_not_trading_is_refused(self):
        self.assertEqual(self.quote(self.stand_in(trading=()), partner="han")["cause"], "partner_not_trading")

    def test_an_amount_not_positive_is_refused(self):
        self.assertEqual(self.quote(self.stand_in(), units=0)["cause"], "amount_not_positive")

    def test_with_two_sellers_the_cheaper_is_chosen(self):
        prices = {"han": 3000.0, "india": 1000.0}
        stand_in = self.stand_in(trading=("han", "india"))
        stand_in.partner_quote_per_tonne = lambda material, partner: prices[partner]
        self.assertEqual(self.quote(stand_in)["partner"], "india")


class BuyAndSettle(unittest.TestCase):
    def test_buy_returns_the_units_when_the_quote_is_good_and_settled(self):
        stand_in = types.SimpleNamespace(stock_purchase_quote=lambda *args: {"ok": True, "units": 0.1},
                                         settle_stock_purchase=lambda quote: True)
        self.assertEqual(LivingStockTradeMixin.buy_stock_from_partner(stand_in, EGGS, 0.1, "han"), 0.1)

    def test_buy_returns_nothing_for_a_refused_quote_and_settles_nothing(self):
        settled = []
        stand_in = types.SimpleNamespace(stock_purchase_quote=lambda *args: {"ok": False},
                                         settle_stock_purchase=settled.append)
        self.assertEqual(LivingStockTradeMixin.buy_stock_from_partner(stand_in, EGGS, 0.1, "han"), 0.0)
        self.assertEqual(settled, [])

    def test_buy_returns_nothing_when_the_buyer_cannot_pay(self):
        stand_in = types.SimpleNamespace(stock_purchase_quote=lambda *args: {"ok": True, "units": 0.1},
                                         settle_stock_purchase=lambda quote: False)
        self.assertEqual(LivingStockTradeMixin.buy_stock_from_partner(stand_in, EGGS, 0.1, "han"), 0.0)

    def test_a_buyer_who_cannot_pay_is_charged_nothing_and_receives_nothing(self):
        imports = []
        market = types.SimpleNamespace(acting=types.SimpleNamespace(can_pay=lambda money: False),
                                       settle_import=lambda *args: imports.append(args))
        stand_in = types.SimpleNamespace(goods_market=market)
        quote = {"cost": 5.0, "material": EGGS, "tonnes": 0.1, "partner": "han"}
        self.assertFalse(LivingStockTradeMixin.settle_stock_purchase(stand_in, quote))
        self.assertEqual(imports, [])

    def test_the_goods_market_is_charged_the_quote_for_the_tonnes_delivered(self):
        imports = []
        market = types.SimpleNamespace(
            acting=types.SimpleNamespace(can_pay=lambda money: True), home_unit_price=lambda material: None,
            settle_import=lambda *args: imports.append(args))
        stand_in = types.SimpleNamespace(
            goods_market=market, _stock_key=lambda material: material,
            partner_civ=lambda partner: {"coin_standard": {"material": "silver_kg", "kg_per_unit": 0.01}})
        quote = {"cost": 5.0, "material": EGGS, "tonnes": 0.1, "partner": "han"}
        self.assertTrue(LivingStockTradeMixin.settle_stock_purchase(stand_in, quote))
        self.assertEqual(imports, [(market.acting, EGGS, 0.1, 5.0, "stock bought abroad")])


class BuyCommand(unittest.TestCase):
    def test_a_refused_quote_is_answered_with_its_cause_and_charges_nothing(self):
        settled = []
        stand_in = types.SimpleNamespace(
            stock_purchase_quote=lambda *args: {"ok": False, "cause": "partner_holds_less", "error": "less"},
            settle_stock_purchase=settled.append)
        reply = stock_purchases.buy_living_stock(stand_in, {"material": EGGS}, 1.0)
        self.assertEqual((reply["ok"], reply["cause"], settled), (False, "partner_holds_less", []))

    def test_a_good_quote_settles_and_reports_what_was_paid_and_held(self):
        purse = {"capital": 100.0}
        quote = {"ok": True, "material": EGGS, "units": 2.0, "partner": "han", "cost": 30.0}

        def settle(offered):
            purse["capital"] -= offered["cost"]
            return True
        stand_in = _Capital(purse, quote, settle)
        reply = stock_purchases.buy_living_stock(stand_in, {"material": EGGS}, 2.0)
        self.assertEqual((reply["ok"], reply["paid"], reply["bought_units"], reply["held_now"]),
                         (True, 30.0, 2.0, 2.0))

    def test_no_material_named_is_refused(self):
        self.assertFalse(stock_purchases.buy_living_stock(types.SimpleNamespace(), {}, 1.0)["ok"])


class _Capital:
    def __init__(self, purse, quote, settle):
        self.purse, self.quote, self.settle = purse, quote, settle

    @property
    def capital(self):
        return self.purse["capital"]

    def stock_purchase_quote(self, *args):
        return self.quote

    def settle_stock_purchase(self, quote):
        return self.settle(quote)

    def stock_held(self, material):
        return 2.0


class YearsTurn(unittest.TestCase):
    RATES = {HERD: {"natural_increase": 0.1, "annual_loss": 0.02, "breeding_minimum_units": 10.0},
             EGGS: {"natural_increase": 0.0, "annual_loss": 0.5, "breeding_minimum_units": 1.0}}

    def turn(self, held):
        changes = {}

        class Holder(LivingStockYearlyMixin):
            society_herds = {}

            def stock_held(self, material):
                return held.get(material, 0.0)

            def change_stock(self, material, units):
                changes[material] = changes.get(material, 0.0) + units

            def stock_place(self):
                return None

            def pasture_room_kg(self, place, pastured):
                return None

            def endemic_stock_loss(self, rates, place=None):
                return 0.0

            def nursery_room_units(self, material, place):
                return None

            def pay_growth_labour(self, material, units):
                return 1.0

        with mock.patch.object(living_stock_yearly, "stock_rates", lambda: self.RATES):
            Holder().step_living_stock()
        return changes

    def test_a_herd_above_its_minimum_gains_its_increase_less_its_loss(self):
        self.assertAlmostEqual(self.turn({HERD: 100.0})[HERD], 100.0 * (0.1 - 0.02))

    def test_a_herd_below_the_breeding_minimum_only_suffers_its_loss(self):
        self.assertAlmostEqual(self.turn({HERD: 5.0})[HERD], -5.0 * 0.02)

    def test_stored_eggs_are_lost_and_not_multiplied(self):
        self.assertAlmostEqual(self.turn({EGGS: 1.0})[EGGS], -0.5)

    def test_a_society_holding_no_stock_gains_none(self):
        self.assertEqual(self.turn({}), {})


if __name__ == "__main__":
    unittest.main()
