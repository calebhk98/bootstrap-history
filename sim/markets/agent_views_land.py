"""The agent economy's land views: rents, the people who fled the state's take and the output by tile."""
from .agent_view_part import AgentViewPart


class AgentLandViews(AgentViewPart):

	def agent_land_rent_per_hectare(self):
		"""Mean rent per hectare-year of the agent economy's land market, in coin; None while it opens."""
		parts = self._answering()
		return None if parts is None else parts.households.land_rent_per_hectare()

	def agent_land_rent_at(self, tile):
		parts = self._answering()
		return None if parts is None else parts.households.land_rent_at_tile(tile)

	def agent_land_rent_paid_by_tile(self):
		parts = self._answering()
		return {} if parts is None else parts.households.land_rent_paid_by_tile()

	def agent_fugitive_share_by_tile(self):
		"""{tile: share of its people away having fled the state's take}; empty before the agent economy exists."""
		return self.parts.market_objects.economy.parts.households.fugitive_share_by_tile()

	def agent_output_tonnes_of(self, material):
		"""{tile: tonnes of `material` made there last year}, every tile that made anything; empty while the economy opens."""
		parts = self._answering()
		return {} if parts is None else parts.producers.output_tonnes_of(material)
