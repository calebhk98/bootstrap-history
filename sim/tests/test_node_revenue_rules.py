"""Node revenue follows what a node produces, at solved prices (apply_revenue and the figures it hands to): output sold less
what is bought, in labour hours; a node that makes nothing earns nothing whatever its authored figure says; the market factor over
a node's baskets; the payback diagnostic. Called on nodes and baskets written here (the shipped goods and wages as prices where a
rule only needs some). The derived tree is test_node_revenue_validation."""
import copy
from unittest import mock

from sim.engine import data
from sim.production import node_output, node_payback_diagnostic, node_revenue, node_revenue_market
from sim.labour.labour_market import production_data
from sim.world import plant_figures
from sim.world.plant_baskets import Baskets

from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

_tree, _document, tree_nodes, tree_wages, tree_goods = data.load()
RATE = data.starting_schedule().money_per_labour_hour

# --- revenue is the output sold less the inputs bought, in labour hours.
baskets = Baskets(outputs={"lime_kg": 100.0}, purchases={"limestone_kg": 150.0}, energy_sold={}, energy_bought={}, labour_hours={"labourer": 50.0}, plant=[])
goods = {"lime_kg": 3.0, "limestone_kg": 1.0}
operated = {"id": "kiln", "kind": "ENGINEERING", "sch": 0.0, "art": 0.0, "lab": {}, "_material_hours": 0.0}
with mock.patch.object(node_output, "entries_gated_by", return_value=[{"operated_by": ["kiln"]}]), \
        mock.patch.object(node_output, "output_baskets", return_value=baskets):
    node_revenue.apply_revenue([operated], goods, {"labourer": 1.0}, 2.0)
check("an operated node's revenue in hours is the baskets' takings over the money per hour",
      operated["_revenue_basis"] == "output" and abs(operated["rev_hours"] - (100.0 * 3.0 - 150.0 * 1.0) / 2.0) < 1e-9, operated)
check("...and its upkeep in hours is its crew's pay plus the plant's", abs(operated["up_hours"] - (50.0 * 1.0 / 2.0)) < 1e-9, operated["up_hours"])
check("...and it states the baskets it came from", operated["_output_per_year"] == {"lime_kg": 100.0} and operated["_purchases_per_year"] == {"limestone_kg": 150.0})
losing = Baskets(outputs={"lime_kg": 10.0}, purchases={"limestone_kg": 150.0}, energy_sold={}, energy_bought={}, labour_hours={}, plant=[])
check("takings are never negative", plant_figures.takings(losing, goods) == 0.0)

# --- a node that makes nothing earns nothing, whatever it states.
node_with_figure = {"id": "nothing_gates_this", "kind": "ENGINEERING", "sch": 0.0, "art": 0.0, "lab": {}, "_material_hours": 0.0, "rev_hours": 1e9}
node_revenue.apply_revenue([node_with_figure], tree_goods, tree_wages, RATE)
check("a typed revenue is never read: a node no entry operates earns nothing", node_with_figure["rev_hours"] == 0.0, node_with_figure["rev_hours"])
check("the authored figure is kept apart, not used", node_with_figure["_rev_hours_authored"] == 1e9)
check("output_baskets gives none for a node no entry gates", node_output.output_baskets({"id": "nothing_gates_this", "sch": 0, "art": 0}, production_data(), tree_goods) is None)

# --- a node's declared yearly output bounds what it is derived to make.
entry = {"outputs": {"lime_kg": 100.0}, "inputs": {"limestone_kg": 150.0}, "labour_hours": {"burner": 10.0}, "capital": []}


class _NoEnergy:
    def can_run(self, entry):
        return True

    def bought(self, carrier, entry):
        return 0.0

    def sold(self, carrier, entry):
        return 0.0


bounded = plant_figures.yearly_baskets([entry], {"lime_kg": 3.0, "limestone_kg": 1.0}, _NoEnergy(), None, 5.0, 0.2)
unbounded = plant_figures.yearly_baskets([entry], {"lime_kg": 3.0, "limestone_kg": 1.0}, _NoEnergy(), None, 5.0, 0.0)
check("a declared output in tonnes bounds the total tonnes a node is derived to make", sum(bounded.outputs.values()) / 1000.0 <= 0.2 * (1 + 1e-9)
      and sum(unbounded.outputs.values()) / 1000.0 > 0.2, (bounded.outputs, unbounded.outputs))

# --- the market factor over a node's baskets.
node = {"_output_per_year": {"a": 10.0}, "_purchases_per_year": {"b": 5.0}}
long_run = {"a": 2.0, "b": 2.0}
check("the market factor follows the output and input prices over their long-run costs: net 10 at long-run costs, 30 at the market",
      abs(node_revenue_market.market_factor(node, long_run, {"a": 4.0, "b": 2.0}.get) - 3.0) < 1e-12)
check("a material nothing prices is valued at its long-run cost", abs(node_revenue_market.market_factor(node, long_run, {"a": 4.0}.get) - 3.0) < 1e-12)
check("a material with no long-run cost adds nothing either year",
      abs(node_revenue_market.market_factor({"_output_per_year": {"a": 10.0, "free": 99.0}, "_purchases_per_year": {}}, {"a": 2.0}, {"a": 4.0, "free": 50.0}.get) - 2.0) < 1e-12)
check("the market factor is one for an authored node and for a flat market",
      node_revenue_market.market_factor({}, {}, lambda material: 2.0) == 1.0
      and node_revenue_market.market_factor({"_output_per_year": {"a": 10.0}, "_purchases_per_year": {}}, {"a": 1.0}, lambda material: None) == 1.0)

# --- the payback diagnostic lists nodes whose build cost is repaid fast by net earnings, quickest first, and changes nothing.
nodes = {"quick": {"rev": 100.0, "up": 10.0, "_total_cost": 9.0, "_revenue_basis": "output"},
         "quicker": {"rev": 100.0, "up": 10.0, "_total_cost": 4.5, "_revenue_basis": "output"},
         "slow": {"rev": 100.0, "up": 10.0, "_total_cost": 900.0},
         "loses": {"rev": 1.0, "up": 10.0, "_total_cost": 1.0},
         "free": {"rev": 100.0, "up": 10.0, "_total_cost": 0.0}}
before = copy.deepcopy(nodes)
rows = node_payback_diagnostic.fast_payback_rows(nodes, threshold_years=1.0)
check("only nodes with positive net earnings and a build cost that repay within the threshold are listed, quickest first",
      [row["node"] for row in rows] == ["quicker", "quick"] and all(row["payback_years"] == row["build_cost"] / row["net_per_year"] for row in rows), rows)
check("a row carries the node, basis, build cost, net and payback", set(rows[0]) == {"node", "basis", "build_cost", "net_per_year", "payback_years"})
check("a threshold of nothing lists nothing", node_payback_diagnostic.fast_payback_rows(nodes, threshold_years=0.0) == [])
check("the diagnostic changes no node", nodes == before)
