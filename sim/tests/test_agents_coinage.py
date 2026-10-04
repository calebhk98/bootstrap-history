"""A struck-coin state short of its need chooses to cut the metal in its coin; no other state does."""
from .harness import check

from sim.agents.api import ActorRecord
from sim.agents.government import Government
from sim.agents.government_coinage import CoinageMixin, debasement_decision
from sim.agents.tuning_coinage import COIN_RESTRIKE_SHARE_PER_YEAR, DEBASEMENT_SHARE_CEILING

from .agents_fake_world import FakeWorld


class State(Government):
	"""The government, which carries the coinage policy."""


check("the government carries the coinage policy", issubclass(Government, CoinageMixin))


class CoinWorld(FakeWorld):
	def __init__(self, regime="struck_coin", stock_value=1000.0):
		super().__init__()
		self.regime = regime
		self.stock_value = stock_value

	def coin_regime(self):
		return self.regime

	def coin_stock_value(self):
		return self.stock_value


def state_short_by(shortfall):
	return State("government:home", ActorRecord(kind="government", unfunded={"army": shortfall}))


check("a state that paid its need cuts nothing", debasement_decision(state_short_by(0.0), CoinWorld()) == 0.0)
small = debasement_decision(state_short_by(5.0), CoinWorld())
check("a short struck-coin state cuts the metal", small > 0.0, small)
expected = 5.0 / (1000.0 * COIN_RESTRIKE_SHARE_PER_YEAR)
check("the cut covers the shortfall from the coin it strikes again", abs(small - expected) < 1e-12, (small, expected))
larger = debasement_decision(state_short_by(10.0), CoinWorld())
check("a larger shortfall cuts more", larger > small, (small, larger))
check("a bigger coin stock needs a smaller cut",
      debasement_decision(state_short_by(5.0), CoinWorld(stock_value=4000.0)) < small)
check("the cut never passes the ceiling",
      debasement_decision(state_short_by(1.0e9), CoinWorld()) == DEBASEMENT_SHARE_CEILING)
for regime in ("weighed_metal", "commodity", "fiat"):
	check("a %s standard has no coin to cut" % regime,
	      debasement_decision(state_short_by(5.0), CoinWorld(regime=regime)) == 0.0)
check("no coin in use gives nothing to strike again",
      debasement_decision(state_short_by(5.0), CoinWorld(stock_value=0.0)) == 0.0)

state = state_short_by(5.0)
world = CoinWorld()
state.decide_debasement(world)
check("the decision is recorded on the government's record", state.record.coin_cut_share == small)
check("the coin keeps the rest of its metal", abs(state.record.coin_metal_kept - (1.0 - small)) < 1e-12)
state.record.unfunded = {}
state.decide_debasement(world)
check("a year with no shortfall records no cut and the lighter coin stays lighter",
      state.record.coin_cut_share == 0.0 and abs(state.record.coin_metal_kept - (1.0 - small)) < 1e-12)
