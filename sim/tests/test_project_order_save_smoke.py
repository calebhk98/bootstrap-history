"""SMOKE (Complaint 841): in a whole game, a project moved to the front of the order is still first after a save and a load into
a fresh game. The rules and the commands are test_project_order."""
import os
import tempfile
import unittest

from sim.engine.saveload import load_state, save_state
from sim.projects.api import PutProjectFirst
from sim.tests.harness import unopened_sim


class ProjectOrderSurvivesALoad(unittest.TestCase):
    def test_a_moved_project_is_first_after_save_and_load(self):
        game = unopened_sim()
        last = game.view("project_order")()[-1]
        game.send(PutProjectFirst(last))
        self.assertEqual(game.view("project_order")()[0], last)
        path = os.path.join(tempfile.mkdtemp(), "order.json")
        save_state(game, path)
        fresh = unopened_sim()
        self.assertNotEqual(fresh.view("project_order")()[0], last)
        load_state(fresh, path)
        self.assertEqual(fresh.view("project_order")()[0], last)


if __name__ == "__main__":
    unittest.main()
