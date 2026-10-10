"""The state's revenue: forms from civ data, assessed per payer, paid by transfer, arrears not overdrafts."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.economy.accounts import Book
from sim.economy.taxes import TaxForm, YearFacts, assess, forms_from_civ_data
from sim.economy.types import EDGE_MINT, EDGE_PRODUCTION, GoodsMove, Transfer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
with open(os.path.join(ROOT, "data", "civilizations", "rome_100ad.json"), encoding="utf-8") as handle:
    ROME = json.load(handle)
FORMS = forms_from_civ_data(ROME["state_revenue"])
GRAIN = FORMS[0].paid_in
PRICES = {GRAIN: 2.0}
STATE = "state"


def facts_with(book_cash=None, **overrides):
    values = dict(
        currency="coin",
        output={("farm_a", GRAIN): 1000.0, ("farm_b", GRAIN): 400.0, ("smith", "tools"): 50.0},
        producer_tile={"farm_a": "t1", "farm_b": "t2", "smith": "t1"},
        working_people={"peasants": 300.0, "artisans": 100.0},
        wage_per_labour_year={"peasants": 10.0, "artisans": 20.0},
        imports_paid={("trader_a", "silk"): 500.0, ("trader_a", "spice"): 100.0},
        exports_received={("trader_b", "tools"): 200.0},
        cash=book_cash if book_cash is not None else {
            "peasants": 1e6, "artisans": 1e6, "trader_a": 1e6, "trader_b": 1e6, "farm_a": 1e6, "farm_b": 1e6})
    values.update(overrides)
    return YearFacts(**values)


def by_form(assessments):
    return {entry.form: entry for entry in assessments}


class FormsTests(unittest.TestCase):
    def test_forms_are_read_from_the_civilisations_data(self):
        self.assertEqual([form.name for form in FORMS], [entry["form"] for entry in ROME["state_revenue"]
                                                         if entry["basis"] != "land_value"])
        self.assertEqual(FORMS[0].paid_in, "wheat_kg")
        self.assertEqual(FORMS[1].paid_in, "")


class ProvinceTests(unittest.TestCase):
    def test_a_form_on_the_harvest_is_levied_only_on_the_tiles_it_covers(self):
        form = TaxForm("tithe", "harvest", 0.1, GRAIN, None, frozenset({"t2"}))
        _transfers, moves, _assessments = assess((form,), facts_with(), STATE, PRICES)
        self.assertEqual({move.giver for move in moves}, {"farm_a"})
        named = TaxForm("tithe", "harvest", 0.1, GRAIN, frozenset({"t2"}))
        _transfers, moves, _assessments = assess((named,), facts_with(), STATE, PRICES)
        self.assertEqual({move.giver for move in moves}, {"farm_b"})

    def test_forms_on_actors_purses_are_left_to_the_actor_layer(self):
        data = [{"form": "a", "basis": "land_value", "rate": 0.01, "tiles": ["t1"]},
                {"form": "b", "basis": "harvest", "rate": 0.1, "paid_in": GRAIN, "except_tiles": ["t1"]}]
        forms = forms_from_civ_data(data)
        self.assertEqual([form.name for form in forms], ["b"])
        self.assertEqual(forms[0].except_tiles, frozenset({"t1"}))


class InKindTests(unittest.TestCase):
    def test_land_tax_moves_a_tenth_of_each_growers_grain_and_creates_none(self):
        facts = facts_with()
        _transfers, moves, assessments = assess(FORMS, facts, STATE, PRICES)
        taken = {move.giver: move for move in moves}
        self.assertAlmostEqual(taken["farm_a"].quantity, 100.0)
        self.assertAlmostEqual(taken["farm_b"].quantity, 40.0)
        self.assertEqual(taken["farm_a"].tile, "t1")
        self.assertNotIn("smith", taken)
        book = Book()
        for (producer, good), quantity in facts.output.items():
            book.move(GoodsMove(EDGE_PRODUCTION, producer, good, facts.producer_tile[producer], quantity, "harvest"))
        before = book.goods_total(GRAIN)
        book.move_many(moves)
        self.assertAlmostEqual(book.goods_total(GRAIN), before)
        self.assertAlmostEqual(book.stock(STATE, GRAIN, "t1"), 100.0)
        self.assertAlmostEqual(by_form(assessments)["land_tax"].collected_quantity, 140.0)

    def test_a_grower_who_no_longer_holds_the_grain_owes_arrears_in_kind(self):
        facts = facts_with(held_goods={("farm_a", GRAIN): 30.0, ("farm_b", GRAIN): 400.0})
        _transfers, moves, assessments = assess(FORMS, facts, STATE, PRICES)
        taken = {move.giver: move.quantity for move in moves}
        self.assertAlmostEqual(taken["farm_a"], 30.0)
        arrears = by_form(assessments)["land_tax"].arrears
        self.assertEqual([(entry.payer, entry.good) for entry in arrears], [("farm_a", GRAIN)])
        self.assertAlmostEqual(arrears[0].amount, 70.0)


class MoneyTests(unittest.TestCase):
    def test_poll_tax_falls_on_cohorts_by_working_people_at_their_wage(self):
        transfers, _moves, _assessments = assess(FORMS, facts_with(), STATE, PRICES)
        paid = {transfer.payer: transfer.amount for transfer in transfers if transfer.purpose == "tax:poll_tax"}
        rate = FORMS[1].rate
        self.assertAlmostEqual(paid["peasants"], rate * 300.0 * 10.0)
        self.assertAlmostEqual(paid["artisans"], rate * 100.0 * 20.0)

    def test_duties_fall_on_importers_and_exporters_by_their_trade(self):
        transfers, _moves, _assessments = assess(FORMS, facts_with(), STATE, PRICES)
        imports = {t.payer: t.amount for t in transfers if t.purpose == "tax:import_duty"}
        exports = {t.payer: t.amount for t in transfers if t.purpose == "tax:export_duty"}
        self.assertAlmostEqual(imports["trader_a"], FORMS[2].rate * 600.0)
        self.assertEqual(list(imports), ["trader_a"])
        self.assertAlmostEqual(exports["trader_b"], FORMS[3].rate * 200.0)
        self.assertEqual(list(exports), ["trader_b"])

    def test_transfers_post_to_the_book_and_the_state_gains_exactly_what_payers_lose(self):
        facts = facts_with()
        book = Book()
        for agent, amount in facts.cash.items():
            book.transfer(Transfer(EDGE_MINT, agent, "coin", amount, "opening"))
        transfers, _moves, _assessments = assess(FORMS, facts, STATE, PRICES)
        book.transfer_many(transfers)
        self.assertAlmostEqual(book.balance(STATE, "coin"), sum(t.amount for t in transfers))
        self.assertAlmostEqual(book.money_supply("coin"), sum(facts.cash.values()))

    def test_a_poor_payer_owes_arrears_and_is_never_overdrawn(self):
        facts = facts_with(book_cash={"peasants": 5.0, "artisans": 1e6, "trader_a": 0.0, "trader_b": 1e6})
        transfers, _moves, assessments = assess(FORMS, facts, STATE, PRICES)
        spent = {}
        for transfer in transfers:
            spent[transfer.payer] = spent.get(transfer.payer, 0.0) + transfer.amount
        self.assertLessEqual(spent["peasants"], 5.0 + 1e-9)
        self.assertNotIn("trader_a", spent)
        poll = by_form(assessments)["poll_tax"]
        self.assertAlmostEqual(poll.arrears[0].amount, FORMS[1].rate * 3000.0 - 5.0)
        duty = by_form(assessments)["import_duty"]
        self.assertAlmostEqual(duty.arrears[0].amount, FORMS[2].rate * 600.0)
        self.assertAlmostEqual(duty.collected_value, 0.0)

    def test_one_purse_pays_several_forms_without_going_below_zero(self):
        both = (TaxForm("first", "coin_stock", 0.6), TaxForm("second", "coin_stock", 0.6))
        transfers, _moves, assessments = assess(both, facts_with(book_cash={"rich": 100.0}), STATE, {})
        self.assertAlmostEqual(sum(t.amount for t in transfers), 100.0)
        self.assertAlmostEqual(assessments[1].arrears[0].amount, 20.0)

    def test_coin_stock_taxes_holders_but_not_the_state_or_edges(self):
        form = (TaxForm("subsidy", "coin_stock", 0.1),)
        cash = {"holder": 200.0, STATE: 900.0, "edge:external": 50.0}
        transfers, _moves, _assessments = assess(form, facts_with(book_cash=cash), STATE, {})
        self.assertEqual([(t.payer, t.amount) for t in transfers], [("holder", 20.0)])


class CapacityTests(unittest.TestCase):
    def test_state_capacity_scales_what_is_collected_and_the_rest_is_evaded_not_owed(self):
        transfers, moves, assessments = assess(FORMS, facts_with(), STATE, PRICES, state_capacity=0.5)
        self.assertAlmostEqual(moves[0].quantity, 50.0)
        duty = by_form(assessments)["import_duty"]
        self.assertAlmostEqual(duty.collected_value, FORMS[2].rate * 600.0 * 0.5)
        self.assertAlmostEqual(duty.evaded_value, FORMS[2].rate * 600.0 * 0.5)
        self.assertEqual(duty.arrears, ())

    def test_capacity_outside_zero_to_one_is_refused(self):
        with self.assertRaises(ValueError):
            assess(FORMS, facts_with(), STATE, PRICES, state_capacity=1.5)


class RefusalAndDeterminismTests(unittest.TestCase):
    def test_an_unknown_basis_names_itself_and_the_known_ones(self):
        with self.assertRaises(ValueError) as raised:
            assess((TaxForm("window_tax", "windows", 0.1),), facts_with(), STATE, PRICES)
        message = str(raised.exception)
        self.assertIn("windows", message)
        self.assertIn("harvest", message)
        self.assertIn("coin_stock", message)

    def test_a_harvest_form_without_a_good_is_refused(self):
        with self.assertRaises(ValueError):
            assess((TaxForm("tithe", "harvest", 0.1),), facts_with(), STATE, PRICES)

    def test_the_same_facts_give_the_same_result_whatever_the_insertion_order(self):
        first = assess(FORMS, facts_with(), STATE, PRICES)
        reversed_output = dict(reversed(list(facts_with().output.items())))
        second = assess(FORMS, facts_with(output=reversed_output), STATE, PRICES)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
