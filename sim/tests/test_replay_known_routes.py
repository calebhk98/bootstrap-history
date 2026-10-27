"""Replay carry-over (Complaint 267): known routes lift fog only for their ids (a stub game: the done set, the
granted set, fog, the revealed set and the interface memory, no game)."""
import os
import tempfile
from types import SimpleNamespace

from .harness import check
from sim.ui import replay
from sim.ui.memory import remembered
from sim.tests.ui_stand_in import Game

QUICK_TOPIC = True


def _stub(done=(), granted=(), fog=True, revealed=()):
    return Game(done=set(done), granted=set(granted), fog=fog, revealed=set(revealed), capital=100.0,
                           state=Game(interface={}))


with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "run.json.routes.json")
    check("a missing routes file reads as empty", replay.read_known_routes(path) == [])
    with open(path, "w") as handle:
        handle.write("{not json")
    check("a corrupt routes file reads as empty", replay.read_known_routes(path) == [])

built = _stub(done={"a", "b", "granted_one"}, granted={"granted_one"})
check("the routes a run built leave out what the society already had", replay.built_routes(built) == ["a", "b"])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "run.routes.json")
    ids = replay.write_known_routes(built, path)
    check("the file lists what the player built", ids == ["a", "b"] and replay.read_known_routes(path) == ids)

carrying = _stub(done={"a"})
remembered(carrying, replay.TOPIC)["carried"] = ["old"]
check("the routes to carry are what was built plus what was already carried",
      replay.routes_to_carry(carrying) == ["a", "old"], replay.routes_to_carry(carrying))

game = _stub(done={"built"}, revealed={"seen"})
done_before, cash_before = set(game.done), game.capital
applied = replay.apply_known_routes(game, ["h0", "h1", "no_such_node"], {"h0", "h1", "h2", "built", "seen"})
check("only ids in the new tree are applied", applied == ["h0", "h1"], applied)
check("applied ids are revealed, others are not", {"h0", "h1", "seen"} <= game.revealed and "h2" not in game.revealed)
check("nothing is completed or paid", game.done == done_before and game.capital == cash_before)
check("memory records what was carried", remembered(game, "replay")["carried"] == applied)

game.fog = False
revealed_before = set(game.revealed)
check("with fog off nothing is applied",
      replay.apply_known_routes(game, ["h2"], {"h2"}) == [] and game.revealed == revealed_before)
