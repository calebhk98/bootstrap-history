"""Complaints/507 stage 5: in a settled economy a traded good sells near what it costs to make at the economy's own
input prices and wages. The cost is the calculator's (`CostBook.cheapest_cost`, plant charged), the price the
economy's. Bounds are from the subject: a market that wanders from cost by more than a factor of three for most of
its goods is not pricing off cost, and a typical good selling below its full cost would not be remade."""
from .harness import *  # noqa: F401,F403

from sim.engine.economy_cost_book import economy_cost_book

YEARS = 4
FACTOR = 3.0
SHARE_WITHIN_FACTOR = 0.5

game = sim(civ="rome_100ad", capital=1e9)
for _year in range(YEARS):
    game._step_market()
book = economy_cost_book(game)
prices = game.goods_market.household_prices()
traded = game.economy.agent_traded_volumes() or {}
held = frozenset(game.state.projects.granted)
ratios = sorted(prices[good] / cost for good in sorted(prices)
                if traded.get(good) for cost in (book.cheapest_cost(good, held),) if cost)
check("the economy trades goods the calculator can cost", len(ratios) >= 30, len(ratios))
median = ratios[len(ratios) // 2]
within = sum(1 for ratio in ratios if 1.0 / FACTOR <= ratio <= FACTOR) / max(1, len(ratios))
check("the typical traded good sells at no less than its cost of making and no more than a factor over it",
      1.0 <= median <= FACTOR, median)
check("at least half the traded goods sell within a factor of three of their cost, either way",
      within >= SHARE_WITHIN_FACTOR, within)
