"""Scenario, Complaints 359 and 364: through a running game, the founder's stock sale and a firm's furnace output go into
the one goods market as supply, a firm's takings carry the founder's output market factor, and the real Han is a partner
whose goods households pay the landed price for. The rules are in test_one_goods_market."""
from .harness import *  # noqa: F401,F403

from sim.engine.agents_port import SimWorld
from sim.engine.state import ActorRecord
from sim.engine.material_units import tonnes_per_unit
from sim.engine import foreign_economies as foreign_module
from unittest import mock

MATERIAL = "iron"
FURNACE_MATERIAL = "pig_iron_kg"


def closing_ratio(game, material=MATERIAL):
    return game.market_state(material)["price_ratio_if_year_closed_now"]


# --- the founder's own stock sale is entered in the same book, under his name, and lowers the price
control = sim(civ="rome_100ad", capital=1e9)
tonnes = control.market_state(MATERIAL)["capacity_tonnes"] * 0.05
selling = sim(civ="rome_100ad", capital=1e9)
selling._material_stock()[MATERIAL] = tonnes
sold = selling.sell_material_stock(MATERIAL, tonnes)
check("the founder's own stock sale is entered in the same book under his name, and lowers the price",
      sold > 0 and abs(selling.goods_market.sold_tonnes(MATERIAL, selling.goods_market.acting_party_id) - sold) < 1e-9
      and selling.goods_market.others_sold_tonnes(MATERIAL) == 0.0
      and closing_ratio(selling) < closing_ratio(control),
      (sold, closing_ratio(selling), closing_ratio(control)))

# --- firm output is supply in the book
furnace_game = sim(civ="rome_100ad", capital=1e9)
no_firm = sim(civ="rome_100ad", capital=1e9)
year = furnace_game.state.scenario.year
firm = furnace_game.actors.add("firm:iron1", ActorRecord(kind="firm", money=1.0e9))
firm.business.open_plant("blast_furnace", year - 10)
firm.knowledge.add("blast_furnace")
furnace_game.advance_actors(year)
no_firm.advance_actors(year)
sold_by_firm = noted_sale_tonnes(furnace_game, FURNACE_MATERIAL, "firm:iron1")
furnace_game._step_market()
no_firm._step_market()
furnace_book = furnace_game.state.economy.market_book.get(furnace_game._material_tag(FURNACE_MATERIAL)[0], {})
no_firm_book = no_firm.state.economy.market_book.get(no_firm._material_tag(FURNACE_MATERIAL)[0], {})
check("a firm running a furnace notes the pig iron it makes as its sale (none without a firm), which does not raise "
      "the price the market posts, and once the year has cleared the market has sold at least as much of it",
      sold_by_firm > 0.0 and noted_sale_tonnes(no_firm, FURNACE_MATERIAL) == 0.0
      and furnace_game.goods_market.home_unit_price(FURNACE_MATERIAL)
      <= no_firm.goods_market.home_unit_price(FURNACE_MATERIAL) * (1.0 + 1e-4)    # prices settle to the in-game solve's tolerance
      and furnace_book.get("traded_tonnes", 0.0) >= no_firm_book.get("traded_tonnes", 0.0) * (1.0 - 1e-6),
      (sold_by_firm, furnace_book.get("traded_tonnes"), no_firm_book.get("traded_tonnes")))
furnace_world = SimWorld(furnace_game)
furnace_node = furnace_game.nodes["blast_furnace"]
expected_takings = (furnace_game.concern_takings("blast_furnace", furnace_world.ramp(year - 10))
                    * furnace_game.node_output_market_factor(furnace_node))
check("the furnace is not a goods-category concern, so a firm's takings carry the same output market factor the founder's do",
      furnace_node.get("cat") not in furnace_game.GOODS_CATEGORIES
      and abs(furnace_world.concern_takings("blast_furnace", year - 10) - expected_takings) <= 1e-6 * abs(expected_takings),
      (furnace_node.get("cat"), furnace_world.concern_takings("blast_furnace", year - 10), expected_takings))

# --- a good nobody offers has no price in the real tree; a real partner's goods are landed at cost plus terms
rome = sim(civ="rome_100ad", capital=1e9)
check("in a real Rome pepper has no price, cannot be bought or quoted, and has no market book entry",
      rome.material_price_basis("pepper_kg") is None and rome.material_trade_quote("pepper_kg") is None
      and not rome.goods_market.can_be_bought("pepper_kg") and rome.goods_market.offered_by("pepper_kg") is None
      and "pepper_kg" not in rome.goods_market.household_prices() and rome.market_state("pepper_kg") is None)

# a partner outside the agent economy trades by the partner book, which is what quotes an import; the shipped Han is
# inside it, so for this section it is put outside (and the game is not played)
_records = foreign_module.foreign_economy_records()
with mock.patch.object(foreign_module, "foreign_economy_records", lambda: tuple(
        dict(record, agent_economy=False) if record["civilization"] == "han_china_100ad" else record
        for record in _records)):
    imports = unopened_sim(civ="rome_100ad", capital=1e9)
    market = imports.goods_market
    prices = market.household_prices()
    facts = imports._foreign_economy_facts("han_china_100ad")
    route = imports._foreign_route(S.load_civ("han_china_100ad"))
    landed = (facts["prices_in_home_money"]["cassia_kg"] * market.partner_price_level("han_china_100ad")
              * (1.0 + market.merchants_cost_share(route, None, "han_china_100ad"))
              + (route.cost_per_tonne + imports._agent_cost_per_tonne("han_china_100ad", route))
              * tonnes_per_unit("cassia_kg"))
    check("the real Han offers cassia, an import quoted at the landed price households pay",
          market.offered_by("cassia_kg") == "han_china_100ad" and imports.material_price_basis("cassia_kg") == "imported"
          and market.can_be_bought("cassia_kg") and imports.material_trade_quote("cassia_kg") is not None
          and abs(prices["cassia_kg"] - landed) < 1e-9 * landed, (prices["cassia_kg"], landed))
