"""BASELINE VALIDATION (CLAUDE.md 4.2, Complaint 640): Complaint 467 (scenario, a baseline validation of the opening): the opening game's skilled trades hold about as many
people as employers will want hours for in the first year, not several times as many (a glutted trade pays the floor).

It is the opening's workforce read against the same opening's producer, mint and state bids, so it needs the opened
economy: no single rule produces it."""
from .harness import *  # noqa: F401,F403

from sim.economy import labour_state, mint, mint_labour, producers, state_budget

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
# the other employers' jobs are jobs too: the mint's yearly capacity and the state's wage bids, as the year posts them
for trade, hours in mint_labour.capacity_hours(setup, record.currency, mint.capacity_fine_kilograms(setup, record)).items():
    bid_hours[trade] = bid_hours.get(trade, 0.0) + hours
for bid in state_budget.wage_labour_bids(setup, record, view, record.state_budget.wage_budget):
    bid_hours[bid.trade] = bid_hours.get(bid.trade, 0.0) + bid.hours
people = labour_state.people_by_trade_everywhere(record.workforce)
# the plot trade's people work their own land (556b), so no employer's bid is what they wait on
plots = labour_state.plot_trade(setup)
skilled = [trade for trade, spec in setup.trades.items()
           if spec.training_years > 0.0 and trade != plots
           and bid_hours.get(trade, 0.0) >= setup.working_hours_per_year]   # under one worker-year of jobs is no job market
check("the opening has skilled trades that producers bid for", len(skilled) >= 2, skilled)
ratios = {trade: people.get(trade, 0.0) * setup.working_hours_per_year / bid_hours[trade] for trade in skilled}
check("no skilled trade opens holding several times the hours producers bid in year one",
      all(ratio <= GLUT_LIMIT for ratio in ratios.values()), ratios)
