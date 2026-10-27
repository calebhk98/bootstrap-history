"""The society's yearly market for materials: the year's flows, the book and the clearing.

Each commodity has a book entry: the society's producing capacity, stock held over, and the capacity it started with. The
year's posted price ratio (spot price over the incumbents' cost, sim/prices/tables.py) comes from `sim/world/market.py`,
clearing that capacity, the stock, the producers' offers (each at its own cost; sim/prices/cost_books.py) and the actors'
output against household demand (population and income, see demand.py). Quotes and purchase bills multiply the incumbents'
price by this ratio.

Everyone who buys or sells goes through the goods market, which writes the year's flows by party. The founder's own workings
enter as a net: output the founder uses himself never reaches the market, so only what he buys, draws beyond his stock and
sells does. What a firm or the state buys or sells is the same kind of entry. Flows are counted through the year and enter
the clearing when it closes: selling adds supply and takes sales from the society's producers, buying adds demand, and
capacity follows the resulting price while unsold goods carry on, so next year's posted price carries them. Within the year
the founder's own orders keep the marginal price curves that already move a bill as it is filled, which is why the posted
price leaves out the founder's flows and counts everyone else's.
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
		"""{"year", "bought": {commodity: {party: tonnes}}, "sold": {commodity: {party: tonnes}}, "reservation", "drawn":
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
			for kind in ("bought", "sold", "reservation"):
				standing = {commodity: {party: tonnes for party, tonnes in parties.items() if party not in seats}
				            for commodity, parties in (previous.get(kind) or {}).items()}
				flows[kind] = {commodity: parties for commodity, parties in standing.items() if parties}
		return flows

	# ---- the book ----

	def market_entry(self, commodity):
		"""The commodity's book entry, opened at the society's present output on first use; None for a commodity nothing
		produces or nothing offers."""
		book = self.world.market_book
		entry = book.get(commodity)
		if entry is None:
			output = self.needs.society_output[commodity]
			if not output > 0.0 or self.goods_market.commodity_is_unsourced(commodity):
				return None
			entry = book[commodity] = {
				"reference_tonnes": output, "capacity_tonnes": output,
				"stock_tonnes": 0.0, "price_ratio": 1.0,
				"society_sales_tonnes": output, "traded_tonnes": output}
		return entry

	def market_flow_figures(self, commodity, with_flows):
		"""(committed demand, founder sales, supply of sellers who take any price, actors' demand, offers of producers who
		name their cost) from this year's flows and the concerns running. The founder's own orders count only `with_flows`;
		every other party's always do."""
		market_api = self.goods_market
		committed = founder_sales = 0.0
		asking = market_api.acting_party_id
		if with_flows:
			committed = (market_api.bought_tonnes(commodity, asking)
			             + market_api.drawn_tonnes(commodity))
			founder_sales = market_api.sold_tonnes(commodity, asking)
		offers = market_api.others_offers(commodity)
		price_takers = market_api.others_sold_tonnes(commodity) - sum(offer.tonnes for offer in offers)
		return (committed, founder_sales, max(0.0, price_takers), market_api.others_bought_tonnes(commodity),
		        offers + self.needs.concern_offers(commodity))

	def market_conditions(self, commodity, entry, with_flows):
		committed, founder_sales, actor_supply, actor_demand, offers = self.market_flow_figures(commodity, with_flows)
		record = self.needs.commodity_record[commodity]
		return market.MarketConditions(
			household_demand_at_anchor_tonnes=(
				entry["reference_tonnes"] * self.household_demand_ratio(commodity)),
			committed_demand_tonnes=committed,
			society_capacity_tonnes=entry["capacity_tonnes"],
			actor_supply_tonnes=actor_supply,
			actor_demand_tonnes=actor_demand, offers=offers,
			founder_sales_tonnes=founder_sales,
			stock_tonnes=entry["stock_tonnes"],
			floor_ratio=self.market_floor_ratio(commodity),
			ceiling_ratio=float(record.get("price_ceiling_factor", market.DEFAULT_CEILING_RATIO)))

	def market_floor_ratio(self, commodity):
		"""The lowest price over the incumbents' cost their producers sell at: a built plant sells at least at what running
		it costs, the running share of that cost; without a split, at its full cost. Stock and price takers sell below this,
		down to the clearing's own stock bound."""
		return rules.floor_ratio(self.needs.commodity_floor_ratio[commodity], market.UNSPLIT_FLOOR_RATIO)

	def market_outcome(self, commodity, with_flows=False):
		"""(conditions, outcome) of the clearing, or None for a commodity nothing produces. Without `with_flows` it is the
		posted price (the founder's trades this year left out); with them, the year as it would close now. Cached until
		something it depends on changes."""
		entry = self.market_entry(commodity)
		if entry is None:
			return None
		signature = (self.needs.population_total(),
		             entry["capacity_tonnes"], entry["stock_tonnes"],
		             self.market_flow_figures(commodity, with_flows),
		             self.needs.concern_versions()[0], self.needs.year())
		cache = self._seat_dict("market_outcome")
		prices = self.needs.material_prices()
		cached = cache.get((commodity, with_flows))
		if cached is not None and cached[0] == signature and cached[2] is prices:
			return cached[1]
		conditions = self.market_conditions(commodity, entry, with_flows)
		result = (conditions, market.clear_market(conditions))
		cache[(commodity, with_flows)] = (signature, result, prices)
		return result

	# ---- what callers read ----

	def market_state(self, material):
		"""The market for one material as of now, for reports and tests."""
		commodity = self.needs.material_pool[material][0]
		result = self.market_outcome(commodity)
		if result is None:
			return None
		conditions, outcome = result
		entry = self.market_entry(commodity)
		closing_conditions, closing = self.market_outcome(commodity, with_flows=True)
		market_api = self.goods_market
		# what the market sold, left unsold and left unmet is the agent economy's record; the static book answers
		# only while the economy opens
		record = self.economy.agent_market_record(commodity) or {
			"sold": closing.society_sales_tonnes, "unsold": closing.unsold_tonnes,
			"unmet": closing.unmet_demand_tonnes}
		return {
			"material": commodity,
			"price_ratio": outcome.price_ratio,
			"price_ratio_if_year_closed_now": closing.price_ratio,
			"floor_ratio": conditions.floor_ratio,
			"ceiling_ratio": conditions.ceiling_ratio,
			"capacity_tonnes": entry["capacity_tonnes"],
			"reference_capacity_tonnes": entry["reference_tonnes"],
			"stock_tonnes": entry["stock_tonnes"],
			"household_demand_tonnes_at_anchor": conditions.household_demand_at_anchor_tonnes,
			"founder_purchases_tonnes": (market_api.bought_tonnes(commodity, market_api.acting_party_id)
			                             + market_api.drawn_tonnes(commodity)),
			"founder_sales_tonnes": closing_conditions.founder_sales_tonnes,
			"actor_supply_tonnes": conditions.actor_supply_tonnes + sum(
				offer.tonnes for offer in market_api.others_offers(commodity)),
			"actor_demand_tonnes": conditions.actor_demand_tonnes,
			"society_sales_tonnes": record["sold"],
			"displaced_by_founder_tonnes":
				market.society_sales_displaced_by_founder(closing_conditions),
			"unsold_tonnes": record["unsold"],
			"unmet_demand_tonnes": record["unmet"],
		}

	# ---- the turn of the year ----

	def open_market_book(self):
		"""An entry for every commodity the price table names, so each one's capacity follows its price from the first
		year."""
		opened = set()
		for material in sorted(self.needs.material_prices()):
			commodity = self.needs.material_pool[material][0]
			if commodity not in opened:     # several materials share a commodity; one look each
				opened.add(commodity)
				self.market_entry(commodity)

	def step_market(self, seats=None):
		"""Close the year: the agent economy's year runs, then the partners' books close on what crossed."""
		self.needs.send(FinishWays())
		self.open_market_book()
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
