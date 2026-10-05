"""`Trader`: a merchant who owns capital and carries goods where the price gap pays.

It values only the margin between a good's price where it is cheap and where it is dear, less
carriage, the interest the cargo's capital would earn and a share lost on the way. The goods move
through the world's market; the trader books what it paid, what it got and the carriage.
"""
from typing import Any, Dict, List, Optional, Tuple

from .base import RecordedActor
from .borrowing import TRACK_RECORD_YEARS
from .policy import Decision, Option
from .tuning import EXIT_LOSS_YEARS
from .trader_routes import gaining_routes, route_key, route_terms  # noqa: F401  (re-exported)
from .tuning_trader import TRADER_DEPTH_SHARE, TRADER_RISK_SHARE


def depth_room(world: Any, source: str, destination: str, material: str, planned: float = 0.0) -> float:
	"""Tonnes a year that traders may still bring to the destination from any source, by the share of
	buyers' depth, less what has already arrived there and `planned` cargo not yet shipped."""
	depth = world.market_depth(material, destination)
	return max(0.0, depth * TRADER_DEPTH_SHARE - world.delivered_this_year(material, destination) - planned)


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
		# cargo already sized for a destination this year, so two sources do not each fill its room
		planned: Dict[Tuple[str, str], float] = {}
		for material in sorted(world.trade_materials()):
			for source, destination, terms in gaining_routes(world, material, places, lambda _source: places):
				arriving = planned.get((material, destination), 0.0)
				tonnes = min(depth_room(world, source, destination, material, arriving), budget / terms["outlay"])
				if tonnes <= 0.0:
					continue
				planned[(material, destination)] = arriving + tonnes
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
		# a year at a loss or with nothing worth carrying both count toward giving up
		self.record.loss_years = self.record.loss_years + 1 if margin < 0 or not chosen else 0
		if self.record.loss_years >= EXIT_LOSS_YEARS:
			self.record.routes.clear()
			self.record.exited_year = world.year
			if self.money > 0.0:
				self.debit(self.money, "edge:pooled capital")  # its owners take back what is left


from .registry import register_actor_kind  # noqa: E402

register_actor_kind("trader", Trader)
