"""Coverage: how much of the nation's people a repeated work serves, and rolling it out to a target share.

A work declares `mechanics.coverage = {"staff_hours_per_person_year": h, "serves": "pupils", "eligible_share": e}`.
One unit of it employs its `annual_labour_hours` a year, so it serves that many hours divided by `h` people; units run
times that, over the people who can use it (all of the nation's, or the share `e` of them, such as school-age
children), is the share covered. A rollout is more units of the same work (they are the places it is repeated
in) until the share asked for is reached or the nation can fill no more.
"""
from sim.refusal import Refusal

from . import coverage_rules


class Coverage:
	def coverage_nodes(self):
		"""Ids of the works that declare `coverage`."""
		return tuple(self.needs.mechanic["coverage"])

	def people_per_unit(self, node_id):
		"""How many people one unit of the work serves: its yearly staff hours over the hours each person needs."""
		spec = self.needs.mechanic["coverage"].get(node_id)
		hours = sum((self.needs.tree_nodes()[node_id].get("annual_labour_hours") or {}).values())
		return coverage_rules.people_per_unit(hours, spec["staff_hours_per_person_year"])

	def people_who_can_use(self, node_id):
		"""The people the work could serve: the nation's, or the share of them its `eligible_share` names."""
		return coverage_rules.people_who_can_use(self.needs.population_total(),
		                                         self.needs.mechanic["coverage"].get(node_id).get("eligible_share", 1.0))

	def coverage_share(self, node_id):
		"""The share of the people who can use the work that it serves while it is open, 0 to 1."""
		if not self.needs.running[node_id]:
			return 0.0
		return coverage_rules.coverage_share(True, self.needs.institution_units[node_id], self.people_per_unit(node_id),
		                                     self.people_who_can_use(node_id))

	def units_for_coverage(self, node_id, share):
		"""The units that serve `share` of the people who can use the work."""
		return coverage_rules.units_for_coverage(share, self.people_who_can_use(node_id), self.people_per_unit(node_id))

	def coverage_row(self, node_id):
		"""What the `rollout` listing says of one work."""
		needs = self.needs
		spec = needs.mechanic["coverage"].get(node_id)
		return {"id": node_id, "name": needs.tree_nodes()[node_id]["name"], "serves": spec.get("serves", "people"),
		        "units": round(needs.institution_units[node_id], 3),
		        "covered": round(self.coverage_share(node_id), 4),
		        "people_per_unit": round(self.people_per_unit(node_id), 1),
		        "units_for_everyone": round(self.units_for_coverage(node_id, 1.0), 1),
		        "most_units_the_nation_can_fill": round(needs.institution_unit_ceiling[node_id], 1)}

	def roll_out(self, node_id, share):
		"""(ok, text): open more of the work, or open it, to cover `share` of the nation's people. The cost, the staff and the
		ceiling on units are the ordinary ones of opening or expanding a venture."""
		needs = self.needs
		if node_id not in self.coverage_nodes() or node_id not in needs.tree_nodes():
			return False, "that is not a work that can be rolled out"
		if node_id not in needs.techniques_held():
			return False, "you have not worked out how to do that yet"
		wanted = self.units_for_coverage(node_id, share)
		have = needs.institution_units[node_id]
		to_open = coverage_rules.rollout_units(wanted, have)
		if to_open is None:
			return False, Refusal("already_covered", "%s already covers %d%% of the people" % (
				needs.tree_nodes()[node_id]["name"], round(100 * self.coverage_share(node_id))))
		ok, text = self.open_venture(node_id, units=to_open)
		if not ok:
			return False, text
		return True, "%s. It now covers %d%% of the people." % (text.rstrip("."), round(100 * self.coverage_share(node_id)))
