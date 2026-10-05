"""Complaint 288: the founder sells a built concern to another actor through the exchange, and sells
farmland back to the land market at the value `buy farm` uses."""
import copy
import os
import random
import tempfile

from .harness import *  # noqa: F401,F403

from sim.agents.api import ActorRecord
from sim.agents.tuning import VALUE_HORIZON_YEARS
from sim.engine.agents_port import SimWorld
from sim.engine.saveload import load_state, save_state
from sim.ui.proto.typed import parse_typed

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if node["rev"] > 0 and not node["pre"] and node["cap"] >= 0)


def make_node(node_id):
    node = copy.deepcopy(NODES[_TEMPLATE_ID])
    node.update(id=node_id, name=node_id, traits=["commerce"], pre=[], lab={"labourer": 100.0},
                mat={}, rev=5000.0, up=100.0, yrs=1.0, risk=0.0, ph=0.0, dev_years=None, dev_people=None)
    node.pop("gains", None)
    return node


EXTRA = [make_node("zz_easy"), make_node("zz_hard")]


def actor_sim(extra_nodes):
    nodes = copy.deepcopy(NODES)
    for node in extra_nodes:
        nodes[node["id"]] = node
    game = S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True, civ=S.load_civ("rome_100ad"))
    game.goal, game.done_year = GOAL, {}
    return game


def founder_runs(game, node_id, opened_ago=0):
    year = game.state.scenario.year
    projects = game.state.projects
    projects.done.add(node_id)
    projects.done_year[node_id] = year - opened_ago
    projects.operating.add(node_id)
    projects.opened_year[node_id] = year - opened_ago
    game._done_changed()

# ---- a concern ------------------------------------------------------------------------------
game = actor_sim(EXTRA)
founder_runs(game, "zz_easy", opened_ago=5)
check("with no buyer the sale is refused and the concern stays",
      not game.sell_concern("zz_easy")["ok"] and "zz_easy" in game.state.projects.operating)
check("a concern the founder does not run cannot be sold", not game.sell_concern("zz_hard")["ok"])

poor = game.actors.add("firm:poor", ActorRecord(kind="firm", money=1.0, knowledge={"zz_easy"}))
rich = game.actors.add("firm:rich", ActorRecord(kind="firm", money=1.0e9, knowledge={"zz_easy"}))
unskilled = game.actors.add("firm:unskilled", ActorRecord(kind="firm", money=1.0e9))
margin = SimWorld(game).concern_margin("zz_easy")
capital_before, rich_before = game.household.capital, rich.money
result = game.sell_concern("zz_easy")
check("the sale goes through", result["ok"], result)
check("the buyer is the one that can pay and make it", result["buyer"] == "firm:rich", result)
check("the price is the concern's margin over the valuation horizon",
      abs(result["price"] - margin * VALUE_HORIZON_YEARS) < 1e-6, (result, margin))
check("the founder is paid and the buyer pays the same",
      abs(game.household.capital - capital_before - result["price"]) < 1e-6
      and abs(rich_before - rich.money - result["price"]) < 1e-6)
check("the concern moves to the buyer", "zz_easy" in rich.concerns
      and "zz_easy" not in game.state.projects.operating and "zz_easy" not in game.state.projects.opened_year)
check("the founder keeps the know-how", "zz_easy" in game.state.projects.done)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    revived = actor_sim(EXTRA)
    load_state(revived, path)
check("the sale survives a save and load", "zz_easy" not in revived.state.projects.operating
      and "zz_easy" in revived.actors.get("firm:rich").concerns)

# ---- farmland -------------------------------------------------------------------------------
land = actor_sim(EXTRA)
land.state.economy.farm_hectares = 100.0
cash = land.household.capital
result = land.sell_farm(40.0)
check("selling farmland removes the hectares", result["ok"] and abs(land.farm_hectares - 60.0) < 1e-9, result)
check("it pays what buy farm charges per hectare",
      abs(land.household.capital - cash - 40.0 * land.farm_price_per_hectare()) < 1e-6)
check("more than is owned is refused and changes nothing",
      not land.sell_farm(61.0)["ok"] and abs(land.farm_hectares - 60.0) < 1e-9)
check("a sale of nothing is refused", not land.sell_farm(0.0)["ok"])

# ---- the protocol ---------------------------------------------------------------------------
check("typed 'sell concern <id>' parses", parse_typed("sell concern zz_easy")[0]
      == {"cmd": "sell", "what": "concern", "id": "zz_easy"}, parse_typed("sell concern zz_easy"))
check("typed 'sell farm <ha>' parses", parse_typed("sell farm 40")[0] == {"cmd": "sell", "what": "farm", "n": 40},
      parse_typed("sell farm 40"))
check("typed 'sell <material> <tonnes>' is unchanged", parse_typed("sell iron 5")[0]
      == {"cmd": "sell", "material": "iron", "n": 5}, parse_typed("sell iron 5"))
