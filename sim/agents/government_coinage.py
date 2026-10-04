"""A state short of its need chooses to strike lighter coin.

Only the decision lives here. A state whose civilisation's coin standard is struck coin, and that
could not pay its standing need from revenue, reserve and credit, picks a share of the coin's metal
to cut. It is recorded on the government's record; applying it (the metal in the average coin, the
price level that follows) belongs to the economy, which reads `coin_cut_share` through the port.
"""
from typing import Any

from .tuning_coinage import COIN_RESTRIKE_SHARE_PER_YEAR, DEBASEMENT_SHARE_CEILING

STRUCK_COIN = "struck_coin"


def debasement_decision(government: Any, world: Any) -> float:
	"""Share of the metal in its coin the state cuts this year; zero unless it is short.

	The shortfall is what its standing need left unfunded after revenue, reserve and credit. Lighter
	coin recovers metal on the part of the stock struck again, so the cut that covers the shortfall
	is the shortfall over that part's worth, never past the ceiling.
	"""
	if world.coin_regime() != STRUCK_COIN:
		return 0.0
	shortfall = sum(government.record.unfunded.values())
	struck_again = world.coin_stock_value() * COIN_RESTRIKE_SHARE_PER_YEAR
	if shortfall <= 0.0 or struck_again <= 0.0:
		return 0.0
	return min(DEBASEMENT_SHARE_CEILING, shortfall / struck_again)


class CoinageMixin:
	"""Mixed into `Government`."""

	def decide_debasement(self, world: Any) -> float:
		"""Choose and record this year's cut; call after the standing need is paid."""
		share = debasement_decision(self, world)
		self.record.coin_cut_share = share  # type: ignore[attr-defined]
		self.record.coin_metal_kept *= 1.0 - share  # type: ignore[attr-defined]
		return share
