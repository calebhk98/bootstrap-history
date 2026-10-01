"""Other economies trade through the home market's books (Complaints/113).

A foreign economy named in data/world/foreign_economies.json has its own
solved long-run costs and market. Goods cross when the price gap exceeds the
freight over the route: imports cap the home price in a shortage, exports
lift the price abroad, and the founder's sales are part of the same market.
"""
from .harness import *  # noqa: F401,F403

SILK = "silk_kg"
HIGH_VALUE_GOOD = "silver_kg"
PARTNER = "han_china_100ad"


def rome():
    return sim(civ="rome_100ad", capital=1e9)


def without_trade(simulation):
    simulation.foreign_economies = lambda: []
    return simulation


def shortage(simulation, commodity, share=0.3):
    entry = simulation._market_entry(commodity)
    entry["capacity_tonnes"] *= share
    return simulation


def cheap_partner(simulation, home_price=10.0, foreign_price=100.0, freight=1.0):
    """A partner whose prices and route are stated, to isolate the flow rule."""
    simulation._foreign_price_pair = lambda commodity, facts: (home_price, foreign_price)
    simulation._route_freight_per_tonne = lambda civilization: freight
    simulation.household._foreign_facts_cache = None
    return simulation


# --- who trades: from data, never an engine id.
s = rome()
check("the data file names the economies that trade with Rome in its year",
      s.foreign_economies() == [PARTNER], s.foreign_economies())
check("...an economy never trades with itself",
      sim(civ=PARTNER, capital=1e9).foreign_economies() == [], None)
check("...and one outside its years does not trade",
      sim(civ="england_1300", capital=1e9).foreign_economies() == [], None)
facts = s._foreign_economy_facts(PARTNER)
check("the partner's prices are its own solved costs in home money",
      facts["prices_in_home_money"] and facts["prices_in_home_money"] != s._material_prices(), None)
check("freight over the route is a finite positive cost per tonne",
      0.0 < facts["freight_per_tonne"] < float("inf"), facts["freight_per_tonne"])

# --- the opening is in balance with a partner whose costs are close: nothing moves for cheap bulk goods.
check("a bulk good the route cannot pay for is not traded",
      s.market_state("iron")["trade_tonnes"] == 0.0, s.market_state("iron")["trade_tonnes"])
check("a good the partner cannot make with its own technologies is not traded",
      all(s._foreign_price_pair(good, facts) is None for good in ("xenon_g", "caesium_g")), None)
check("land does not cross a border",
      s._foreign_price_pair("hectare_land", facts) is None, None)

# --- imports cap a home shortage.
traded = cheap_partner(shortage(rome(), SILK), home_price=100.0, foreign_price=10.0)
alone = without_trade(shortage(rome(), SILK))
check("a home shortage with no trade pushes the price well above cost",
      alone.market_price_ratio(SILK) > 1.5, alone.market_price_ratio(SILK))
check("a cheaper partner over a cheap route caps the shortage price",
      traded.market_price_ratio(SILK) < alone.market_price_ratio(SILK),
      (traded.market_price_ratio(SILK), alone.market_price_ratio(SILK)))
check("...and goods come in",
      traded.market_state(SILK)["trade_tonnes"] > 0.0, traded.market_state(SILK).get("trade_tonnes"))
dear_route = cheap_partner(shortage(rome(), SILK), home_price=100.0, foreign_price=10.0,
                           freight=1000.0)
check("freight dearer than the gap keeps the shortage price",
      abs(dear_route.market_price_ratio(SILK) - alone.market_price_ratio(SILK)) < 1e-9, None)

# --- exports raise the price abroad, and flow out of the home market.
exporter = cheap_partner(rome(), home_price=10.0, foreign_price=100.0)
check("a dearer partner draws exports from the home market",
      exporter.market_state(SILK)["trade_tonnes"] < 0.0,
      exporter.market_state(SILK).get("trade_tonnes"))
check("...which lifts the home price above its long-run cost",
      exporter.market_price_ratio(SILK) > 1.0, exporter.market_price_ratio(SILK))
exporter.step()
check("...and the partner's price falls with the goods it receives",
      exporter.state.economy.foreign_market_book[PARTNER][SILK]["price_ratio"] < 1.0, None)
traded.step()
check("what home imports in a shortage lifts the price abroad, which sells it",
      traded.state.economy.foreign_market_book[PARTNER][SILK]["price_ratio"] > 1.0, None)
check("...and the year's tonnage is recorded",
      exporter.foreign_trade_summary()["exports_tonnes"] > 0.0, exporter.foreign_trade_summary())

# --- the founder's sales go through the same market.
seller = cheap_partner(rome(), home_price=100.0, foreign_price=100.0, freight=1.0)
seller._material_stock()[SILK] = seller.market_state(SILK)["capacity_tonnes"] * 0.5
no_partner = without_trade(rome())
no_partner._material_stock()[SILK] = seller._material_stock()[SILK]
seller.sell_material_stock(SILK, seller._material_stock()[SILK])
no_partner.sell_material_stock(SILK, no_partner._material_stock()[SILK])
check("a founder's sale is cushioned by a partner who buys: the closing price falls less",
      seller.market_state(SILK)["price_ratio_if_year_closed_now"]
      > no_partner.market_state(SILK)["price_ratio_if_year_closed_now"],
      (seller.market_state(SILK)["price_ratio_if_year_closed_now"],
       no_partner.market_state(SILK)["price_ratio_if_year_closed_now"]))

# --- the foreign book saves and loads.
s = cheap_partner(rome(), home_price=10.0, foreign_price=100.0)
s.step()
_save_path = os.path.join(tempfile.gettempdir(), "foreign_market_book_save_test.json")
_protocol.save_state(s, _save_path)
s_loaded = rome()
_protocol.load_state(s_loaded, _save_path)
os.remove(_save_path)
check("the foreign book survives a save and a load",
      s_loaded.state.economy.foreign_market_book == s.state.economy.foreign_market_book,
      None)

# --- the data file only names civilisations that exist.
from sim.engine.foreign_economies import foreign_economy_records
for _record in foreign_economy_records():
    check("a foreign economy names a civilisation file that exists: " + _record["civilization"],
          os.path.exists(os.path.join(ROOT, "data", "civilizations",
                                      _record["civilization"] + ".json")), None)
