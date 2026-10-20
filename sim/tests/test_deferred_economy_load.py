"""SCENARIO (save round trip and deferred build): A game built to load a save does not open its own economy, and ends up exactly as the game that did:
same tree money fields, same saved text. A save without the tree's pricing refuses, and the game is built
the long way."""
from .harness import *  # noqa: F401,F403
from sim.engine.saveload import EconomyNotOpened, load_state, save_state

played = sim(capital=1e9)
path = os.path.join(tempfile.mkdtemp(), "session.json")
save_state(played, path)
check("scenario: a save keeps the money an hour was worth when its tree was priced",
      played.state.economy.nodes_money_per_labour_hour is not None)


def built(defer):
    game = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                 civ=S.load_civ("rome_100ad"), cfg=None, defer_economy=defer)
    game.goal, game.done_year = GOAL, {}
    return game


normal, deferred = built(False), built(True)
check("scenario: a deferred game has not opened its economy", not deferred.economy.agent.opened())
load_state(normal, path)
load_state(deferred, path)
check("scenario: the tree's money fields are the same", normal.nodes == deferred.nodes)
check("scenario: the deferred game still lacks nothing: its economy opens from the record",
      deferred.economy.agent.opened() and deferred.labour.money_per_labour_hour() == normal.labour.money_per_labour_hour())
other_path = os.path.join(tempfile.mkdtemp(), "again.json")
save_state(normal, other_path)
save_state(deferred, other_path + "2")
with open(other_path) as first, open(other_path + "2") as second:
    check("scenario: both save the same text", first.read() == second.read())

played.state.economy.nodes_money_per_labour_hour = None
unpriced = os.path.join(tempfile.mkdtemp(), "unpriced.json")
save_state(played, unpriced)
refused = False
try:
    load_state(built(True), unpriced)
except EconomyNotOpened:
    refused = True
check("scenario: a save without the tree's pricing is refused by a deferred game", refused)
