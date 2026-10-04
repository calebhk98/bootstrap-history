"""`Trader`: a merchant who owns capital and carries goods where the price gap pays.

It values only the margin between a good's price where it is cheap and where it is dear, less
carriage, the interest the cargo's capital would earn and a share lost on the way. The goods move
through the world's market; the trader books what it paid, what it got and the carriage.
"""
from typing import Any, Dict, List, Optional

from .base import RecordedActor
from .borrowing import TRACK_RECORD_YEARS
from .policy import Decision, Option
from .tuning import EXIT_LOSS_YEARS
from .tuning_trader import TRADER_DEPTH_SHARE, TRADER_RISK_SHARE


def route_key(material: str, source: str, destination: str) -> str:
	return "%s@%s>%s" % (material, source, destination)


def route_terms(world: Any, source: str, destination: str, material: str) -> Optional[Dict[str, float]]:
	"""Per tonne: what a cargo costs to buy and carry, and what carrying it gains before the cost of
	its capital. None when either end has no price."""
	bought = world.price_at(material, source)
	sold = world.price_at(material, destination)
	if not bought or not sold or bought <= 0.0 or sold <= 0.0:
		return None
	freight = world.freight_between(source, destination, material, 1.0)
	outlay = bought + freight
	return {"bought": bought, "sold": sold, "freight": freight, "outlay": outlay,
			"gain": sold - outlay - bought * TRADER_RISK_SHARE}


def depth_room(world: Any, source: str, destination: str, material: str) -> float:
	"""Tonnes a year that traders may still bring to the destination, by the share of buyers' depth."""
	depth = world.market_depth(material, destination)
	return max(0.0, depth * TRADER_DEPTH_SHARE - world.shipped_this_year(material, source, destination))


class Trader(RecordedActor):
	kind = "trader"
	# it borrows for cargo, which it sizes itself, not for copies
	borrows_for_copies = False

	def credit_earning(self, world: Any) -> float:
		return max(0.0, self.record.last_margin)

	def credit_standing(self, world: Any) -> float:
		"""Trusted as its record lengthens, and not at all while it runs at a loss."""
		if self.record.loss_years > 0 or self.record.founded_year is None:
			return 0.0
		return min(1.0, max(0.0, world.year - self.record.founded_year) / TRACK_RECORD_YEARS)

	def cargo_budget(self, world: Any) -> float:
		return max(0.0, self.money) + self.spare_credit(world)

	def places(self, world: Any) -> List[str]:
		home = self.record.location
		if home is None:
			return []
		return sorted({home} | set(world.trade_places(home)))

	def route_options(self, world: Any) -> List[Option]:
		"""One option per route that gains: a cargo sized by the buyers' depth left and by the budget."""
		budget = self.cargo_budget(world)
		rate = max(world.market_rate(), 0.0)
		options = []
		places = self.places(world)
		for material in sorted(world.trade_materials()):
			for source in places:
				for destination in places:
					terms = route_terms(world, source, destination, material) if source != destination else None
					if terms is None or terms["gain"] <= 0.0:
						continue
					tonnes = min(depth_room(world, source, destination, material), budget / terms["outlay"])
					if tonnes <= 0.0:
						continue
					interest = terms["bought"] * rate
					options.append(Option(
						subject=route_key(material, source, destination),
						worth=tonnes * (terms["sold"] - interest - terms["bought"] * TRADER_RISK_SHARE),
						cost=tonnes * terms["outlay"],
						detail={"material": material, "source": source, "destination": destination, "tonnes": tonnes}))
		return options

	def ship_cargo(self, option: Option, world: Any) -> float:
		"""Buy at the source, carry and sell at the destination; the margin made."""
		detail = option.detail
		tonnes = detail["tonnes"]
		paid, received = world.ship(self.actor_id, detail["material"], tonnes, detail["source"], detail["destination"])
		freight = world.freight_between(detail["source"], detail["destination"], detail["material"], tonnes)
		self.debit(paid, "edge:market purchase")
		self.debit(freight, "edge:freight")
		self.credit(received, "edge:market sale")
		margin = received - paid - freight
		route = self.record.routes.setdefault(
			option.subject, {"material": detail["material"], "tonnes": 0.0, "margin": 0.0, "years": 0})
		route.update(source=detail["source"], destination=detail["destination"],
					 tonnes=tonnes, margin=margin, years=route["years"] + 1)
		return margin

	def act(self, world: Any) -> None:
		if self.record.exited_year is not None:
			return
		interest = self.pay_interest(world)
		options = self.route_options(world)
		chosen = self.decision_policy.choose(self, Decision("trade", options, self.cargo_budget(world))) if options else []
		shipped = {option.subject for option in chosen}
		for key, route in self.record.routes.items():
			if key not in shipped:
				route["tonnes"] = 0.0
		margin = sum(self.ship_cargo(option, world) for option in chosen) - interest
		self.record.last_margin = margin
		self.record.loss_years = self.record.loss_years + 1 if margin < 0 else 0
		if self.record.loss_years >= EXIT_LOSS_YEARS:
			self.record.routes.clear()
			self.record.exited_year = world.year


from .registry import register_actor_kind  # noqa: E402

register_actor_kind("trader", Trader)
