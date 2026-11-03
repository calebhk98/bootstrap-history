"""The agent economy's own life: whether it opened, its record, its last year and its health, for the engine's year and the tools."""
from sim.economy import api as economy_api

from .agent_view_part import AgentViewPart
from .port_health import health_report, staple_good
from .port_setup import build_setup


class AgentOutcomeViews(AgentViewPart):

	def agent_economy_opened(self):
		return self.parts.market_objects.economy.agent.opened()

	def open_agent_economy(self):
		"""Open the agent economy (with its hidden spin-up) if it is not open, and count the game's money at its wage."""
		self.parts.market_objects.economy.open_agent()

	def flush_agent_record(self):
		"""Bring the saved copy of the agent economy up to date; the game's save asks first."""
		self.parts.market_objects.economy.flush_record()

	def agent_spin_up_result(self):
		"""How the opening's hidden first stage ended: {"settled", "years", "gap"}; empty while it opens or when none ran."""
		return self._economy().agent.spin_up_result()

	def agent_health(self, metals=(), staple=None):
		"""The agent economy's health figures over the years this game has played (port_health.py)."""
		return health_report(self._economy().agent, metals, staple)

	def agent_last_outcome(self):
		"""The agent economy's outcome for the last year this process ran (its accounts, wages and prices); None on a game
		loaded and not yet stepped, since the outcome is not saved (the health figures are: agent_health)."""
		return self.parts.market_objects.economy.parts.year.last_outcome

	def agent_opening_figures(self):
		"""What the running agent economy opened with that the opening checks compare: its unskilled trade, interest rate
		and coin metal."""
		economy = self.parts.market_objects.economy.agent.economy()
		return {"unskilled_trade": economy_api.unskilled_trade(economy), "opening_rate": economy_api.opening_rate(economy),
		        "backing_good": economy_api.backing_good(economy)}

	def agent_stale_goods(self):
		"""The goods whose markets did not clear lately: their shown price is what they would cost to make, not a trade."""
		return self.parts.market_objects.economy.parts.prices.stale_goods()

	def agent_traded_staple(self):
		"""The staple good households buy most of whose market cleared lately; None when none did."""
		return staple_good(self.parts.market_objects.economy.agent, self.agent_stale_goods())

	def agent_opening_setup(self):
		"""The setup of the opening this game saved."""
		world = self.parts.market_objects.economy.world
		return build_setup(world, world.agent_record()["opening"])
