"""A civilisation is granted only the technologies its own file declares, so no other civilisation is handed Roman
institutions for nothing. Read from the civilisation files and the tree; no game."""

QUICK_TOPIC = True

import unittest

from .harness import NODES
from sim.engine.data import load_civ
from sim.engine.starting_techs import declared_starting_techs

ROMAN_MARKERS = ("_roman", "_rome", "annona", "insula", "societas", "collegium",
                 "argentarii", "latifundi", "cursus", "pharos")


class StartingGrantsTests(unittest.TestCase):
    def test_no_other_civilisation_is_handed_roman_institutions_for_nothing(self):
        for civ_id in ("han_china_100ad", "norse_900ad", "mexica_1500", "england_1300"):
            granted = declared_starting_techs(load_civ(civ_id), NODES)
            self.assertTrue(granted, civ_id)
            roman = sorted(name for name in granted if any(marker in name for marker in ROMAN_MARKERS))
            self.assertEqual(roman, [], civ_id)
