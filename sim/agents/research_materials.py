"""The materials a year of research or copying consumes, taken from the actor's own stores or bought as goods.

An actor that keeps what it buys (a firm) covers the year's materials in two steps: it draws what its stores hold, then
bids at the market for the rest, so the goods are delivered into its stores by the market's close and the money for them
goes out through that purchase. The money covered here is not paid a second time through the project's other costs.
TEMPORARY HEURISTIC (CLAUDE.md 4.4): the bid is taken as filled, as the market does not report what a bid bought;
retire: Complaint 492 (bids read back from the book, as for a state's plant inputs).
"""
from typing import Callable, Dict, Optional


def cover_year(stores: Dict[str, float], needs_tonnes: Dict[str, float],
			   cost_of: Callable[[str, float], Optional[float]], buy: Callable[[str, float, float], None]) -> float:
	"""Draw each needed material from `stores`, bid for the shortfall with `buy(material, tonnes, budget)`, and return the
	money value (at `cost_of`, None when nobody sells) of the tonnes so covered. A shortfall nobody sells is left
	uncovered, so its money stays owed through the project's ordinary payment."""
	covered = 0.0
	for material in sorted(needs_tonnes):
		tonnes = needs_tonnes[material]
		if tonnes <= 0.0:
			continue
		drawn = min(tonnes, stores.get(material, 0.0))
		if drawn > 0.0:
			stores[material] = stores.get(material, 0.0) - drawn
			covered += cost_of(material, drawn) or 0.0
		shortfall = tonnes - drawn
		if shortfall > 1e-12:
			budget = cost_of(material, shortfall)
			if budget is not None and budget > 0.0:
				buy(material, shortfall, budget)
				covered += budget
	return covered
