"""Complaint 508 / 507 stage 6: what a screen or an interest group reads as a market's sales, unsold stock and
unmet demand is the agent economy's record of that market, not the engine's static commodity book.

Builds a whole game, so it is not in the quick tier."""
from .harness import check, sim

from sim.economy import api as economy_api
from sim.engine.agents_port import SimWorld
from sim.engine import need_substitutes
from sim.engine.material_units import tonnes_per_unit

game = sim(civ="rome_100ad", capital=1e9)
game.economy.open_agent()
economy = game.economy.agent.economy()


def main_material(commodity):
    """The material the commodity's quote prices: the first of its materials that has a quote."""
    for material in game.economy.materials_in(commodity) + [commodity]:
        if game.economy.trade_quote(material) is not None:
            return material
    return None


def record_tonnes(commodity):
    material = main_material(commodity)
    record = economy_api.market_record(economy, material)
    return {name: value * tonnes_per_unit(material) for name, value in record.items()}


traded = sorted({game.economy.commodity_of(good) for good, volume in economy_api.traded_volumes(economy).items()
                 if volume > 0.0 and game.market_state(good) is not None})
traded = [commodity for commodity in traded if main_material(commodity) is not None]
check("the opened game has traded commodities to compare", len(traded) > 10, len(traded))

mismatched = {"society_sales_tonnes": [], "unsold_tonnes": [], "unmet_demand_tonnes": []}
for commodity in traded:
    state = game.market_state(commodity)
    expected = record_tonnes(commodity)
    for field_name, record_name in (("society_sales_tonnes", "sold"), ("unsold_tonnes", "unsold"),
                                    ("unmet_demand_tonnes", "unmet")):
        if abs(state[field_name] - expected[record_name]) > 1e-9 * max(1.0, abs(expected[record_name])):
            mismatched[field_name].append((commodity, state[field_name], expected[record_name]))
for field_name, rows in mismatched.items():
    check("market_state's %s is the economy's record for every traded good" % field_name, not rows, rows[:5])

view = SimWorld(game)
expected_value = 0.0
for commodity in sorted({game.economy.commodity_of(material) for material in need_substitutes.serving("food")}):
    quote = game.economy.trade_quote(main_material(commodity)) if main_material(commodity) else None
    if quote is not None and game.market_state(commodity) is not None:
        expected_value += record_tonnes(commodity)["sold"] * quote["buy_per_tonne"]
check("the sales a tithe falls on are the economy's sold tonnes at the quote",
      abs(view.tithable_sales_value("food") - expected_value) <= 1e-9 * max(1.0, expected_value),
      (view.tithable_sales_value("food"), expected_value))
