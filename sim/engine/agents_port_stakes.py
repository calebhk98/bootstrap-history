"""What interest groups can see of the stakes of workers out of a job, a church and an academy: the labour core's
unhired hours, the technique that displaced them, the rent of land, and the sales of goods a tithe falls on.
Mixed into `SimWorld`."""
from typing import Any, Dict, Tuple

from sim.agents.api import Sector
from . import need_substitutes


class StakeView:
	"""Read-only questions behind the stakes the strata, foundations and the state's servants have."""

	_sim: Any

	def idle_hours_by_trade(self) -> Dict[str, Tuple[float, float]]:
		"""(hours offered and not hired, hours offered) of each trade in the last clearing of the labour core."""
		return self._sim.economy.agent_idle_hours_by_trade()  # type: ignore[no-any-return]

	def running_techniques(self) -> Dict[str, int]:
		"""Every technique someone runs now (the founder, the firms and the other actors) and the year it was opened."""
		sim = self._sim
		running: Dict[str, int] = {}
		projects = sim.state.projects
		for node_id in projects.operating:
			running[node_id] = int(projects.opened_year.get(node_id, 0))
		for actor in sim.actors.of_kind("firm"):
			for node_id in actor.record.concerns:
				running[node_id] = max(running.get(node_id, 0), int(actor.record.opened_year.get(node_id, 0)))
		return running

	def displacing_technique(self, trade: str) -> Any:
		"""The running technique that most recently began doing its category's work with fewer hands of `trade`, or None."""
		return Sector.displacing_technique(trade, self.running_techniques(), self._sim.nodes)

	def technique_name(self, node_id: str) -> str:
		return str(self._sim.nodes.get(node_id, {}).get("name", node_id))

	def land_rent_per_hectare(self) -> float:
		"""Mean rent per hectare-year the land market let land at last year, in coin (zero while the economy opens)."""
		rent = self._sim.economy.agent_land_rent_per_hectare()
		return 0.0 if rent is None else float(rent)

	def tithable_sales_value(self, need_id: str) -> float:
		"""Money's worth of what the society's producers sold this year of the commodities of the goods that serve one need."""
		sim = self._sim
		commodities = {sim.economy.commodity_of(material) for material in need_substitutes.serving(need_id)}
		total = 0.0
		for commodity in sorted(commodities):
			state = sim.market_state(commodity)
			quote = self._commodity_quote(commodity)  # type: ignore[attr-defined]
			if state is not None and quote is not None:
				total += state["society_sales_tonnes"] * quote["buy_per_tonne"]
		return total

	def substitutes_of(self, material: str) -> Any:
		"""The materials that serve a need `material` serves."""
		return need_substitutes.substitutes_of(material)
