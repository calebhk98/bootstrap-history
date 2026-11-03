"""`Trader`: a merchant who owns capital and carries goods where the price gap pays.

It values only the margin between a good's price where it is cheap and where it is dear, less
carriage, the interest the cargo's capital would earn and a share lost on the way. The goods move
through the world's market; the trader books what it paid, what it got and the carriage.
"""
from typing import Any, Dict, List, Optional, Tuple

from sim.refusal import Refusal

from . import ledger
from .base import RecordedActor
from .edges import EDGE_FREIGHT, EDGE_MARKET, EDGE_POOLED_CAPITAL
from .borrowing import TRACK_RECORD_YEARS
from .policy import Decision, Option
from .tuning import EXIT_LOSS_YEARS
from .trader_routes import gaining_routes, paying_tonnes, price_answers, route_key
from .tuning_trader import TRADER_DEPTH_SHARE, TRADER_RISK_SHARE


def depth_room(world: Any, source: str, destination: str, material: str, planned: float = 0.0) -> float:
	"""Tonnes a year that traders may still bring to the destination from any source, by the share of
	buyers' depth, less what has already arrived there and `planned` cargo not yet shipped."""
	depth = world.trade.market_depth(material, destination)
	return max(0.0, depth * TRADER_DEPTH_SHARE - world.trade.delivered_this_year(material, destination) - planned)


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
		return min(1.0, max(0.0, world.setting.year - self.record.founded_year) / TRACK_RECORD_YEARS)

	def cargo_budget(self, world: Any) -> float:
		return max(0.0, self.money) + self.spare_credit(world)

	def places(self, world: Any) -> List[str]:
		home = self.record.location
		if home is None:
			return []
		return sorted({home} | set(world.trade.trade_places(home)))

	def route_options(self, world: Any) -> List[Option]:
		"""One option per route that gains: a cargo sized by the buyers' depth left and by the budget."""
		budget = self.cargo_budget(world)
		rate = max(world.credit.market_rate(), 0.0)
		options = []
		places = self.places(world)
		# cargo already sized for a destination this year, so two sources do not each fill its room
		planned: Dict[Tuple[str, str], float] = {}
		for material in sorted(world.trade.trade_materials()):
			for source, destination, terms in gaining_routes(world, material, places, lambda _source: places):
				arriving = planned.get((material, destination), 0.0)
				tonnes = budget / terms["outlay"]
				if price_answers(world, material, destination):
					tonnes = paying_tonnes(world, source, destination, material, terms, tonnes, rate)
				else:
					tonnes = min(depth_room(world, source, destination, material, arriving), tonnes)
				if tonnes <= 0.0:
					continue
				planned[(material, destination)] = arriving + tonnes
				interest = terms["bought"] * rate
				landed = world.trade.price_after_cargo(material, destination, tonnes, True)
				average_sold = terms["sold"] if landed is None else (terms["sold"] + landed) / 2.0
				options.append(Option(
					subject=route_key(material, source, destination),
					worth=tonnes * (average_sold - interest - terms["bought"] * TRADER_RISK_SHARE),
					cost=tonnes * terms["outlay"],
					detail={"material": material, "source": source, "destination": destination, "tonnes": tonnes}))
		return options

	def ship_cargo(self, option: Option, world: Any) -> Optional[float]:
		"""Buy at the source, carry and sell at the destination; the margin made. Nothing moves, and the answer is
		None, when an end has no price (the shipment is refused) or the carriage cannot be priced."""
		detail = option.detail
		tonnes = detail["tonnes"]
		freight = world.trade.freight_between(detail["source"], detail["destination"], detail["material"], tonnes)
		if freight is None:
			return None
		shipped = world.trade.ship(self.actor_id, detail["material"], tonnes, detail["source"], detail["destination"])
		if isinstance(shipped, Refusal):
			return None
		paid, received = shipped
		ledger.transfer(self, world.setting.edge(EDGE_MARKET), paid, "edge:market purchase")
		ledger.transfer(self, world.setting.edge(EDGE_FREIGHT), freight, EDGE_FREIGHT)
		ledger.transfer(world.setting.edge(EDGE_MARKET), self, received, "edge:market sale")
		margin = received - paid - freight
		route = self.record.routes.setdefault(
			option.subject, {"material": detail["material"], "tonnes": 0.0, "margin": 0.0, "years": 0})
		route.update(source=detail["source"], destination=detail["destination"],
					 tonnes=tonnes, margin=margin, years=route["years"] + 1)
		return margin

	def default(self, world: Any) -> None:
		"""A trader in default stops carrying cargo; the claim is written off."""
		super().default(world)
		self.record.routes.clear()
		self.record.exited_year = world.setting.year

	def act(self, world: Any) -> None:
		if self.record.exited_year is not None:
			return
		interest = self.pay_interest(world)
		if self.record.exited_year is not None:
			return
		options = self.route_options(world)
		chosen = self.decision_policy.choose(self, Decision("trade", options, self.cargo_budget(world))) if options else []
		shipped = {option.subject for option in chosen}
		for key, route in self.record.routes.items():
			if key not in shipped:
				route["tonnes"] = 0.0
		results = [(option, self.ship_cargo(option, world)) for option in chosen]
		for option, made in results:
			route = self.record.routes.get(option.subject)
			if made is None and route is not None:   # a refused or unpriced shipment leaves no cargo and no margin for the year
				route["tonnes"], route["margin"] = 0.0, 0.0
		margin = sum(made for _option, made in results if made is not None) - interest
		self.record.last_margin = margin
		# a year at a loss or with nothing carried (nothing worth carrying, or every shipment refused) counts toward giving up
		self.record.loss_years = self.record.loss_years + 1 if margin < 0 or all(made is None for _option, made in results) else 0
		if self.record.loss_years >= EXIT_LOSS_YEARS:
			self.record.routes.clear()
			self.record.exited_year = world.setting.year
			if self.money > 0.0:
				ledger.transfer(self, world.setting.edge(EDGE_POOLED_CAPITAL), self.money, EDGE_POOLED_CAPITAL)  # its owners take back what is left
