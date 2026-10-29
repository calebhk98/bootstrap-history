"""The founder sells a built concern to another actor through the exchange (the actors module addresses the exchange to the seat)."""
from sim.actors.api import SellSeatConcern


class Sales:
	def _not_selling(self, node_id):
		"""Why the acting seat has nothing to sell under this id, or None when it runs it."""
		if node_id not in self.seat.business.operating() or node_id in self.needs.techniques_granted():
			return "you are not running %s, so there is nothing to sell" % node_id
		return None

	def quote_concern_sale(self, node_id):
		"""What `sell_concern` would do now, without doing it: {"ok", "buyer", "price"} or {"ok": False, "error"}."""
		error = self._not_selling(node_id)
		if error is not None:
			return {"ok": False, "error": error}
		terms = self.needs.concern_sale_terms(node_id)
		if not terms["ok"]:
			return terms
		return {"ok": True, "concern": node_id, "buyer": terms["buyer"], "price": round(terms["price"], 1),
		        "capital": round(self.needs.acting_balance(), 1)}

	def sell_concern(self, node_id):
		"""Sell a concern you run to the actor the exchange picks, at the price it sets. {"ok", ...}."""
		error = self._not_selling(node_id)
		if error is not None:
			return {"ok": False, "error": error}
		sale = self.needs.send(SellSeatConcern(node_id))
		if not sale["ok"]:
			return sale
		return {"ok": True, "sold": node_id, "buyer": sale["buyer"], "price": round(sale["price"], 1),
		        "capital": round(self.needs.acting_balance(), 1)}
