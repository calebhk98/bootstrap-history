"""An epidemic year cuts each playing seat's staff by the working-age share the disease model killed, a quiet year takes
nothing (the disease module's `hit_seats`), and a node with neither revenue nor upkeep is knowledge, not a venture
(the production module's `is_venture`). Each rule is called on a stand-in carrying only what it reads."""
QUICK_TOPIC = True

import contextlib
import types
import unittest

from sim.disease.api import HitSeatsWithEpidemic
from sim.disease.module import Disease
from sim.hazards.api import LoseCapital
from sim.reporting.api import RecordEvent
from sim.tests import module_harness, production_host
from sim.workforce.api import ScaleDeputies, SurviveStaff


@contextlib.contextmanager
def _act_as(seat_id):
    yield


def _module(working_age):
    """The disease module over one seat of 10000 people, its views answered by plain values; it loses no cash."""
    return module_harness.build(Disease, views={
        "working_age": working_age, "seat_list": {"playing": ["founder"]}, "act_as": _act_as,
        "staff": {"scholars": 5000.0, "artisans": 5000.0, "employees": {}}, "staff_snapshot": {}},
        answers={LoseCapital: 0.0})


class EpidemicHitsSeatsTest(unittest.TestCase):
    def test_an_epidemic_year_applies_the_survival_of_the_working_age_share_killed(self):
        module = _module(7500.0)
        share = module.hit_seats(HitSeatsWithEpidemic({"working_age": 2500.0}, 100))
        self.assertAlmostEqual(share, 0.25, places=12)
        sent = module_harness.sent(module)
        survival = [command for command in sent if isinstance(command, SurviveStaff)]
        self.assertEqual(len(survival), 1)
        self.assertAlmostEqual(survival[0].survival_share, 0.75, places=12)
        deputies = [command for command in sent if isinstance(command, ScaleDeputies)]
        self.assertAlmostEqual(deputies[0].share, 0.75, places=12)
        events = [command for command in sent if isinstance(command, RecordEvent)]
        self.assertEqual((len(events), events[0].kind, events[0].facts["took_nothing"]), (1, "hazard_hit", False))

    def test_a_quiet_year_takes_nothing(self):
        module = _module(7500.0)
        self.assertEqual(module.hit_seats(HitSeatsWithEpidemic({}, 100)), 0.0)
        self.assertEqual(module_harness.sent(module), [])


class KnowledgeIsNotAVentureTest(unittest.TestCase):
    def _game(self, granted=()):
        nodes = {"knowledge": {"rev": 0, "up": 0}, "earner": {"rev": 5.0, "up": 0}, "keeper": {"rev": 0, "up": 2.0}}
        return production_host.build(tree_nodes=nodes, techniques_granted=set(granted))

    def test_only_a_node_that_earns_or_costs_to_keep_is_a_venture(self):
        game = self._game()
        self.assertFalse(game.is_venture("knowledge"))
        self.assertTrue(game.is_venture("earner"))
        self.assertTrue(game.is_venture("keeper"))

    def test_a_granted_node_is_never_a_venture(self):
        game = self._game(granted=("earner",))
        self.assertFalse(game.is_venture("earner"))


if __name__ == "__main__":
    unittest.main()
