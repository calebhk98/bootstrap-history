"""What a state does with money it holds beyond the need.

The reserve it keeps against risk (a few years of the standing need) is supply on the loanable-funds market,
so the state is a saver and is paid its share of the interest borrowers pay (`economy_interest_pool.py`). What a surplus
leaves beyond that reserve first relieves the hunger its country's bodies of people report (paid to them, by
`ledger.transfer`), then buys works: labourers hired at the going wage, which is demand on the labour
market like every other line the state keeps up. Nothing is paid to nobody.
"""
from typing import Any, List

from . import budget, ledger
from .edges import EDGE_BUILDERS
from .tuning_spending import MAX_WORKS_SHARE_OF_WORKING_AGE, RESERVE_CEILING_YEARS_OF_NEED


class SurplusMixin:
	"""Mixed into `Government`."""

	def relieve_strata(self, excess: float, world: Any) -> float:
		"""Pay the bodies of people in its country the cost of the food and housing they report going without,
		as far as `excess` reaches (shared by need when it does not). Returns what was paid."""
		needs = []
		food_cost, housing_cost = world.subsistence_cost_per_person_year(), world.housing_cost_per_person_year()
		for stratum in world.country_strata():
			shortfall = stratum.record.shortfall
			need = stratum.record.members * (food_cost * shortfall.get("food", 0.0) + housing_cost * shortfall.get("housing", 0.0))
			if need > 0.0:
				needs.append((stratum, need))
		total = sum(need for _stratum, need in needs)
		if total <= 0.0 or excess <= 0.0:
			return 0.0
		covered = min(1.0, excess / total)
		for stratum, need in needs:
			ledger.transfer(self, stratum, need * covered, "relief")
			stratum.record.allowance += need * covered
		return total * covered

	def build_works(self, lines: List[budget.Line], world: Any) -> None:
		"""Reserve beyond what it holds against risk relieves its people's reported need, then hires labourers
		for works, as many as what is left pays at the going wage and the labour market allows."""
		excess = self.money - RESERVE_CEILING_YEARS_OF_NEED * sum(line.money for line in lines)  # type: ignore[attr-defined]
		excess -= self.relieve_strata(excess, world)
		wage = world.pay_per_person_year("labourer")
		if excess <= 0.0 or wage <= 0.0:
			return
		people = min(excess / wage, MAX_WORKS_SHARE_OF_WORKING_AGE * world.national_people("labourer"))
		if people <= 0.0:
			return
		works = budget.Line("works", "requisition", {"labourer": people}, people * wage)
		ledger.transfer(self, world.edge(EDGE_BUILDERS), works.money, works.name)
		self.employ_standing([works], 1.0, world)  # type: ignore[attr-defined]
