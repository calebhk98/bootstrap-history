"""Scenario for Complaint 624 in a whole game: the cut a Rome state decides on reaches the economy, which recoins at a
lighter weight, so the supply, the metal in each coin and the price level differ from a twin game that did not debase.
The rules are in test_state_debasement_prices."""
from .harness import *  # noqa: F401,F403
import random

from sim.agents.government import Government

YEARS = 3
CUT = 0.5   # of the metal in the coin struck again, each year: far past what a state does, so the effect stands clear of noise


def run(cut):
    original = Government.apply_debasement

    def decide(self, amount, world):   # the state's chosen cut, whatever the fiscal response covered
        self.record.coin_cut_share = cut
        return cut
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ("rome_100ad"))
    game.goal, game.done_year = GOAL, {}
    Government.apply_debasement = decide
    try:
        for _year in range(YEARS):
            game.step()
    finally:
        Government.apply_debasement = original
    agent = game.economy.agent
    economy = agent.economy()
    return {"supply": economy.record.book.money_supply(economy.setup.currency_id),
            "price_level": agent.outcomes[-1].basket_price_level,
            "backing": economy.record.currency.backing_per_unit}


twin = run(0.0)
debased = run(CUT)
check("a debasing state has more coin in circulation than its twin", debased["supply"] > 1.05 * twin["supply"], (debased, twin))
check("each coin holds less metal", debased["backing"] < twin["backing"], (debased, twin))
check("the price level rises against the twin within a few years", debased["price_level"] > 1.05 * twin["price_level"],
      (debased["price_level"], twin["price_level"]))
