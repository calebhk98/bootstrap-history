"""A sack: what it takes from a site (capital, staff, projects), and then, maybe, the knowledge written down there.

The dice draws below have an exact place in the sequence `shocks` makes its draws in: the yearly chance of an attack coming
to nothing, the chance of a sack, and the chance and the sample of the corpus lost.

Needs: corpus_hedge, legacy_dice, acting_balance, staff, staff_snapshot, active_projects, money_text, corpus_nodes, mechanic, goal,
tree_nodes, tree_closure, losable_node_ids."""
from typing import Any, Dict, List

from sim.coin.api import PlunderHousehold
from sim.knowledge.api import ForgetTechnique
from sim.projects.api import ResetProjectProgress, ShutForgotten
from sim.reporting.api import RecordEvent
from sim.workforce.api import ReportStaffReduction, ScaleDeputies, SurviveStaff

from . import constants, rules
from .toll import sack_toll


class Sack:

	def sack_chance(self, hazard: Dict[str, Any], year: int) -> None:
		"""The sack_chance branch of the year's shocks: an attack may come to nothing, or a site be sacked."""
		dice = self.needs.legacy_dice()
		if "sack_chance" in hazard:
			relief, why, lapsed = self.hazard_relief_detail("sack_chance")
			probability = hazard["sack_chance"] * relief
			if why and dice.random() < hazard["sack_chance"] - probability:
				self.needs.send(RecordEvent.of("hazard_attack_averted", "%s: an attack comes to nothing (%s)"
				                               % (hazard.get("name", "crisis"), "; ".join(why[:3])),
				                               hazard=hazard.get("name", "crisis"), lapsed_hedges=lapsed))
			if dice.random() < probability:
				self.sack_site(hazard, year)

	def _people_on_books(self) -> float:
		staff = self.needs.staff()
		return staff["artisans"] + staff["scholars"] + sum(staff["employees"].values())

	def sack_site(self, hazard: Dict[str, Any], year: int) -> None:
		"""What a sack itself takes: capital, staff, projects reset; then, maybe, the corpus."""
		dice = self.needs.legacy_dice()
		capital_before = max(0.0, self.needs.acting_balance())
		people_before = self._people_on_books()   # all staff, so the message matches what the state renders
		projects_before = len(self.needs.active_projects())
		self.needs.send(PlunderHousehold(constants.SACK_TAKE_STRENGTH, "sack and plunder", False))
		staff_before = self.needs.staff_snapshot()
		self.needs.send(SurviveStaff(constants.SACK_STAFF_RETENTION))
		self.needs.send(ReportStaffReduction("the sack of a site", staff_before))
		self.needs.send(ScaleDeputies(constants.SACK_DIRECTORS_RETENTION))
		self.needs.send(ResetProjectProgress())
		people_after = self._people_on_books()
		capital_taken = capital_before - max(0.0, self.needs.acting_balance())
		hit_capital, hit_people, hit_projects = sack_toll(capital_taken, people_before - people_after, projects_before)
		took = []
		if hit_capital:
			took.append("%s taken" % self.needs.money_text(capital_taken, grouped=True))
		if hit_people:
			took.append("%.1f of your people gone" % (people_before - people_after))
		if hit_projects:
			took.append("%d project%s back to the beginning" % (projects_before, "" if projects_before == 1 else "s"))
		name = hazard.get("name", "crisis")
		self.needs.send(RecordEvent.of("site_sacked", "%s: a site is sacked - %s" % (name, ", ".join(took) or "you had nothing it could take"),
		                               hazard=name, took_nothing=not took, people_gone=round(people_before - people_after, 2)))
		loss_probability, fraction, hedge_before = self.needs.corpus_hedge()
		if dice.random() < loss_probability:
			self.sack_corpus_loss(year, fraction, hedge_before)

	def sack_corpus_loss(self, year: int, fraction: float, hedge_before: Any) -> None:
		"""The corpus lost to a sack: which technologies, and what it does to the goal road. The sample is drawn right
		after the loss roll and nowhere else. Not losable: society's inheritance, and dispersed copies (beyond reach)."""
		losable = self.needs.losable_node_ids()
		if losable:
			drop = self.needs.legacy_dice().sample(losable, rules.losable_after_roll(losable, fraction))
			self.needs.send(ShutForgotten(tuple(drop)))
			self.needs.send(ForgetTechnique(tuple(drop), year=year))   # dated, for rebuilding
			self.log_corpus_loss(drop, hedge_before)

	def best_corpus_node(self) -> Any:
		best_first = self.needs.corpus_nodes()
		return best_first[0] if best_first else None

	def log_corpus_loss(self, drop: List[str], hedge_before: Any) -> None:
		"""Name what a sack's corpus loss took, and what it does to the goal road. Makes no dice draws: `drop` is decided."""
		corpus = [tech_id for tech_id in self.needs.mechanic["corpus"] if tech_id in drop]
		on_road = 0
		goal = self.needs.goal()["node"]
		if goal and goal in self.needs.tree_nodes():
			try:
				if self._goal_closure is None:
					self._goal_closure = self.needs.tree_closure(goal)
				on_road = sum(1 for tech_id in drop if tech_id in self._goal_closure)
			except Exception:
				on_road = 0
		never_dispersed = hedge_before != self.best_corpus_node()
		self.needs.send(RecordEvent.of("knowledge_lost", rules.corpus_loss_message(drop, not never_dispersed, corpus, on_road),
		                               forgotten=sorted(drop), corpus_never_dispersed=never_dispersed, corpus_went=bool(corpus), on_road=on_road))
