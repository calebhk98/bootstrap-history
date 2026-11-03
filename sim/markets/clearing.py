"""The society's yearly market for materials: the close of the year and the market's report.

Prices and traded volumes belong to the agent economy (sim/economy, through the port), which clears every seat's and actor's
orders together. This module keeps what the founder's running works drew from the market and reports a market's sales from the
economy's record.
"""
from sim.assembly.api import Part
from sim.demography.api import RecordFoodEaten, rules as demography_rules
from sim.foreign_trade.api import ResetActorTradeTallies
from sim.land.api import FinishWays
from sim.reporting.api import CloseRealOutput

from . import port_goods_orders


class Clearing(Part):

	# ---- the year's flows ----

	def legacy_market_flows(self):
		"""{"year", "drawn": {commodity: tonnes}}: what the founder's running works drew from the market this year, written by
		the goods market; it starts again from nothing when the year turns. The live record."""
		world = self.world
		year = self.needs.year()
		if not world.market_flows or world.market_flows.get("year") != year:
			world.market_flows = {"year": year, "drawn": {}}
		return world.market_flows

	# ---- what callers read ----

	def market_state(self, material):
		"""The market for one material as of now, for reports: what the agent economy's markets of its commodity sold, left
		unsold and left unmet last year, split into the acting seat's own sales in that clearing (it sells through the same markets, so the
		market's total holds them) and everyone else's. None while the economy opens or when the commodity has no priced material."""
		commodity = self.needs.material_pool[material][0]
		record = self.parts.market_objects.economy.agent_market_record(commodity)
		if record is None:
			return None
		displaced = min(record["sold"], port_goods_orders.traded_tonnes(self.parts.market_objects.economy.agent.stored, self.parts.market_objects.goods_market.acting_party_id, "sold").get(commodity, 0.0))
		return {
			"material": commodity,
			"society_sales_tonnes": record["sold"] - displaced,
			"displaced_by_founder_tonnes": displaced,
			"unsold_tonnes": record["unsold"],
			"unmet_demand_tonnes": record["unmet"],
		}

	# ---- the turn of the year ----

	def step_market(self, seats=None):
		"""Close the year: the agent economy's year runs, then the actors' trade tallies reset."""
		self.needs.send(FinishWays())
		economy = self.parts.market_objects.economy
		economy.open_agent()
		outcome = economy.parts.year.run_year()
		accounts = outcome.accounts
		if accounts is None:
			self.needs.send(RecordFoodEaten(None, {}))
		else:
			self.needs.send(RecordFoodEaten(demography_rules.national_eaten_over_need(accounts),
			                                demography_rules.eaten_over_need_by_tile(accounts)))
		self.needs.send(ResetActorTradeTallies())
		self.needs.send(CloseRealOutput())
