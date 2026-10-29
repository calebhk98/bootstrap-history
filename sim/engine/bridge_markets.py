"""Bridge entries the markets module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine as the old mixin code did,
and is never cached."""
from sim.markets.api import RepriceOpeningMoney

from . import opening_money
from .bridge import bridge_command, bridge_view


# ---- commands: the opening's money ----

@bridge_command(RepriceOpeningMoney)
def reprice_opening_money(sim, command):
    """Every seat's purse and the tree's money fields move to the money an hour of work is worth at the economy."""
    opening_money.reprice_opening_money(sim, command.before)


# ---- the module's own objects, for engine code that still reaches them through the game ----

@bridge_view("legacy_economy")
def legacy_economy(sim):
    """The port over the agent economy (the markets module's `economy`)."""
    return sim.assembly.modules["markets"].economy


@bridge_view("legacy_goods_market")
def legacy_goods_market(sim):
    """The one goods market every buyer and seller asks (the markets module's `goods_market`)."""
    return sim.assembly.modules["markets"].goods_market
