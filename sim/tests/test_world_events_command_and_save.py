"""The world event log (Complaint 493, 640): the `world_events` command reads the log of a stand-in game and filters it by
window and kind, and the log is part of the hazards module's saved state."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.state import deserialize_state, serialize_state
from sim.hazards.state import HazardsWorld
from sim.tests import hazards_host
from sim.ui.proto.dispatch_world_events import _cmd_world_events
from sim.tests.ui_stand_in import Game

LOG = [
    {"year": 90, "kind": "flood", "actors": ["rome"], "tiles": [], "cause": "river", "facts": {"population_loss": 5.0}},
    {"year": 99, "kind": "tile_transfer", "actors": ["rome", "han"], "tiles": ["t1"], "cause": "conquest",
     "facts": {"to_owner": "han", "control": "garrisoned"}},
    {"year": 100, "kind": "flood", "actors": ["han"], "tiles": [], "cause": "river", "facts": {"population_loss": 1.0}},
]


def game():
    module = hazards_host.build(world=HazardsWorld(world_events=[dict(row) for row in LOG]))
    return Game(state=Game(scenario=Game(year=100)),
                                 view=lambda name: module.world_events)


class WorldEventsCommandTests(unittest.TestCase):
    def test_by_default_the_last_ten_years_are_read(self):
        reply = _cmd_world_events(game(), {}, {"cmd": "world_events"}, None)
        self.assertEqual((reply["ok"], reply["years"], [row["year"] for row in reply["events"]]), (True, 10, [90, 99, 100]))

    def test_a_number_narrows_the_window(self):
        reply = _cmd_world_events(game(), {}, {"cmd": "world_events", "id": "5"}, None)
        self.assertEqual([row["year"] for row in reply["events"]], [99, 100])

    def test_a_kind_filters_the_rows(self):
        reply = _cmd_world_events(game(), {}, {"cmd": "world_events", "id": "tile_transfer"}, None)
        self.assertEqual((reply["kind"], [row["actors"] for row in reply["events"]]), ("tile_transfer", [["rome", "han"]]))


class WorldEventsSaveTests(unittest.TestCase):
    def test_the_log_round_trips_through_serialize_and_deserialize(self):
        world = HazardsWorld(world_events=[dict(row) for row in LOG], said_output={"a war": 210}, said_debasement=214)
        again = deserialize_state(serialize_state(world), HazardsWorld)
        self.assertEqual(again, world)


if __name__ == "__main__":
    unittest.main()
