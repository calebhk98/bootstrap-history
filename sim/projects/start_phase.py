"""The year's start of new projects: the optimizer walks the goal order and starts whatever it judges best.

The phase is `start_projects` of sim/engine/year_phases.py. What it leaves for the phases after it (the director hours
free and the hired-labour room, both measured before any start) is the view `start_hours`."""
from typing import Dict, List, Optional, Tuple

from .auto_start import judge_start_candidate
from .commands import PostBounty
from sim.reporting.api import RecordAutomation, RecordAutomationSkip
from .phase_rules import candidates_in_order, max_active_projects, money_is_thin, non_bountied_count


class StartPhase:
	def _setup_start_phase(self) -> None:
		self._start_hours: Dict[Optional[str], Tuple[float, float]] = {}     # acting seat -> (pool, hired room) of its last start phase

	def start_hours(self) -> Tuple[float, float]:
		"""(director hours free, hired-labour room) as the acting seat's start phase measured them this year."""
		return self._start_hours[self.clock.acting_seat]

	def start_projects_phase(self, seat_id: str) -> None:
		needs = self.needs
		hours = needs.hours_available
		pool = max(0.0, hours["director_pool"] - hours["director_committed"])
		hired_left = hours["hired_cap"]
		self._start_hours[self.clock.acting_seat] = (pool, hired_left)
		# MANUAL MODE STOPS HERE. This loop is "the optimizer": it walks the goal order and starts whatever it judges
		# best, which is exactly the behaviour a free-choice player must NOT get; the only way anything starts is
		# then the start command. Everything after (materials, staff, money, hazards, the calendar) runs as before.
		automation = needs.automation()
		if automation["manual"] or needs.year() < needs.debt_status()["credit_frozen_until"]:
			return
		self._start_what_it_can(automation["bounty_set"], hours["director_pool"])

	def _start_what_it_can(self, bounty_set, director_pool: float) -> None:
		needs = self.needs
		limits = needs.project_limits()
		staff = needs.staff()
		max_active = max_active_projects(limits["base"], director_pool, limits["per_director_hours"], staff["scholars"],
		                                 limits["per_scholar"], staff["artisans"], limits["per_artisan"])
		# EARN A LIVING FIRST: a founder who arrives with little and walks the goal-ordered list starves, so when the
		# surplus is thin the optimizer prefers whatever pays best for what it costs; the goal order resumes the
		# moment there is money to pursue it with.
		upkeep = needs.upkeep()
		revenue = needs.revenue_estimate()
		fixed = upkeep + needs.living_cost(revenue, upkeep) + needs.mine_operating_cost()
		candidates = candidates_in_order(needs.project_order(), lambda node_id: needs.tree[node_id], needs.project_cost, money_is_thin(revenue, fixed))
		projects = needs.legacy_projects()
		# Only a normal start and a bounty change the count, so it is tracked as they happen, not rebuilt per node.
		non_bountied_active = non_bountied_count(projects.active, self.seat.bountied)
		room = needs.funding_capacity() - self.committed_cost()
		said_blocked = False
		too_dear: List[Tuple[str, float]] = []
		for node_id in candidates:
			verdict = judge_start_candidate(non_bountied_active, max_active, lambda: needs.start_check(node_id, False, None, False)[0],
			                                lambda: needs.project_cost(node_id), room)
			if verdict == "cap":
				needs.send(RecordAutomationSkip("auto_start", "further projects",
				                                "%d projects already active; the cap is %d" % (non_bountied_active, max_active),
				                                {"reason_kind": "active_project_cap", "active": non_bountied_active, "cap": max_active}))
				break
			if verdict == "blocked":
				# one row a year, for the highest-priority candidate; the rest would flood the trail
				if not said_blocked:
					said_blocked = True
					needs.send(RecordAutomationSkip("auto_start", needs.tree[node_id]["name"],
					                                needs.start_refusal(node_id) or "cannot start yet"))
				continue
			# Do not begin what you cannot pay for: a project started on unaffordable capacity gets its bill left
			# unpaid, creditors halt everything, and the spend already made is lost. The room is the same two
			# figures the player-facing aggregate warning reads, so the two cannot drift apart.
			if verdict == "too_dear":
				too_dear.append((node_id, room))
				continue
			before = needs.acting_balance()
			if node_id in bounty_set and self.bounty_eligible(node_id) and self.post_bounty(PostBounty(node_id)):
				needs.send(RecordAutomation("auto_start", "bounty", needs.tree[node_id]["name"],
				                            "on the bounty list and eligible, so a bounty was posted instead of starting it", before))
				# a bounty adds to both `active` and `bountied`: the count of non-bountied projects is unchanged
				room = needs.funding_capacity() - self.committed_cost()
				continue
			self.initialize_project(node_id)
			non_bountied_active += 1
			room = needs.funding_capacity() - self.committed_cost()
		if too_dear:
			# one row a year: the highest-priority candidate and how many more were dearer than their room
			first, first_room = too_dear[0]
			cost = needs.project_cost(first)
			needs.send(RecordAutomationSkip(
				"auto_start", needs.tree[first]["name"],
				"costs %.0f and the room left to commit is %.0f; %d candidates in all cost more than the room"
				% (cost, first_room, len(too_dear)),
				{"reason_kind": "cost_over_room", "cost": cost, "room": first_room, "candidates": len(too_dear)}))

