"""Complaints 359 and 364: sellers and buyers go through one goods market, and a good nothing
offers has no price households spend on.

The founder, a firm and the state all deal with `Sim.goods_market`; the same sale moves the
clearing price the same way whoever makes it, firm output is supply in the book, and a good no
home technique in reach and no partner offers draws no household spending.
"""
from .harness import *  # noqa: F401,F403

from sim.engine.actors import SimWorld
from sim.engine.goods_market_api import FOUNDER
from sim.engine.market_demand import household_demand_by_material
from sim.engine.state import ActorRecord
from sim.engine.project_materials import tonnes_per_unit

MATERIAL = "iron"


def closing_ratio(game, material=MATERIAL):
    return game.market_state(material)["price_ratio_if_year_closed_now"]


# --- the same sale moves the clearing price the same way, whoever makes it ---------------------
founder_game = sim(civ="rome_100ad", capital=1e9)
firm_game = sim(civ="rome_100ad", capital=1e9)
control = sim(civ="rome_100ad", capital=1e9)
tonnes = control.market_state(MATERIAL)["capacity_tonnes"] * 0.05
founder_game.goods_market.note_sale(FOUNDER, MATERIAL, tonnes)
firm_game.goods_market.note_sale("firm:1", MATERIAL, tonnes)
check("a sale by the founder lowers the price the year would close at",
      closing_ratio(founder_game) < closing_ratio(control) - 1e-6,
      (closing_ratio(founder_game), closing_ratio(control)))
check("...and the same sale by a firm moves it exactly the same way",
      abs(closing_ratio(founder_game) - closing_ratio(firm_game)) < 1e-12,
      (closing_ratio(founder_game), closing_ratio(firm_game)))

selling = sim(civ="rome_100ad", capital=1e9)
selling._material_stock()[MATERIAL] = tonnes
sold = selling.sell_material_stock(MATERIAL, tonnes)
check("the founder's own stock sale is entered in the same book under his name, and lowers the price",
      sold > 0 and abs(selling.goods_market.sold_tonnes(MATERIAL, FOUNDER) - sold) < 1e-9
      and selling.goods_market.others_sold_tonnes(MATERIAL) == 0.0
      and closing_ratio(selling) < closing_ratio(control),
      (sold, closing_ratio(selling), closing_ratio(control)))
check("a firm's sales are in the posted price; the founder's own orders stay out of it",
      firm_game.market_state(MATERIAL)["price_ratio"] < control.market_state(MATERIAL)["price_ratio"]
      and founder_game.market_state(MATERIAL)["price_ratio"] == control.market_state(MATERIAL)["price_ratio"],
      (firm_game.market_state(MATERIAL)["price_ratio"], founder_game.market_state(MATERIAL)["price_ratio"]))
check("the founder has no second path in: the old note methods are gone from the engine",
      not any(hasattr(founder_game, name) for name in
              ("market_note_sale", "market_note_purchase", "market_note_draw")))

# --- a buyer other than the founder raises demand in the same book -----------------------------
buying = sim(civ="rome_100ad", capital=1e9)
buying.goods_market.note_purchase("government:rome", MATERIAL, tonnes)
check("the state's purchases reach the book as the actors' demand",
      abs(buying.actor_demand(MATERIAL) - tonnes) < 1e-9 and closing_ratio(buying) > closing_ratio(control),
      (buying.actor_demand(MATERIAL), closing_ratio(buying)))
founder_buys = sim(civ="rome_100ad", capital=1e9)
founder_buys.goods_market.note_purchase(FOUNDER, MATERIAL, tonnes)
check("...while the founder's purchases are his own, not the actors'",
      founder_buys.actor_demand(MATERIAL) == 0.0 and abs(closing_ratio(founder_buys) - closing_ratio(buying)) < 1e-12,
      (founder_buys.actor_demand(MATERIAL), closing_ratio(founder_buys), closing_ratio(buying)))

