"""What the engine does on its own, every year, about staffing: closing what nobody is left to watch, reopening it when
there are people again, and warning first.

close_unstaffed_ventures() shuts what nobody is left to supervise, reopen_restaffed_ventures() brings back what can be
supervised again, staffing_closure_warnings() tells a player what is about to shut before it does."""
from sim.agents.api import business_review
from sim.reporting.api import RecordEvent

from .constants import (FOUNDER_IS_WORTH, STAFFING_CLOSURE_SLACK, STAFFING_NO_SLACK_BAND, STAFFING_WARNING_BAND)
from .staffing_events import unstaffed_closure_line
from .staffing_warning_rows import staffing_warning_rows


class Staffing:
	def close_unstaffed_ventures(self, year):
		"""Shut just enough of what nobody is left to watch, lowest net value first.

		Not a policy and not an automation you can switch off: it is the same rule `open` already applies, applied on
		the years after the first. A shop whose keeper you dismissed is a shop that stops trading, and the alternative -
		which is what the game did - is a fortune of concerns running themselves for ever on an empty payroll."""
		needs = self.needs
		planned = self.concerns_to_close_for_staffing()
		shortfalls = self._staffing_shortfalls(self.staffing_held_totals()) if planned else {}
		earnings_stopped = round(needs.concern_rows_stopped(planned), 1)
		closed = [closure.entry_key for closure in self.review_ventures((business_review.STAFF_SHORT,), year)]
		if closed:
			self.record_staffing_closures(len(closed), shortfalls)
			# plain line: unstaffed_closure_line builds the LogLine and its kind
			needs.send(RecordEvent.from_line(unstaffed_closure_line(
				closed, shortfalls, self.staffing_shortfall_words(shortfalls), self.staffing_shut_count(),
				self.STAFFING_REMEDIES, earnings_stopped), seat=None, year=year))
		return closed

	def review_ventures(self, rules=business_review.ALL_RULES, year=None):
		"""The seat's business under the yearly review (sim/agents/business_review.py); what closed and why. Plants it
		shuts are dated `year` (the scenario's when not given)."""
		world = self.needs.actor_world()
		world.review_year = year
		return self.needs.legacy_projects().business.review(self.needs.legacy_household_actor(), world, rules)

	def note_venture_year(self):
		"""Tally each running plant's margin, and the years running it has lost money (the loss rule's input)."""
		self.needs.actor_world().founder_review().tally(self.needs.legacy_projects().business)

	def staffing_closed_hand_shortfall(self):
		"""(scholars, craftsmen) the household lacks to reopen every concern shut for want of staff.

		The same need `staffing_open_refusal` reads (a concern's hands against `venture_staff_free`), summed over the
		staffing closures; hires aimed at it are what `reopen_restaffed_ventures` then uses."""
		needs = self.needs
		projects = needs.legacy_projects()
		nodes = needs.tree_nodes()
		needed_scholars, needed_craftsmen = 0.0, 0.0
		for node_id in sorted(projects.closures):
			if (self.staff_closure_age(node_id) is None or node_id not in projects.done
					or node_id not in nodes):
				continue
			held = self._staffing_draw_of(node_id, needs.reopen_units[node_id])
			needed_scholars += held.get("scholars", 0.0)
			needed_craftsmen += held.get("craftsmen", 0.0)
		free_scholars, free_craftsmen = needs.venture_staff_free()
		return max(0.0, needed_scholars - free_scholars), max(0.0, needed_craftsmen - free_craftsmen)

	def reopen_restaffed_ventures(self, year):
		"""Bring back what the staffing rule shut, the moment you have the people to watch it again - not a policy, the
		other half of one.

		close_unstaffed_ventures is deliberately not a policy a player can switch off: it is the world taking back a
		concern nobody is left to watch. The world must also give it back, the moment the shortfall is fixed, rather
		than leaving reopening to `auto_open`, a SEPARATE policy that defaults off - which would leave a player
		retyping `open` on the same handful of ids every few years, for no decision at all.

		So this runs unconditionally, like the rule it undoes, and it is careful to undo only THAT rule: only staffing
		closures are candidates, so a concern a player shut on purpose with `mothball` never reappears on its own."""
		needs = self.needs
		reopened = needs.legacy_projects().business.review_reopening(needs.legacy_household_actor(), needs.actor_world())
		if reopened:
			self.record_staffing_reopenings(len(reopened))
			still_shut = self.staffing_shut_count()
			needs.send(RecordEvent.in_year(year, "concerns_reopened", "you have the people again: %s reopen%s on "
			           "their own, now that somebody is free to "
			           "watch %s; %d still shut for want of staff"
			           % (", ".join(sorted(reopened)[:4])
			              + (" and others" if len(reopened) > 4 else ""),
			              "" if len(reopened) == 1 else "s",
			              "it" if len(reopened) == 1 else "them",
			              still_shut), reopened=sorted(reopened), still_shut=still_shut))
		return reopened

	def staffing_closure_warnings(self, limit=3):
		"""Which running concern the staffing rule would shut NEXT if attrition keeps biting, and how many people of
		slack still stand between here and that. Silent while the household is comfortably staffed (the common case):
		only reports when the SAME margin close_unstaffed_ventures itself would act on has shrunk to
		STAFFING_WARNING_BAND or less, in whichever of scholars or craftsmen actually binds for that concern."""
		needs = self.needs
		if not needs.operating():
			return []
		sch_used, art_used = needs.venture_staff_used()
		staff = needs.staff()
		alive = needs.founder()["alive"]
		own = FOUNDER_IS_WORTH if alive else 0.0
		nodes = needs.tree_nodes()
		concerns = [{"id": node_id, "name": nodes[node_id]["name"], "revenue": nodes[node_id]["rev"],
		             "upkeep": nodes[node_id]["up"], "hands": needs.venture_hands[node_id]}
		            for node_id in sorted(needs.operating())]
		return staffing_warning_rows(
			concerns, needs.effective_scholars(), staff["artisans"] + own, staff["scholars"], staff["artisans"],
			sch_used, art_used, bool(needs.game_config().get("immortal")) or not alive,
			STAFFING_CLOSURE_SLACK, STAFFING_WARNING_BAND, STAFFING_NO_SLACK_BAND, limit,
			lambda kind: next(why for node, why in needs.staff_sources()[kind] if node == "HIRE"),
			lambda net: "%s/year" % needs.money_text(net, grouped=True, short=True))
