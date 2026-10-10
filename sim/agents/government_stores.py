"""A state's revenue and the goods it holds.

Each form of revenue is assessed on its base (revenue.py). What is paid in coin is credited to the purse;
what is paid in kind (a share of the harvest) enters the stores as tonnes. The lines the state keeps up
draw on the stores before they buy at the market, and what the stores hold beyond a year of what the
lines draw is sold into the goods market at the price it quotes.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): the stores keep one year of what the lines draw and do not spoil;
a granary model with spoilage and a state's own reserve policy would replace both.
"""
import dataclasses
from typing import Any, Dict, List

from . import ledger
from .budget_line import Line
from .edges import EDGE_TAXPAYERS
from .revenue_bases import earned_income


class StoresMixin:
	"""Mixed into `Government`."""

	def receive_revenue(self, world: Any) -> None:
		"""Take this year's revenue: coin into the purse, goods into the stores, and note both by form."""
		record = self.record  # type: ignore[attr-defined]
		assessments = world.revenue_assessments()
		record.revenue_by_form = {assessed.form: assessed.money for assessed in assessments}
		collected = self.collect_from_payers(assessments)
		record.revenue_by_form.update(collected)
		record.revenue_in_kind = {assessed.form: assessed.money for assessed in assessments if assessed.in_kind}
		record.in_kind_received = {}
		for assessed in assessments:
			if assessed.in_kind:
				record.in_kind_received[assessed.material] = record.in_kind_received.get(assessed.material, 0.0) + assessed.tonnes
				record.stores[assessed.material] = record.stores.get(assessed.material, 0.0) + assessed.tonnes
		unmodelled = sum(assessed.money for assessed in assessments if not assessed.in_kind and not assessed.payers)
		ledger.transfer(world.edge(EDGE_TAXPAYERS), self, unmodelled, "taxation")

	def collect_from_payers(self, assessments: List[Any]) -> Dict[str, float]:
		"""Take each payer's share of the forms that fall on actors, from the purse it holds; the income
		assessed is not assessed again. Returns what was taken by form."""
		taken: Dict[str, float] = {}
		touched: Dict[str, Any] = {}
		for assessed in assessments:
			taken[assessed.form] = 0.0
			for payer, amount in assessed.payers:
				paid = min(amount, max(0.0, payer.money))
				if paid > 0.0:
					ledger.transfer(payer, self, paid, "taxation")
					taken[assessed.form] += paid
				if assessed.basis == "stratum_income":  # only earned income is assessed once; rent is a different base
					touched[payer.actor_id] = payer
		for actor_id, payer in touched.items():
			self.record.income_assessed[actor_id] = earned_income(payer)  # type: ignore[attr-defined]
		return {form: money for form, money in taken.items() if any(a.form == form and a.payers for a in assessments)}

	def draw_stores(self, lines: List[Line], world: Any) -> List[Line]:
		"""The lines as they stand once the stores have supplied what they can of each good; what is
		drawn leaves the stores, and the line buys only the rest."""
		stores = self.record.stores  # type: ignore[attr-defined]
		drawn_lines = []
		for line in lines:
			materials, cost = dict(line.materials), line.material_cost
			price_per_tonne = line.material_cost / sum(line.materials.values()) if line.materials else 0.0
			for material in sorted(stores):
				commodity = world.commodity_of(material)
				wanted = materials.get(commodity, 0.0)
				take = min(stores[material], wanted)
				if take > 0.0:
					cost -= price_per_tonne * take
					materials[commodity] = wanted - take
					stores[material] -= take
			drawn_lines.append(dataclasses.replace(line, materials={c: t for c, t in materials.items() if t > 0.0},
												   material_cost=max(0.0, cost)))
		return drawn_lines
