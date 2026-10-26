"""The founder's seat as the owner of a reviewed business: how its plants are shut, spared and seized.

`Business.review` (sim/agents/business_review.py) decides which plants close and why; this answers what is
particular to the founder's seat: the supervision pool, the policy that lets losses be shed, the credit line,
and the way a shut plant is mothballed rather than forgotten."""
from sim.agents.api import edges


class SeatReview:
	"""The hooks of `Reviewable` for the acting seat, answered from the simulation."""

	def __init__(self, world, year=None, sim=None):
		self._world = world
		self._sim = sim if sim is not None else world._sim
		self._year = self._sim.state.scenario.year if year is None else year

	def tally(self, business):
		"""Tally each running plant's year: its margin once ramped up, and the years running it has lost money."""
		for node_id in sorted(self._sim.state.projects.operating):
			if node_id in self._sim.nodes:
				business.note_year(node_id, self._world.concern_margin(node_id))

	def staff_closures(self):
		return self._sim.concerns_to_close_for_staffing()

	def reopening_order(self, entry_keys):
		"""Staff closures still worth reopening (known, in the tree), best earning for the hands they tie up first."""
		sim, world = self._sim, self._world
		reopenable = [node_id for node_id in entry_keys if node_id in sim.state.projects.done and node_id in sim.nodes]
		return sorted(reopenable, key=lambda node_id: -(world.concern_margin(node_id)
														/ max(0.01, sum(world.concern_staff(node_id).values()))))

	def reopens_staffed_plant(self, entry_key):
		did_open, _message = self._sim.open_venture(entry_key)
		return did_open

	def sheds_losses(self):
		return bool(self._sim.state.founder.policy.get("auto_shed", True))

	def cuts_losses_now(self):
		"""In arrears with a yearly deficit: the books force the seat to shut what costs more than it returns."""
		sim = self._sim
		if sim.state.household.capital >= 0:
			return False
		return sim.revenue() - sim.upkeep() - sim.living_cost() - sim.mine_operating_cost() < 0

	def spares_plant(self, entry_key):
		sim = self._sim
		return entry_key in sim.state.projects.granted or sim.never_abandon(entry_key)

	def serves_beyond_takings(self, entry_key):
		return entry_key in self._sim.CAPABILITY_INSTITUTIONS

	def standing_margin(self, entry_key):
		return self._world.concern_margin(entry_key)

	def creditors_press(self):
		return self._sim.state.household.capital < -self._sim.credit_limit()

	def shut(self, entry_key, reason):
		self._sim.close_work(entry_key, reason, self._year)

	def proceeds_of_seizure(self, entry_key):
		size = self._sim.state.projects.business.size_of(entry_key)
		return self._world.upkeep(entry_key, size) * self._sim.CREDITOR_SEIZURE_VALUE_MULTIPLE

	def receive_seizure(self, entry_key, proceeds):
		self._sim.receive_from_edge(edges.EDGE_CREDITORS, proceeds, "concern seized by creditors")
