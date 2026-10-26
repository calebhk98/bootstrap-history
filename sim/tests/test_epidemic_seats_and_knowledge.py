"""An epidemic year cuts each playing seat's staff by the working-age share the disease model killed, a quiet year takes
nothing (`DiseasePortMixin.epidemic_hits_seats`), and a node with neither revenue nor upkeep is knowledge, not a venture
(`CapabilityMixin.is_venture`). Each rule is called on a stand-in carrying only what it reads."""
QUICK_TOPIC = True

import contextlib
import types
import unittest

from sim.engine.disease_port import DiseasePortMixin
from sim.engine.projects_capability import CapabilityMixin
from sim.tests import event_stand_in


class _Seat(DiseasePortMixin):
    """The members `epidemic_hits_seats` reads from the game, recording the survival it is told to apply."""
    send = event_stand_in.send
    PLAGUE_CASH_LOSS_SHARE = 0.0

    def __init__(self, working_age):
        self.population = types.SimpleNamespace(working_age=working_age)
        self.state = types.SimpleNamespace(household=types.SimpleNamespace(
            scholars=5000.0, artisans=5000.0, employees={}, directors_extra=2.0, log=[]))
        self.labour = types.SimpleNamespace(staff_snapshot=lambda: {}, log_staff_reduction=lambda name, before: None)
        self.survival_applied = []

    def playing_seats(self):
        return ["founder"]

    @contextlib.contextmanager
    def act_as(self, seat_id):
        yield

    def apply_staff_survival(self, survival):
        self.survival_applied.append(survival)

    def lose_capital(self, amount, reason):
        return 0.0


class EpidemicHitsSeatsTest(unittest.TestCase):
    def test_an_epidemic_year_applies_the_survival_of_the_working_age_share_killed(self):
        seat = _Seat(working_age=7500.0)
        share = seat.epidemic_hits_seats({"working_age": 2500.0}, 100)
        self.assertAlmostEqual(share, 0.25, places=12)
        self.assertEqual(len(seat.survival_applied), 1)
        self.assertAlmostEqual(seat.survival_applied[0], 0.75, places=12)
        self.assertAlmostEqual(seat.state.household.directors_extra, 2.0 * 0.75, places=12)

    def test_a_quiet_year_takes_nothing(self):
        seat = _Seat(working_age=7500.0)
        self.assertEqual(seat.epidemic_hits_seats({}, 100), 0.0)
        self.assertEqual(seat.survival_applied, [])
        self.assertEqual(seat.state.household.directors_extra, 2.0)
        self.assertEqual(seat.state.household.log, [])


class KnowledgeIsNotAVentureTest(unittest.TestCase):
    def _game(self, granted=()):
        game = types.SimpleNamespace()
        nodes = {"knowledge": {"rev": 0, "up": 0}, "earner": {"rev": 5.0, "up": 0}, "keeper": {"rev": 0, "up": 2.0}}
        game.nodes = nodes
        game.state = types.SimpleNamespace(projects=types.SimpleNamespace(granted=set(granted)))
        game.is_concern_node = lambda node_id: CapabilityMixin.is_concern_node(game, node_id)
        return game

    def test_only_a_node_that_earns_or_costs_to_keep_is_a_venture(self):
        game = self._game()
        self.assertFalse(CapabilityMixin.is_venture(game, "knowledge"))
        self.assertTrue(CapabilityMixin.is_venture(game, "earner"))
        self.assertTrue(CapabilityMixin.is_venture(game, "keeper"))

    def test_a_granted_node_is_never_a_venture(self):
        game = self._game(granted=("earner",))
        self.assertFalse(CapabilityMixin.is_venture(game, "earner"))


if __name__ == "__main__":
    unittest.main()
