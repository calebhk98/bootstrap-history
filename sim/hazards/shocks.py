"""The year's dated hazards for every seat: each seat meets them with its own works, the world is hit once.

Per hazard: every seat resolves its causes and condition; seats lose staff, cash and sites by their own exposure (own dice,
own log); population, output, the coin and the society's values change once, at the mildest figure any seat's works leave
(merge.py). One seat runs the same draws in the same order as a game with no other seat. The order of the dice is the
order of the calls below; save/load and the equivalence check depend on it.

Needs: civilisation, year, seat_list, game_random, act_as, events_enabled,
techniques_held, wage_index, money_text, money_real, event_log."""
from typing import Any, Dict, List, Optional

from sim.demography.api import CutPopulation, RefreshDemographicIndexes
from sim.polity.api import ShiftValueWeight
from sim.refusal import LogLine, Refusal
from sim.reporting.api import ErodeMoney, RecordEvent
from sim.reporting.api import NoteWageShock
from sim.workforce.api import LoseStaff

from .commands import SayOnce
from . import constants, rules, staff_loss_words
from .condition import hazard_given_condition
from .merge import mildest_hazard
from .state import OUTPUT
from .toll import staff_loss_toll


class Shocks:

	def step_dated_shocks(self, seats: Optional[List[str]]) -> None:
		"""The phase `dated_shocks`: the world is hit once, each seat in `seats` meets the year's hazards with its own works."""
		self.disaster_this_year = None
		if not self.needs.events_enabled():
			return
		year = self.needs.year()
		logged_before = len(self.needs.event_log())
		self.shocks(year, seats)
		hazards = self.needs.civilisation().get("hazards", [])
		names = [hazard.get("name", "a hazard") for hazard in hazards
		         if hazard.get("years", [0, 0])[0] <= year <= hazard.get("years", [0, 0])[-1]]
		if names:
			self.disaster_this_year = {"name": ", ".join(names),
			                           "messages": [message for _, message in self.needs.event_log()[logged_before:]]}

	def shocks(self, year: int, seats: Optional[List[str]] = None) -> None:
		"""Dated catastrophes, read from the civilisation file, for `seats` (the seats still playing). One step per hazard
		kind, in this order, for every hazard whose window is open."""
		seats = list(self.needs.seat_list()["playing"] if seats is None else seats)
		for hazard in self.needs.civilisation().get("hazards", []):
			hazard_start, hazard_end = hazard.get("years", [0, 0])
			if not (hazard_start <= year <= hazard_end):
				continue
			met = {}
			for seat_id in seats:
				with self.needs.act_as(seat_id):
					kept = self.apply_event_causes(hazard, year, hazard_start)
					if kept is not None:
						kept = self.resolve_hazard_condition(kept, year, hazard_start)
				if kept is not None:
					met[seat_id] = kept
			if not met:
				continue
			self.staff_loss_seats(met, year)
			for seat_id in met:
				with self.needs.act_as(seat_id):
					self.sack_chance(met[seat_id], year)
			self.output_factor_seats(met, year)
			self.real_erosion_seats(met, year)
			self.values_seats(met, year, hazard_start, hazard_end)

	def resolve_hazard_condition(self, hazard: Dict[str, Any], year: int, hazard_start: int) -> Dict[str, Any]:
		"""History on rails, but the household may have changed the ground it runs on: technology changes how much a dated
		hazard hurts, never whether it happens on schedule. Only a hazard whose file gives it a `condition` is touched.
		Told, not silent, in all three cases (fires as written, fires altered, is averted), once, the year the window opens."""
		condition = hazard.get("condition")
		if not condition:
			return hazard
		needed = condition.get("requires_all") or []
		held = self.needs.techniques_held()
		met = all(tech_id in held for tech_id in needed)
		if year == hazard_start:
			key = hazard.get("name", "hazard")
			if self.say_once(SayOnce(key)):
				text = condition.get("met_message" if met else "unmet_message")
				if text:
					self.needs.send(RecordEvent.of("hazard_condition_met" if met else "hazard_condition_unmet", text, hazard=key))
		return hazard_given_condition(hazard, met)

	def apply_event_causes(self, hazard: Dict[str, Any], year: int, hazard_start: int) -> Optional[Dict[str, Any]]:
		"""The event as its stated causes leave it this year, or None when they do not hold. Told once, the year the window
		opens, when the causes fail."""
		kept, report = self.effective_hazard(hazard)
		if report["failed"] and year == hazard_start:
			key = "causes:" + hazard.get("name", "hazard")
			if self.say_once(SayOnce(key)):
				self.needs.send(RecordEvent.of("hazard_condition_failed", "%s: %s, so it %s" % (
					hazard.get("name", "hazard"), rules.failed_causes_words(report),
					"does not come" if kept is None else "comes weaker")))
		return kept

	# ---- staff_loss: seats lose people and cash, the population is cut once ----

	def staff_loss_seats(self, met: Dict[str, Dict[str, Any]], year: int) -> None:
		if not any("staff_loss" in hazard for hazard in met.values()):
			return
		if not self.needs.game_random().random() < constants.STAFF_LOSS_HAZARD_ANNUAL_CHANCE:
			return
		reports = {}
		for seat_id, hazard in met.items():
			if "staff_loss" in hazard:
				with self.needs.act_as(seat_id):
					reports[seat_id] = self.staff_loss_of_seat(hazard)
		world_hazard = mildest_hazard(met.values())
		raw = min(report["raw"] for report in reports.values())
		if world_hazard is not None and "staff_loss" in world_hazard:
			raw = self.staff_loss_exposure(world_hazard["staff_loss"])["before_defences"]
		wage_index_before = self.needs.wage_index()
		self.needs.send(CutPopulation(raw))
		for seat_id in reports:
			with self.needs.act_as(seat_id):
				self.needs.send(NoteWageShock(met[seat_id].get("name", "a plague"), self.needs.wage_index() - wage_index_before))
		# refresh population and wage screens now, not at year end
		self.needs.send(RefreshDemographicIndexes(year))
		for seat_id, report in reports.items():
			self.needs.send(RecordEvent.from_line(self.staff_loss_message(met[seat_id], report, raw), seat_id))   # a ready LogLine

	def staff_loss_of_seat(self, hazard: Dict[str, Any]) -> Dict[str, Any]:
		"""What one wave takes from the acting seat's people and cash; returns the figures its message needs."""
		historical = hazard["staff_loss"]
		# national prevalence after the country's own medicine; the household's own mitigations cut its risk only where the
		# nation has not adopted them
		exposure = self.staff_loss_exposure(historical)
		loss = exposure["loss"]
		people_before = self.needs.send(LoseStaff(hazard.get("name", "a plague"), 1 - loss, 1 - loss))["people_before"]
		cash = self.lose_capital(loss * constants.PLAGUE_CASH_LOSS_SHARE, "plague losses")   # the trade that stopped takes cash with it
		return {"historical": historical, "raw": exposure["before_defences"], "med_relief": exposure["national_relief"],
		        "relief": exposure["relief"], "why": exposure["why"], "lapsed_hedges": exposure["lapsed_hedges"], "loss": loss,
		        "cash": cash, "people_before": people_before,
		        "sources": self.national_public_health_sources()}   # read under this seat, so its line names its own works

	def staff_loss_message(self, hazard: Dict[str, Any], report: Dict[str, Any], raw: float) -> LogLine:
		"""The log line for one seat; `raw` is the national toll the world took."""
		loss, why, relief, med_relief = report["loss"], report["why"], report["relief"], report["med_relief"]
		historical = report["historical"]
		hit = []
		people_hit, cash_hit = staff_loss_toll(report["people_before"], report["cash"])
		if people_hit:
			hit.append(staff_loss_words.staff_clause(loss, relief, why))
		if cash_hit:
			hit.append("%s of takings lost while the trade stood idle" % self.needs.money_text(report["cash"], grouped=True))
		took_nothing = not hit
		if not hit:
			hit.append("you had nothing it could take")
		message = "%s: %s" % (hazard.get("name", "hazard"), ", ".join(hit))
		# a separate sentence, so a spared household does not read the national toll as its own
		message += staff_loss_words.national_toll_sentence(
			raw, historical, med_relief, ", ".join(report["sources"]) or "none named" if med_relief > 0.02 else "")
		return LogLine("hazard_hit", message, hazard=hazard.get("name", "hazard"), took_nothing=took_nothing,
		               lapsed_hedges=report["lapsed_hedges"],
		               defence=staff_loss_words.defence_kind(relief, why) if report["people_before"] > 0.05 else "no_staff",
		               national_toll_percent=round(raw * 100), national_sources=list(report["sources"]))

	# ---- output_factor: war and its aftermath, the world's output floor ----

	def output_factor_seats(self, met: Dict[str, Dict[str, Any]], year: int) -> None:
		"""Each seat's works set a floor the output factor falls to; the world takes the highest floor."""
		floors, reasons = {}, {}
		for seat_id, hazard in met.items():
			if "output_factor" in hazard:
				with self.needs.act_as(seat_id):
					relief, why, lapsed = self.hazard_relief_detail("output_factor")
				floors[seat_id] = rules.output_floor(hazard["output_factor"], relief)
				reasons[seat_id] = (why, lapsed)
		if not floors:
			return
		before = self.world.output_factor
		self.world.output_factor = rules.lowered_output_factor(before, floors.values())
		self.bump(OUTPUT)
		# logged only on the first hit or after 20 years: no noise on recovery
		said = self.world.said_output or {}
		name = next(hazard.get("name", "crisis") for hazard in met.values() if "output_factor" in hazard)
		if before > self.world.output_factor and year - said.get(name, -99) >= 20:
			said[name] = year
			self.world.said_output = said
			for seat_id, (why, lapsed) in reasons.items():
				self.needs.send(RecordEvent.from_line(LogLine(
					"hazard_output_fall", "%s: trade and output fall to %d%% of normal%s" % (
						name, self.world.output_factor * 100,
						" (your own strength holds off worse: %s)" % "; ".join(why[:3]) if why else ""),
					hazard=name, lapsed_hedges=lapsed), seat_id))

	# ---- real_erosion: debasement, the coin once, each seat's held cash ----

	def real_erosion_seats(self, met: Dict[str, Dict[str, Any]], year: int) -> None:
		holders = {seat_id: hazard for seat_id, hazard in met.items() if "real_erosion" in hazard}
		if not holders:
			return
		world_hazard = mildest_hazard(met.values())
		if world_hazard is not None and "real_erosion" in world_hazard:
			self.needs.send(ErodeMoney(world_hazard["real_erosion"]))
		lines = {}
		for seat_id, hazard in holders.items():
			with self.needs.act_as(seat_id):
				relief, why, lapsed = self.hazard_relief_detail("real_erosion")
				bite = hazard["real_erosion"] * constants.REAL_EROSION_CASH_LOSS_SHARE * relief
				had = max(0.0, self.needs.acting_balance())
				self.lose_capital(bite, "debasement and real erosion")
				lines[seat_id] = (hazard, why, had - max(0.0, self.needs.acting_balance()), lapsed)
		said = self.world.said_debasement
		if not said or year - said >= 15:
			self.world.said_debasement = year
			for seat_id, (hazard, why, lost, lapsed) in lines.items():
				# the money lost held, not quoted costs (which reflect reality)
				self.needs.send(RecordEvent.from_line(LogLine(
					"hazard_coin_debased", "%s: the coin is worth %d%% less than it "
					"was%s. Quoted costs are what a thing really takes to make, so they do not move; what debases "
					"is the money in your chest, and this year it took %s"
					% (hazard.get("name", "debasement"), (1 - self.needs.money_real()) * 100,
					   "; you feel less of it (%s)" % "; ".join(why) if why else "",
					   self.needs.money_text(lost, grouped=True) if lost > 0.5 else "nothing, because you were holding none"),
					hazard=hazard.get("name", "debasement"), lapsed_hedges=lapsed), seat_id))

	# ---- values: the society's beliefs shift once ----

	def values_seats(self, met: Dict[str, Dict[str, Any]], year: int, hazard_start: int, hazard_end: int) -> None:
		"""Gradual shifts in what the society believes, spread evenly across the hazard's own window."""
		hazard = mildest_hazard(met.values())
		if hazard is None or "values" not in hazard:
			return
		span = max(1, int(hazard_end) - int(hazard_start) + 1)
		changed = {}
		for field, total_delta in hazard["values"].items():
			if field.startswith("_") or not isinstance(total_delta, (int, float)):
				continue
			answer = self.needs.send(ShiftValueWeight(field, total_delta / span))
			if isinstance(answer, Refusal):
				continue
			before, after = answer
			if abs(after - before) > 1e-9:
				changed[field] = after
		# logged at the start, the end and every ten years: visible change without noise
		if changed and (year == hazard_start or year == hazard_end or (year - hazard_start) % 10 == 0):
			line = "%s: the society's values are shifting (%s)" % (
				hazard.get("name", "hazard"), ", ".join("%s now %.2f" % (field, value) for field, value in sorted(changed.items())))
			for seat_id in met:
				self.needs.send(RecordEvent.from_line(LogLine("hazard_values_shift", line), seat_id))
