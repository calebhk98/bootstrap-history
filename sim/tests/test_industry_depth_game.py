"""Complaint 111, whole game: the opening industries are seeded once from the agent economy's producers,
whatever is read first, and what the seed holds frees, speeds and steadies the concerns it should.

Slow topic: it builds a whole game (and an agent economy), so it is not in the quick tier.
"""
from .harness import *  # noqa: F401,F403
from sim.labour.api import tenure_held
from sim.ui import protocol as _PROTO

_game = sim()
_ventures = [node_id for node_id in sorted(_game.state.projects.granted) if _game.is_venture(node_id)]
check("set-up: the society runs some techniques at the opening", bool(_ventures), _ventures)

_node = _ventures[0]
_depth_first = _game.industry_depth(_node)
_game.seed_opening_industry_experience()
check("reading depth first or seeding first gives the same stock (the seed happens once)",
      abs(_game.industry_depth(_node) - _depth_first) < 1e-12, (_depth_first, _game.industry_depth(_node)))
check("a technique nobody runs at the opening starts with no tenure",
      all(tenure_held(_game.state.projects.tenure, node_id) == 0.0
          for node_id in sorted(NODES) if node_id not in _game.state.projects.granted
          and node_id not in _game.state.projects.done))

_before = tenure_held(_game.state.projects.tenure, _node)
_game.accrue_industry_experience()
_after = tenure_held(_game.state.projects.tenure, _node)
check("a technique the opening producers keep running holds its stock from year to year",
      abs(_after - _before) <= 0.05 * max(_before, 1e-9), (_before, _after))

_path = os.path.join(HERE, "_industry_tenure_roundtrip.json")
_PROTO.save_state(_game, _path)
_loaded = sim()
_PROTO.load_state(_loaded, _path)
check("tenure survives a save and a load",
      abs(tenure_held(_loaded.state.projects.tenure, _node) - _after) < 1e-9)
check("a loaded game does not seed again", _loaded.state.projects.industry_seeded)
try:
    os.remove(_path)
except OSError:
    pass

_hands = _game.venture_hands(_node)
check("a seeded concern runs without its founder: no scholar of his is tied up",
      _hands[0] == 0.0 or not _game.concern_runs_without_founder(_node), _hands)
check("the learning ratio of a seeded concern is a share of its stated takings",
      0.0 < _game.concern_learning_ratio(_node) <= 1.0 + 1e-9, _game.concern_learning_ratio(_node))
