"""Scenarios (Complaint 640): the UI's memory rides along with every save and load of a played game, forks included, and a
save with nothing remembered forgets the previous game's memory. The rules are in test_ui_memory."""
import os
import tempfile

from sim.ui import memory

from .harness import check, sim

game = sim()
check("a new game's interface slot starts empty", game.state.interface == {})

with tempfile.TemporaryDirectory() as folder:
    first, fork = os.path.join(folder, "game.json"), os.path.join(folder, "fork.json")
    memory.remembered(game, "notes")["1"] = {"year": 100, "text": "aqueduct for the mill town"}
    memory.save_state(game, first)
    check("saving writes no sidecar for the memory", not os.path.exists(first + ".meta.json"))

    later = sim()
    memory.load_state(later, first)
    check("loading restores the memory into a fresh game",
          memory.remembered(later, "notes").get("1", {}).get("text") == "aqueduct for the mill town")

    memory.save_state(later, fork)
    reread = sim()
    memory.load_state(reread, fork)
    check("a fork saved under a new name carries the memory", "1" in memory.remembered(reread, "notes"))

    bare = sim()
    bare_path = os.path.join(folder, "bare.json")
    memory.save_state(bare, bare_path)
    memory.load_state(later, bare_path)
    check("loading a save with nothing remembered forgets the previous game's memory",
          memory.remembered(later, "notes") == {})
