"""What a state does with money it holds beyond the need.

The reserve it keeps against risk (a few years of the standing need) is supply on the loanable-funds market,
so the state is a saver and is paid its share of the interest borrowers pay (`economy_interest_pool.py`). What a surplus
leaves beyond that reserve first relieves the hunger its country's bodies of people report (paid to them, by
`ledger.transfer`), then raises the works it wants and lacks: masons and others hired at the going wage, which is demand on the
labour market like every other line the state keeps up. Nothing is paid to nobody, and what no work wants stays in the reserve.
"""
from typing import Any, List

from . import budget, ledger, state_works
from .edges import EDGE_BUILDERS
from .tuning_spending import MASONRY_PERSON_YEARS_PER_M2, MAX_STATE_SHARE_OF_TRADE, RESERVE_CEILING_YEARS_OF_NEED


class SurplusMixin:
	"""Mixed into `Government`."""

	def relieve_strata(self, excess: float, world: Any) -> float:
		"""Pay the bodies of people in its country the cost of the floors of the needs they report going without,
		as far as `excess` reaches (shared by need when it does not). Returns what was paid."""
		needs = []
		floor_costs = world.need_floor_costs_per_person_year()
		for stratum in world.country_strata():
			shortfall = stratum.record.shortfall
			need = stratum.record.members * sum(cost * shortfall.get(need_id, 0.0) for need_id, cost in floor_costs.items())
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
		"""Reserve beyond what it holds against risk relieves its people's reported need, restocks the granary
		when grain is cheap, then raises the works it wants and lacks (`state_works.py`), as many as what is left
		pays at the going wage and the trades allow. What no work wants stays in the reserve."""
		excess = self.money - RESERVE_CEILING_YEARS_OF_NEED * sum(line.money for line in lines)  # type: ignore[attr-defined]
		excess -= self.relieve_strata(excess, world)
		excess -= self.restock_granary(excess, world)  # type: ignore[attr-defined]
		for work, gap in state_works.gaps(world):
			wage = world.pay_per_person_year(work.trade)
			if excess <= 0.0 or wage <= 0.0:
				continue
			share_cap = MAX_STATE_SHARE_OF_TRADE * world.national_people(work.trade)
			people = min(gap * MASONRY_PERSON_YEARS_PER_M2, excess / wage, share_cap)
			if people <= 0.0:
				continue
			built = budget.Line("building " + work.name, "requisition", {work.trade: people}, people * wage)
			ledger.transfer(self, world.edge(EDGE_BUILDERS), built.money, built.name)
			state_works.held(world)[work.name] += people / MASONRY_PERSON_YEARS_PER_M2
			self.employ_standing([built], 1.0, world)  # type: ignore[attr-defined]
			excess -= built.money
