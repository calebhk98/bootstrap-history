"""Complaint 506: small display and wording bugs found in a Rome playtest. Each is a function of its inputs (a reply, a
name, a list of known materials) called on values built here; the subject of most is presentation, and says so."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.agents.group import InterestGroup
from sim.agents.group_strata import definite
from sim.engine.blockers import BLOCKER_MEANING
from sim.tests.harness import NODES
from sim.engine.shortage_conditions import material_words, slowed_projects
from sim.ui import market_report
from sim.ui.cli_interactive import _civ_title
from sim.ui.proto.help import example_node_id
from sim.ui.proto.render_screen_why import _material_row_text
from sim.ui.proto.render_typed import render_pretty
from sim.ui.proto.typed import parse_typed
from sim.ui.proto.ventures import _VENTURE_SUPERVISION_NOTE

LEVERAGE = {"ok": True, "leverage_points": [
    {"lever": "literacy general", "why_it_matters": "more people who can read", "figures": {"literacy_general": 0.119}},
    {"lever": "finance", "why_it_matters": "money removes the cost bottleneck", "figures": {"credit_limit": 23515.9}}],
    "note": "A broad approach can make a hard goal cheaper."}


class PetitionTests(unittest.TestCase):
    def test_a_petition_says_the_blame_lands_on_the_founder_when_his_share_is_material(self):
        # presentation: the sentence
        self.assertIn("The blame lands on you", InterestGroup.blame_words(1.0))

    def test_and_says_nothing_of_blame_when_his_share_is_slight(self):
        # presentation: the sentence
        self.assertEqual(InterestGroup.blame_words(0.05), "")


class NamesTests(unittest.TestCase):
    def test_a_stratum_name_that_opens_with_an_article_is_not_given_a_second_one(self):
        # presentation: the grammar of a name
        self.assertEqual(definite("The Roman Empire under Trajan artisans"), "the Roman Empire under Trajan artisans")

    def test_a_proper_name_keeps_its_own_opening_and_a_common_noun_gets_one(self):
        # presentation: the grammar of a name
        self.assertEqual(definite("Rome artisans"), "Rome artisans")
        self.assertEqual(definite("artisans"), "the artisans")

    def test_a_bc_start_year_is_not_repeated_as_a_negative_number(self):
        # presentation: the title of a start
        self.assertEqual(_civ_title({"name": "Ptolemaic Egypt, 100 BC", "year": -100}), "Ptolemaic Egypt, 100 BC")
        self.assertEqual(_civ_title({"name": "Somewhere", "year": -100}), "Somewhere, 100 BC")
        self.assertEqual(_civ_title({"name": "Rome", "year": 100}), "Rome, 100 AD")

    def test_a_material_key_reads_in_player_words(self):
        # presentation: the words of a material
        self.assertEqual(material_words("alum_kg"), "alum")
        self.assertEqual(material_words("hectare_land"), "hectare land")


class ScreenTests(unittest.TestCase):
    def test_leverage_reads_as_text_not_python_dictionaries(self):
        # presentation: the screen
        text = render_pretty("leverage", LEVERAGE)
        self.assertNotIn("{", text)
        self.assertIn("literacy general", text)

    def test_quit_prints_a_farewell_not_the_protocol_field(self):
        # presentation: the screen
        text = render_pretty("quit", {"ok": True, "bye": True, "message": "Goodbye."})
        self.assertNotIn("bye: True", text)
        self.assertIn("Goodbye.", text)

    def test_a_land_row_is_counted_in_hectares_and_not_said_to_be_supplied_in_years(self):
        # presentation: the row
        row = _material_row_text({"material": "hectare_land", "needed_tonnes": 0.008, "held_tonnes": 0.0,
                                  "missing_tonnes": 0.008, "cost_of_missing": 10.0, "not_produced": True,
                                  "own_unit": {"dimension": "area", "unit": "hectares", "needed": 8.0, "held": 0.0,
                                               "missing": 8.0}})
        self.assertIn("hectares", row)
        self.assertIn("nothing produces", row)
        for word in ("lib", "about"):
            self.assertNotIn(word, row)

    def test_the_supervision_note_does_not_claim_a_figure_is_a_third_of_a_third(self):
        # presentation: the note
        self.assertNotIn("third of a third", _VENTURE_SUPERVISION_NOTE)

    def test_the_money_blocker_covers_the_yearly_draw_rate_as_well_as_the_bill(self):
        # presentation: the blocker's meaning
        self.assertIn("draw rate", BLOCKER_MEANING["money"])


class TypedCommandTests(unittest.TestCase):
    def test_the_usage_example_names_a_real_node(self):
        self.assertIn(example_node_id(), NODES)

    def test_a_bare_path_asks_for_the_route_to_the_goal(self):
        self.assertEqual(parse_typed("path")[0], {"cmd": "path"})

    def test_market_with_a_material_parses_the_material(self):
        self.assertEqual(parse_typed("market iron_kg")[0], {"cmd": "market", "material": "iron_kg"})

    def test_market_offset_is_still_paging(self):
        self.assertEqual(parse_typed("market offset 5")[0], {"cmd": "market", "offset": 5})

    def test_quote_sell_concern_parses(self):
        self.assertEqual(parse_typed("quote sell concern zz_quoted")[0],
                         {"cmd": "quote", "what": "sell", "target": "concern", "id": "zz_quoted"})


class MarketReportTests(unittest.TestCase):
    KNOWN = ["alum_kg", "coal_kg", "iron_bar_kg", "iron_ore_kg", "tin_kg"]

    def report(self, **keywords):
        rows = lambda sim, offset, limit, only=None: {"total": 1, "offset": 0, "limit": 1,
                                                        "rows": [{"material": only}] if only else []}
        with mock.patch.object(market_report, "priceable_materials", lambda sim: self.KNOWN), \
                mock.patch.object(market_report, "material_rows", rows), \
                mock.patch.object(market_report, "wage_rows", lambda sim: [{"trade": "smith"}]):
            return market_report.market_report(None, **keywords)

    def test_market_with_a_material_lists_that_one_material_only(self):
        reply = self.report(material="coal_kg")
        self.assertTrue(reply["ok"])
        self.assertEqual([row["material"] for row in reply["materials"]["rows"]], ["coal_kg"])

    def test_and_the_wages_table_is_left_out(self):
        self.assertEqual(self.report(material="coal_kg")["wages"], [])
        self.assertEqual(self.report()["wages"], [{"trade": "smith"}])

    def test_the_material_is_matched_whatever_its_case_or_padding(self):
        self.assertTrue(self.report(material="  Coal_kg ")["ok"])

    def test_an_unknown_material_is_refused_and_points_back_to_the_full_table(self):
        reply = self.report(material="zzzz_nothing")
        self.assertIs(reply["ok"], False)
        # presentation: the pointer back to the table
        self.assertIn("'market' lists them all", reply["error"])

    def test_a_near_miss_suggests_the_real_name(self):
        reply = market_report.unknown_material_reply("coal_kx", self.KNOWN)
        self.assertIs(reply["ok"], False)
        self.assertIn("coal_kg", reply["error"])

    def test_a_name_inside_a_real_one_suggests_it(self):
        self.assertIn("iron_bar_kg", market_report.unknown_material_reply("bar", self.KNOWN)["error"])

    def test_no_suggestion_when_nothing_is_near(self):
        self.assertNotIn("did you mean", market_report.unknown_material_reply("qqqqqqq", self.KNOWN)["error"])


class ShortageLineTests(unittest.TestCase):
    @staticmethod
    def game(throttles):
        return SimpleNamespace(state=SimpleNamespace(projects=SimpleNamespace(active_keys_sorted=lambda: list(throttles))),
                               peek_project_resource_throttle=lambda node_id: (throttles[node_id], None))

    def test_with_no_project_running_nothing_is_slowed_by_a_shortage(self):
        self.assertEqual(slowed_projects(self.game({})), [])

    def test_a_project_the_shortage_does_not_touch_is_not_slowed(self):
        self.assertEqual(slowed_projects(self.game({"a": 1.0, "b": 1.0})), [])

    def test_only_the_projects_it_slows_are_named_in_id_order(self):
        self.assertEqual(slowed_projects(self.game({"c": 0.2, "a": 0.5, "b": 1.0})), ["a", "c"])


if __name__ == "__main__":
    unittest.main()
