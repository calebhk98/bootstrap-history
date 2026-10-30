"""The markets module's kernels (Complaint 661): economy computations a mod may replace, chosen as the largest of a game year
(`python3 sim/simulator.py play --civ rome_100ad --session FILE` then profiling `step 2`; Complaint 497 lists the measurement).

The module hands them to the agent economy through its setup (`EconomySetup.kernels`), bound by the assembly."""
from sim.assembly.api import Kernel
from sim.geography import api as geography_api
from sim.labour import api as labour_api

FETCH_WAGE = "markets.fetch_wage"
LEAST_COST_TREE = "markets.least_cost_tree"

KERNELS = (
	Kernel(FETCH_WAGE, labour_api.fetch_wage,
	       inputs="area, wanted hours, going wage, highest bid, a function listing (wage, area) offers, and lookups for the hours an area sells at a wage, "
	              "the hours bid for in an area and the spare hours of a list of sources",
	       output="the lowest wage at which hands fetched from other areas fill the shortage, or None",
	       samples=labour_api.fetch_wage_samples),
	Kernel(LEAST_COST_TREE, geography_api.least_cost_tree,
	       inputs="adjacency (per state, the (state, cost) steps out of it), the (cost, state) starts, states per tile, and the tiles to settle or None",
	       output="the least cost to every state; with tiles to settle only the least over each of those tiles' states is contractual",
	       samples=geography_api.cost_tree_samples,
	       observe=geography_api.settled_costs),
)
