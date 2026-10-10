"""Two seats in one whole game (slow: builds a game): both step with the year, hazards hit each by its own works
and the world once, one seat's end leaves the other playing, and a save keeps both."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import load_state, save_state

game = sim(civ="rome_100ad", capital=1000.0, events=True)
game.join_seat("second", {"capital": 300.0, "country": None})
first_year = game.year
second_capital_before = game.state.seats["second"].household.capital
game.step()
check("the year advanced once for two seats", game.year == first_year + 1, game.year)
check("the second seat's purse moved with the year (its living costs and interest are its own)",
      game.state.seats["second"].household.capital != second_capital_before, None)
check("the first seat's purse is not the second's",
      game.state.seats["founder"].household is not game.state.seats["second"].household, None)

# the end rule: the second seat's run ends, the first goes on
game.state.seats["second"].founder.dead_reason = "denounced: as a sorcerer"
check("the run is not over while a seat plays", not game.run_over() and game.playing_seats() == ["founder"], game.playing_seats())
year_before = game.year
ended_capital = game.state.seats["second"].household.capital
game.step()
check("the year still advances for the seat that plays", game.year == year_before + 1, game.year)
check("an ended seat's purse is not stepped", game.state.seats["second"].household.capital == ended_capital, None)

# save and load keep both seats
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    load_state(game, path)
check("a save keeps both seats and who has ended",
      sorted(game.state.seats) == ["founder", "second"] and game.ended_seats() == ["second"], list(game.state.seats))
