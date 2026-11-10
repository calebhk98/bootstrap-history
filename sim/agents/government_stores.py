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

from sim.compiled_tables.sums import python_sum

from . import assessment_kernels as kernels, assessment_table, ledger, revenue_labour, state_enterprises
from .budget_line import Line
from .edges import EDGE_TAXPAYERS
from .revenue_bases import earned_income


class Stores:
	"""A state's revenue and goods held, on the government that owns the record and the purse."""

	def __init__(self, government: Any) -> None:
		self.government = government

	def receive_revenue(self, world: Any) -> None:
		"""Take this year's revenue: coin into the purse, goods into the stores, and note both by form. The year's assessments are
		a table (`assessment_table.py`); the kernels add what the forms take in kind, in labour and in coin, and decide what each
		payer pays (`assessment_kernels.plan_collection`); Python posts the money."""
		record = self.government.record
		table = assessment_table.as_table(world.revenue.revenue_assessments())
		kernels.receipts(table.forms, float(revenue_labour.HOURS_PER_WORKING_DAY))
		record.revenue_by_form = {names.form: table.money_of(row) for row, names in enumerate(table.rows)}
		collected = self.collect_from_payers(table)
		record.revenue_by_form.update(collected)
		if state_enterprises.monopoly_revenue(record) > 0.0:   # already in the purse: the plants' takings last year
			record.revenue_by_form["state enterprises"] = state_enterprises.monopoly_revenue(record)
		record.revenue_in_kind = {names.form: table.money_of(row) for row, names in enumerate(table.rows) if table.in_kind(row)}
		self.take_in_kind(table)
		record.corvee_due = {}
		labour_rows = [row for row in range(len(table)) if table.in_labour(row)]
		destinations, group = assessment_table.group_numbers([table.rows[row].labour_to for row in labour_rows])
		owed = assessment_table.accumulated([0.0] * len(destinations), group, table.forms.labour_hours[labour_rows])
		record.corvee_due = {destination: float(owed[number]) for number, destination in enumerate(destinations)}
		unmodelled = float(python_sum(table.forms.coin_money, len(table))) if len(table) else 0
		ledger.transfer(world.setting.edge(EDGE_TAXPAYERS), self.government, unmodelled, "taxation")

	def take_in_kind(self, table: Any) -> None:
		"""What was taken in kind this year by good, and into the stores on top of what they held (each form added in its turn)."""
		record = self.government.record
		in_kind_rows = [row for row in range(len(table)) if table.in_kind(row)]
		materials, group = assessment_table.group_numbers([table.rows[row].material for row in in_kind_rows])
		tonnes = table.forms.tonnes[in_kind_rows]
		received = assessment_table.accumulated([0.0] * len(materials), group, tonnes)
		held = assessment_table.accumulated([record.stores.get(material, 0.0) for material in materials], group, tonnes)
		record.in_kind_received = {material: float(received[number]) for number, material in enumerate(materials)}
		for number, material in enumerate(materials):
			record.stores[material] = float(held[number])

	def collect_from_payers(self, table: Any) -> Dict[str, float]:
		"""Take each payer's share of the forms that fall on actors, from the purse it holds; the income
		assessed is not assessed again. Returns what was taken by form. The kernel decides the first posting of each payer; a payer's
		later rows read its purse again, as the earlier postings left it."""
		payers, actors = table.payers, table.payer_actors
		first_seen: Dict[int, int] = {}
		for row, actor in enumerate(actors):
			payers.first_visit[row] = 0 if id(actor) in first_seen else 1
			payers.purse_now[row] = 0.0 if id(actor) in first_seen else actor.money
			first_seen.setdefault(id(actor), row)
		kernels.plan_collection(payers)
		taken: Dict[str, float] = {}
		touched: Dict[str, Any] = {}
		row = 0
		for form, names in enumerate(table.rows):
			taken[names.form] = 0.0
			for payer in names.payers:
				paid = float(payers.collected[row]) if payers.decided[row] else min(float(payers.owed[row]), max(0.0, payer.money))
				if paid > 0.0:
					ledger.transfer(payer, self.government, paid, "taxation")
					taken[names.form] += paid
				if names.basis == "stratum_income":  # only earned income is assessed once; rent is a different base
					touched[payer.actor_id] = payer
				row += 1
		for actor_id, payer in touched.items():
			self.government.record.income_assessed[actor_id] = earned_income(payer)
		return {name: money for name, money in taken.items() if any(names.form == name and names.payers for names in table.rows)}

	def draw_stores(self, lines: List[Line], world: Any) -> List[Line]:
		"""The lines as they stand once the stores have supplied what they can of each good; what is
		drawn leaves the stores, and the line buys only the rest."""
		stores = self.government.record.stores
		drawn_lines = []
		for line in lines:
			materials, cost, unbuyable = dict(line.materials), line.material_cost, dict(line.unbuyable)
			price_per_tonne = line.material_cost / sum(line.materials.values()) if line.materials else 0.0
			for material in sorted(stores):
				commodity = world.quotes.commodity_of(material)
				take = min(stores[material], unbuyable.get(commodity, 0.0))   # what nobody sells is met from the stores first
				if take > 0.0:
					unbuyable[commodity] -= take
					stores[material] -= take
				wanted = materials.get(commodity, 0.0)
				take = min(stores[material], wanted)
				if take > 0.0:
					cost -= price_per_tonne * take
					materials[commodity] = wanted - take
					stores[material] -= take
			drawn_lines.append(dataclasses.replace(line, materials={c: t for c, t in materials.items() if t > 0.0},
												   material_cost=max(0.0, cost),
												   unbuyable={c: t for c, t in unbuyable.items() if t > 1e-12}))
		return drawn_lines
