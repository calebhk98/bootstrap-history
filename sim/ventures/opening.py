"""Opening a venture by hand, and founding more of an institution that is already open.

The automatic counterparts (closing what staffing can no longer cover, reopening it, opening what plainly pays) are the
projects module's."""
from sim.agents.api import edges
from sim.ledger.api import PayEdge
from sim.projects.api import NoteConcernChange
from sim.refusal import LogLine, Refusal

from .needed_commands import BumpInstitutionUnitsVersion
from .net_loss import flags_net_loss


class Opening:
	def open_venture(self, node_id, pay=True, units=None):
		"""Start actually running something you have worked out how to do.

		`units` only means anything for SCALABLE_INSTITUTIONS (see that set's comment): how much capacity to found, where 1.0
		is the ordinary, historically-calibrated size every other figure in the engine assumes. Omit it and a first founding is
		1.0. Ask for LESS and you found a starter place - a fraction of the cost, a fraction of the yearly bleed, a fraction of
		what it gives back - which running() needs to be affordable at low income, since a fixed 1.0 size has no smaller step to
		start at. Ask for units on something ALREADY open and you are asking to expand it - see _expand_institution."""
		needs = self.needs
		nodes = needs.tree_nodes()
		if node_id not in nodes:
			return False, "no such node"
		projects = needs.legacy_projects()
		if node_id not in projects.done:
			return False, ("you have not worked out how to do that yet, so there "
			               "is nothing to open")
		if node_id in projects.granted:
			if needs.practisable[node_id]:
				# Society skill already in your practice: it's where your income comes from. Cannot open it again.
				return False, Refusal("already_your_practice", "you are already doing that - it is your practice, "
				                      "and it is where most of your income comes from. "
				                      "It is a skill this society has, not a concern "
				                      "you opened, so there is nothing to open and "
				                      "nothing to close")
			return False, ("that is something the society has, not a concern "
			               "of yours to run")
		if not needs.is_venture[node_id]:
			return False, ("that is knowledge, not a going concern: there is "
			               "nothing to open and nothing it would earn. It has "
			               "already changed what you can build")
		scalable_institutions = needs.capability_sets()[1]
		if node_id in projects.operating:
			if node_id in scalable_institutions and units and float(units) > 0:
				return self._expand_institution(node_id, float(units), pay)
			return False, "you are already running that"
		scalable = node_id in scalable_institutions
		fee, unit_count = self.opening_fee(node_id, units)
		refusal = needs.open_refusal(node_id, unit_count)
		if refusal:
			return False, refusal
		money_text = needs.money_text
		if pay:
			if fee > needs.spending_power("open"):
				# Report the same spending power the test checked.
				return False, Refusal("cash_short", "opening it costs %s in stock and premises, "
				                      "and between %s in cash and what anyone will "
				                      "advance against a purchase you can raise %s"
				                      % (money_text(fee, grouped=True), money_text(needs.acting_balance(), grouped=True),
				                         money_text(needs.spending_power("buy"), grouped=True)))
			needs.send(PayEdge(edges.EDGE_BUILDERS, fee, "opening a venture"))
		# A reopening keeps the plant's first opening year, so the ramp does not restart.
		year = needs.year()
		projects.business.open_plant(node_id, year)
		projects.business.note_opened_year_if_unknown(node_id, year)
		if scalable:
			projects.business.set_size(node_id, unit_count)
			needs.send(BumpInstitutionUnitsVersion())
		needs.send(NoteConcernChange("opening", node_id, "opened"))
		earns = self.venture_real_earnings(node_id, unit_count, fully_ramped=True)
		upkeep = self.venture_upkeep_quote(node_id, unit_count)
		costs = upkeep["now"]
		# A reopened concern keeps its original start, so it only mentions a ramp it is still climbing.
		still_ramping = needs.venture_ramp[node_id] < 1.0
		ramp_note = (
			" It reaches that over the first %d years as custom finds it - "
			"expect less at first, not a mistake in the figure."
			% needs.game_config()["revenue_ramp_years"]) if earns > 0 and still_ramping else ""
		# Flag net-loss concerns explicitly; exclude capability institutions.
		loss_note = (
			" !! this costs more than it earns (%s a year net), even once "
			"it is fully ramped up - that may be the right call for what it "
			"unlocks, but check 'why %s' if it is not what you meant."
			% (money_text(costs - earns, grouped=True), node_id)
			if flags_net_loss(costs, earns, node_id in needs.capability_sets()[0])
			else "")
		staffing_note = (" (%s once fully staffed)"
		                 % money_text(upkeep["at_full_staffing"], grouped=True)
		                 if upkeep["at_full_staffing"] > costs + 0.5 else "")
		charge_note = (" The opening charge was %s, for stock and premises."
		               % money_text(fee, grouped=True) if pay else "")
		return True, LogLine("venture_opened", "%s open%s: it earns %s a year and costs %s a year to "
		                     "run at today's staffing%s.%s%s%s"
		                     % (node_id, "" if unit_count == 1.0 else " at %.2f of a full founding" % unit_count,
		                        money_text(earns, grouped=True), money_text(costs, grouped=True),
		                        staffing_note, charge_note, ramp_note, loss_note),
		                     net_loss_warned=bool(loss_note))

	# Expansion: reusing "open" with units field keeps protocol backward-compatible.
	def _expand_institution(self, node_id, add_units, pay=True):
		"""Found more of an institution that is already open."""
		needs = self.needs
		have = needs.institution_units[node_id]
		ceiling = needs.institution_unit_ceiling[node_id]
		room = max(0.0, ceiling - have)
		if room < 0.02:
			return False, ("%s is already as big as this many people can fill: "
			               "about %.1f units of it, bounded by the population "
			               "(and, for a school or an academy, by how much of it "
			               "literacy says is not needed on the land)"
			               % (node_id, ceiling))
		add_units = min(add_units, room)
		node = needs.tree_nodes()[node_id]
		scholars_free, craftsmen_free = self.venture_staff_free()
		need_scholars, need_craftsmen = self.venture_hands(node_id)
		need_scholars, need_craftsmen = need_scholars * add_units, need_craftsmen * add_units
		if need_scholars > scholars_free + 0.01 or need_craftsmen > craftsmen_free + 0.01:
			return False, Refusal("supervisors_missing", "nobody free to keep an eye on the extra %.2f units "
			                      "of it: it needs %.2f more scholars and %.2f more "
			                      "craftsmen to supervise, and you have %.2f and %.2f "
			                      "not already watching something else"
			                      % (add_units, need_scholars, need_craftsmen, scholars_free, craftsmen_free),
			                      scholars_needed=need_scholars, craftsmen_needed=need_craftsmen,
			                      scholars_free=scholars_free, craftsmen_free=craftsmen_free)
		fee = needs.institution_unit_cost(node_id, have, add_units)
		money_text = needs.money_text
		if pay:
			if fee > needs.spending_power("buy"):
				return False, ("expanding %s by %.2f units costs %s, and "
				               "between %s in cash and what anyone will advance "
				               "against a purchase you can raise %s"
				               % (node_id, add_units, money_text(fee, grouped=True),
				                  money_text(needs.acting_balance(), grouped=True),
				                  money_text(needs.spending_power("buy"), grouped=True)))
			needs.send(PayEdge(edges.EDGE_BUILDERS, fee, "expanding a venture"))
		units_now = have + add_units
		needs.legacy_projects().business.set_size(node_id, units_now)
		needs.send(BumpInstitutionUnitsVersion())
		earns, costs = node["rev"] * units_now, node["up"] * units_now
		return True, ("%s expanded from %.2f to %.2f units for %s: it "
		              "now earns about %s a year and costs about %s to run"
		              % (node_id, have, units_now, money_text(fee, grouped=True),
		                 money_text(earns, grouped=True), money_text(costs, grouped=True)))
