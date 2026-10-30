"""Who a concern ties up: its crew figures, the hands and foremen it holds, and who is free for something new."""
import collections

from sim.agents.api import business_crew_rule
from sim.projects.api import constants as project_constants

from . import constants


class Crew:
	def crew_figures(self, node_id):
		"""The plant's own data for the one crew rule (sim/agents/business_crew_rule.py)."""
		needs = self.needs
		return business_crew_rule.figures_of(
			needs.tree_nodes()[node_id], lambda: needs.unskilled_trade(), needs.hours_per_person_year(), constants.VENTURE_SUPERVISION,
			lambda: constants.VENTURE_HANDS_PER_REVENUE_LABOUR_HOURS * needs.money_per_labour_hour(), constants.VENTURE_FOREMAN_SHARE,
			node_id in needs.capability_sets()[0], needs.venture_garrison(node_id))

	def venture_hands(self, node_id):
		"""(scholars, craftsmen) of your own that running this ties up (the crew rule, business_crew_rule.hands)."""
		return business_crew_rule.hands(self.crew_figures(node_id), lambda: self.needs.concern_runs_without_founder[node_id])

	def venture_hands_founder_staffed(self, node_id):
		"""(scholars, craftsmen) a concern of this kind needs while its founder still runs it."""
		return business_crew_rule.founder_staffed_hands(self.crew_figures(node_id))

	def concern_staff_by_trade(self, node_id):
		"""{trade: people} one plant of this concern needs of the shared pool, for any owner."""
		figures = self.crew_figures(node_id)
		scholars = business_crew_rule.hands(figures, lambda: self.needs.concern_runs_without_founder[node_id])[0]
		return business_crew_rule.staff_by_trade(figures, scholars)

	def venture_foreman(self, node_id):
		"""The skilled trade and FTE that supervise a concern (business_crew_rule.foreman)."""
		return business_crew_rule.foreman(self.crew_figures(node_id))

	def venture_foremen_used(self, excluding=None):
		"""Skilled-foreman FTE held by operating concerns, by trade."""
		needs = self.needs
		nodes = needs.tree_nodes()
		used = collections.defaultdict(float)
		for node_id in sorted(self.operating()):
			if node_id == excluding or node_id not in nodes:
				continue
			trade, fte = self.venture_foreman(node_id)
			if trade:
				used[trade] += fte * needs.institution_units[node_id]
			for garrison_trade, people in needs.venture_garrison(node_id, needs.institution_units[node_id]).items():
				used[garrison_trade] += people
		return dict(used)

	def venture_foreman_free(self, trade, excluding=None):
		"""Employed specialists still free to supervise another concern."""
		return max(0.0, self.needs.staff()["employees"].get(trade, 0.0) - self.venture_foremen_used(excluding).get(trade, 0.0))

	def venture_staff_who_is_watching_what(self):
		"""Which concerns are holding your people, and how many each holds.

		Mothballing every concern the game shows elsewhere can still free no scholars at all, if some of them are held by
		something that screen never lists. This is that something, shown. Largest holder first, because that is the one to
		close."""
		nodes = self.needs.tree_nodes()
		rows = []
		for node_id in sorted(self.operating()):
			if node_id not in nodes:
				continue
			scholars, craftsmen = self.venture_hands(node_id)
			if scholars > 0.005 or craftsmen > 0.005:
				rows.append({"id": node_id, "scholars": round(scholars, 2), "craftsmen": round(craftsmen, 2)})
		rows.sort(key=lambda row: -(row["scholars"] + row["craftsmen"]))
		return rows

	def venture_staff_used(self):
		"""People of your own tied up supervising what you already have open."""
		# SORTED: this sums floats over a set and the total gates `open` with a hard comparison, so the order must be fixed
		nodes = self.needs.tree_nodes()
		scholars_used = craftsmen_used = 0.0
		for node_id in sorted(self.operating()):
			if node_id not in nodes:
				continue
			scholars, craftsmen = self.venture_hands(node_id)
			scholars_used += scholars
			craftsmen_used += craftsmen
		return scholars_used, craftsmen_used

	def venture_staff_free(self):
		"""People you could put behind something new. You cannot run fifty businesses with three people, and this is the
		whole of why choosing WHICH to run is a decision rather than an accounting formality."""
		scholars_used, craftsmen_used = self.venture_staff_used()
		own = project_constants.FOUNDER_IS_WORTH if self.needs.founder()["alive"] else 0.0
		return (max(0.0, self.needs.effective_scholars() - scholars_used),
		        max(0.0, self.needs.staff()["artisans"] + own - craftsmen_used))
