"""The founder's seat as the owner of a reviewed business: how its plants are shut, spared and seized.

`Business.review` (sim/agents/business_review.py) decides which plants close and why; this answers what is particular to
the founder's seat: the supervision pool, the policy that lets losses be shed, the credit line, and the way a shut plant is
mothballed rather than forgotten."""
from sim.agents.api import edges
from sim.finance.api import constants as finance_constants
from sim.ledger.api import ReceiveFromEdge


class SeatReview:
	"""The hooks of `Reviewable` for the acting seat, answered by the projects module and the views it reads."""

	def __init__(self, module, world, year=None):
		self._module = module
		self._world = world
		self._year = module.needs.year() if year is None else year

	def staff_closures(self):
		return self._module.concerns_to_close_for_staffing()

	def reopening_order(self, entry_keys):
		"""Staff closures still worth reopening (known, in the tree), best earning for the hands they tie up first."""
		needs, world = self._module.needs, self._world
		done, nodes = needs.techniques_held(), needs.tree_nodes()
		reopenable = [node_id for node_id in entry_keys if node_id in done and node_id in nodes]
		return sorted(reopenable, key=lambda node_id: -(world.concern_margin(node_id)
		                                                / max(0.01, sum(world.concern_staff(node_id).values()))))

	def reopens_staffed_plant(self, entry_key):
		did_open, _message = self._module._open_venture(entry_key)
		return did_open

	def sheds_losses(self):
		return bool(self._module.needs.founder()["policy"].get("auto_shed", True))

	def cuts_losses_now(self):
		"""In arrears with a yearly deficit: the books force the seat to shut what costs more than it returns."""
		needs = self._module.needs
		if needs.acting_balance() >= 0:
			return False
		return needs.revenue_estimate() - needs.upkeep() - needs.living_cost(None, None, None) - needs.mine_operating_cost() < 0

	def spares_plant(self, entry_key):
		needs = self._module.needs
		return entry_key in needs.techniques_granted() or needs.never_abandon[entry_key]

	def serves_beyond_takings(self, entry_key):
		return entry_key in self._module.needs.capability_sets()[0]

	def standing_margin(self, entry_key):
		return self._world.concern_margin(entry_key)

	def creditors_press(self):
		needs = self._module.needs
		return needs.acting_balance() < -needs.credit_limit(None, None, None)

	def shut(self, entry_key, reason):
		self._module.close_work(entry_key, reason, self._year)

	def proceeds_of_seizure(self, entry_key):
		size = self._module.needs.venture_size[entry_key]
		return self._world.upkeep(entry_key, size) * finance_constants.CREDITOR_SEIZURE_VALUE_MULTIPLE

	def receive_seizure(self, entry_key, proceeds):
		self._module.needs.send(ReceiveFromEdge(edges.EDGE_CREDITORS, proceeds, "concern seized by creditors"))
