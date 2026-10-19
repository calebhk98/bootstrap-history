"""Complaint 597: a relation set through the commands survives a real save and load, and a joined seat of a partner
country reads and writes its own country's side. Slow topic: it builds a game."""
import os
import tempfile
import unittest

from .harness import NODES, unopened_sim
from sim.agents.api import relations
from sim.engine.saveload import load_state, save_state
from sim.ui.proto.dispatch import _agent_dispatch


class RelationsSaveTests(unittest.TestCase):
    def test_a_note_and_a_term_survive_a_save_and_load_and_a_partner_seat_writes_its_own_side(self):
        game = unopened_sim()
        home = game.civ["id"]
        partner = "han"
        self.assertTrue(_agent_dispatch(game, NODES, {"cmd": "join", "seat": "envoy", "country": partner})["ok"])
        self.assertTrue(_agent_dispatch(game, NODES, {"cmd": "set_relation", "with": partner, "note": "slow to pay"})["ok"])
        self.assertTrue(_agent_dispatch(game, NODES, {"cmd": "set_relation", "with": partner, "term": "grain", "value": 2})["ok"])
        reply = _agent_dispatch(game, NODES, {"cmd": "set_relation", "with": home, "stance": "wary", "as": "envoy"})
        self.assertTrue(reply["ok"], reply)
        refused = _agent_dispatch(game, NODES, {"cmd": "set_relation", "with": partner, "stance": "hostile", "side": partner})
        self.assertEqual(refused["cause"], "not_your_country")
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "save.json")
            save_state(game, path)
            revived = unopened_sim()
            load_state(revived, path)
        ours = relations.read(revived.stores, home, partner)
        self.assertEqual((ours["note"], ours["treaty"]), ("slow to pay", {"grain": 2}))
        self.assertEqual(relations.read(revived.stores, partner, home)["stance"], "wary")
        shown = _agent_dispatch(revived, NODES, {"cmd": "relations", "with": partner})
        self.assertEqual(shown["theirs"]["stance"], "wary")


if __name__ == "__main__":
    unittest.main()
