"""What a capability or institution IS: built, scaled, and still running.

`is_venture` decides whether a node is a going concern at all, `running` decides whether a built one is actually open for business
today rather than merely known, and `institution_units` / `institution_unit_ceiling` / `institution_unit_cost` answer "how much of
it", for the handful of institutions (the `scalable` capability mechanic) that come in more than one size. `capability_gaps` is the
player-facing report built on `running`: which completed institutions are silently not paying out because nobody opened them.

`has` answers "do you know how / did you build it", and for a piece of knowledge that is the whole story. For an establishment it is
not: a school with nobody paid to keep it open trains no scholars, a workshop whose doors are shut houses nobody. `running` is `has`
for everything that has no doors to shut, and for a concern the test that its doors are open.
Needs: the views of READS_BY_OWNER in module_spec.py."""
from . import rules
from .constants import INSTITUTION_EXPANSION_CONVEXITY


class Capability:

	def is_venture(self, node_id):
		"""Is this something you could run as a going concern, as opposed to a
		piece of knowledge that simply changes what you can do?"""
		return node_id not in self.needs.techniques_granted() and self.is_concern_node(node_id)

	def is_concern_node(self, node_id):
		"""Does the tree describe a going concern here (it earns or costs to keep up), whoever holds it?"""
		node = self.needs.tree_nodes().get(node_id)
		return node is not None and (node["rev"] > 0 or node["up"] > 0)

	def capability_gaps(self):
		"""Completed capability institutions that are NOT currently operating, each with the real running()-gated
		benefit it is not collecting right now (the capability nodes' `lost_benefit`, plague_preparedness aside).

		fin_university is the one entry needing its own gate in the table: its sole running()-gated effect
		(update_protection, society.py) is an `or` with school_founded, so closing it costs nothing while
		school_founded is still open, and warning anyway would be a false alarm.
		"""
		nodes = self.needs.tree_nodes()
		not_operating_benefit = self.needs.capability_sets()[2]
		out = []
		for node_id in sorted(not_operating_benefit):
			if node_id not in nodes or node_id not in self.needs.techniques_held() or self.running(node_id):
				continue
			if any(self.running(other) for other in
			       self.needs.mechanic["capability"].get(node_id).get("redundant_with", ())):
				continue
			benefit = not_operating_benefit[node_id]
			out.append({
				"id": node_id,
				"benefit_switched_off": benefit,
				"warning": ("Critical capability completed but not "
				            "operating: %s. %s is currently inactive."
				            % (node_id, benefit)),
				"fix": "open %s" % node_id,
			})
		return out

	def institution_units(self, node_id):
		"""How much of this institution is actually running, as a number rather than a flag.

		0 if it is not open. 1.0 is a single, ordinary founding - exactly the size every rev/up/places/room figure
		elsewhere in the engine was calibrated against. Above 1.0 is genuine expansion; below 1.0 is a starter
		founding smaller than the calibrated size (see open_venture's `units` argument), the bridge that lets a founder
		who cannot afford the whole of a workshop afford a part of it. For anything not scalable this is just
		running() cast to a float, because there is nothing to found a second of.
		"""
		if node_id not in self.needs.capability_sets()[1]:
			return 1.0 if self.running(node_id) else 0.0
		if node_id not in self.needs.operating():
			return 0.0
		return max(0.0, self.needs.venture_size[node_id])

	def institution_unit_ceiling(self, node_id):
		"""The most units of this institution the empire can actually fill.

		Bounded by population, and by food through the proxy the model has: literacy_general, the share of the people not tied
		to subsistence farming, which could plausibly be literate at all. A school's ceiling rising with it is the same fact
		counted from the other side (a farming society can spare few hands for a classroom), and schools are among the things
		that raise literacy_general in the first place. One unit is NOT one literal schoolhouse: at this model's scale one unit
		is the whole of Rome's original school_founded, the same abstraction a "tonnes_per_year" mine uses for however many
		shafts that tonnage comes out of.
		"""
		needs = self.needs
		if node_id not in needs.capability_sets()[1]:
			return 1.0
		if node_id in needs.coverage():
			# a work that serves a share of the people is repeated until everyone who can use it is served
			return max(1.0, needs.units_for_coverage(node_id, 1.0))
		if needs.mechanic["capability"].get(node_id).get("scalable") == "literacy":
			return rules.literacy_ceiling(needs.pop_scale(), needs.literacy("literacy_general"),
			                              needs.literacy_references()["reference_general"])
		# Workshops, collegia and a freedman staff draw on craftsmen rather than the literate few, so population alone bounds them.
		return rules.population_ceiling(needs.pop_scale())

	def institution_unit_cost(self, node_id, have_units, add_units):
		"""Money to take this institution from `have_units` to `have_units + add_units`, where one unit costs exactly
		what founding it has always cost (venture_capex): a run that only founds the original single unit pays what it always paid.
		Each further unit costs more than the last, the way a second school draws on the same small pool of the literate."""
		return rules.institution_cost_between(self.needs.venture_capex[node_id], have_units, add_units, INSTITUTION_EXPANSION_CONVEXITY)

	def running(self, node_id):
		"""Built, and still being maintained - which is what a capability needs.

		True for anything you have done that is not a going concern (knowledge does not close), for this society's own
		crafts, and for a concern you actually have open.
		"""
		needs = self.needs
		if node_id not in needs.techniques_held():
			return False
		node = needs.tree_nodes()[node_id]
		if (node.get("requires_running") or node.get("requires_ways")) and needs.gate_blocked(node_id):
			return False
		if node_id in needs.techniques_granted() or not self.is_venture(node_id):
			return True
		# Scalable institutions have a smaller size to start at (institution_units can sit below 1.0), so a founder who cannot
		# afford the whole of one founds as much as the surplus will carry; a concern counts as running only while it is open.
		return node_id in needs.operating()
