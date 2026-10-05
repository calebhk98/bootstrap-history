"""The UI's own memory (sim/ui/memory.py) lives in the save's `interface` slot and rides along
with every save and load, forks included. Run with `--only ui_memory`."""
import os
import tempfile

from sim.ui import memory

from .harness import check, sim

game = sim()
check("a new game's interface slot starts empty", game.state.interface == {})

with tempfile.TemporaryDirectory() as folder:
    first, fork = os.path.join(folder, "game.json"), os.path.join(folder, "fork.json")
    memory.remembered(game, "notes")["1"] = {"year": 100, "text": "aqueduct for the mill town"}
    check("what the UI remembers sits in the state's interface slot",
          game.state.interface.get("notes", {}).get("1", {}).get("year") == 100, game.state.interface)

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

    memory.remembered(later, "notes")["2"] = {"year": 101, "text": "only in the copy"}
    check("two games never share one memory", "2" not in memory.remembered(reread, "notes"))

    bare = sim()
    bare_path = os.path.join(folder, "bare.json")
    memory.save_state(bare, bare_path)
    memory.load_state(later, bare_path)
    check("loading a save with nothing remembered forgets the previous game's memory",
          memory.remembered(later, "notes") == {})

    memory.merge_session_meta(first, {"checkpoint": True})
    check("another writer of the sidecar still works",
          memory.settings.load_session_meta(first).get("checkpoint") is True)
