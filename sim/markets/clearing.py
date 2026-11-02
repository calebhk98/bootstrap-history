"""The society's yearly market for materials: the year's flows by party and the close of the year.

Prices and traded volumes belong to the agent economy (sim/economy, through the port). This module keeps the goods market's
flows by party and reports a market's sales from the economy's record.

Everyone who buys or sells goes through the goods market, which writes the year's flows by party. The founder's own workings
enter as a net: output the founder uses himself never reaches the market, so only what he buys, draws beyond his stock and
sells does. What a firm or the state buys or sells is the same kind of entry.
"""
from sim.demography.api import RecordFoodEaten, rules as demography_rules
from sim.foreign_trade.api import ClosePartnerBooks
from sim.land.api import FinishWays
from sim.reporting.api import CloseRealOutput
from sim.world import market

from . import rules


class Clearing:

	# ---- the year's flows ----

	def legacy_market_flows(self):
		"""{"year", "bought": {commodity: {party: tonnes}}, "sold": {commodity: {party: tonnes}}, "drawn":
		{commodity: tonnes}}, written by the goods market. When the year turns the acting seat's flows and draws start
		again from nothing; every other party's entries stand until it deals again, as a firm's output and the state's
		purchases are standing orders. The live record: the goods market writes into it."""
		world = self.world
		year = self.needs.year()
		flows = world.market_flows
		if not flows or flows.get("year") != year:
			previous = flows or {}
			flows = world.market_flows = {"year": year, "drawn": {}}
			seats = self.needs.seat_list()["joined"]
			for kind in ("bought", "sold"):
				standing = {commodity: {party: tonnes for party, tonnes in parties.items() if party not in seats}
				            for commodity, parties in (previous.get(kind) or {}).items()}
				flows[kind] = {commodity: parties for commodity, parties in standing.items() if parties}
		return flows

	def market_floor_ratio(self, commodity):
		"""The lowest price over the incumbents' cost their producers sell at: a built plant sells at least at what running
		it costs, the running share of that cost; without a split, at its full cost (the trading partners' books read it)."""
		return rules.floor_ratio(self.needs.commodity_floor_ratio[commodity], market.UNSPLIT_FLOOR_RATIO)

	# ---- what callers read ----

	def market_state(self, material):
		"""The market for one material as of now, for reports: what the agent economy's markets of its commodity sold, left
		unsold and left unmet last year, split into the acting seat's own sales (it sells through the same markets, so the
		market's total holds them) and everyone else's. None while the economy opens or when the commodity has no priced material."""
		commodity = self.needs.material_pool[material][0]
		record = self.economy.agent_market_record(commodity)
		if record is None:
			return None
		market_api = self.goods_market
		displaced = min(record["sold"], market_api.sold_tonnes(commodity, market_api.acting_party_id))
		return {
			"material": commodity,
			"society_sales_tonnes": record["sold"] - displaced,
			"displaced_by_founder_tonnes": displaced,
			"unsold_tonnes": record["unsold"],
			"unmet_demand_tonnes": record["unmet"],
		}

	# ---- the turn of the year ----

	def step_market(self, seats=None):
		"""Close the year: the agent economy's year runs, then the partners' books close on what crossed."""
		self.needs.send(FinishWays())
		economy = self.economy
		economy.run_agent_year()
		outcome = economy.agent.outcomes[-1]
		accounts = getattr(outcome, "accounts", None)
		if accounts is None:
			self.needs.send(RecordFoodEaten(None, {}))
		else:
			self.needs.send(RecordFoodEaten(demography_rules.national_eaten_over_need(accounts),
			                                demography_rules.eaten_over_need_by_tile(accounts)))
		self.needs.send(ClosePartnerBooks())
		self.needs.send(CloseRealOutput())
