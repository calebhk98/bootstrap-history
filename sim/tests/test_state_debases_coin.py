"""Complaint 272: the cut a struck-coin state decides on lowers the metal in its coin each year, through
the currency's own debasement; a state that cuts nothing leaves the coin alone."""
from .harness import *  # noqa: F401,F403
import random

from sim.agents.api import COIN_RESTRIKE_SHARE_PER_YEAR
from sim.agents.government import Government
from sim.economy import currency


def agent_game(civ):
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ(civ),
                 cfg={"agent_economy": True})
    game.goal, game.done_year = GOAL, {}
    return game


def home_coin(game):
    return game.economy.agent.economy().record.currency


spec = currency.currency_from_coin_standard("realm", {"regime": "struck_coin", "material": "silver_kg",
                                                      "kg_per_unit": 0.0027, "source": "test"}, "denarius", issuer="state")
lighter = currency.debase_by_cut(spec, 0.2, 0.1)
check("a cut over the share struck again lowers the average coin's metal by their product",
      abs(lighter.backing_per_unit - spec.backing_per_unit * (1.0 - 0.2 * 0.1)) < 1e-15, lighter)
check("no cut leaves the coin as it was", currency.debase_by_cut(spec, 0.0, 0.1) == spec)
fiat = currency.currency_from_coin_standard("x", {"regime": "fiat"}, "note", issuer="state")
check("a coin that is not struck is left alone", currency.debase_by_cut(fiat, 0.2, 0.1) == fiat)



def deciding(cut):
    """A government that decides this cut each year, whatever its purse says."""
    def decide(self, world):
        self.record.coin_cut_share = cut
        return cut
    return decide


def metal_change_in_a_year(game, cut):
    original = Government.decide_debasement
    Government.decide_debasement = deciding(cut)
    try:
        before = home_coin(game).backing_per_unit
        game.step()
    finally:
        Government.decide_debasement = original
    return home_coin(game).backing_per_unit / before


for civ in ("rome_100ad",):
    game = agent_game(civ)
    game.step()
    check("%s: a state that cuts nothing leaves the metal in the coin" % civ,
          metal_change_in_a_year(game, 0.0) == 1.0)
    check("%s: the state's cut lowers the metal in the coin once, by the cut over the share struck again" % civ,
          abs(metal_change_in_a_year(game, 0.2) - (1.0 - 0.2 * COIN_RESTRIKE_SHARE_PER_YEAR)) < 1e-9)
