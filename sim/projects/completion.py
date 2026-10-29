"""What finishing a piece of work actually does, and what a failed attempt costs.

`_complete` rolls the dice on the project's live risk: a failed roll is `_fail_attempt` (the attempt is counted, part of
the calendar banked, the loss charged and logged); a finished project leaves the record in hand, becomes a held technique,
applies its effects, earns standing, and may hand over the staff an institution grants. The goal's road is read before
and after so the log can say how finishing moved it."""
from sim.agents.api import edges
from sim.knowledge.api import LearnTechnique, RevealFrom
from sim.diffusion.api import ApplyTechEffects
from sim.ledger.api import PayEdge
from sim.living_stock.api import ChangeHeld
from sim.polity.api import AddGovernance, AddScandal, CarryOutTransfers, GainReputation
from sim.production.api import LearnFromFailure
from sim.reporting.api import RecordEvent
from sim.seats.api import RecordGoalReached
from sim.workforce.api import GrantStaff, LoseCrew, ReleaseHours

from . import failure_text, goal_rules
from .completion_rules import road_line, severity_of_loss, staff_shortfall
from .constants import (FAILURE_RESET_SHARE, GOAL_PATH_FAILURE_WEIGHT, MINOR_FAILURE_SHARE, PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT,
                        REPUTATION_GAIN_BASE, REPUTATION_GAIN_REVENUE_BONUS, REPUTATION_GAIN_STATE_INTEREST_COEFFICIENT)
from .failure_cause import failure_cause
from .failure_diagnosis import SHORTFALL_FACTOR_RANGE, failure_teaches, measured_report, unmeasured_report
from .permanent_benefit import permanent_parts
from .risk_rules import attempt_fails


