"""What a trader actor asks of the world: the places with a market, prices there, freight and depth.

A place is a civilisation id: the home society and each foreign economy trading with it this year.
Prices are per tonne in home money (the foreign side is its solved price converted through its coin).
Freight between home and a partner is the partner route's freight per tonne. What households at a
place buy for themselves in a year is the depth a trader sizes its cargo to.
"""
from typing import Any, Dict, List, Optional, Tuple

from .foreign_capacity import budget_scaled_final_tonnes, household_tonnes_by_material
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
				per_unit = {material: sim.partner_price_per_unit(place, material)
							for material in sim._foreign_economy_facts(place)["prices_in_home_money"]}
			prices = {}
			for material, price in per_unit.items():
				tonnes = tonnes_per_unit(material)
				if price and price > 0.0 and tonnes and tonnes > 0.0:
					prices[material] = price / tonnes
			return prices
		return self._once("trade_prices:" + place, compute)  # type: ignore[attr-defined,no-any-return]

	def _depth_by_material(self, place: str) -> Dict[str, float]:
		"""Tonnes a year households at a place buy of each good: at home from live prices and size, as the
		engine's own foreign trade does; a partner at its own solved prices."""
		if place != self._home_place():
			return household_tonnes_by_material(place)
		def compute() -> Dict[str, float]:
			sim = self._sim  # type: ignore[attr-defined]
			per_hour = sim.labour.money_per_labour_hour()
			prices = sim.goods_market.household_prices()
			return budget_scaled_final_tonnes({material: price / per_hour for material, price in prices.items()
											   if price > 0.0}, sim._opening_population())
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
			refused = not_traded_materials()
			return sorted(material for material in wanted if material in home and material in abroad
						  and material not in refused)
		return self._once("trade_materials", compute)  # type: ignore[attr-defined,no-any-return]

	def price_at(self, material: str, place: str) -> Optional[float]:
		return self._prices_per_tonne(place).get(material)

	def freight_between(self, source: str, destination: str, material: str, tonnes: float) -> float:
		"""Carriage over each partner's route between the two places; two partners trade through home, so
		both legs are paid. Nothing within one place."""
		if source == destination:
			return 0.0
		home = self._home_place()
		per_tonne = 0.0
		for partner in (source, destination):
			if partner != home:
				per_tonne += float(self._sim._foreign_economy_facts(partner)["freight_per_tonne"] or 0.0)  # type: ignore[attr-defined]
		return per_tonne * tonnes

	def market_depth(self, material: str, place: str) -> float:
		"""Tonnes a year buyers at a place take; at a partner no more than its market book's demand, the
		scale its price moves on when traders sell into it."""
		depth = float(self._depth_by_material(place).get(material, 0.0))
		if place == self._home_place():
			return depth
		sim = self._sim  # type: ignore[attr-defined]
		entry = sim._foreign_entry(place, sim._material_tag(material)[0], sim._foreign_economy_facts(place))
		return depth if entry is None else min(depth, float(entry["reference_tonnes"]))

	def price_after_cargo(self, material: str, place: str, tonnes: float, landing: bool) -> Optional[float]:
		"""Price per tonne at a place once `tonnes` more of a good land there (`landing`) or are taken from it, on
		top of this year's cargo; None where the place's market does not answer (the home society's, while it has
		no book for the good: the agent economy is off)."""
		price = self.price_at(material, place)
		if not price:
			return None
		if place == self._home_place():
			landed, taken, _limit = self._sim.actor_home_trade(material)  # type: ignore[attr-defined]
			factor = self._sim.economy.agent_price_response(  # type: ignore[attr-defined]
				material, landed + (tonnes if landing else 0.0), taken + (0.0 if landing else tonnes))
			return None if factor is None else price * factor
		return price * self._sim.partner_price_response(place, material, tonnes, landing)  # type: ignore[attr-defined,no-any-return]

	def _delivered(self) -> Dict[Tuple[str, str], float]:
		return self._memo.setdefault("delivered", {})  # type: ignore[attr-defined,no-any-return]

	def delivered_this_year(self, material: str, destination: str) -> float:
		return self._delivered().get((material, destination), 0.0)

	def ship(self, trader_id: str, material: str, tonnes: float, source: str, destination: str) -> Tuple[float, float]:
		"""Buy at the source and sell at the destination; (money paid, money received). The home side
		goes through the economy: orders at the port when the agent economy runs, the goods market's flows when it does
		not. A partner's side is tallied for its market book to close on
		(foreign_actor_trade.py)."""
		if tonnes <= 0.0:
			return 0.0, 0.0
		paid = (self.price_at(material, source) or 0.0) * tonnes
		received = (self.price_at(material, destination) or 0.0) * tonnes
		home = self._home_place()
		sim = self._sim  # type: ignore[attr-defined]
		if sim.economy.runs_agent_economy():
			# the agent economy takes the home side in as orders at the port when it clears the year
			if source == home:
				sim.note_actor_home_trade(material, tonnes, False, (received - self.freight_between(source, destination, material, tonnes)) / tonnes)
			if destination == home:
				sim.note_actor_home_trade(material, tonnes, True)
		else:
			if source == home:
				self.market_purchase(trader_id, self.commodity_of(material), tonnes)  # type: ignore[attr-defined]
			if destination == home:
				self.market_sale(trader_id, material, tonnes)  # type: ignore[attr-defined]
		if destination != home:
			sim.note_actor_trade(destination, material, tonnes, True)
		if source != home:
			sim.note_actor_trade(source, material, tonnes, False)
		key = (material, destination)
		self._delivered()[key] = self._delivered().get(key, 0.0) + tonnes
		return paid, received
