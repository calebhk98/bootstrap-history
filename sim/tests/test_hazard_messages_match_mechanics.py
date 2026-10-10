"""Hazard text agrees with hazard mechanics: the "lapsed" label follows
whether a counter is actually closed, and sacks and epidemics leave whole
people."""
import copy
import random
import unittest

from .harness import *  # noqa: F401,F403


_GAME = []
_RESTORED_FIELDS = ("scholars", "artisans", "employees", "directors_extra", "rng",
                    "civ_diffusion", "STAFF_LOSS_HAZARD_ANNUAL_CHANCE")


def _fresh(test):
    """The one game every test borrows; what a test changes on it is put back when the test ends."""
    if not _GAME:
        _GAME.append(sim(civ="rome_100ad", capital=1e9))
    household = _GAME[0]
    held = {name: copy.copy(getattr(household, name)) for name in _RESTORED_FIELDS}
    on_instance = {name for name in _RESTORED_FIELDS if name in household.__dict__}
    held_done = set(household.done)

    def restore():
        for name, value in held.items():
            if name in on_instance or isinstance(getattr(type(household), name, None), property):
                setattr(household, name, value)
            else:
                household.__dict__.pop(name, None)
        household.done.clear()
        household.done.update(held_done)
        household._done_changed()
    test.addCleanup(restore)
    return household


def _hazard_named(household, kind):
    return next(hazard for hazard in household.civ["hazards"] if kind in hazard)


class LapsedLabelFollowsClosure(unittest.TestCase):

    def test_running_knowledge_partly_adopted_nationally_is_not_lapsed(self):
        household = _fresh(self)
        household.done.add("germ_theory")
        household._done_changed()
        household.civ_diffusion = lambda node_id: 0.4
        multiplier, reasons = household.hazard_relief("staff_loss", beyond_national=True)
        self.assertLess(multiplier, 1.0)
        joined = "; ".join(reasons)
        self.assertNotIn("lapsed", joined)
        self.assertNotIn("is closed", joined)

    def test_closed_venture_is_still_labelled_lapsed(self):
        household = _fresh(self)
        household.done.add("plague_preparedness")
        household._done_changed()
        self.assertTrue(household.is_venture("plague_preparedness"))
        _, reasons = household.hazard_relief("staff_loss", beyond_national=True)
        self.assertIn("lapsed", "; ".join(reasons))

    def test_national_adoption_is_named_in_the_label(self):
        household = _fresh(self)
        household.done.add("germ_theory")
        household._done_changed()
        household.civ_diffusion = lambda node_id: 0.4
        _, reasons = household.hazard_relief("staff_loss", beyond_national=True)
        self.assertIn("adopted nationally", "; ".join(reasons))


class StaffStaysWhole(unittest.TestCase):

    def _assert_whole(self, household):
        counts = [household.scholars, household.artisans]
        counts += list(household.employees.values())
        for count in counts:
            self.assertEqual(count, round(count), counts)

    def _staffed(self):
        household = _fresh(self)
        household.scholars, household.artisans = 7.0, 9.0
        household.employees = {"carpenter": 3.0, "smith": 5.0}
        household.directors_extra = 2.0
        return household

    def test_epidemic_leaves_whole_people(self):
        for seed in range(6):
            household = self._staffed()
            household.STAFF_LOSS_HAZARD_ANNUAL_CHANCE = 2.0
            household.rng = random.Random(seed)
            hazard = _hazard_named(household, "staff_loss")
            household._shock_staff_loss(hazard, hazard["years"][0])
            self._assert_whole(household)

    def test_sack_leaves_whole_people(self):
        for seed in range(6):
            household = self._staffed()
            household.rng = random.Random(seed)
            hazard = _hazard_named(household, "sack_chance")
            household._sack_site(hazard, hazard["years"][0])
            self._assert_whole(household)
