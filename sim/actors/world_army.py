"""What a state asks about its army: the threat, the force it wants and keeps, what a soldier wears out, the fleet."""
from typing import Any, List, Optional, Tuple

from sim.agents.api import army_goal, sack_pressure
from sim.labour import api as labour_api


class Army:
	"""The home state's force. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def needs(self) -> Any:
		return self.world.needs

	def threat_pressure(self) -> float:
		"""Probability a year of the civilisation's own hazards sack a site: the declared
		sack chances of those running now, before any relief the founder has bought."""
		return sack_pressure(self.needs.civilisation().get("hazards", []), self.world.setting.year)

	def army_wanted(self) -> float:
		"""Soldiers the state wants: the opening force the civilisation starts with, raised by the
		threat its hazards describe. The garrison follows the frontier, not the head count."""
		opening = float(self.needs.civilisation().get("standing_army", 0.0))
		return army_goal(opening, self.threat_pressure())

	def soldiers_under_arms(self) -> float:
		"""Soldiers the state keeps now: what it paid for last year, else the force it wants."""
		kept = self.world.setting.government().record.army
		return kept if kept > 0.0 else self.army_wanted()

	def equipment_kg_per_soldier(self) -> float:
		"""Iron and ammunition one equipped soldier uses a year, at the equipment the state's
		armies have taken up from the founder's work."""
		return self.needs.military_equipment_burden(self.needs.diffusion_index["military"])

	def military_work_ids(self) -> Tuple[str, ...]:
		return tuple(self.needs.diffusible_ids["military"])

	def equipment_kg_at_adoption(self, adoption: float) -> float:
		return self.needs.military_equipment_burden(adoption)

	def equipment_material(self) -> str:
		return str(labour_api.role_field(self.needs.trade_registry(), "soldier", "equipment_material"))

	def fleet_goods(self, holder_id: Optional[str] = None) -> List[Any]:
		"""Available naval vessels, their crews, service lives and a state's holdings (the founder's state's by default)."""
		return self.needs.fleet_goods(holder_id or self.world.setting.government().actor_id)
