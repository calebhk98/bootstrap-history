"""What the player is told about the hazards ahead: what kind of thing helps, which first steps are in sight, how long a hedge
takes, and one line per hazard on whether what stands between now and then is enough.

Needs: tree_nodes, techniques_held, critical_path, visible_to_player, start_check, project_cost, civilisation, year."""
from typing import Any, Dict, List, Optional

from . import constants, rules
from .hedge_steps import hedge_wants, startable_first
from .hedge_timing import lead_time_range, remaining_floor_years
from .window import hazards_not_yet_past


class Advice:

	def calendar_floor_remaining(self, goal: str) -> Optional[float]:
		"""Minimum calendar years before `goal` is finished, even if every prerequisite still open were started today: the
		critical path's own floor, less whatever of that chain is already done."""
		nodes = self.needs.tree_nodes()
		if goal not in nodes:
			return None
		_total, chain = self.needs.critical_path(goal)
		return remaining_floor_years(nodes, chain, self.needs.techniques_held())

	def hazard_advice(self, kind: str, hazard: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		"""What KIND of thing would help, without naming what you cannot see. Under fog this must not turn into a list of
		node ids to go and build: it names the kind of answer, in the same words a person in the year 100 would use. With
		the `hazard` itself, each defence is also listed with what it takes off that hazard's own figure."""
		beyond_national = kind == "staff_loss"
		multiplier, why = self.hazard_relief(kind, beyond_national=beyond_national)
		out = {"you_currently_take": round(multiplier, 3), "because_of": why}
		if hazard is not None and kind in hazard:
			base = hazard[kind]
			if kind == "staff_loss":
				base = self.staff_loss_exposure(base)["before_defences"]
			elif kind == "output_factor":
				base = 1.0 - base
			out["mitigations"] = self.mitigation_table(kind, base, beyond_national)
		if multiplier > 0.75:
			out["what_would_help"] = constants.ADVICE_WORDS.get(kind, "")
			# things you could begin today, which you can already see; never the hedge itself, so no tree by the back door
			step = self.hedge_first_steps(kind)
			if step:
				out["you_could_begin_now_toward_it"] = step
			# how long before any of it helps, as numbers only: a range, because these words bundle hedges that take a few
			# years (a patron) and hedges that take decades (three dispersed academies)
			nodes, held = self.needs.tree_nodes(), self.needs.techniques_held()
			lead_time = lead_time_range(
				floor_years for node, _share, _label in self.hazard_counters().get(kind, ())
				if not node.startswith("_") and node in nodes and node not in held
				for floor_years in [self.calendar_floor_remaining(node)]
				if floor_years is not None)
			if lead_time is not None:
				out["even_started_today_the_real_hedges_here_take_years"] = lead_time
		return out

	def hedge_first_steps(self, kind: str, limit: int = 4) -> List[Dict[str, Any]]:
		"""The hedges against `kind` that you can actually see, and what each one is waiting for. Deliberately narrow: the
		counters themselves and their direct prerequisites, and only those fog would let you see anyway. If nothing near
		is visible, the words on their own are the honest answer and this says nothing."""
		want, leads_to, counters = hedge_wants(self.hazard_counters().get(kind, ()), self.needs.tree_nodes(), self.needs.techniques_held())
		seen, out = set(), []
		for _distance, node_id in sorted(want):
			if node_id in seen:
				continue
			seen.add(node_id)
			if not self.needs.visible_to_player(node_id):
				continue
			can_start, why = self.needs.start_check(node_id, False, None, True)
			entry = {"id": node_id, "name": self.needs.tree[node_id]["name"],
			         "cost": round(self.needs.project_cost(node_id), 1),
			         "because_it_gives_you": leads_to.get(node_id),
			         "can_begin_now": bool(can_start),
			         "waiting_on": None if can_start else why}
			# the whole road, not this node's own floor: a counter is often the last of several steps that each look as
			# beginnable as it does, with a generation behind the total
			if node_id in counters:
				floor = self.calendar_floor_remaining(node_id)
				if floor is not None:
					entry["years_even_if_you_start_today"] = floor
			out.append(entry)
			if len(out) >= limit:
				break
		return startable_first(out)

	def hazard_timeline(self, limit: int = 4) -> List[Dict[str, Any]]:
		"""What is coming, how many years off, and whether what stands between now and then is enough: one line per hazard,
		nearest first. The gap between how long until it lands and how long the hedge takes, not the bare year count, is
		what escalates."""
		rows = []
		year = self.needs.year()
		for hazard, year_start, _year_end, in_progress in hazards_not_yet_past(self.needs.civilisation(), year):
			if self.effective_hazard(hazard)[0] is None:
				continue                  # its stated causes do not hold as things stand
			years_until = 0 if in_progress else (year_start - year)
			name = hazard.get("name", "hazard")
			kinds = rules.hazard_kinds_in(hazard)
			if not kinds:
				continue
			# the worst-defended kind and its own lead times; a hazard that is both a sack and an output shock is as urgent
			# as its slowest hedge, not the average
			worst_multiplier, quick_hedge, strong_hedge = 0.0, None, None
			for hazard_kind in kinds:
				multiplier, _why = self.hazard_relief(hazard_kind)
				if multiplier <= worst_multiplier:
					continue
				worst_multiplier = multiplier
				quick_hedge = strong_hedge = None
				if multiplier > 0.75:
					quick_hedge, strong_hedge = rules.hedge_lead_times(self.hazard_advice(hazard_kind))
			urgency, headline = rules.timeline_state(in_progress, worst_multiplier, years_until, quick_hedge, strong_hedge, name)
			rows.append({"name": name, "years_until": years_until, "in_progress": in_progress, "urgency": urgency,
			             "headline": headline})
		rows.sort(key=lambda row: (0 if row["in_progress"] else 1, row["years_until"]))
		return rules.compact_timeline(rows[:limit], constants.HAZARD_TIMELINE_WARN_TAGS)
