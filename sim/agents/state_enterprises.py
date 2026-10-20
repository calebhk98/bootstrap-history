"""The plants a state owns: its monopolies and the works it runs for its own use (an arsenal, a saltern, a mine).

A state's plants sit in its `business`, the same object a firm's plants sit in, and run through the same books
(`business_books.py`): crew from the labour market, upkeep, wages and takings at the economy's prices. What differs
is what the owner does with them. A monopoly is a plant of an entry that makes the good; its takings are the state's
revenue. A plant holds its inputs physically: it draws them from the state's stores, then buys the rest with the purse,
and makes only the share it found. Goods the state's own standing lines draw (an army's iron) go to its stores
before any is sold.
"""
from typing import Any, Dict, List, Tuple

from . import ledger
from . import business_books
from .edges import EDGE_CUSTOMERS


def entries_for(government: Any, world: Any) -> List[str]:
	"""The entries the state should run a plant of: those it declares, and for each monopoly it holds that none of
	its plants makes, the first known entry that makes the good."""
	record = government.record
	wanted = set(record.state_enterprises)
	made = {material for entry_key in government.business.entry_keys() for material in world.materials_made_by(entry_key)}
	for material in sorted(record.state_monopolies):
		if material in made or any(material in world.materials_made_by(entry_key) for entry_key in wanted):
			continue
		makers = sorted(entry_key for entry_key in world.concerns_making(material) if government.knows(entry_key, world))
		if makers:
			wanted.add(makers[0])
	return sorted(wanted)


def open_enterprises(government: Any, world: Any) -> List[str]:
	"""Open a plant of each entry the state should run and does not yet; the entries opened."""
	opened = []
	for entry_key in entries_for(government, world):
		if government.business.plant_of(entry_key) is None:
			government.business.open_plant(entry_key, world.year)
			opened.append(entry_key)
	return opened


def run(government: Any, world: Any) -> float:
	"""One year of every plant the state runs; the year's margin. Takings and margin are kept on its record."""
	business = government.business
	takings = margin = 0.0
	for entry_key in sorted(business.operating()):
		plant_margin = (business_books.operate(business, government, entry_key, world, 0.0)
						- business_books.carry(business, government, entry_key, world))
		business.note_year(entry_key, plant_margin)
		takings += business.plant_of(entry_key).takings
		margin += plant_margin
	government.record.enterprise_takings, government.record.enterprise_margin = takings, margin
	return margin


def monopoly_revenue(record: Any) -> float:
	"""What the state's plants took last year: its monopoly revenue, read from the plants and not from a rate."""
	return record.enterprise_takings


def input_share(government: Any, entry_key: str, size: float, world: Any) -> float:
	"""The share of a plant's inputs for the year the state can lay hands on: what its stores hold and what its purse buys
	at the market's price. Inputs found are consumed (drawn from the stores, the rest bid for) and the share is what
	the plant can make. TEMPORARY HEURISTIC (CLAUDE.md 4.4): the bid is taken as filled, as the market does not report
	what a state's bid bought; retire: Complaint 492 (the state's bids read back from the book)."""
	needs = {material: tonnes * size for material, tonnes in world.concern_inputs(entry_key).items() if tonnes * size > 0.0}
	if not needs:
		return 1.0
	stores = government.record.stores
	shortfalls = {material: max(0.0, tonnes - stores.get(material, 0.0)) for material, tonnes in needs.items()}
	cost = sum(world.material_cost(material, tonnes) for material, tonnes in shortfalls.items())
	affordable = 1.0 if cost <= 0.0 else min(1.0, max(0.0, government.money) / cost)
	share = min((tonnes - shortfalls[material] * (1.0 - affordable)) / tonnes for material, tonnes in needs.items())
	value = 0.0
	for material, tonnes in sorted(needs.items()):
		used = tonnes * share
		drawn = min(used, stores.get(material, 0.0))
		stores[material] = stores.get(material, 0.0) - drawn
		if used - drawn > 1e-12:
			world.market_purchase(government.actor_id, world.commodity_of(material), used - drawn,
								  world.material_cost(material, used - drawn))
		value += world.material_cost(material, used)
	if not world.sells_on_book(entry_key):
		# takings here are net of the inputs at the market's price, which the state has now paid for itself
		ledger.transfer(world.edge(EDGE_CUSTOMERS), government, value, "takings")
	return share


def keep_for_own_use(government: Any, material: str, tonnes: float, world: Any) -> float:
	"""Of `tonnes` a plant made, the tonnes the state keeps in its stores because its standing lines draw them; the
	rest is for the market."""
	wanted = government.record.material_need.get(world.commodity_of(material), 0.0)
	kept = max(0.0, min(tonnes, wanted - government.record.stores.get(material, 0.0)))
	if kept > 0.0:
		government.record.stores[material] = government.record.stores.get(material, 0.0) + kept
	return kept


def sell(government: Any, world: Any) -> None:
	"""Put the plants' output to its use: kept for the state's lines first, the rest sold into the goods market."""
	for material in sorted({made for entry_key in government.concerns for made in world.materials_made_by(entry_key)}):
		by_concern: List[Tuple[str, float]] = government.output_by_concern(material, world)
		total = sum(tonnes for _entry_key, tonnes in by_concern)
		kept = keep_for_own_use(government, material, total, world)
		share = 0.0 if total <= 0.0 else (total - kept) / total
		world.market_sale(government.actor_id, material, total - kept, [(entry_key, tonnes * share) for entry_key, tonnes in by_concern])


def needs_of(lines: List[Any]) -> Dict[str, float]:
	"""Tonnes of each commodity the lines draw."""
	need: Dict[str, float] = {}
	for line in lines:
		for commodity, tonnes in line.materials.items():
			need[commodity] = need.get(commodity, 0.0) + tonnes
	return need
