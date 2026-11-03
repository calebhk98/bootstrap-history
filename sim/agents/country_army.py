"""What a country's state asks about its army: the threat its hazards describe, the force it wants and keeps."""
from typing import Any, List, Optional

from . import budget, country_hazards
from .country_part import SharedPart
from .tuning_country import ARMY_SHARE_OF_POPULATION

# the keys of a civilisation's data a country's state reads
HAZARDS_KEY = "hazards"
STANDING_ARMY_KEY = "standing_army"


def output_factor(world: Any) -> float:
	"""Share of its output the country keeps this year after the war and aftermath its own hazards describe."""
	return country_hazards.output_factor(world.profile.extra.get(HAZARDS_KEY, []), world.shared.setting.year)


class CountryArmy(SharedPart):
	"""The country's force, from its profile and its civilisation's declared hazards."""

	part = "army"

	def equipment_kg_per_soldier(self) -> float:
		"""Iron and ammunition one equipped soldier uses a year at the share of the military work the country's own
		state holds (its knowledge and what its civilisation starts with)."""
		work = self.shared.military_work_ids()
		known = set(getattr(self.world.setting.government(), "knowledge", ())) | set(self.world.knowledge.baseline_knowledge())
		return self.shared.equipment_kg_at_adoption(sum(1 for node_id in work if node_id in known) / len(work) if work else 0.0)

	def threat_pressure(self) -> float:
		"""Probability a year of the country's own declared hazards sack a site."""
		return budget.sack_pressure(self.world.profile.extra.get(HAZARDS_KEY, []), self.world.shared.setting.year)

	def army_wanted(self) -> float:
		"""Soldiers the state wants: the force its civilisation declares, else a share of its people, raised by
		the threat its hazards describe."""
		declared = self.world.profile.extra.get(STANDING_ARMY_KEY)
		opening = float(declared) if declared is not None else self.world.people.population_total() * ARMY_SHARE_OF_POPULATION
		return budget.army_goal(opening, self.threat_pressure())

	def soldiers_under_arms(self) -> float:
		"""Soldiers the state keeps now: what it paid for last year, else the force it wants."""
		kept = self.world.setting.government().record.army
		return kept if kept > 0.0 else self.army_wanted()

	def fleet_goods(self, holder_id: Optional[str] = None) -> List[Any]:
		return self.shared.fleet_goods(holder_id or self.world.setting.government().actor_id)
