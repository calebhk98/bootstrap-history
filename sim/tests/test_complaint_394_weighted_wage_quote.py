"""Complaint 394 (wage quote): the engine's quoted wage of a trade weights each labour market by the hours
hired there, so a market where nobody is hired does not set the national figure."""
from .harness import *  # noqa: F401,F403
from sim.economy import api

game = sim()
agent = game.economy.agent
economy = agent.economy()
record = economy.record
trade = "weighted_wage_probe_trade"
record.memory.wages[trade + "|work@busy_tile"] = 10.0
record.memory.wages[trade + "|work@empty_tile"] = 1000.0
record.hours_hired[trade + "|work@busy_tile"] = 100.0
agent._answers = None
coin = economy.setup.coin_per_unit
quoted = agent.answers()[1][trade]
check("the quoted wage ignores a market with no hours hired", abs(quoted - 10.0 * coin) < 1e-9, quoted)
check("the quote is the economy api's weighted wage", abs(quoted - api.wages_by_trade_weighted(economy)[trade] * coin) < 1e-9)
