"""What a trader actor asks of the world: the places with a market, prices there, freight and depth.

A place is a civilisation id: the home society and each foreign economy trading with it this year.
Prices are per tonne in home money (the foreign side is its solved price converted through its coin).
Freight between home and a partner is the partner route's freight per tonne. What households at a
place buy for themselves in a year is the depth a trader sizes its cargo to.
"""
from typing import Any, Dict, List, Optional, Tuple

from .foreign_capacity import household_tonnes_by_material
from .foreign_economies import not_traded_materials
from .project_materials import tonnes_per_unit


class TradeView:
	"""Mixed into `SimWorld`."""

	def _home_place(self) -> str:
		return str(self._sim.civ.get("id"))  # type: ignore[attr-defined]

	def trade_places(self, location: Optional[str]) -> List[str]:
		"""Every place with a market this year, the home society first; `location` is not filtered."""
		return [self._home_place()] + list(self._sim.foreign_economies())  # type: ignore[attr-defined]

	def country_of_place(self, place: str) -> Optional[str]:
		"""A place is a country; None for the home one, as actors of the home country carry no country."""
		return None if place == self._home_place() else place

	def _prices_per_tonne(self, place: str) -> Dict[str, float]:
		def compute() -> Dict[str, float]:
			sim = self._sim  # type: ignore[attr-defined]
			if place == self._home_place():
				per_unit = sim.economy.material_prices()
			else:
				per_unit = sim._foreign_economy_facts(place)["prices_in_home_money"]
			prices = {}
			for material, price in per_unit.items():
				tonnes = tonnes_per_unit(material)
				if price and price > 0.0 and tonnes and tonnes > 0.0:
					prices[material] = price / tonnes
			return prices
		return self._once("trade_prices:" + place, compute)  # type: ignore[attr-defined,no-any-return]

	def _depth_by_material(self, place: str) -> Dict[str, float]:
		return household_tonnes_by_material(place)

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
			refused = not_traded_materials()
			return sorted(material for material in wanted if material in home and material in abroad
						  and material not in refused)
		return self._once("trade_materials", compute)  # type: ignore[attr-defined,no-any-return]

	def price_at(self, material: str, place: str) -> Optional[float]:
		return self._prices_per_tonne(place).get(material)

	def freight_between(self, source: str, destination: str, material: str, tonnes: float) -> float:
		"""Carriage between home and a partner over the partner's route; nothing within one place."""
		if source == destination:
			return 0.0
		home = self._home_place()
		partner = destination if source == home else source
		if partner == home:
			return 0.0
		facts = self._sim._foreign_economy_facts(partner)  # type: ignore[attr-defined]
		return float(facts["freight_per_tonne"] or 0.0) * tonnes

	def market_depth(self, material: str, place: str) -> float:
		return float(self._depth_by_material(place).get(material, 0.0))

	def _shipped(self) -> Dict[Tuple[str, str, str], float]:
		return self._memo.setdefault("shipped", {})  # type: ignore[attr-defined,no-any-return]

	def shipped_this_year(self, material: str, source: str, destination: str) -> float:
		return self._shipped().get((material, source, destination), 0.0)

	def ship(self, trader_id: str, material: str, tonnes: float, source: str, destination: str) -> Tuple[float, float]:
		"""Buy at the source and sell at the destination; (money paid, money received). The home side
		goes through the one goods market; a partner's side is outside the modelled actors."""
		if tonnes <= 0.0:
			return 0.0, 0.0
		paid = (self.price_at(material, source) or 0.0) * tonnes
		received = (self.price_at(material, destination) or 0.0) * tonnes
		home = self._home_place()
		if source == home:
			self.market_purchase(trader_id, self.commodity_of(material), tonnes)  # type: ignore[attr-defined]
		if destination == home:
			self.market_sale(trader_id, material, tonnes)  # type: ignore[attr-defined]
		key = (material, source, destination)
		self._shipped()[key] = self._shipped().get(key, 0.0) + tonnes
		return paid, received
