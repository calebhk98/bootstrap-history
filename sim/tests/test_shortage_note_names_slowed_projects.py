"""The shortage note names the slowed projects from the tree's nodes (sim/materials/throttle.py, step_shortage_notes)."""

QUICK_TOPIC = True

import unittest

from sim.materials.state import MaterialsSeat
from sim.reporting.api import RecordEvent
from sim.tests import materials_stand_in


class ShortageNoteTests(unittest.TestCase):
    def test_the_event_carries_the_names_of_the_slowed_projects(self):
        module = materials_stand_in.build(seat=MaterialsSeat(binding="coal", throttle=0.3), tree_nodes={"kiln": {"name": "Kiln"}})
        module.slowed_projects = lambda: ["kiln"]
        module.note_shortage = lambda material, throttle: True
        module.step_shortage_notes()
        events = materials_stand_in.sent(module, RecordEvent)
        self.assertEqual([event.kind for event in events], ["material_shortage"])
        self.assertIn("Kiln", events[0].text)   # presentation: the note names the projects it slows


if __name__ == "__main__":
    unittest.main()
