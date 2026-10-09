"""The opening workforce includes the trades the mint strikes with, so the mint can hire its engravers
(an England with no engraver in the capital's labour area never struck a coin)."""
from .harness import *  # noqa: F401,F403
from sim.economy import mint, mint_labour
from sim.economy.setup import labour_area

game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ("england_1300"),
             cfg={"agent_economy": True})
economy = game.economy.agent.economy()
record, setup = economy.record, economy.setup
needed = mint_labour.capacity_hours(setup, record.currency, mint.capacity_fine_kilograms(setup, record))
staff = record.workforce.workers.get(labour_area(setup.capital_tile), {})
check("the mint's recipe asks for hours in a trade beyond the unskilled one", len(needed) > 1, needed)
for trade in sorted(needed):
    check("the capital's labour area opens with %s workers for the mint" % trade, sum(staff.get(trade, [])) > 0.0)
