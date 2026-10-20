"""A state's labour dues in use: conscripts fill its army unpaid, and the rest of the labour takes the place of the
wages its roads, buildings and walls would cost, then raises the works it lacks. The hours it takes are the working
time its people lose (the engine hands them to the economy, which withdraws them from the hours households offer)."""
from typing import Any, List, Tuple

from . import revenue_labour, state_works
from .budget_line import Line
from .tuning_spending import MASONRY_PERSON_YEARS_PER_M2


class CorveeMixin:
	"""Mixed into `Government`."""

	def conscript_years(self, world: Any) -> float:
		"""Person-years of army service owed this year."""
		return revenue_labour.person_years(self.record.corvee_due.get(revenue_labour.ARMY_DUE, 0.0), world)  # type: ignore[attr-defined,no-any-return]

	def corvee_hours_taken(self) -> float:
		"""Hours the state called up from its people this year, for its army and its works."""
		return sum(self.record.corvee_hours.values())  # type: ignore[attr-defined,no-any-return]

	def serve_conscripts(self, served: float, world: Any) -> None:
		"""Book the hours the conscripts who could be spared take from their households."""
		self.record.corvee_hours[revenue_labour.ARMY_DUE] = served * world.hours_per_person_year  # type: ignore[attr-defined]

	def staff_works_by_corvee(self, lines: List[Line], world: Any) -> List[Line]:
		"""The lines with the labour owed to the works taking the place of their wages; what is left over is kept to
		raise works. All the hours owed are taken from the households whether or not the works use them."""
		hours = self.record.corvee_due.get(revenue_labour.WORKS_DUE, 0.0)  # type: ignore[attr-defined]
		self.record.corvee_hours[revenue_labour.WORKS_DUE] = hours  # type: ignore[attr-defined]
		lines, spare = revenue_labour.offset_upkeep(lines, revenue_labour.person_years(hours, world))
		self.record.corvee_spare_years = spare  # type: ignore[attr-defined]
		return lines

	def build_works_by_corvee(self, world: Any) -> float:
		"""Raise the works the state lacks with the labour left over, unpaid; the masonry raised."""
		years = self.record.corvee_spare_years  # type: ignore[attr-defined]
		raised = 0.0
		for work, gap in state_works.gaps(world):
			if years <= 0.0:
				break
			used = min(years, gap * MASONRY_PERSON_YEARS_PER_M2)
			state_works.held(world)[work.name] += used / MASONRY_PERSON_YEARS_PER_M2
			years -= used
			raised += used / MASONRY_PERSON_YEARS_PER_M2
		self.record.corvee_spare_years = years  # type: ignore[attr-defined]
		return raised
