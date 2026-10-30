"""What it costs to keep a concern or institution open this year: `upkeep` and its parts, an institution's upkeep scaled by how full
its places are, and the people one unit is built to support.
Needs: the views of READS_BY_OWNER in module_spec.py."""
from . import node_upkeep, rules
from .constants import INSTITUTION_PLACES_FALLBACK_UPKEEP_LABOUR_HOURS_PER_HEAD


class Upkeep:

	def upkeep(self):
		# You do not pay to maintain what you do not own, but you do bear the small standing cost of the practice you actually
		# run, and not the running costs of a concern you have not opened: both follow `operating`, so closing something stops the
		# bleeding, and knowing how to do something costs nothing to know.
		return sum(self.upkeep_by_concern().values())

	def upkeep_by_concern(self):
		"""{node id: yearly running cost} for each concern or practice that is paid for; `upkeep` is its sum."""
		practice_set = self._practice_set()
		operating = self.needs.operating()
		return {node_id: self.needs.venture_real_upkeep(node_id, None)
		        for node_id in self._revenue_upkeep_candidates()
		        if node_id in operating or node_id in practice_set}

	def institution_upkeep(self, node_id, units=None, fully_staffed=False):
		"""What this concern actually costs to keep open THIS year.

		`units` prices a stated size of a scalable institution instead of what is open; `fully_staffed` skips the
		occupancy scaling (every place filled).

		For almost everything, its upkeep. For an establishment whose purpose is to support PEOPLE - a school, an academy, a
		workshop, a licensed collegium, a freedman staff - it scales with how much of that support you are using, because a
		school with three scholars in it does not cost what a school with forty does. A third school costs three schools' upkeep
		at three schools' worth of places to fill it against. An institution not yet open is priced as a first founding (one
		unit), not zero: the affordability gate calls this on things it has not opened yet.
		"""
		capability, scalable, _benefit = self.needs.capability_sets()
		node = self.needs.tree_nodes()[node_id]
		_units = (self.institution_units(node_id) if node_id in self.needs.operating() else 1.0) \
			if node_id in scalable else 1.0
		if units is not None and node_id in scalable:
			_units = float(units)
		# The crew's pay is in the payroll (`living_cost` through `wage_bill`), so only the non-crew part is charged here.
		upkeep_amount = node["up"] * node_upkeep.non_labour_share(node) * _units
		if (fully_staffed or node_id not in capability or upkeep_amount <= 0
		        or self.needs.mechanic["upkeep_full"].get(node_id)):
			return upkeep_amount
		places = self.institution_places(node_id) * _units
		if places <= 0:
			return upkeep_amount
		return rules.occupancy_scaled_upkeep(upkeep_amount, places, self.needs.headcount())

	def institution_places(self, node_id):
		"""Roughly how many people ONE UNIT of this establishment is built to support; callers wanting the total for a scalable
		institution multiply by `institution_units`. Read off the same table staff_capacity() and supervision_room() use; anything
		absent is sized by its own upkeep at about a wage a head."""
		return rules.institution_places(self.needs.mechanic["institution_places"].get(node_id), self.needs.tree_nodes()[node_id]["up"],
		                                self.priced(INSTITUTION_PLACES_FALLBACK_UPKEEP_LABOUR_HOURS_PER_HEAD))
