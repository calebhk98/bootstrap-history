"""What an actor asks about a concern it could run: its crew, cost, takings, margin and ramp."""
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from sim.agents.api import business_books, business_plant_books, supply
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import plant_figures


class Concerns:
	"""The founder's concerns as the pioneer's figures. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world
		self._shared_answers: Dict[str, Any] = {}

	@property
	def needs(self) -> Any:
		return self.world.needs

	def concern_staff(self, node_id: str) -> Dict[str, float]:
		"""People of each trade one plant of this concern needs: the one crew rule (business_crew_rule), which reads the plant's data."""
		return self.needs.concern_staff[node_id]

	def concern_wage_bill(self, node_id: str, capacity: float = 1.0) -> float:
		"""Yearly wages of the people running this concern needs, at the going wage, for a firm
		running it at `capacity` times its founding size."""
		labour = self.world.labour
		return self.world.capacity.span_factor(capacity) * sum(
			people * labour.hours_per_person_year * labour.labour_market.quote(trade)
			for trade, people in self.concern_staff(node_id).items())

	def plant_costs(self, node_id: str) -> Optional[Tuple[float, float]]:
		"""(upkeep, wage bill) of a plant of the concern at its founding size at home."""
		return business_plant_books.home_costs(self.world, node_id)

	def copy_cost(self, node_id: str) -> float:
		"""Money the pioneer's version of this work costs, labour included."""
		with self.needs.shared_answers(self._shared_answers):
			return self.needs.project_cost(node_id)

	def copy_risk(self, node_id: str) -> float:
		return self.needs.effective_risk(node_id)

	def concern_gross(self, node_id: str) -> float:
		"""Yearly takings of the founder's concern once it has ramped up."""
		return self.needs.concern_gross(node_id)

	def entry_gross(self, node_id: str, rivals: float, entrants: float) -> float:
		"""Yearly takings one more operator would have at full ramp once `entrants` operators
		(itself included) have joined the `rivals` already selling."""
		needs = self.needs
		takings = needs.concern_takings(node_id, 1.0) * needs.node_output_market_factor(self.world.setting.nodes[node_id])
		return takings / (rivals + entrants)

	def concern_margin(self, node_id: str) -> float:
		"""Yearly profit of the founder's concern once it has ramped up."""
		return self.concern_gross(node_id) - self.upkeep(node_id)

	def proven_concerns(self) -> List[str]:
		"""Concerns any seat has run at a profit long enough to be believed."""
		needs = self.needs
		proven: Set[str] = set()
		for seat_id in needs.seat_list()["playing"] or [needs.acting_seat()]:
			with needs.act_as(seat_id):
				proven.update(self._proven_concerns_of_acting_seat())
		return sorted(proven)

	def _proven_concerns_of_acting_seat(self) -> List[str]:
		needs = self.needs
		year = self.world.setting.year
		granted = needs.techniques_granted()
		proven = []
		for node_id in sorted(needs.operating()):
			if node_id in granted or not needs.is_venture[node_id]:
				continue
			opened = needs.venture_opened_year(node_id, year)
			if year - opened >= self.world.disclosure.proof_years(node_id) and self.concern_margin(node_id) > 0:
				proven.append(node_id)
		return proven

	def ramp(self, opened_year: int, node_id: Optional[str] = None) -> float:
		depth = 0.0 if node_id is None else self.needs.industry_depth[node_id]
		return plant_figures.ramp(self.world.setting.year - opened_year, self.needs.game_setting["revenue_ramp_years"], depth,
								  self.needs.ramp_share_at_full_depth())

	def scale_ceiling(self, node_id: str) -> float:
		"""The most founding sizes one concern of this kind can be run at, from the industry's experience."""
		return float(self.needs.industry_scale_ceiling[node_id])

	def concern_takings(self, node_id: str, opened_year: int, rivals: float = 0.0, capacity: float = 1.0) -> float:
		"""Yearly takings of a concern an actor runs at `capacity` times its founding size, at the
		prices the economy cleared, split with the capacity of its rivals."""
		needs = self.needs
		takings = business_books.takings_of_size(needs.concern_takings(node_id, self.ramp(opened_year, node_id)), capacity,
												 needs.node_output_market_factor(self.world.setting.nodes[node_id]))
		return takings / (capacity + rivals)

	def concern_output_tonnes(self, node_id: str, material: str, opened_year: int, staffed: float) -> float:
		node = self.world.setting.nodes[node_id]
		if not node.get("annual_output_t"):
			return supply.concern_output_tonnes(node, node_id, material, self.ramp(opened_year, node_id), staffed,
												self._derived_tonnes(node_id, material),
												production=self.world.site.production_catalog())
		return supply.concern_output_tonnes(node, node_id, material,
											self.ramp(opened_year, node_id), staffed
											* self.needs.concern_volume_ratio(node_id), production=self.world.site.production_catalog())

	def _derived_tonnes(self, node_id: str, material: str) -> float:
		"""Tonnes a year of a material the concern's staff and plant turn out now, from the production data (its
		baskets), the mass of a unit of the material taken from what the data states of it."""
		baskets = self.needs.concern_baskets_now[node_id]
		units = 0.0 if baskets is None else baskets.outputs.get(material, 0.0)
		if units <= 0.0:
			return 0.0
		kilograms = self.needs.unit_mass_kg(material)
		return units * kilograms / KILOGRAMS_PER_TONNE if math.isfinite(kilograms) else 0.0

	def upkeep(self, node_id: str, capacity: float = 1.0) -> float:
		return self.needs.concern_upkeep(node_id, capacity)
