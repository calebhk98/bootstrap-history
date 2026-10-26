"""Bridge views more than one module reads: the year, the tree, which nodes are ventures, the acting seat's staff."""
from sim.assembly.api import KEYED

from .bridge import bridge_view


@bridge_view("year")
def year(sim):
	return sim.state.scenario.year


@bridge_view("tree", kind=KEYED)
def tree(sim, node_id):
	"""The tech tree's node `node_id`, or None when the tree has none."""
	return sim.nodes.get(node_id)


@bridge_view("is_venture", kind=KEYED)
def is_venture(sim, node_id):
	return sim.is_venture(node_id)


@bridge_view("staff", seat_scoped=True)
def staff(sim):
	"""The acting seat's household staff: hired hands by trade, and its scholars and artisans."""
	household = sim.state.household
	return {"employees": household.employees, "scholars": household.scholars, "artisans": household.artisans}


@bridge_view("tree_nodes")
def tree_nodes(sim):
	"""The whole tech tree, node data by id (the object itself: a re-derivation replaces it)."""
	return sim.nodes
