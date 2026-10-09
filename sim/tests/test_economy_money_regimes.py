"""Each civilisation's money works as its own regime on the agent economy: England struck silver with a
mint charge, Norse weighed silver, Han and Rome struck coin, Mexica cacao beans. More metal mined
raises the money stock and the price level under struck and weighed money, and the mint holds the metal
of the money in circulation."""
from .harness import *  # noqa: F401,F403
from sim.economy import mint
from sim.economy.types import EDGE_PRODUCTION, GoodsMove

REGIME_OF = {"england_1300": "struck_coin", "han_china_100ad": "struck_coin", "rome_100ad": "struck_coin",
             "norse_900ad": "weighed_metal", "mexica_1500": "commodity"}


def agent_game(civ):
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ(civ))
    game.goal, game.done_year = GOAL, {}
    return game


def play(civ, years, mined_share=0.0):
    """Years of play; each year the first merchant lands `mined_share` of the metal in circulation as
    freshly mined metal, to sell on the market. Returns (money, price level, record, setup)."""
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
    return (record.book.money_supply(spec.currency_id), record.memory.basket_price_levels[spec.currency_id], record, setup)


for civ_id, regime in sorted(REGIME_OF.items()):
    standard = S.load_civ(civ_id)["coin_standard"]
    check("%s's data names its money regime, %s" % (civ_id, regime), standard.get("regime") == regime, standard)
check("England's mint keeps a charge", S.load_civ("england_1300")["coin_standard"]["mint_charge_share"] > 0.0)
check("only a struck coin carries a mint charge in the data", all(
    "mint_charge_share" not in S.load_civ(civ_id)["coin_standard"] for civ_id, regime in REGIME_OF.items()
    if regime != "struck_coin"))
production = json.load(open(os.path.join(ROOT, "data", "production", "94_agri_organics_gaps.json")))["materials"]
check("Mexica's money is made of cacao, a good in the production catalogue",
      S.load_civ("mexica_1500")["coin_standard"]["material"] in production
      and "cacao_kg" in production["cacao_kg"]["outputs"])

for civ_id in ("england_1300", "norse_900ad"):
    regime = REGIME_OF[civ_id]
    # new coin reaches prices with a lag: it lands with mine owners and savers before it is spent
    base_money, base_level, _record, _setup = play(civ_id, 8)
    more_money, more_level, record, setup = play(civ_id, 8, mined_share=0.1)
    check("%s (%s): more metal mined raises the money stock" % (civ_id, regime), more_money > 1.2 * base_money,
          (base_money, more_money))
    check("%s (%s): and the price level" % (civ_id, regime), more_level > 1.03 * base_level, (base_level, more_level))
    spec = record.currency
    held = sum(mint.stock_by_tile(record.book, spec.backing_good).values())
    check("%s (%s): the mint holds the metal of the money in circulation, no less" % (civ_id, regime),
          held >= 0.99 * record.book.money_supply(spec.currency_id) * spec.backing_per_unit)
    check("%s (%s): money and goods are conserved" % (civ_id, regime), record.book.check_conservation(1e-9).ok)

money, _level, record, setup = play("mexica_1500", 4)
check("Mexica runs four years on cacao money with money and goods conserved",
      record.currency.regime == "commodity" and record.currency.backing_good == "cacao_kg"
      and money > 0.0 and record.book.check_conservation(1e-9).ok, record.book.check_conservation(1e-9).breaches[:3])
check("Mexica's cacao is produced and traded", any(volume > 0.0 for key, volume in record.volumes.items()
                                                  if key.startswith("cacao_kg|")))