# --- firm output is supply in the book ---------------------------------------------------------
FURNACE_MATERIAL = "pig_iron_kg"
furnace_game = sim(civ="rome_100ad", capital=1e9)
no_firm = sim(civ="rome_100ad", capital=1e9)
year = furnace_game.state.scenario.year
firm = furnace_game.actors.add("firm:iron1", ActorRecord(kind="firm", money=1.0e9))
firm.concerns.add("blast_furnace")
firm.knowledge.add("blast_furnace")
firm.record.opened_year["blast_furnace"] = year - 10
furnace_game.advance_actors(year)
no_firm.advance_actors(year)
sold_by_firm = furnace_game.goods_market.sold_tonnes(furnace_game._material_tag(FURNACE_MATERIAL)[0], "firm:iron1")
check("a firm running a furnace puts the pig iron it makes into the book as its sale",
      sold_by_firm > 0.0, sold_by_firm)
check("...and the market counts it as the actors' supply",
      furnace_game.market_state(FURNACE_MATERIAL)["actor_supply_tonnes"] > 0.0
      and abs(furnace_game.actor_supply(FURNACE_MATERIAL) - sold_by_firm) < 1e-9,
      (furnace_game.market_state(FURNACE_MATERIAL)["actor_supply_tonnes"], sold_by_firm))
check("...so the firm's output lowers the price the market posts",
      furnace_game.market_price_ratio(FURNACE_MATERIAL) < no_firm.market_price_ratio(FURNACE_MATERIAL),
      (furnace_game.market_price_ratio(FURNACE_MATERIAL), no_firm.market_price_ratio(FURNACE_MATERIAL)))
furnace_world = SimWorld(furnace_game)
furnace_node = furnace_game.nodes["blast_furnace"]
check("the furnace is not a goods-category concern, so its takings carry only the output market factor",
      furnace_node.get("cat") not in furnace_game.GOODS_CATEGORIES, furnace_node.get("cat"))
expected_takings = (furnace_game.concern_takings("blast_furnace", furnace_world.ramp(year - 10))
                    * furnace_game.node_output_market_factor(furnace_node))
check("a firm's takings carry the same output market factor the founder's do",
      abs(furnace_world.concern_takings("blast_furnace", year - 10) - expected_takings) < 1e-6 * expected_takings,
      (furnace_world.concern_takings("blast_furnace", year - 10), expected_takings))

# --- a good nobody offers has no household price and draws no spending -------------------------
rome = sim(civ="rome_100ad", capital=1e9)
market = rome.goods_market
check("pepper is priced only as the mature technique would price it", rome.material_price_basis("pepper_kg") == "mature")
check("no home technique in reach and no partner offers pepper", market.offered_by("pepper_kg") is None,
      market.offered_by("pepper_kg"))
prices = market.household_prices()
check("so households are given no price for it", "pepper_kg" not in prices)
per_hour = rome.money_per_labour_hour()
wanted = household_demand_by_material({material: price / per_hour for material, price in prices.items() if price > 0.0},
                                      rome._opening_population(), 550.0)
check("and the need it served draws no spending on it", wanted.get("pepper_kg", 0.0) == 0.0, wanted.get("pepper_kg"))
check("a commodity nobody offers has no market book entry", rome.market_state("pepper_kg") is None)
check("a good the home makes keeps its price", "wheat_kg" in prices or "fabric_kg" in prices)

check("a partner offers cassia", market.offered_by("cassia_kg") == "han_china_100ad", market.offered_by("cassia_kg"))
facts = rome._foreign_economy_facts("han_china_100ad")
landed = (facts["prices_in_home_money"]["cassia_kg"] * rome.partner_price_level("han_china_100ad")
          * (1.0 + rome._trader_cost_share(facts["route"]))
          + facts["freight_per_tonne"] * tonnes_per_unit("cassia_kg"))
check("...and households pay what it costs the partner plus freight plus merchants' terms",
      abs(prices["cassia_kg"] - landed) < 1e-9 * landed, (prices["cassia_kg"], landed))
