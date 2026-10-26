"""How the state notices a household and what it takes: the household's visible scale, the state's notice of it, the requisition
and office it assesses, the tail risk of confiscation and the military's leverage that softens it.

A household that reaches real scale must eventually draw a state reaction of its own: the state can requisition output, demand
military supply, press an office on a household, or threaten confiscation. Every input is a number the game already tracks for
another purpose, combined freshly for the question; nothing is stored. The state's reach (0..1) is the first factor: a state
with few officials or long roads caps the product so low that no threshold is crossed.

Needs: danger_lines, base_annual_wage, headcount, acting_balance, labour_state_weights, techniques_held,
techniques_granted, tree_nodes, effect_best, civilisation, mass_text."""
from sim.agents.api import demand_answer
from sim.world import military_logistics

from . import constants, rules, state_notice_rules
from .military_rules import leverage_of


class Notice:

	# ---- what the state cares about, and how alarming a technique is ----

	def state_trait_weights(self):
		"""What the state cares about, per trait, for this civilisation."""
		return rules.state_trait_weights(self.needs.labour_state_weights(), self.world.value_weights)

	def state_interest(self, node_record):
		return rules.state_interest(node_record.get("traits", []), self.state_trait_weights())

	def alarm_of(self, node_record):
		"""How alarming this technology is to this civilisation, before defences. Not speed, and not money: producing an
		effect a society has no category for is what frightens it."""
		alarm = rules.alarm_before_effects(node_record.get("traits", []), self.world.value_weights,
		                                   self.seat.familiarity, self.seat.protection)
		# a recognised scholar doing something strange is a scholar; a stranger doing the same thing is a sorcerer
		return self.needs.effect_factor("alarm_factor", alarm)

	# ---- the military ----

	def military_leverage(self):
		"""0..1: how much of the military branch the founder can put in a patron's hands. Sqrt-scaled and capped, so the first
		working gun matters enormously to a patron and the fortieth barely adds; counts founder-built nodes, not the
		inherited ones."""
		nodes = self.needs.tree_nodes()
		military_node_count = sum(1 for node_id in self.needs.techniques_held() - self.needs.techniques_granted()
		                          if "military" in nodes[node_id].get("traits", ()))
		return leverage_of(military_node_count, constants.MILITARY_LEVERAGE_SATURATES_AT)

	def military_equipment_burden_kg_per_soldier_per_year(self, adoption=None):
		"""What an army costs to field and keep fed, in kilograms of worked iron and ammunition (never money) per soldier a
		year: a straight line from a soldier with cold steel only to one with a modern rifle, by how far the founder's work
		has been taken up (`adoption`, 0..1; the founder's own leverage when not given). A transitional heuristic."""
		melee_kg = military_logistics.annual_iron_and_ammunition_burden_kg_per_soldier()
		rifle_kg = military_logistics.annual_iron_and_ammunition_burden_kg_per_soldier(
			firearm=military_logistics.MODERN_SERVICE_RIFLE,
			engagements_per_year=constants.MILITARY_EQUIPMENT_ERA_CAMPAIGN_TEMPO_ENGAGEMENTS_PER_YEAR)
		leverage = self.military_leverage() if adoption is None else adoption
		return melee_kg + leverage * (rifle_kg - melee_kg)

	# ---- how visible the household is ----

	def household_scale(self):
		"""0..1: how large and visible this household is to a state deciding whether it is worth the bother of leaning on:
		headcount and visible wealth weigh heaviest, eminence a smaller share."""
		seat = self.seat
		return self.visible_scale(self.needs.headcount(), demand_answer.visible_wealth(self.needs.acting_balance(), seat.concealed),
		                          seat.eminence, seat.defiance)

	def visible_scale(self, headcount, wealth, eminence, defiance=0.0):
		"""household_scale's rule for any taxpayer: what an observer can count of its staff, its wealth and (for a person) its
		prominence, and a surcharge for having defied the state (what is hidden is not counted in `wealth`)."""
		return rules.visible_scale(headcount, wealth, eminence, demand_answer.notice_surcharge(defiance),
		                           self.needs.danger_lines()["eminence"], self.needs.base_annual_wage["labourer"])

	# ---- the state's notice and its levies ----

	def state_notice(self):
		"""0..1: state_reach times household_scale: the single gate every pressure checks before it does anything."""
		return self.state_reach() * self.household_scale()

	def _notice_over(self, threshold):
		"""0..1: how far past `threshold` the state's notice stands, as a share of the remaining distance to full notice."""
		return state_notice_rules.share_past(self.state_notice(), threshold)

	def notice_over(self, scale, capacity=None):
		"""How far past the notice line a taxpayer of this visible scale stands. `capacity` is the state's (this one's when
		not given)."""
		notice = (self.state_reach() if capacity is None else capacity) * scale
		return state_notice_rules.share_past(notice, constants.STATE_NOTICE_THRESHOLD)

	def levy_shares(self, scale, protection=0.0, state=None):
		"""(requisition share, office share) of a year's revenue the state assesses on a taxpayer of this visible scale: one
		rule for the founder's household, a firm or any other actor. `state` is (capacity, tax share, requisition rate, office
		rate) of another country's state; the founder's own state when not given."""
		if state is None:
			capacity, tax_share = self.state_reach(), float(self.needs.civilisation()["starting_tax_share"])
			requisition_rate, office_rate = self.state_levy_rates()
		else:
			capacity, tax_share, requisition_rate, office_rate = state
		return state_notice_rules.levy_shares_at(self.notice_over(scale, capacity), tax_share * capacity, requisition_rate,
		                                         office_rate, protection, constants.REQUISITION_PROTECTION_DISCOUNT)

	def state_levy_rates(self):
		"""(requisition, office) share of income the state takes at full notice; nothing before the state has budgeted a year."""
		state = self.needs.cast_state()
		record = None if state is None else state.records.get("government:" + str(self.needs.civilisation().get("id")))
		if record is None:
			return 0.0, 0.0
		return record.levy_requisition_rate, record.levy_office_rate

	def requisition_report(self):
		"""(share of this year's revenue, [why it is smaller than listed]) the state takes as goods at its own price. Protection
		bargains it down; it does not buy exemption."""
		if self.state_notice() <= constants.STATE_NOTICE_THRESHOLD:
			return 0.0, []
		share = self.levy_shares(self.household_scale(), self.seat.protection)[0]
		why = []
		if self.seat.protection > 0:
			why.append("bargained down by standing and patronage (protection %d%%)" % round(self.seat.protection * 100))
		why.extend(self.group_levy_reasons())
		return max(0.0, share), why

	def office_report(self):
		"""(share of this year's revenue, the office's name in this civilisation) a pressed civic office costs every year it
		runs. Protection does not discount it; it gives protection back."""
		if self.state_notice() <= constants.STATE_NOTICE_THRESHOLD:
			return 0.0, None
		state_pressure_cfg = self.needs.civilisation().get("state_pressure") or {}
		share = self.levy_shares(self.household_scale())[1]
		return share, state_pressure_cfg.get("office_name", "a civic office")

	def military_demand_eligible(self):
		"""Is this household both militarily useful and visible enough that a state which can fight would ask it for supply?"""
		return state_notice_rules.military_demand_eligible(
			self.military_leverage(), constants.MIL_LEVERAGE_FLOOR_FOR_DEMAND, self.state_notice(),
			constants.STATE_NOTICE_THRESHOLD_MILITARY)

	def state_military_ask(self, taxable, scale):
		"""What the state asks of one militarily useful taxpayer in arms this year."""
		return self.needs.state_treasury().military_ask(taxable, scale, self.needs.actor_world())

	def confiscation_risk(self):
		"""(yearly probability, [what is holding it off]) of the treasury's tail risk at the top of the state-notice scale: a
		patron and standing, dispersal of the household's holdings, and being useful to the state mitigate it."""
		over = self._notice_over(constants.STATE_NOTICE_THRESHOLD_CONFISCATION)
		if over <= 0.0:
			return 0.0, []
		dispersal = 0.0
		held = self.needs.effect_best("confiscation_dispersal")
		if held is not None:
			dispersal = max(dispersal, held[1]["flat"])
		chance, active = state_notice_rules.confiscation_chance(
			over, constants.CONFISCATION_MAX_RATE, self.seat.protection, constants.CONFISCATION_PROTECTION_DISCOUNT,
			dispersal, self.military_leverage(), constants.CONFISCATION_MILITARY_USEFULNESS_DISCOUNT)
		return chance, [constants.CONFISCATION_PROTECTION_LABELS[index] for index in active]

	def confiscation_status(self):
		"""What the `risk` screen shows: this year's confiscation chance, the protections holding it down, and those not yet in force."""
		chance, active = self.confiscation_risk()
		return {"chance_this_year": round(chance, 4), "held_off_by": active,
		        "not_yet_in_force": [label for label in constants.CONFISCATION_PROTECTION_LABELS if label not in active]}

	def state_pressure_report(self):
		"""What `risk`/`state` shows before any of this bites; a dormant household gets None and only what is live gets a field."""
		notice = self.state_notice()
		req_share, _req_why = self.requisition_report()
		off_share, off_name = self.office_report()
		conf_p, conf_why = self.confiscation_risk()
		state_pressure_cfg = self.needs.civilisation().get("state_pressure") or {}
		groups = self.interest_groups()
		if req_share <= 0.0005 and off_share <= 0.0005 and conf_p <= 0.0 and not self.military_demand_eligible() and not groups:
			return None
		out = {"now": round(notice, 3), "noticed_above": constants.STATE_NOTICE_THRESHOLD,
		       "confiscation_risk_above": constants.STATE_NOTICE_THRESHOLD_CONFISCATION}
		if req_share > 0.0005:
			out["requisition"] = ("%s takes about %d%% of this year's revenue"
			                      % (state_pressure_cfg.get("requisition_name", "the state"), round(req_share * 100)))
		if off_share > 0.0005 and off_name:
			out["office"] = ("%s costs about %d%% of revenue a year, and buys protection in return" % (off_name, round(off_share * 100)))
		if self.military_demand_eligible():
			burden_kg = self.military_equipment_burden_kg_per_soldier_per_year()
			out["military_supply"] = ("%s may demand your output; refusing a state that can still fight is not free "
			                          "(equipping one soldier your way costs it about %s of iron and ammunition a year)"
			                          % (state_pressure_cfg.get("military_name", "the arsenal"),
			                             self.needs.mass_text(burden_kg, digits=1, unit="kilogram")))
		if conf_p > 0:
			out["confiscation_chance_this_year"] = round(conf_p, 4)
			out["confiscation_reduced_by"] = conf_why
		if groups:
			out["interest_groups"] = ["%s: %s" % (group["name"], group["cause"]) for group in groups]
		out["what_helps"] = "a patron or standing; holdings not all in one place; being useful to a state that fights"
		return out
