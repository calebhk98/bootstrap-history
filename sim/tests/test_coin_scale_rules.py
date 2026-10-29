"""Every money figure reaches the player in the civilisation's own coin through one conversion, labour hours to money: the opening wage
schedule's money per hour, a cost declared in hours, a tree priced in a coin, and a node's revenue in hours, which ignores the coin.
Each is called on inputs written here or on the shipped data, with the coin heavier by a stated factor."""
import copy
from types import SimpleNamespace

from sim.engine import data, money_units
from sim.production import node_revenue
from sim.workforce.wage_schedule import build_schedule

from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

COIN_SCALE = 2.5

# --- the opening schedule: a coin heavier by the scale makes an hour's money, and so a year's wage, that much smaller.
rome = data.load_civ("rome_100ad")
heavier_rome = copy.deepcopy(rome)
heavier_rome["coin_standard"]["kg_per_unit"] *= COIN_SCALE
light, heavy = build_schedule(data.TRADE_REGISTRY, rome), build_schedule(data.TRADE_REGISTRY, heavier_rome)
check("a coin heavier by a factor makes the money one labour hour is worth smaller by that factor",
      abs(heavy.money_per_labour_hour * COIN_SCALE / light.money_per_labour_hour - 1.0) < 1e-9, (light.money_per_labour_hour, heavy.money_per_labour_hour))
check("...and a labourer's annual wage with it",
      abs(heavy.annual_wage("labourer") * COIN_SCALE / light.annual_wage("labourer") - 1.0) < 1e-9, (light.annual_wage("labourer"), heavy.annual_wage("labourer")))


# --- a cost declared in hours is read as hours times the reader's money per hour.
class _Declared:
    HOURS = 40.0
    PRICE = money_units.PricedInLabourHours("HOURS")


def _reader(rate):
    reader = _Declared()
    reader.labour = SimpleNamespace(money_per_labour_hour=lambda: rate)
    return reader


check("a cost in hours read through a coin is the hours times the money per hour", _reader(0.5).PRICE == 20.0)
check("the same hours in a coin heavier by a factor read as smaller by that factor",
      abs(_reader(0.5 / COIN_SCALE).PRICE * COIN_SCALE / _reader(0.5).PRICE - 1.0) < 1e-12)
check("read from the class the declaration is its hours", _Declared.PRICE == 40.0)

# --- a tree priced in a coin: capital, upkeep and revenue are their hours times the money per hour; rebasing changes only the coin.
def _hand_nodes():
    return {"a": {"rev_hours": 10.0, "up_hours": 2.0, "cap_hours": 30.0, "lab": {"labourer": 5.0}, "_material_hours": 4.0}}


wages_per_hour = {"labourer": 1.0}
priced = _hand_nodes()
money_units.price_nodes(priced.values(), wages_per_hour, 3.0)
check("price_nodes states capital, upkeep and revenue as their hours times the money per hour",
      (priced["a"]["rev"], priced["a"]["up"], priced["a"]["cap"]) == (30.0, 6.0, 90.0), priced["a"])
check("...and the total cost as labour at the wages, materials and capital",
      priced["a"]["_total_cost"] == 5.0 * 1.0 + 4.0 * 3.0 + 90.0 and priced["a"]["_money_per_labour_hour"] == 3.0, priced["a"])
check("rebasing to the coin a tree is already in returns the same tree", money_units.rebased_nodes(priced, wages_per_hour, 3.0) is priced)
rebased = money_units.rebased_nodes(priced, wages_per_hour, 3.0 / COIN_SCALE)
check("rebasing to another coin prices copies in it and leaves the shared tree alone",
      rebased is not priced and priced["a"]["rev"] == 30.0 and abs(rebased["a"]["rev"] * COIN_SCALE - 30.0) < 1e-9, (rebased["a"], priced["a"]))
check("...and the hours are the same in either coin", rebased["a"]["rev_hours"] == priced["a"]["rev_hours"])

# --- a node's revenue and upkeep in hours ignore the coin: money prices, wages and the money per hour scale together.
_tree, _document, tree_nodes, tree_wages, tree_goods = data.load()
earner = min((node["id"] for node in tree_nodes.values() if node.get("_revenue_basis") == "output"), key=lambda node_id: (tree_nodes[node_id]["_total_cost"], node_id))
rate = data.starting_schedule().money_per_labour_hour
in_coin = copy.deepcopy(tree_nodes[earner])
in_heavier_coin = copy.deepcopy(tree_nodes[earner])
node_revenue.apply_revenue([in_coin], tree_goods, tree_wages, rate)
node_revenue.apply_revenue([in_heavier_coin], {good: price * COIN_SCALE for good, price in tree_goods.items()},
                           {trade: wage * COIN_SCALE for trade, wage in tree_wages.items()}, rate * COIN_SCALE)
check("the node chosen earns from its output", in_coin["_revenue_basis"] == "output" and in_coin["rev_hours"] > 0.0, in_coin["rev_hours"])
check("its revenue and upkeep in hours are the same in a coin heavier by a factor",
      abs(in_heavier_coin["rev_hours"] - in_coin["rev_hours"]) <= 1e-9 * in_coin["rev_hours"]
      and abs(in_heavier_coin["up_hours"] - in_coin["up_hours"]) <= 1e-9 * max(1.0, in_coin["up_hours"]), (in_coin["rev_hours"], in_heavier_coin["rev_hours"]))

# --- material prices in hours do not depend on the coin.
light_prices = data.calculated_goods_prices([], "rome_100ad", rate)
heavy_prices = data.calculated_goods_prices([], "rome_100ad", rate * COIN_SCALE)
check("each material's price in hours is the same in a heavier coin",
      all(abs(heavy_prices[material] / (rate * COIN_SCALE) - price / rate) <= price / rate * 1e-9 + 1e-12 for material, price in light_prices.items())
      and len(light_prices) > 100, len(light_prices))
