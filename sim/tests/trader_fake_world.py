"""A fake world of priced places with buying depth and per-tonne carriage, for the trader topics."""
from sim.agents.api import ActorRegistry, ActorsState

from .agents_fake_world import FakeWorld


class TradeWorld(FakeWorld):
	"""Places with prices and buying depth; carriage per tonne between any two; shipments tallied."""

	def __init__(self, prices, depth, freight=2.0, slippage=0.0, **kwargs):
		super().__init__(**kwargs)
		self.place_prices = prices  # place -> material -> price per tonne
		self.depth = depth  # place -> material -> tonnes a year
		self.freight_per_tonne = freight
		self.slippage = slippage  # share of the sale takings lost on the way
		self.shipped = {}
		self.countries = {}

	def trade_places(self, location):
		everywhere = sorted(self.place_prices)
		return everywhere if location is None else [place for place in everywhere if place != location]

	def trade_materials(self):
		return sorted({material for goods in self.place_prices.values() for material in goods})

	def price_at(self, material, place):
		return self.place_prices.get(place, {}).get(material, 0.0)

	def freight_between(self, source, destination, material, tonnes):
		return self.freight_per_tonne * tonnes

	def market_depth(self, material, place):
		return self.depth.get(place, {}).get(material, 0.0)

	def delivered_this_year(self, material, destination):
		return sum(tonnes for (good, _source, place), tonnes in self.shipped.items()
				   if good == material and place == destination)

	def ship(self, trader_id, material, tonnes, source, destination):
		key = (material, source, destination)
		self.shipped[key] = self.shipped.get(key, 0.0) + tonnes
		return (tonnes * self.price_at(material, source),
				tonnes * self.price_at(material, destination) * (1.0 - self.slippage))

	def country_of_place(self, place):
		return self.countries.get(place)

	def new_year(self):
		self.shipped = {}
		self.year += 1


def make_registry():
	return ActorRegistry(ActorsState(home_country="home"))
