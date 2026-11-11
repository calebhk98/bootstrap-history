"""A state's labour dues in use: conscripts fill its army unpaid, and the rest of the labour takes the place of the
wages its roads, buildings and walls would cost, then raises the works it lacks. The hours it takes are the working
time its people lose (the engine hands them to the economy, which withdraws them from the hours households offer)."""
from typing import Any, List

from . import revenue_labour, state_masonry, state_works
from .budget_line import Line


class Corvee:
	"""A state's labour dues, on the government that owns the record."""

	def __init__(self, government: Any) -> None:
		self.government = government

	def conscript_years(self, world: Any) -> float:
		"""Person-years of army service owed this year."""
		return revenue_labour.person_years(self.government.record.corvee_due.get(revenue_labour.ARMY_DUE, 0.0), world)

	def corvee_hours_taken(self) -> float:
		"""Hours the state called up from its people this year, for its army and its works."""
		return sum(self.government.record.corvee_hours.values())

	def serve_conscripts(self, served: float, world: Any) -> None:
		"""Book the hours the conscripts who could be spared take from their households."""
		self.government.record.corvee_hours[revenue_labour.ARMY_DUE] = served * world.labour.hours_per_person_year

	def staff_works_by_corvee(self, lines: List[Line], world: Any) -> List[Line]:
		"""The lines with the labour owed to the works taking the place of their wages; what is left over is kept to
		raise works. All the hours owed are taken from the households whether or not the works use them."""
		hours = self.government.record.corvee_due.get(revenue_labour.WORKS_DUE, 0.0)
		self.government.record.corvee_hours[revenue_labour.WORKS_DUE] = hours
		lines, spare = revenue_labour.offset_upkeep(lines, revenue_labour.person_years(hours, world))
		self.government.record.corvee_spare_years = spare
		return lines

	def build_works_by_corvee(self, world: Any) -> float:
		"""Raise the works the state lacks with the labour left over, unpaid; the masonry raised."""
		years = self.government.record.corvee_spare_years
		raised = 0.0
		years_per_m2 = state_masonry.person_years_total(world)
		for work, gap in state_works.gaps(world):
			if years <= 0.0:
				break
			used = min(years, gap * years_per_m2)
			state_works.held(world)[work.name] += used / years_per_m2
			years -= used
			raised += used / years_per_m2
		self.government.record.corvee_spare_years = years
		return raised
