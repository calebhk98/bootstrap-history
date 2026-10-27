"""The religious house: a body of people kept by land, mill tolls and loans, that spends part of its surplus on land.

It extends the shipped church (rent of endowed land, tithe, stipends at the going pay of a trade) with what the
Han and Roman record show religious bodies also doing: milling other people's grain for a toll, and lending. It has
a rule for its surplus: a declared share of what is left after a year's stipends buys land at the capitalised rent
(rent over the market rate) up to a declared ceiling, so its estate grows with what rent gives it. The rest stays in its purse,
where the credit market lends it to borrowers, the founder among them, and the interest comes back through the
purse book. Nothing here names a faith, a place or a civilisation: every figure is data on the cast entry (`plan`).
"""
from sim.agents.api import edges, foundation, ledger

MILLING = "milling"
LAND_PURCHASE = "land purchase"


def register(api):
	class ReligiousHouse(foundation.Church):
		"""A church with mill tolls, a lending purse, and land bought from surplus."""
		kind = "religious_house"
		# the credit market offers this actor's purse to borrowers (`lender_offers`, sim/finance/capital_market.py)
		lends_from_purse = True

		def terms(self):
			return self.record.plan or {}

		def collections(self, world):
			lines = super().collections(world)
			terms = self.terms()
			toll_share = float(terms.get("mill_share_of_grain", 0.0)) * float(terms.get("toll_rate", 0.0))
			if toll_share > 0.0 and terms.get("milled_need"):
				lines[MILLING] = toll_share * world.tithable_sales_value(str(terms["milled_need"]))
			return lines

		def invest_surplus(self, world):
			share = float(self.terms().get("land_share_of_surplus", 0.0))
			rent = world.land_rent_per_hectare()
			rate = max(world.market_rate(), world.starting_rate())
			surplus = max(0.0, self.money - self.stipends_due(world))
			if share <= 0.0 or rent <= 0.0 or rate <= 0.0 or surplus <= 0.0:
				return
			price = rent / rate
			room = float(self.terms().get("land_ceiling_hectares", 0.0)) - self.record.endowment_hectares
			spend = min(share * surplus, max(0.0, room) * price)
			if spend <= 0.0:
				return
			ledger.transfer(self, world.edge(edges.EDGE_LANDOWNERS), spend, LAND_PURCHASE)
			self.record.endowment_hectares += spend / price

		def advance(self, world):
			super().advance(world)
			self.invest_surplus(world)

	api.actor_kind("religious_house", ReligiousHouse)
