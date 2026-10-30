"""When a trade a project needs will first have hands: the start gate, the start reply and the stall gate read one rule
(start_rules.py `trade_wait_years`, `trade_wait_outlasts`)."""
from . import start_rules


class TradeWait:
	def years_until_trade_has_hands(self, trade):
		"""0 when hands exist now; else years until the soonest trainees join; None when nobody is on the way."""
		needs = self.needs
		return start_rules.trade_wait_years(needs.market_supply[trade], needs.year(), needs.training_queue(), trade)

	def trades_the_project_waits_for(self, node_id):
		"""{trade: years until the first hands} for each trade the project owes hours to that nobody holds yet."""
		waits = {}
		for trade, want in (self.needs.tree_nodes()[node_id].get("lab") or {}).items():
			wait = self.years_until_trade_has_hands(trade) if want > 0 else 0.0
			if wait is None or wait > 0.0:
				waits[trade] = wait
		return waits

	def trade_wait_outlasts(self, trade_id):
		"""True when no hands exist and none arrive before the stall gate would abandon the project."""
		return start_rules.trade_wait_outlasts(self.years_until_trade_has_hands(trade_id), start_rules.STALL_YEARS_BEFORE_ABANDONMENT)
