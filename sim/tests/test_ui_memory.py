"""The UI's own memory (sim/ui/memory.py) rides along with every save and load, forks included.

The engine's save and load are stubbed, so this builds no game and runs in milliseconds."""
import json
import os
import tempfile

from sim.ui import memory

from .harness import check


class _Game:
    """Stands in for a Sim: memory only needs an object it can key on."""


def _stub_engine():
    memory.engine_save_state = lambda game, path: open(path, "w").write("{}")
    memory.engine_load_state = lambda game, path: None


_stub_engine()
with tempfile.TemporaryDirectory() as folder:
    first, fork = os.path.join(folder, "game.json"), os.path.join(folder, "fork.json")
    game = _Game()
    memory.save_state(game, first)
    check("a game with nothing remembered writes no sidecar", not os.path.exists(first + ".meta.json"))

    memory.remembered(game, "notes")["1"] = {"year": 100, "text": "aqueduct for the mill town"}
    memory.save_state(game, first)
    with open(first + ".meta.json") as handle:
        sidecar = json.load(handle)
    check("what the UI remembers is written under its own sidecar key",
          sidecar.get(memory.SIDECAR_KEY, {}).get("notes", {}).get("1", {}).get("year") == 100, sidecar)

    memory.merge_session_meta(first, {"checkpoint": True})
    with open(first + ".meta.json") as handle:
        sidecar = json.load(handle)
    check("another writer of the sidecar keeps the UI's memory",
          sidecar.get("checkpoint") is True and memory.SIDECAR_KEY in sidecar, sidecar)

    later = _Game()
    memory.load_state(later, first)
    check("loading restores the memory into a fresh game",
          memory.remembered(later, "notes").get("1", {}).get("text") == "aqueduct for the mill town")

    memory.save_state(later, fork)
    reread = _Game()
    memory.load_state(reread, fork)
    check("a fork saved under a new name carries the memory", "1" in memory.remembered(reread, "notes"))

    memory.remembered(later, "notes")["2"] = {"year": 101, "text": "only in the copy"}
    check("two games never share one memory", "2" not in memory.remembered(reread, "notes"))

    bare = os.path.join(folder, "bare.json")
    open(bare, "w").write("{}")
    memory.load_state(later, bare)
    check("loading a save with no sidecar forgets the previous game's memory",
          memory.remembered(later, "notes") == {})

with tempfile.TemporaryDirectory() as folder:
    read_only = _Game()
    memory.remembered(read_only, "programme")  # a read creates an empty topic
    path = os.path.join(folder, "read.json")
    memory.save_state(read_only, path)
    check("topics only read, never written, leave no sidecar", not os.path.exists(path + ".meta.json"))
