"""How an active project draws the founder's own hours and the hired trades' time each year.

project_hour_pace and active_hours_still_wanted say how many of the founder's own hours a project asks for; the hired-trade
drawdown (lab_max_span, trade_draw_plan, trade_demand_vs_supply, lab_year_draw) says how much of each trade's time it
draws, and the plan is the one the portfolio screens read before the allocation runs."""
from sim.workforce.api import DrawTradeHours

from . import progress_rules
from .constants import LAB_CREW_RATE_MULT, LAB_MAX_SPAN_FLOOR_YEARS, LAB_MAX_SPAN_MULTIPLE
from .trade_demand import trade_demand_table


class ProgressHours:
	def project_hour_pace(self, node_id):
		"""How many of YOUR OWN hours active project `node_id` would draw this year if nothing else competed for the
		pool - the year's own uncapped want, read here rather than re-derived, so anything reporting on it before the
		allocation runs cannot silently disagree with what the year actually offers."""
		record, node = self.seat.active[node_id], self.needs.tree_nodes()[node_id]
		# A bounty is worked by whoever claims the prize, not by the poster.
		if node_id in self.seat.bountied:
			return 0.0
		# Throttle not applied here; caller applies. Returns WANT, not allocation.
		return progress_rules.hour_pace(record["ph_left"], node["ph"], node["yrs"])

	def active_hours_still_wanted(self):
		"""{project id: hours} for every active project that would still like a real amount of your own time this year,
		at the pace project_hour_pace gives it - not what it will actually get, just what it is still asking for. Sorted
		iteration: this feeds a caller that may sum or rank it, and the active record's own order is not fixed."""
		out = {}
		nodes = self.needs.tree_nodes()
		for node_id in sorted(self.seat.active):
			if node_id not in nodes:
				continue
			pace = self.project_hour_pace(node_id)
			if pace > 0.5:
				out[node_id] = pace
		return out

	def project_useful_hours(self, node_id):
		"""The most of your own hours active project `node_id` can use in a year: its pace (project_hour_pace) bounded by
		the work left, times the same resource throttle the year applies."""
		record = self.seat.active[node_id]
		return min(record["ph_left"], self.project_hour_pace(node_id)) * self.needs.resource_throttle(node_id)[0]

	def lab_max_span(self, node_id):
		"""The most years a project may spend trying to find enough of a hired trade before it is given up on."""
		return progress_rules.max_span_years(LAB_MAX_SPAN_FLOOR_YEARS, self.needs.tree_nodes()[node_id]["yrs"], LAB_MAX_SPAN_MULTIPLE)

	def _effective_lab_left(self, node_id, project_state):
		"""What is left of each hired trade's total for active project `node_id`, read-only: never writes the record's
		`lab_left`, unlike lab_year_draw (the only place allowed to initialise it for real)."""
		return progress_rules.effective_lab_left(project_state, self.needs.tree_nodes()[node_id])

	def trade_draw_plan(self, node_id, lab_left=None):
		"""What project `node_id` would like to draw from each hired trade this year, if the trade could supply it
		without limit: the DEMAND side of lab_year_draw, read-only and with no knowledge of what any other project wants
		or what the trade can supply. `lab_left` None means a project that has not started yet."""
		return progress_rules.trade_draw_plan(self.needs.tree_nodes()[node_id], lab_left, LAB_CREW_RATE_MULT)

	def trade_shortage_kind(self, trade_id, need, total_demand=None):
		"""Why a trade is short for a project that wants `need` hours a year of it: "staffing" when the society cannot
		field that much at all, "booked" when it can but the portfolio's demand exceeds it, else None."""
		return progress_rules.shortage_kind(self.needs.hours_you_can_call_on[trade_id], need, total_demand)

	def trade_shortfall_note(self, project_state):
		"""The step-log reason for a project short of hired trades."""
		return progress_rules.shortfall_note(project_state)

	def trade_demand_vs_supply(self):
		"""Aggregate, by hired trade: what this year's ACTIVE portfolio wants from it against what the trade can actually
		supply - read-only, so calling this to look never changes what lab_year_draw later does."""
		desired_by_project = {
			node_id: {trade_id: plan["desired"] for trade_id, plan in self.trade_draw_plan(
				node_id, self._effective_lab_left(node_id, self.seat.active[node_id])).items()}
			for node_id in sorted(self.seat.active)}
		return trade_demand_table(desired_by_project, lambda trade_id: self.needs.hours_you_can_call_on[trade_id])

	def lab_year_draw(self, node_id, project_state, frac, hired_left):
		"""This year's hired-labour draw for active project `node_id`.

		Returns (hh, worst, frac, abandon): `hh` is the total hired hours drawn this year (what the year checks against
		`hired_left`), `worst` the worst-supplied trade's shortfall against its own historical pace (it drives the
		founder-hours give-back), `frac` the money-pacing fraction, reduced when a trade came up short of its own pace,
		and `abandon` None or a reason the project should be dropped because it ran out of calendar (lab_max_span).

		Mutates the record's `lab_left` and sends the trade hours drawn, exactly where the code this replaced did."""
		needs = self.needs
		node = needs.tree_nodes()[node_id]
		if project_state.get("lab_left") is None:
			project_state["lab_left"] = self._effective_lab_left(node_id, project_state)
		lab_left = project_state["lab_left"]
		hired_hours = 0.0
		worst = 1.0
		plan = self.trade_draw_plan(node_id, lab_left)
		need_by_trade = {trade_id: min(entry["nominal"], entry["left"]) for trade_id, entry in plan.items()}

		def free_hours(trade_id):
			return needs.hours_you_can_call_on[trade_id] - needs.hour_commitments()["trade_hours_used"].get(trade_id, 0.0)

		for trade_id, plan_entry in sorted(plan.items()):
			left, nominal = plan_entry["left"], plan_entry["nominal"]
			have = max(0.0, free_hours(trade_id))
			# Ceiling is crew, not calendar. Take what's useful and available.
			drawn = min(left, plan_entry["ceiling"], have)
			lab_left[trade_id] = max(0.0, left - drawn)
			needs.send(DrawTradeHours(trade_id, drawn))
			hired_hours += drawn
			# Warning drawn at old pace. Shortfall triggers give-back.
			target = min(nominal, left)
			if target > 0:
				worst = min(worst, drawn / target)
		if worst < 1.0:
			project_state["status"] = "BLOCKED_INPUTS"
			frac *= worst
			short_trades = progress_rules.short_trades(lab_left, node, free_hours)
			project_state["short_of_trade"] = short_trades
			project_state["short_of_trade_staffing"] = [
				trade_id for trade_id in short_trades
				if self.trade_shortage_kind(trade_id, need_by_trade.get(trade_id, 0.0)) == "staffing"]
		else:
			project_state["status"] = "ACTIVE"
			project_state.pop("short_of_trade", None)
			project_state.pop("short_of_trade_staffing", None)
		# DEADLINE: prevents creep. Unmet trades trigger abandonment.
		if project_state["yrs"] >= self.lab_max_span(node_id) and any(value > 0.5 for value in lab_left.values()):
			unmet = sorted(trade_id for trade_id, value in lab_left.items() if value > 0.5)
			return hired_hours, worst, frac, (
				"after %d years there was still not enough %s here to finish "
				"it. What was spent is lost; you still know what you learned "
				"along the way" % (int(self.lab_max_span(node_id)), " or ".join(unmet[:2])))
		return hired_hours, worst, frac, None
