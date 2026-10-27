"""What a concern turns out and earns against its opening, remembered while the techniques held are unchanged (volume_rules.py has the arithmetic).

Needs: legacy_game, held_goods_prices_in_hours."""
import json
from typing import Any, List

from sim.diffusion.api import NoteFirstRuns
from sim.prices.api import prices as price_solver

from . import volume_rules

# (civilisation as text, {techniques held: labour-hour prices}); a solve reads only these two
_PRICES_IN_HOURS: List[Any] = [None, {}]


class Volume:

	def _concern_prices_in_hours(self, held):
		"""Labour-hour prices under the techniques `held`; remembered while the civilisation is unchanged, so
		every concern asking about the same techniques shares one answer."""
		civilisation = self._game().civ
		civilisation_text = json.dumps(civilisation, sort_keys=True, default=str)
		if _PRICES_IN_HOURS[0] != civilisation_text:
			_PRICES_IN_HOURS[:] = [civilisation_text, {}]
		remembered = _PRICES_IN_HOURS[1]
		key = frozenset(held)
		if key not in remembered:
			remembered[key] = {material: price for material, price in sorted(
				self.needs.held_goods_prices_in_hours(held).items()) if price > 0.0}
		return remembered[key]

	def _concern_ratios(self, node_id):
		game = self._game()
		node = game.nodes[node_id]
		if node.get("_revenue_basis") != "output":
			return 1.0, 1.0, None

		game.send(NoteFirstRuns(game.view("techniques_in_use")()))
		held = game.view("techniques_spread")()

		def work_out():
			granted = frozenset(game.state.projects.granted)
			prices = game._done_memo("concern_opening_prices", granted,
			                         lambda: self._concern_prices_in_hours(granted))
			return volume_rules.ratios(node, price_solver.default_production_entries(), (granted, prices), (held, prices))
		return game._done_memo("concern_ratios", (node_id, held), work_out)

	def concern_volume_ratio(self, node_id):
		"""What the concern turns out now over what it turned out at the opening, from the same staff."""
		return self._concern_ratios(node_id)[0]

	def concern_value_ratio(self, node_id):
		"""The concern's net sales at the solved prices of the techniques held now, over the opening's."""
		return self._concern_ratios(node_id)[1]

	def concern_baskets_now(self, node_id):
		"""What the concern makes and buys in a year with the techniques held now; None for a node
		whose revenue is not derived from output."""
		return self._concern_ratios(node_id)[2]
