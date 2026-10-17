"""Shared by the money-regime topics: a civilisation played on the agent economy with and without freshly mined
metal, and the checks on what the extra metal does to the money stock, the price level and the mint."""
import statistics

from .harness import *  # noqa: F401,F403
from sim.economy import mint
from sim.economy.types import EDGE_PRODUCTION, GoodsMove

REGIME_OF = {"england_1300": "struck_coin", "han_china_100ad": "struck_coin", "rome_100ad": "struck_coin",
             "norse_900ad": "weighed_metal", "mexica_1500": "commodity"}

# Years for freshly mined metal to pass from mine owners and savers into prices: the fewest each civilisation's
# price level needs to rise clear of its unmined twin.
MONEY_LAG_YEARS = {"england_1300": 5, "norse_900ad": 8}
# The price level still cycles in the first decades (Complaint 473), so it is compared as a mean over these years
# from the lag on, not at one year that may sit in a trough of the cycle. Norse silver passes into prices late and
# against a level that drifts up on the short spin-up (Complaint 526), so its window is later and wider.
PRICE_LEVEL_YEARS = {"england_1300": 4, "norse_900ad": 7}


def agent_game(civ):
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ(civ))
    game.goal, game.done_year = GOAL, {}
    return game


def play(civ, years, mined_share=0.0, levels=None):
    """Years of play; each year the first merchant lands `mined_share` of the metal in circulation as
    freshly mined metal, to sell on the market. Returns (money, price level, record, setup); `levels`, when
    given, gets each year's price level."""
    game = agent_game(civ)
    economy = game.economy.agent.economy()
    record, setup = economy.record, economy.setup
    spec = record.currency
    for _year in range(years):
        if mined_share > 0.0:
            merchant = record.merchants[sorted(record.merchants)[0]]
            embodied = record.book.money_supply(spec.currency_id) * spec.backing_per_unit
            record.book.move(GoodsMove(EDGE_PRODUCTION, merchant.agent_id, spec.backing_good, merchant.home_tile,
                                       embodied * mined_share, "mined"))
        game.step()
        if levels is not None:
            levels.append(record.memory.basket_price_levels[spec.currency_id])
    return (record.book.money_supply(spec.currency_id), record.memory.basket_price_levels[spec.currency_id], record, setup)


def check_more_metal_raises_money(civ_id):
    regime = REGIME_OF[civ_id]
    # new coin reaches prices with a lag: it lands with mine owners and savers before it is spent
    window = PRICE_LEVEL_YEARS[civ_id]
    years = MONEY_LAG_YEARS[civ_id] + window - 1
    base_levels, more_levels = [], []
    base_money, _base_level, _record, _setup = play(civ_id, years, levels=base_levels)
    more_money, _more_level, record, setup = play(civ_id, years, mined_share=0.1, levels=more_levels)
    base_level = statistics.fmean(base_levels[-window:])
    more_level = statistics.fmean(more_levels[-window:])
    check("%s (%s): more metal mined raises the money stock" % (civ_id, regime), more_money > 1.2 * base_money,
          (base_money, more_money))
    check("%s (%s): and the price level" % (civ_id, regime), more_level > 1.03 * base_level, (base_level, more_level))
    spec = record.currency
    held = sum(mint.stock_by_tile(record.book, spec.backing_good).values())
    check("%s (%s): the mint holds the metal of the money in circulation, no less" % (civ_id, regime),
          held >= 0.99 * record.book.money_supply(spec.currency_id) * spec.backing_per_unit)
    check("%s (%s): money and goods are conserved" % (civ_id, regime), record.book.check_conservation(1e-9).ok)
