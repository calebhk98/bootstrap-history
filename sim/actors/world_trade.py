"""What a trader actor asks of the world: the places with a market, prices there, freight and depth.

A place is a civilisation id: the home society and each foreign economy trading with it this year.
Prices are per tonne in home money (the foreign side is its solved price converted through its coin).
What households at a
place buy for themselves in a year is the depth a trader sizes its cargo to.
"""
from typing import Dict, List, Optional, Tuple

from sim.foreign_trade.api import NoteActorHomeTrade, NoteActorTrade, NoteCargoLeg
from sim.world.material_units import tonnes_per_unit


class TradeView:
	"""Mixed into `ActorWorld`."""

	def _home_place(self) -> str:
		return str(self.needs.civilisation().get("id"))  # type: ignore[attr-defined]

	def trade_places(self, location: Optional[str]) -> List[str]:
		"""Every place with a market this year: the home society; `location` is not filtered."""
		return [self._home_place()]

	def country_of_place(self, place: str) -> Optional[str]:
		"""A place is a country; None for the home one, as actors of the home country carry no country."""
		return None if place == self._home_place() else place

	def _prices_per_tonne(self, place: str) -> Dict[str, float]:
		def compute() -> Dict[str, float]:
			needs = self.needs  # type: ignore[attr-defined]
			per_unit = needs.material_prices()
			prices = {}
			for material, price in per_unit.items():
				tonnes = tonnes_per_unit(material)
				if price and price > 0.0 and tonnes and tonnes > 0.0:
					prices[material] = price / tonnes
			return prices
		return self._once("trade_prices:" + place, compute)  # type: ignore[attr-defined,no-any-return]

	def _depth_by_material(self, place: str) -> Dict[str, float]:
		"""Tonnes a year households at a place buy of each good: at home from live prices and size, as the
		engine's own foreign trade does."""
		def compute() -> Dict[str, float]:
			needs = self.needs  # type: ignore[attr-defined]
			per_hour = needs.money_per_labour_hour()
			prices = needs.household_prices()
			return needs.home_household_tonnes({material: price / per_hour for material, price in prices.items()
												if price > 0.0})
		return self._once("trade_depth:home", compute)  # type: ignore[attr-defined,no-any-return]

	def trade_materials(self) -> List[str]:
		"""Goods households buy that are priced at home and at some partner and may cross a border."""
		def compute() -> List[str]:
			places = self.trade_places(None)
			if len(places) < 2:
				return []
			home = self._prices_per_tonne(places[0])
			wanted = set()
			for place in places:
				wanted.update(material for material, tonnes in self._depth_by_material(place).items() if tonnes > 0.0)
			abroad = set()
			for place in places[1:]:
				abroad.update(self._prices_per_tonne(place))
			refused = self.needs.not_traded_materials()  # type: ignore[attr-defined]
			return sorted(material for material in wanted if material in home and material in abroad
						  and material not in refused)
		return self._once("trade_materials", compute)  # type: ignore[attr-defined,no-any-return]

	def has_market(self, material: str, place: str) -> bool:
		if place != self._home_place():
			return True
		return self.needs.agent_price_response(material, 0.0, 0.0) is not None  # type: ignore[attr-defined,no-any-return]

	def price_at(self, material: str, place: str) -> Optional[float]:
		return self._prices_per_tonne(place).get(material)

	def freight_between(self, source: str, destination: str, material: str, tonnes: float) -> float:
		"""The tariff on a cargo between two places; nothing within one place."""
		if source == destination:
			return 0.0
		return self.duty_between(source, destination, material, tonnes)

	def duty_between(self, source: str, destination: str, material: str, tonnes: float) -> float:
		"""The tariff the destination country's state charges on a cargo from the source country (a share of its value
		at the source); infinite when that state embargoes the source. Part of what the route costs a trader."""
		if tonnes <= 0.0 or source == destination:
			return 0.0
		return float(self.needs.border_duty_per_tonne(source, destination, self.price_at(material, source) or 0.0)) * tonnes

	def market_depth(self, material: str, place: str) -> float:
		"""Tonnes a year buyers at a place take."""
		return float(self._depth_by_material(place).get(material, 0.0))

	def price_after_cargo(self, material: str, place: str, tonnes: float, landing: bool) -> Optional[float]:
		"""Price per tonne at a place once `tonnes` more of a good land there (`landing`) or are taken from it, on
		top of this year's cargo; None where the place's market does not answer (the home society's, while it has
		no book for the good: the economy opens)."""
		price = self.price_at(material, place)
		if not price:
			return None
		landed, taken = self.needs.actor_home_trade[material]  # type: ignore[attr-defined]
		factor = self.needs.agent_price_response(  # type: ignore[attr-defined]
			material, landed + (tonnes if landing else 0.0), taken + (0.0 if landing else tonnes))
		return None if factor is None else price * factor

	def _delivered(self) -> Dict[Tuple[str, str], float]:
		return self._memo.setdefault("delivered", {})  # type: ignore[attr-defined,no-any-return]

	def delivered_this_year(self, material: str, destination: str) -> float:
		return self._delivered().get((material, destination), 0.0)

	def ship(self, trader_id: str, material: str, tonnes: float, source: str, destination: str) -> Tuple[float, float]:
		"""Buy at the source and sell at the destination; (money paid, money received), the quotes the trader is
		booked at. The cargo is noted as a leg and settled once the year's market has cleared (sim/foreign_trade/cargo.py): its
		home side is orders in the book; a partner's side is tallied for its market book to close on (sim/foreign_trade/actor_trade.py)."""
		if tonnes <= 0.0:
			return 0.0, 0.0
		if self.duty_between(source, destination, material, tonnes) == float("inf"):
			return 0.0, 0.0   # the destination's state embargoes the source: nothing crosses
		paid = (self.price_at(material, source) or 0.0) * tonnes
		received = (self.price_at(material, destination) or 0.0) * tonnes
		home = self._home_place()
		needs = self.needs  # type: ignore[attr-defined]
		if source == home:
			needs.send(NoteActorHomeTrade(material, tonnes, False))
		if destination == home:
			needs.send(NoteActorHomeTrade(material, tonnes, True))
		if destination != home:
			needs.send(NoteActorTrade(destination, material, tonnes, True, needs.landed_cost(
				paid, self.freight_between(source, destination, material, tonnes))))
		if source != home:
			needs.send(NoteActorTrade(source, material, tonnes, False))
		needs.send(NoteCargoLeg(trader_id, material, tonnes, source, destination, paid, received,
								self.freight_between(source, destination, material, tonnes), home,
								self.duty_between(source, destination, material, tonnes)))
		key = (material, destination)
		self._delivered()[key] = self._delivered().get(key, 0.0) + tonnes
		return paid, received
