"""SCENARIO: in a Rome game pure knowledge is never switched off and a household technique diffuses to the nation.
The relief arithmetic is in `test_plague_mitigation_realism`."""
import unittest

from .harness import *  # noqa: F401,F403
from .plague_fixture import ANTONINE, with_hazard

_MEDICAL_NODES = ("germ_theory", "med_quarantine_sanitation", "md2_vaccine_plague")


def _fresh():
    return with_hazard(unopened_sim(civ="rome_100ad", capital=1e9), ANTONINE)


class InstitutionVersusKnowledge(unittest.TestCase):

    def test_pure_knowledge_is_not_switched_off(self):
        household = _fresh()
        household.done.add("germ_theory")
        household._done_changed()
        self.assertFalse(household.is_venture("germ_theory"))
        self.assertLess(household.hazard_relief("staff_loss")[0], 1.0)


class NationalRelief(unittest.TestCase):

    def test_household_technique_diffuses_to_the_nation(self):
        nation = _fresh()
        for node_id in _MEDICAL_NODES:
            nation.done.add(node_id)
        year = nation.year
        reliefs = []
        for age in (0, 50, 400):
            nation.done_year = {node_id: year - age for node_id in _MEDICAL_NODES}
            reliefs.append(nation.medical_diffusion_relief())
        self.assertEqual(reliefs[0], 0.0)
        self.assertLess(reliefs[0], reliefs[1])
        self.assertLess(reliefs[1], reliefs[2])
