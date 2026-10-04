"""Replay carry-over (Complaint 267): known routes lift fog only for their ids."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.ui import replay
from sim.ui.memory import remembered

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "run.json.routes.json")
    check("a missing routes file reads as empty", replay.read_known_routes(path) == [])
    with open(path, "w") as handle:
        handle.write("{not json")
    check("a corrupt routes file reads as empty", replay.read_known_routes(path) == [])

_game = sim()
_game.fog = True
_game.revealed = set()
_built = sorted(_game.done - _game.granted)
_unknown_id = "no_such_node_for_replay_test"
_hidden = sorted(set(NODES) - set(_game.done) - _game.revealed)[:3]

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "run.routes.json")
    _game.done.add(_hidden[0])
    ids = replay.write_known_routes(_game, path)
    check("the file lists what the player built", _hidden[0] in ids and replay.read_known_routes(path) == ids)
    _game.done.discard(_hidden[0])

_done_before, _cash_before = set(_game.done), _game.capital
applied = replay.apply_known_routes(_game, [_hidden[0], _hidden[1], _unknown_id], NODES)
check("only ids in the new tree are applied", applied == sorted([_hidden[0], _hidden[1]]))
check("applied ids are revealed, others are not",
      {_hidden[0], _hidden[1]} <= set(_game.revealed) and _hidden[2] not in _game.revealed)
check("nothing is completed or paid", set(_game.done) == _done_before and _game.capital == _cash_before)
check("memory records what was carried", remembered(_game, "replay")["carried"] == applied)

_game.fog = False
_revealed_before = set(_game.revealed)
check("with fog off nothing is applied",
      replay.apply_known_routes(_game, [_hidden[2]], NODES) == [] and set(_game.revealed) == _revealed_before)
