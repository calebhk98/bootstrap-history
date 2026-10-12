"""A game built to load a save does not open its own economy, and ends up exactly as the game that did:
same tree money fields, same saved text. Without the note beside the save it refuses and the game is
built the long way."""
from .harness import *  # noqa: F401,F403
from sim.engine.saveload import EconomyNotOpened, load_state, save_state
from sim.engine.nodes_price_note import note_path

played = sim(capital=1e9)
path = os.path.join(tempfile.mkdtemp(), "session.json")
save_state(played, path)
check("a save writes the note of its tree's pricing", os.path.exists(note_path(path)))


def built(defer):
    game = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                 civ=S.load_civ("rome_100ad"), cfg=None, defer_economy=defer)
    game.goal, game.done_year = GOAL, {}
    return game


normal, deferred = built(False), built(True)
check("a deferred game has not opened its economy", not deferred.economy.agent.opened())
load_state(normal, path)
load_state(deferred, path)
check("the tree's money fields are the same", normal.nodes == deferred.nodes)
check("the deferred game still lacks nothing: its economy opens from the record",
      deferred.economy.agent.opened() and deferred.labour.money_per_labour_hour() == normal.labour.money_per_labour_hour())
other_path = os.path.join(tempfile.mkdtemp(), "again.json")
save_state(normal, other_path)
save_state(deferred, other_path + "2")
with open(other_path) as first, open(other_path + "2") as second:
    check("both save the same text", first.read() == second.read())

os.remove(note_path(path))
refused = False
try:
    load_state(built(True), path)
except EconomyNotOpened:
    refused = True
check("without the note a deferred game refuses the save", refused)
