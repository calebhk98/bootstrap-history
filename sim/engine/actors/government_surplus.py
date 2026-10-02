"""What a state does with money it holds beyond the need.

The reserve it keeps against risk (a few years of the standing need) is supply on the loanable-funds market,
so the state is a saver and is paid its share of the interest borrowers pay (`economy_interest_pool.py`). What a surplus
leaves beyond that reserve buys works: labourers hired at the going wage, which is demand on the labour
market like every other line the state keeps up. Nothing is paid to nobody.
"""
from typing import Any, List

from . import budget
from .tuning_spending import MAX_WORKS_SHARE_OF_WORKING_AGE, RESERVE_CEILING_YEARS_OF_NEED


class SurplusMixin:
	"""Mixed into `Government`."""

	def build_works(self, lines: List[budget.Line], world: Any) -> None:
		"""Reserve beyond what it holds against risk hires labourers for works, as many as the
		surplus pays at the going wage and the labour market allows."""
		excess = self.money - RESERVE_CEILING_YEARS_OF_NEED * sum(line.money for line in lines)  # type: ignore[attr-defined]
		wage = world.pay_per_person_year("labourer")
		if excess <= 0.0 or wage <= 0.0:
			return
		people = min(excess / wage, MAX_WORKS_SHARE_OF_WORKING_AGE * world.national_people("labourer"))
		if people <= 0.0:
			return
		works = budget.Line("works", "requisition", {"labourer": people}, people * wage)
		self.debit(works.money, works.name)  # type: ignore[attr-defined]
		self.employ_standing([works], 1.0, world)  # type: ignore[attr-defined]
