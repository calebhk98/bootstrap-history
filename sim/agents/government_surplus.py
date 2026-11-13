"""What a state does with money it holds beyond the need.

The reserve it keeps against risk (a few years of the standing need) is supply on the loanable-funds market,
so the state is a saver and is paid its share of the interest borrowers pay (sim/finance/capital_market.py). What a surplus
leaves beyond that reserve first relieves the hunger its country's bodies of people report (paid to them, by
`ledger.transfer`), then raises the works it wants and lacks: masons and others hired at the going wage, which is demand on the
labour market like every other line the state keeps up. Nothing is paid to nobody, and what no work wants stays in the reserve.
"""
from typing import Any, List

from . import budget, government_levers, ledger, state_masonry, state_works
from .edges import EDGE_BUILDERS
from .tuning_spending import MAX_STATE_SHARE_OF_TRADE, RESERVE_CEILING_YEARS_OF_NEED


class Surplus:
	"""A state's use of money beyond its need, on the government that owns the purse."""

	def __init__(self, government: Any) -> None:
		self.government = government

	def relieve_strata(self, excess: float, world: Any) -> float:
		"""Pay the bodies of people in its country the cost of the floors of the needs they report going without,
		as far as `excess` reaches (shared by need when it does not). Returns what was paid."""
		needs = []
		floor_costs = world.people.need_floor_costs_per_person_year()
		for stratum in world.people.country_strata():
			shortfall = stratum.record.shortfall
			need = stratum.record.members * sum(cost * shortfall.get(need_id, 0.0) for need_id, cost in floor_costs.items())
			if need > 0.0:
				needs.append((stratum, need))
		total = sum(need for _stratum, need in needs)
		if total <= 0.0 or excess <= 0.0:
			return 0.0
		covered = min(1.0, excess / total)
		for stratum, need in needs:
			ledger.transfer(self.government, stratum, need * covered, "relief")
			stratum.record.allowance += need * covered
		return total * covered

	def build_works(self, lines: List[budget.Line], world: Any) -> None:
		"""Reserve beyond what it holds against risk relieves its people's reported need, restocks the granary
		when grain is cheap, then raises the works it wants and lacks (`state_works.py`), as many as what is left
		pays at the going wage and the trades allow. What no work wants stays in the reserve."""
		excess = self.government.money - government_levers.reserve_years(self.government.record, RESERVE_CEILING_YEARS_OF_NEED) * sum(line.money for line in lines)
		excess -= self.relieve_strata(excess, world)
		excess -= self.government.granary.restock_granary(excess, world)
		crew = state_masonry.person_years_by_trade(world)
		wage = {trade: world.labour.pay_per_person_year(trade) for trade in crew}
		people_cap = {trade: MAX_STATE_SHARE_OF_TRADE * world.labour.national_people(trade) for trade in crew}
		for work, gap in state_works.gaps(world):
			if excess <= 0.0 or any(pay <= 0.0 for pay in wage.values()):
				continue
			raised = state_masonry.square_metres_raisable(gap, excess, crew, wage, people_cap)
			if raised <= 0.0:
				continue
			built = budget.Line("building " + work.name, "requisition", {trade: raised * years for trade, years in crew.items()},
								sum(raised * years * wage[trade] for trade, years in crew.items()))
			ledger.transfer(self.government, world.setting.edge(EDGE_BUILDERS), built.money, built.name)
			state_works.held(world)[work.name] += raised
			self.government.employ_standing([built], 1.0, world)
			excess -= built.money