class Completion:
	def _setup_completion(self) -> None:
		self._goal_closures = {}                  # goal -> the nodes it needs (the tree does not change under a goal)

	def reputation_gain_of(self, node):
		"""The standing finishing `node` adds; `why` quotes this same figure."""
		return (REPUTATION_GAIN_BASE
		        + REPUTATION_GAIN_STATE_INTEREST_COEFFICIENT * max(0.0, self.needs.state_interest(node))
		        + (REPUTATION_GAIN_REVENUE_BONUS if node["rev"] > 0 else 0.0))

	def substitute_quality_discount(self):
		"""What a purchasable substitute scores against the stated quality of the option."""
		return PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT

	def failure_reset_share(self):
		"""The share of a failed project's bill that is lost."""
		return FAILURE_RESET_SHARE

	def goal_closure_ids(self):
		"""Every node the current goal needs, cached per goal."""
		goal = self.needs.goal()["node"]
		cache = self._goal_closures
		if goal not in cache:
			try:
				cache[goal] = set(self.needs.tree_closure(goal))
			except Exception:
				cache[goal] = set()
		return cache[goal]

	def failure_severity(self, node_id, lost, means):
		"""'minor' or 'major', from the loss against the player's means and whether the failed project sits on the goal's
		road."""
		return severity_of_loss(lost, means, node_id in self.goal_closure_ids(), MINOR_FAILURE_SHARE, GOAL_PATH_FAILURE_WEIGHT)

	def goal_snapshot(self):
		"""The goal's live measure(s) and road progress, or None without a goal."""
		needs = self.needs
		goal = needs.goal()["node"]
		nodes = needs.tree_nodes()
		if goal not in nodes:
			return None
		road = self.goal_closure_ids()
		measures = {}
		condition = nodes[goal].get("win_condition")
		done = needs.techniques_held()
		if condition and goal not in done:
			try:
				metric = condition.get("metric") or "goal measure"
				fraction = metric in goal_rules.FRACTION_METRICS
				measures[metric.replace("_", " ")] = (needs.win_condition_value(condition), fraction)
				for label, ceiling in goal_rules.GOAL_DETERMINANTS.get(metric, ()):
					measures[label] = (float(needs.literacy_ceiling[ceiling]), True)
			except (ValueError, AttributeError):
				pass
		return goal_rules.snapshot(measures, len(road & done), len(road))

	def goal_effect_lines(self, node_id, before):
		"""Log lines saying how finishing `node_id` moved the goal."""
		needs = self.needs
		after = self.goal_snapshot()
		moved, _gained = goal_rules.goal_movement(before, after)
		lines = ["goal effect: %s %s -> %s" % row for row in moved]
		goal = needs.goal()["node"]
		if (before and node_id != goal and node_id in self.goal_closure_ids()
		        and goal not in needs.techniques_held()):
			lines.append(road_line(needs.fog_of_war(), after["road_done"], after["road_total"]))
		return lines

	def opening_shortfall(self, node_id):
		"""(need scholars, need craftsmen, free scholars, free craftsmen) when today's free staff could not supervise
		this concern, else None."""
		need_scholars, need_craftsmen = self.needs.venture_hands[node_id]
		free_scholars, free_craftsmen = self.needs.venture_staff_free()
		return staff_shortfall(need_scholars, need_craftsmen, free_scholars, free_craftsmen)

	def _complete(self, node_id):
		needs = self.needs
		node = needs.tree_nodes()[node_id]
		_risk_this_attempt = self.effective_risk(node_id)
		if attempt_fails(needs.game_random().random(), _risk_this_attempt):
			self._fail_attempt(node_id, _risk_this_attempt)
			return
		goal_before = self.goal_snapshot()
		del self.seat.active[node_id]
		self.seat.bountied.discard(node_id)
		# A FINISHED PROJECT CANNOT BE GIVEN MORE HOURS. Unlike stopping or halting one - both of which carry what was
		# already paid forward if the player starts the same id again - there is no "again" once it is done, so a
		# standing order aimed at this id would otherwise sit in `allocate`'s list for ever, pointed at nothing.
		needs.send(ReleaseHours(node_id))
		needs.send(LearnTechnique(node_id, year=needs.year()))
		for material, units in (node.get("grants") or {}).items():
			needs.send(ChangeHeld(material, units))
		needs.send(CarryOutTransfers(node_id))
		# A technology changes the society that built it. Only for work YOU completed: a society is not altered by owning
		# something it always had. The alarm is read before the work's own effects apply, which is the figure `why` quotes.
		alarm = needs.alarm_of(node)
		needs.send(ApplyTechEffects(node_id))
		needs.send(RevealFrom(node_id))
		# Visible, useful, State-approved work builds standing. Obscure laboratory work does not, however important it
		# is, which is a real and annoying fact about how credibility actually accrues.
		needs.send(GainReputation(self.reputation_gain_of(node)))
		needs.send(AddScandal(alarm))
		needs.send(AddGovernance(needs.state_interest(node)))
		# The staff an institution grants are recorded as a grant, NOT added to the payroll: the year resyncs the pools
		# from the employees, so a bare addition would be overwritten the next time it runs.
		#
		# ONLY WITHOUT auto_hire: with it on - the optimizer's default, off for a player - the staff capacity already
		# counts this same institution and the year's smoothing grows the pools toward that ceiling on its own; granting
		# it a second time here as well would double-count every one of these three institutions against a tree
		# calibrated to open up much more slowly.
		hire_mode = needs.automatic_policy("auto_hire")
		if not hire_mode or hire_mode == "replace":
			grant = needs.mechanic["staff_grant"].get(node_id)
			if grant:
				needs.send(GrantStaff(**grant))
		if needs.is_venture[node_id] and not needs.automatic_policy("auto_open"):
			# Built is not open: say what is switched off until it is opened.
			benefit = needs.capability_sets()[2].get(node_id)
			held = permanent_parts(node, needs.tech_effects[node_id] or {})
			needs.send(RecordEvent.of("project_completed", "completed: %s. STATUS: CLOSED / NOT OPERATING. %s%s Open it "
			           "('open %s') to begin and to start paying upkeep."
			           % (node["name"],
			              ("In force already, open or not: %s. " % "; ".join(held)) if held else "",
			              ("Not in effect until open: %s." % benefit) if benefit
			              else "Nothing is earning yet.", node_id)))
			shortfall = self.opening_shortfall(node_id)
			if shortfall:
				needs.send(RecordEvent.of("opening_shortfall", "with today's staff you could not open it: it needs %.1f "
				           "scholars and %.1f craftsmen to supervise, and %.1f and %.1f "
				           "are free." % shortfall))
		else:
			needs.send(RecordEvent.of("project_completed", "completed: " + node["name"]))
		for line in self.goal_effect_lines(node_id, goal_before):
			needs.send(RecordEvent.of("goal_effect", line))
		needs.send(RecordGoalReached(node_id, needs.year()))

	def _fail_attempt(self, node_id, _risk_this_attempt):
		"""A project's roll failed: count the attempt, bank part of the calendar, charge the loss within what the purse
		and credit line bear, and log it. A bounty's claimant redoes the work at no cost to the poster."""
		needs = self.needs
		node = needs.tree_nodes()[node_id]
		_yrs_before = self.seat.active[node_id]["yrs"]
		self.seat.failed_attempts[node_id] += 1
		_diagnosis = self._note_failure(node_id)
		if failure_teaches(needs.mechanic["diagnosis_instrument"].get(node_id), needs.techniques_held()):
			needs.send(LearnFromFailure(node_id))
		claimed = node_id in self.seat.bountied
		# A bounty's claimant redoes the work: the poster's prize holds and no hours or money fall on the poster.
		self.seat.active[node_id]["ph_left"] = (
			0.0 if claimed else
			node["ph"] * self.rebuild_work_factor(node_id) * FAILURE_RESET_SHARE)
		# THE CALENDAR CLOCK IS NOT WIPED: a failed attempt must not reset the multi-year diffusion clock to zero,
		# restarting the whole process from nothing. Even ONE failed attempt already does real social groundwork
		# (workshops retooled, a workforce that has seen it once, a regulator who already sat through the pitch), so the
		# first failure already banks a real share of the elapsed clock, not zero - it is the risk term, not this one,
		# that has nothing to show after only one failure. What this banks keeps growing, with diminishing returns, as
		# the failure count grows, and is capped well short of the whole clock (RETRY_CALENDAR_CAP) so a retried
		# programme is only ever readier, never instantly ready.
		_retain = self._retry_calendar_retain(node_id)
		self.seat.active[node_id]["yrs"] = _yrs_before * _retain
		_lost = 0.0 if claimed else needs.failure_loss(node_id)
		_severity = self.failure_severity(node_id, max(0.0, _lost), needs.funding_capacity())
		# What the purse and the credit line left cannot bear is not forgiven: it is added to what the project still
		# costs, paid through the gated instalments.
		_borne = needs.bearable_part_of(_lost)
		needs.send(PayEdge(edges.EDGE_DESTROYED, _borne, "failure losses"))
		if not claimed:
			for _loss_line in self.lose_what_was_risked(node_id):
				needs.send(RecordEvent.of("failure_loss", "%s: %s" % (node["name"], _loss_line)))
		self.seat.active[node_id]["cost_left"] = (self.seat.active[node_id].get("cost_left") or 0.0) + (_lost - _borne)
		# A failure always announces itself; its size sets how loudly.
		_next_risk = self.effective_risk(node_id)
		_banked = self.seat.active[node_id]["yrs"]
		attempts = self.seat.failed_attempts[node_id]
		if claimed:
			needs.send(RecordEvent.of("project_failed", failure_text.claimed_line(node["name"], attempts, _next_risk),
			                          project=node_id, severity="claimed", lost=0.0))
			return
		lost_text = needs.money_text(max(0.0, _lost), grouped=True)
		if _severity == "minor":
			needs.send(RecordEvent.of("project_failed", failure_text.minor_line(
				node["name"], lost_text, FAILURE_RESET_SHARE, attempts, _next_risk, _diagnosis),
				project=node_id, severity="minor", lost=max(0.0, _lost)))
			return
		needs.send(RecordEvent.of("project_failed", failure_text.major_line(
			node["name"], failure_cause(node, needs.state_interest(node)), FAILURE_RESET_SHARE,
			needs.plain_number(node["ph"] * FAILURE_RESET_SHARE), lost_text, attempts,
			failure_teaches(needs.mechanic["diagnosis_instrument"].get(node_id), needs.techniques_held()), _next_risk,
			_risk_this_attempt, _banked, _yrs_before, _diagnosis), project=node_id, severity="major", lost=max(0.0, _lost)))

	def _note_failure(self, node_id):
		"""Record a failure that was or was not diagnosable and return the sentence for the report ("" when the node
		needs no instrument)."""
		needs = self.needs
		spec = needs.mechanic["diagnosis_instrument"].get(node_id)
		if spec is None:
			return ""
		instrument_name = needs.tree_nodes()[spec["instrument"]]["name"]
		if failure_teaches(spec, needs.techniques_held()):
			low, high = SHORTFALL_FACTOR_RANGE
			return measured_report(spec, needs.game_random().uniform(low, high), instrument_name)
		return unmeasured_report(spec, instrument_name)

	def lose_what_was_risked(self, node_id):
		"""Take the crew, hull and cargo a failed attempt put at risk. Returns the log lines saying what went."""
		needs = self.needs
		risks = needs.tree_nodes()[node_id].get("risks")
		if not risks:
			return []
		lines = []
		crew = tuple(sorted((risks.get("crew") or {}).items()))
		for trade, have, kept in (needs.send(LoseCrew(crew)) if crew else ()):
			if round(have) - kept > 0:
				lines.append("crew lost: %d of %d %s" % (round(have) - kept, round(have), trade))
		for kind in goal_rules.STOCK_RISKS:
			for material, share in sorted((risks.get(kind) or {}).items()):
				lost = needs.stock_held[material] * share
				if lost > 0:
					needs.send(ChangeHeld(material, -lost))
					lines.append("%s lost: %.3g of %s" % (kind, lost, material))
		return lines
