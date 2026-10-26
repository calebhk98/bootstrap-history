"""The engine bridge's application of the commands hazards sends to owners that have not moved: each does what the old hazard
code did inline, on a stand-in game that holds only what the write touches."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim.demography.api import CutPopulation, RefreshDemographicIndexes
from sim.engine import bridge_hazards
from sim.projects.api import ShutForgotten
from sim.projects.api import ResetProjectProgress
from sim.reporting.api import RecordEvent
from sim.seats.api import FounderDies
from sim.workforce import rules as workforce_rules
from sim.workforce.api import ReportStaffReduction, ScaleDeputies


class SurvivingPeople(unittest.TestCase):
    def test_everyone_survives_a_share_of_one_and_no_one_a_share_of_zero(self):
        self.assertEqual(workforce_rules.surviving_people(random.Random(1), 40.0, 1.0), 40.0)
        self.assertEqual(workforce_rules.surviving_people(random.Random(1), 40.0, 0.0), 0.0)

    def test_the_headcount_is_whole_and_one_draw_is_made_per_person(self):
        dice = random.Random(3)
        kept = workforce_rules.surviving_people(dice, 12.4, 0.5)
        self.assertEqual(kept, float(int(kept)))
        mirror = random.Random(3)
        for _ in range(12):
            mirror.random()
        self.assertEqual(dice.random(), mirror.random())


class Writes(unittest.TestCase):
    def test_deputies_are_multiplied_by_the_share(self):
        game = SimpleNamespace(state=SimpleNamespace(household=SimpleNamespace(directors_extra=4.0)))
        bridge_hazards.scale_deputies(game, ScaleDeputies(0.5))
        self.assertEqual(game.state.household.directors_extra, 2.0)

    def test_works_of_forgotten_techniques_are_no_longer_running_or_shut(self):
        projects = SimpleNamespace(operating={"a", "b", "c"}, mothballed={"a", "c"})
        game = SimpleNamespace(state=SimpleNamespace(projects=projects))
        bridge_hazards.shut_forgotten(game, ShutForgotten(("a", "b")))
        self.assertEqual((projects.operating, projects.mothballed), ({"c"}, {"c"}))

    def test_every_project_in_hand_goes_back_to_the_beginning(self):
        active = {"b": {"ph_left": 1.0, "yrs": 3.0}, "a": {"ph_left": 2.0, "yrs": 1.0}}
        game = SimpleNamespace(state=SimpleNamespace(projects=SimpleNamespace(active=active)),
                               nodes={"a": {"ph": 100.0}, "b": {"ph": 50.0}})
        bridge_hazards.reset_project_progress(game, ResetProjectProgress())
        self.assertEqual(active, {"a": {"ph_left": 100.0, "yrs": 0.0}, "b": {"ph_left": 50.0, "yrs": 0.0}})

    def test_the_log_of_staff_lost_is_asked_with_the_cause_and_the_headcount_before(self):
        asked = []
        game = SimpleNamespace(labour=SimpleNamespace(log_staff_reduction=lambda cause, before: asked.append((cause, before))))
        bridge_hazards.report_staff_reduction(game, ReportStaffReduction("a sack", {"smith": 3.0}))
        self.assertEqual(asked, [("a sack", {"smith": 3.0})])

    def test_the_population_is_cut_and_its_figures_refreshed_by_the_demographic_owner(self):
        calls = []
        game = SimpleNamespace(_apply_population_mortality_shock=lambda share: calls.append(("cut", share)),
                               _refresh_demographic_indexes=lambda year: calls.append(("refresh", year)))
        bridge_hazards.cut_population(game, CutPopulation(0.2))
        bridge_hazards.refresh_demographic_indexes(game, RefreshDemographicIndexes(150))
        self.assertEqual(calls, [("cut", 0.2), ("refresh", 150)])

    def test_a_founder_who_dies_has_the_reason_set_and_the_run_ends_in_the_log(self):
        sent = []
        game = SimpleNamespace(state=SimpleNamespace(founder=SimpleNamespace(dead_reason=None)), send=sent.append)
        bridge_hazards.founder_dies(game, FounderDies("denounced"))
        self.assertEqual(game.state.founder.dead_reason, "denounced")
        self.assertEqual([(command.kind, command.text) for command in sent if isinstance(command, RecordEvent)],
                         [("run_ends", "RUN ENDS: denounced")])


if __name__ == "__main__":
    unittest.main()
