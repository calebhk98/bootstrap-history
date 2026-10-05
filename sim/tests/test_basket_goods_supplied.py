"""Complaints/391: every good a civilisation's households buy is supplied by a technique it holds,
by an enabled partner, or is declared unsupplied with a reason in its own file."""
import json
import os
import unittest

from sim.engine import civ_basket_check as check
from sim.engine import civ_start_check as start_check
from sim.engine.catalog import load_production_catalog
from sim.engine.need_data import load_needs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PRODUCTION = {"soap": {"requires_node": "lye"}, "bread": {"requires_node": None}}
GOODS = {"soap": {}, "bread": {}, "wild_game": {}}
REASON = "imported from outside the modelled partners"


def _civ(techs, declared=None, **extra):
    return dict({"year": 1300, "starting_techs": techs, "unsupplied_basket_goods": declared or {}}, **extra)


def _unsupplied(civilisations, economies):
    return check.unsupplied_basket_goods("home", civilisations, PRODUCTION, GOODS, economies)


class BasketSupplyRule(unittest.TestCase):

    def test_a_good_whose_every_recipe_is_gated_on_an_unheld_node_is_unsupplied(self):
        self.assertEqual(_unsupplied({"home": _civ([])}, []), ["soap"])

    def test_a_held_gate_or_a_raw_good_is_not_flagged(self):
        self.assertEqual(_unsupplied({"home": _civ(["lye"])}, []), [])

    def test_a_partner_in_the_year_that_holds_the_gate_and_sells_supplies_it(self):
        civilisations = {"home": _civ([]), "far": _civ(["lye"])}
        economies = [{"civilization": "far", "enabled": True, "from_year": 1000, "until_year": 1400}]
        self.assertEqual(_unsupplied(civilisations, economies), [])
        economies[0]["until_year"] = 1200
        self.assertEqual(_unsupplied(civilisations, economies), ["soap"])
        economies[0].update(until_year=1400, enabled=False)
        self.assertEqual(_unsupplied(civilisations, economies), ["soap"])

    def test_a_partner_that_refuses_to_sell_does_not_supply(self):
        civilisations = {"home": _civ([]), "far": _civ(["lye"], will_not_sell=["soap"])}
        self.assertEqual(_unsupplied(civilisations, [{"civilization": "far", "enabled": True}]), ["soap"])

    def test_an_undeclared_good_and_a_stale_entry_are_errors_and_unreviewed_warns(self):
        errors, _ = check.basket_supply_findings({"home": _civ([])}, PRODUCTION, GOODS, [])
        self.assertEqual(len(errors), 1)
        errors, warnings = check.basket_supply_findings(
            {"home": _civ([], {"soap": REASON})}, PRODUCTION, GOODS, [])
        self.assertEqual((errors, warnings), ([], []))
        errors, _ = check.basket_supply_findings({"home": _civ(["lye"], {"soap": REASON})}, PRODUCTION, GOODS, [])
        self.assertEqual(len(errors), 1)
        _, warnings = check.basket_supply_findings(
            {"home": _civ([], {"soap": "unreviewed"})}, PRODUCTION, GOODS, [])
        self.assertEqual(len(warnings), 1)


class ShippedCivilisationsSupplyTheirBaskets(unittest.TestCase):

    def test_every_unsupplied_basket_good_has_a_reason(self):
        with open(os.path.join(ROOT, "data", "world", "foreign_economies.json"), encoding="utf-8") as handle:
            economies = json.load(handle)["economies"]
        errors, _warnings = check.basket_supply_findings(
            start_check.load_civilisations(ROOT), load_production_catalog(ROOT),
            load_needs(ROOT)["goods"], economies)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
