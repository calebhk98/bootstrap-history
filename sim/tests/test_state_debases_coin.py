"""Complaints 272 and 624: the cut a struck-coin state decides on is a recoinage. The coin struck again holds
less metal, the same metal makes more coin, and the new coin goes to the issuer; a state that cuts nothing
leaves the coin alone."""
from .harness import *  # noqa: F401,F403
import random

from sim.agents.api import COIN_RESTRIKE_SHARE_PER_YEAR
from sim.agents.government import Government
from sim.economy import currency


def agent_game(civ):
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ(civ))
    game.goal, game.done_year = GOAL, {}
    return game


def home_coin(game):
    return game.economy.agent.economy().record.currency


spec = currency.currency_from_coin_standard("realm", {"regime": "struck_coin", "material": "silver_kg",
                                                      "kg_per_unit": 0.0027, "source": "test"}, "denarius", issuer="state")
SUPPLY = 1000.0
struck = currency.units_struck_by_cut(spec, SUPPLY, 0.2, 0.1)
check("coin struck again at a cut yields the coin its saved metal makes", abs(struck - SUPPLY * 0.1 * 0.2 / 0.8) < 1e-12, struck)
lighter = currency.debase_by_cut(spec, SUPPLY, 0.2, 0.1)
check("the metal is conserved: more coin, each holding less",
      abs(lighter.backing_per_unit * (SUPPLY + struck) - spec.backing_per_unit * SUPPLY) < 1e-12, lighter)
check("no cut leaves the coin as it was", currency.debase_by_cut(spec, SUPPLY, 0.0, 0.1) == spec)
fiat = currency.currency_from_coin_standard("x", {"regime": "fiat"}, "note", issuer="state")
check("a coin that is not struck is left alone", currency.debase_by_cut(fiat, SUPPLY, 0.2, 0.1) == fiat)
check("a coin that is not struck yields nothing", currency.units_struck_by_cut(fiat, SUPPLY, 0.2, 0.1) == 0.0)



def deciding(cut):
    """A government that decides this cut each year, whatever its purse says."""
    def decide(self, world):
        self.record.coin_cut_share = cut
        return cut
    return decide


def money_supply(game):
    economy = game.economy.agent.economy()
    return economy.record.book.money_supply(economy.setup.currency_id)


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
    check("%s: the state's cut lowers the metal in the coin once, the coin it saves struck as more coin" % civ,
          abs(metal_change_in_a_year(game, 0.2) - 1.0 / (1.0 + 0.2 * COIN_RESTRIKE_SHARE_PER_YEAR / 0.8)) < 1e-9)
    before_supply = money_supply(game)
    metal_change_in_a_year(game, 0.2)
    check("%s: the coin saved is new money in circulation" % civ, money_supply(game) > before_supply, (before_supply, money_supply(game)))
