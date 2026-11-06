"""The agent economy's producers, volumes and trade books: what is made, what is traded and what crossed a border."""
from .agent_view_part import AgentViewPart


class AgentVolumeViews(AgentViewPart):

	def agent_producers_by_good(self):
		"""{good: [(tile, recipe id)]} of the producers the agent economy runs; None while it opens."""
		parts = self._answering()
		return None if parts is None else parts.producers.by_good()

	def agent_producer_runs(self):
		"""[{tile, runs, inputs, outputs}] of each producer that ran last year (runs of its recipe; the recipe's flows per run);
		None while the agent economy opens."""
		parts = self._answering()
		return None if parts is None else parts.producers.runs_last_year()

	def agent_trades_good(self, material):
		"""Whether the agent economy has a market for the material (False while it opens)."""
		parts = self._answering()
		return parts is not None and parts.prices.trades_good(material)

	def agent_producer_capacity(self, material):
		"""Tonnes a year the agent economy's producers can make of a material; None while the economy opens."""
		parts = self._answering()
		return None if parts is None else parts.producers.capacity_tonnes(material)

	def producers_stamp(self):
		"""Changes whenever the economy's producers do (as its year closes)."""
		return int(self._economy().world.agent_record().get("years_run", 0))

	def producer_capacities(self):
		"""[(recipe id, capacity in runs)] of every producer in the opened agent economy; empty before it opens."""
		return self._economy().parts.producers.capacities()

	def goods_carried_last_year(self):
		"""Last year's goods carried between the economy's tiles, {origin: {destination: tonnes}}."""
		return self.parts.market_objects.economy.agent.carried_last_year()

	def agent_opening_basket(self):
		"""(units a year households bought at the opening, their opening prices in labour hours), or None while it opens."""
		parts = self._answering()
		return None if parts is None else parts.households.opening_basket(None)

	def agent_volume_baseline(self):
		"""{good: the volume traded in the first year it cleared any}, or None before a year has closed."""
		parts = self._answering()
		return None if parts is None else parts.households.volume_baseline(None)

	def agent_traded_volumes(self):
		"""{good: units the home markets traded last year}, or None before a year has closed."""
		parts = self._answering()
		return None if parts is None else parts.households.traded_volumes(None)

	def country_trade_book(self, country):
		"""{good: tonnes and value each way} of what crossed the country's border last year; empty while the economy opens."""
		parts = self._answering()
		return {} if parts is None else parts.households.trade_book(country)

	def country_opening_basket(self, country):
		parts = self._answering()
		return None if parts is None else parts.households.opening_basket(country)

	def country_volume_baseline(self, country):
		parts = self._answering()
		return None if parts is None else parts.households.volume_baseline(country)

	def country_traded_volumes(self, country):
		parts = self._answering()
		return None if parts is None else parts.households.traded_volumes(country)

	def agent_country(self, country):
		"""What the agent economy answers for a partner country in it, or None (home, or a country not in the economy)."""
		parts = self._answering()
		return None if parts is None else parts.households.country(country)
