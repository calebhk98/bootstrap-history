"""market_screen: the `market` command's registration, typed parse and rendering (Complaint 640: a reply built here, no game;
the command against a whole game is test_market_screen_scenario)."""
from .harness import check
from sim.ui.proto import command_registry as _registry
from sim.ui.proto.render_typed import render_pretty as _render_pretty
from sim.ui.proto.typed import parse_typed as _parse_typed
from sim.tests.ui_stand_in import Game

QUICK_TOPIC = True

check("market is a registered command with a help page",
      _registry.resolve("market") is not None
      and _registry.page("market")["usage"], _registry.resolve("market"))
check("typed 'market offset 10 limit 5' parses",
      _parse_typed("market offset 10 limit 5")[0] == {"cmd": "market", "offset": 10, "limit": 5},
      _parse_typed("market offset 10 limit 5"))

_row = {"material": "steel_plate_kg", "buy_per_tonne": 100.0, "sell_per_tonne": 80.0, "market_available_tonnes_per_year": 5.0,
        "own_supply": False, "price_basis": "solved"}
_reply = {"ok": True, "materials": {"rows": [_row], "total": 1}, "wages": [{"trade": "smith", "a_year_of_one": 500.0, "available_here": True, "you_employ": 0}]}
_text = _render_pretty("market", _reply)
# presentation: the screen's section headings
check("the rendered screen has its two sections", all(word in _text for word in ("MATERIAL", "WAGES")), _text[:400])
# presentation: the note on a gated price
check("a price at a technique the society lacks says so",
      "priced at a technique you do not have" in _render_pretty(
          "market", {"ok": True, "materials": {"rows": [dict(_row, price_basis="gated")], "total": 1}, "wages": []}),
      None)
check("a price at a technique the society holds carries no such note",
      "priced at a technique you do not have" not in _text, None)


# ---- the screen's numbers, from a stand-in sim (what test_market_screen_scenario ran in a whole game)
import types
import unittest
from unittest import mock

from sim.ui import market_report


def _quote(buy):
    return {"buy_per_tonne": buy, "sell_per_tonne": buy * 0.8, "making_cost_per_tonne": 50.0,
            "price_at_tile_per_tonne": 100.0, "market_available_tonnes_per_year": 3.456, "price_kind": "market"}


def _sim_quoting(prices):
    return Game(
        material_trade_quote=lambda material: _quote(prices[material]) if material in prices else None,
        material_price_basis=lambda material: "solved", MATERIAL_CHECKS={},
        view=lambda name: (lambda: {"employees": {"smith": 2.0}}), labour=Game(
            market=Game(quote_annual=lambda trade: 500.4),
            trade_available=lambda trade: trade == "smith"))


class MarketRowTests(unittest.TestCase):
    def rows(self, offset, limit, only=None, own=("steel",)):
        sim = _sim_quoting({"alum_kg": 10.0, "steel_kg": 20.0, "tin_kg": 30.0})
        with mock.patch.object(market_report.ui_port, "own_production_tags", lambda game: [(key, key) for key in own]), \
                mock.patch.object(market_report.ui_port, "own_material_supply", lambda game, tag: 1.0), \
                mock.patch.object(market_report, "priceable_materials", lambda game: ["alum_kg", "steel_kg", "tin_kg"]):
            return market_report.material_rows(sim, offset, limit, only)

    def test_offset_and_limit_page_the_table_and_total_counts_all(self):
        page = self.rows(1, 1)
        self.assertEqual([row["material"] for row in page["rows"]], ["steel_kg"])
        self.assertEqual(page["total"], 3)

    def test_a_row_carries_the_quotes_buy_price_rounded_and_the_basis(self):
        row = self.rows(0, 1)["rows"][0]
        self.assertEqual((row["buy_per_tonne"], row["sell_per_tonne"], row["price_over_long_run_cost"],
                          row["market_available_tonnes_per_year"], row["price_basis"]),
                         (10.0, 8.0, 2.0, 3.46, "solved"))

    def test_a_material_the_actor_produces_is_flagged_own_supply(self):
        flags = {row["material"]: row["own_supply"] for row in self.rows(0, 10, own=("steel_kg",))["rows"]}
        self.assertEqual(flags, {"alum_kg": False, "steel_kg": True, "tin_kg": False})

    def test_one_named_material_is_one_row_whatever_the_page(self):
        page = self.rows(2, 10, only="alum_kg")
        self.assertEqual([row["material"] for row in page["rows"]], ["alum_kg"])

    def test_a_quote_with_no_making_cost_has_no_price_ratio(self):
        sim = _sim_quoting({})
        sim.material_trade_quote = lambda material: dict(_quote(10.0), making_cost_per_tonne=None)
        with mock.patch.object(market_report.ui_port, "own_production_tags", lambda game: []):
            row = market_report.material_rows(sim, 0, 1, only="alum_kg")["rows"][0]
        self.assertIsNone(row["price_over_long_run_cost"])


class WageRowTests(unittest.TestCase):
    def test_a_row_per_trade_with_a_rounded_year_wage_availability_and_staff(self):
        rows = {row["trade"]: row for row in market_report.wage_rows(_sim_quoting({}))}
        self.assertEqual(set(rows), set(market_report.WAGES))
        self.assertEqual((rows["smith"]["a_year_of_one"], rows["smith"]["available_here"], rows["smith"]["you_employ"]),
                         (500.0, True, 2.0))


class MarketReportTests(unittest.TestCase):
    def test_an_unpriced_material_is_refused_with_near_misses(self):
        with mock.patch.object(market_report, "priceable_materials", lambda game: ["alum_kg", "steel_kg"]):
            reply = market_report.market_report(None, material="alum_g")
        self.assertFalse(reply["ok"])
        self.assertIn("alum_kg", reply["error"])
