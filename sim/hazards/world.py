"""Base-rate shocks for every country in the game, and famine watch, as yearly world phases (Complaint 493).

The kinds, rates and losses are data (data/world/world_hazards.json). A country's draw is a hash of the game's seed, the
country, the kind and the year, so it does not move when another country joins and uses no shared dice. A hit cuts the
country's people (the home society by its cohort shock, a partner by its strata) and writes a record to the world event log
(events.py); every seat's log carries a line.

Needs: civilisation, partners_in_agent_economy, weather_seed, seat_list, events_enabled, country_strata."""
import random
from typing import Any, Dict, List

from sim.demography.api import KillPeople
from sim.refusal import LogLine
from sim.reporting.api import RecordEvent

from . import rules, world_data
from .commands import RecordWorldEvent


class WorldHazards:

	def countries_in_game(self) -> List[str]:
		"""The home country, then every partner whose people live in the agent economy, sorted."""
		return [self.needs.civilisation()["id"]] + list(self.needs.partners_in_agent_economy())

	def country_draw(self, country: str, kind: str, year: int) -> float:
		"""The country's uniform draw for one kind in one year."""
		return random.Random(rules.draw_seed(self.needs.weather_seed(0), country, kind, year)).random()

	def hit_country(self, country: str, hazard: Dict[str, Any]) -> Dict[str, Any]:
		"""Apply one hazard to one country: people lost, a record in the log, a line in every playing seat's log."""
		entry = self.needs.send(KillPeople(country, hazard["population_loss"], hazard["cause"], kind=hazard["kind"],
		                                   facts={"population_loss": hazard["population_loss"]}))
		died = entry["facts"]["died"]
		for seat_id in self.needs.seat_list()["playing"]:
			self.needs.send(RecordEvent.from_line(LogLine(
				"world_hazard", "%s in %s: about %d people die" % (hazard["cause"], country, round(died)),
				hazard=hazard["kind"], country=country, died=died), seat_id))
		return entry

	def step_world_hazards(self, seats: List[str]) -> None:
		"""The phase `world_hazards`: each country draws each kind once; a hit applies to that country alone."""
		if not self.needs.events_enabled():
			return
		year = self.needs.year()
		for country in self.countries_in_game():
			for hazard in world_data.hazards():
				if self.country_draw(country, hazard["kind"], year) < hazard["annual_chance"]:
					self.hit_country(country, hazard)

	def step_famine_watch(self, seats: List[str]) -> None:
		"""The phase `famine_watch`: write a famine record for each country whose people leave a large share of their food
		need unmet."""
		threshold = world_data.famine_food_shortfall()
		for country in self.countries_in_game():
			people, shortfall = rules.famine_shortfall(
				(stratum["members"], stratum["shortfall"].get("food", 0.0)) for stratum in self.needs.country_strata[country])
			if people <= 0.0:
				continue
			if shortfall >= threshold:
				self.record_world_event(RecordWorldEvent("famine", actors=(country,), cause="food unmet",
				                                         facts={"food_shortfall": shortfall, "people": people}))
