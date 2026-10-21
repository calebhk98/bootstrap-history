"""Scenario for Complaint 644 in a whole game: teaching machinists in Rome 100 AD gives partial hands inside the stall
window. The rules are in test_trade_first_hands."""
from .harness import *  # noqa: F401,F403
from sim.engine.projects_trade_wait import STALL_YEARS_BEFORE_ABANDONMENT, years_until_trade_has_hands
from .agent_command_helpers import ask_agent

COUNT = 2
game = sim(civ="rome_100ad", capital=500000)
ask_agent(game, cmd="train", trade="machinist", n=COUNT)
rows = [row for row in game.state.household.training if row[2] == "machinist"]
check("the cohort is written as an early slice and the rest", len(rows) == 2, rows)
check("the rows add up to the people taught", abs(sum(row[3] for row in rows) - COUNT) < 1e-9, rows)
wait = years_until_trade_has_hands(game, "machinist")
check("the first hands arrive inside the stall window", wait is not None and wait < STALL_YEARS_BEFORE_ABANDONMENT - 1, wait)
check("the rest arrive later", rows[0][1] < rows[1][1], rows)
