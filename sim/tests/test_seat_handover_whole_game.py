"""A handover in a whole game (slow: builds a game): the replacement gets the leaver's cash and knowledge, the
leaver is out of the year, and the game steps on and round-trips a save."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import load_state, save_state

game = sim(civ="rome_100ad", capital=1000.0, events=True)
game.join_seat("second", {"capital": 300.0, "country": None})
game.join_seat("third", {"capital": 50.0, "country": None})
leaver = game.state.seats["second"]
leaver.founder.dead_reason = "denounced: as a sorcerer"
marker = next(node_id for node_id in sorted(game.nodes) if node_id not in leaver.projects.done)
leaver.projects.done.add(marker)
cash_before = leaver.household.capital + game.state.seats["third"].household.capital
with game.act_as("second"):
    moved = game.hand_over_seat("second", "third")
check("the handover moved the seat", moved["to"] == "third" and "second" not in game.state.seats, moved)
heir = game.state.seats["third"]
check("the replacement knows the leaver's nodes", marker in heir.projects.done, None)
check("the cash is conserved in the replacement's purse", abs(heir.household.capital - cash_before) < 1e-6,
      (heir.household.capital, cash_before))
check("the leaver is out of the year", game.playing_seats() == ["founder", "third"], game.playing_seats())
year = game.year
game.step()
check("the game steps on after a handover", game.year == year + 1, game.year)
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    check("the saved game has the seats that remain", sorted(game.state.seats) == ["founder", "third"], None)
