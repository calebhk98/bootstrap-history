"""BASELINE VALIDATION (CLAUDE.md 4.2, Complaint 640): A no-intervention baseline's occupational distribution is plausible (Complaint 619, DESIGN 4.2): each
occupation group's share of working people (labour force by main occupation, as the sources count it) lies inside a wide band taken from the literature
(data/world/occupation_groups.json, which cites each source and marks recalled figures). A plausibility band,
not a fit. Whole games (slow). Run with `python3 -m sim.tests --slow --only occupational_distribution`."""

import collections
import json
import os
import random
import unittest

from . import harness  # noqa: F401  (sets the short spin-up the suite's games open on)
from sim.engine.ui_port import ROOT, Sim, load, load_civ
from sim.labour.api import hours_by_trade_of_all_employers, occupation_groups, occupational_report, people_by_trade_of_all_employers, shares_by_group

CIVILISATIONS = ("rome_100ad", "england_1300", "han_china_100ad")
YEARS = 1


def employer_hours(game):
    return hours_by_trade_of_all_employers(game.labour, game.state.economy.society_labour_hours)


def employer_people(game):
    return people_by_trade_of_all_employers(game.labour)


def play(civ_id):
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ_id))
    game.done_year = {}
    for _year in range(YEARS):
        game.step()
    return game


class GroupData(unittest.TestCase):
    def test_every_registry_trade_is_in_exactly_one_group(self):
        with open(os.path.join(ROOT, "data", "world", "trades.json"), encoding="utf-8") as handle:
            registry = set(json.load(handle)["trades"])
        counted = collections.Counter(trade for group in occupation_groups()["groups"].values() for trade in group["trades"])
        self.assertEqual(set(counted), registry)
        self.assertEqual([trade for trade, times in counted.items() if times > 1], [])

    def test_every_band_cites_a_source_or_is_the_unattributed_cap(self):
        data = occupation_groups()
        for group_id, group in data["groups"].items():
            low, high = group["band"]
            self.assertLessEqual(low, high)
            for source in group["sources"]:
                self.assertIn(source, data["sources"])
            if group_id != "unattributed":
                self.assertTrue(group["sources"], group_id)


class BaselineValidation(unittest.TestCase):
    """A baseline validation (CLAUDE.md 4.2) against sourced bands: slow only, never a picked year. It fails while
    the attribution of hours to trades is open (Complaint 619); the bands stay as sourced."""

    @classmethod
    def setUpClass(cls):
        cls.games = {civ_id: play(civ_id) for civ_id in CIVILISATIONS}
        for civ_id, game in cls.games.items():
            for basis, hours in (("people", employer_people(game)), ("hours", employer_hours(game))):
                for row in occupational_report(hours):
                    print("%s %-6s %-16s share %.4f band %s..%s %s" % (
                        civ_id, basis, row["group"], row["share"], row["low"], row["high"],
                        "ok" if row["inside"] else "OUTSIDE"))

    def test_each_group_share_is_inside_its_band(self):
        """The bands are shares of the labour force by main occupation (the sources count people), so the reading
        is each trade's head count in the labour core; hours in the field are printed above for comparison. A
        household that farms its own plot and spends the rest of its year on other work is a farming household."""
        for civ_id, game in self.games.items():
            people = employer_people(game)
            self.assertIsNotNone(people, civ_id)
            for row in occupational_report(people):
                with self.subTest(civ=civ_id, group=row["group"]):
                    self.assertTrue(row["inside"], "Complaint 619 (open): %s %s share %.4f outside %s..%s" % (
                        civ_id, row["group"], row["share"], row["low"], row["high"]))


if __name__ == "__main__":
    unittest.main()
