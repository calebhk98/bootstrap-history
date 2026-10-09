"""The live engine's yearly material market (Complaints/135, 102).

A material's spot price is its long-run cost times a ratio from a market that
clears each year from stock, the society's capacity and demand (households
from population and income, plus what the founder buys). These checks pin
that the ratio is neutral at the opening, moves with population, income,
stock windfalls and the founder's own trades, and that the society's
capacity follows the price.
"""
from .harness import *  # noqa: F401,F403
from functools import partial

sim = partial(sim, agent_economy=False)   # legacy: pins the engine's own yearly material market



MATERIAL = "iron"


def quote_buy(simulation, material=MATERIAL):
    return simulation.material_trade_quote(material)["buy_per_tonne"]


# --- the opening is in long-run balance: every price is the old one.
s = sim(civ="rome_100ad", capital=1e9)
check("a fresh society's market is in balance: spot ratio is exactly one",
      abs(s.market_price_ratio(MATERIAL) - 1.0) < 1e-9, s.market_price_ratio(MATERIAL))
check("...for a material nobody ever named too",
      abs(s.market_price_ratio("fabric_kg") - 1.0) < 1e-9, s.market_price_ratio("fabric_kg"))
check("...but not for one only a partner makes: its trade has to be built, so it opens dear",
      s.market_price_ratio("silk_kg") > 1.5, s.market_price_ratio("silk_kg"))
check("the actors' supply is one stub call, zero until firms exist",
      s.actor_supply(MATERIAL) == 0.0, s.actor_supply(MATERIAL))

# --- population drives household demand: a plague lowers it, capacity does not follow at once.
s = sim(civ="rome_100ad", capital=1e9)
s._apply_population_mortality_shock(0.4)
ratio_after_plague = s.market_price_ratio(MATERIAL)
check("a plague that kills much of the population leaves a glut: price below long-run cost",
      ratio_after_plague < 0.95, ratio_after_plague)
check("...and the glut is bounded by the cost of capacity already built",
      ratio_after_plague >= s.market_state(MATERIAL)["floor_ratio"] - 1e-9, ratio_after_plague)
check("...and the quote the founder sees falls with it",
      quote_buy(s) < quote_buy(sim(civ="rome_100ad", capital=1e9)), quote_buy(s))

# --- more people drive it the other way.
s = sim(civ="rome_100ad", capital=1e9)
s.population.children *= 2.0
s.population.working_age *= 2.0
s.population.elderly *= 2.0
check("a society twice as large buys more and the shortage lifts the price above long-run cost",
      s.market_price_ratio(MATERIAL) > 1.05, s.market_price_ratio(MATERIAL))

# --- stock windfall: every household finds iron in their room.
s = sim(civ="rome_100ad", capital=1e9)
before = s.market_price_ratio(MATERIAL)
s.goods_market.add_stock(MATERIAL, s.market_state(MATERIAL)["capacity_tonnes"] * 0.5)
after = s.market_price_ratio(MATERIAL)
check("a windfall of stock lowers the price at once, with no production change",
      after < before - 0.05, (before, after))

# --- the founder's trades reach the market: counted through the year, they
# clear with it when it closes. The quote within the year keeps its own
# marginal curves, so the posted price does not jump on one's own order.
s = sim(civ="rome_100ad", capital=1e9)
base_state = s.market_state(MATERIAL)
tonnes = base_state["capacity_tonnes"] * 0.05
s.goods_market.note_purchase(s.goods_market.acting_party_id, MATERIAL, tonnes)
bought_state = s.market_state(MATERIAL)
check("what the founder buys adds demand: the year, closed now, would price higher",
      bought_state["price_ratio_if_year_closed_now"] > base_state["price_ratio_if_year_closed_now"],
      (base_state["price_ratio_if_year_closed_now"], bought_state["price_ratio_if_year_closed_now"]))
check("...while the posted price within the year does not move on one's own order",
      bought_state["price_ratio"] == base_state["price_ratio"], bought_state["price_ratio"])

s = sim(civ="rome_100ad", capital=1e9)
s_control = sim(civ="rome_100ad", capital=1e9)
state_before = s.market_state(MATERIAL)
s._material_stock()[MATERIAL] = state_before["capacity_tonnes"] * 0.02
sold = s.sell_material_stock(MATERIAL, s._material_stock()[MATERIAL])
state_after = s.market_state(MATERIAL)
check("the founder can sell iron into this market", sold > 0, sold)
check("what the founder sells reaches supply: the year, closed now, would price lower",
      state_after["price_ratio_if_year_closed_now"] < state_before["price_ratio_if_year_closed_now"],
      (state_before["price_ratio_if_year_closed_now"], state_after["price_ratio_if_year_closed_now"]))
check("...and the society's own producers lose the sales the founder took",
      state_after["society_sales_tonnes"] < state_before["society_sales_tonnes"]
      and state_after["displaced_by_founder_tonnes"] > 0,
      (state_before["society_sales_tonnes"], state_after["society_sales_tonnes"]))
s.step()
s_control.step()
check("a year on, the sale has left the society's producers with less capacity than "
      "an identical society whose founder sold nothing",
      s.market_state(MATERIAL)["capacity_tonnes"]
      < s_control.market_state(MATERIAL)["capacity_tonnes"],
      (s.market_state(MATERIAL)["capacity_tonnes"],
       s_control.market_state(MATERIAL)["capacity_tonnes"]))

# --- a year passes: capacity follows the price, and the price returns toward cost.
s = sim(civ="rome_100ad", capital=1e9)
s._apply_population_mortality_shock(0.4)
capacity_0 = s.market_state(MATERIAL)["capacity_tonnes"]
price_path = [s.market_price_ratio(MATERIAL)]
for _year in range(5):
    s.step()
    price_path.append(s.market_price_ratio(MATERIAL))
check("producers cut capacity while the price sits below cost",
      s.market_state(MATERIAL)["capacity_tonnes"] < capacity_0,
      (capacity_0, s.market_state(MATERIAL)["capacity_tonnes"]))
check("...and a glut's price recovers toward long-run cost as they do",
      price_path[-1] > price_path[0], price_path)

# --- a firm's output is one sale in the book: record it and watch the price.
s = sim(civ="rome_100ad", capital=1e9)
base_ratio = s.market_price_ratio(MATERIAL)
_firm_output = s.market_state(MATERIAL)["capacity_tonnes"] * 0.2
s.goods_market.note_sale("firm:stub", MATERIAL, _firm_output)
check("actor supply (once firms produce) lowers the price through the same clearing",
      s.market_price_ratio(MATERIAL) < base_ratio, (base_ratio, s.market_price_ratio(MATERIAL)))

# --- the state saves and loads with the market book.
s = sim(civ="rome_100ad", capital=1e9)
s._apply_population_mortality_shock(0.4)
for _year in range(2):
    s.step()
_save_path = os.path.join(tempfile.gettempdir(), "market_book_save_test.json")
_protocol.save_state(s, _save_path)
s_loaded = sim(civ="rome_100ad", capital=1e9)
_protocol.load_state(s_loaded, _save_path)
os.remove(_save_path)
check("the market book survives a save and a load",
      abs(s_loaded.market_state(MATERIAL)["capacity_tonnes"]
          - s.market_state(MATERIAL)["capacity_tonnes"]) < 1e-9,
      (s_loaded.market_state(MATERIAL)["capacity_tonnes"],
       s.market_state(MATERIAL)["capacity_tonnes"]))
