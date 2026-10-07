"""Complaint 467: the opening game's skilled trades hold about as many people as employers will want hours
for in the first year, not several times as many (a glutted trade pays the floor)."""
from .harness import *  # noqa: F401,F403

from sim.economy import labour_state, producers

GLUT_LIMIT = 3.0   # a trade may hold this many times the hours bid before it counts as glutted

game = sim(civ="rome_100ad", events=False)
game.economy.open_agent()
economy = game.economy.agent.economy()
record, setup = economy.record, economy.setup
view = economy.view()
bid_hours = {}
for producer_id, producer in sorted(record.producers.items()):
    plan = producers.plan(producer, setup.recipes[producer.recipe_id], view,
                          record.book.balance(producer_id, setup.currency_id))
    for bid in plan.labour_bids:
        bid_hours[bid.trade] = bid_hours.get(bid.trade, 0.0) + bid.hours
people = labour_state.people_by_trade_everywhere(record.workforce)
skilled = [trade for trade, spec in setup.trades.items() if spec.training_years > 0.0 and bid_hours.get(trade, 0.0) > 0.0]
check("the opening has skilled trades that producers bid for", len(skilled) >= 2, skilled)
ratios = {trade: people.get(trade, 0.0) * setup.working_hours_per_year / bid_hours[trade] for trade in skilled}
check("no skilled trade opens holding several times the hours producers bid in year one",
      all(ratio <= GLUT_LIMIT for ratio in ratios.values()), ratios)
