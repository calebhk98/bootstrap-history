"""The only door into sim/economy/: what code outside the package may import.

Outside code imports from here and reaches the simulation's economy through an `Economy` (built by
sim/engine/economy_port*.py), never through a submodule or a private name. The accessors below read the
record's internals so that callers do not hold `economy.record.<field>` in their own code.
"""
WALL = "two-way"  # nothing here reaches sim/engine/; the engine hands it what it needs (sim/engine/economy_port.py)

from . import households, taxes, tile_costs
from .currency import currency_from_coin_standard
from .economy import Economy
from .foreign import external_orders
from .notional import shown_prices
from .producers import Producer, expected_output_prices, live_input_prices, live_wages
from .protocols import AgentOrders, YearInputs
from .recipes import recipes_from_production_data
from .record import EconomyRecord
from .setup import EconomySetup, TradeSpec, goods_specs
from .types import EDGE_EXTERNAL, EDGE_LEGACY, GoodsMove, Offer, Transfer
from .unit_cost import variable_cost_per_run
from .year_close import rebase_price_level
from .year_labour import trade_premium

__all__ = [
    "households", "taxes", "tile_costs", "currency_from_coin_standard", "Economy", "external_orders",
    "shown_prices", "Producer", "expected_output_prices", "live_input_prices", "live_wages", "AgentOrders",
    "YearInputs", "recipes_from_production_data", "EconomyRecord", "EconomySetup", "TradeSpec",
    "goods_specs", "EDGE_EXTERNAL", "EDGE_LEGACY", "GoodsMove", "Offer", "Transfer",
    "variable_cost_per_run", "rebase_price_level", "trade_premium",
    "traded_volumes", "opening_quantities", "wages_by_trade", "interest_rate", "producers_of",
    "external_trade_net", "external_trade_volume", "account_balance", "account_holdings",
]

_KEY_SEPARATOR = "|"


def traded_volumes(economy):
    """Last year's traded quantity of each good, summed over its markets."""
    totals = {}
    for key, volume in economy.record.volumes.items():
        good = key.split(_KEY_SEPARATOR, 1)[0]
        totals[good] = totals.get(good, 0.0) + volume
    return totals


def opening_quantities(economy):
    """Quantity of each good in the opening basket."""
    return dict(economy.record.opening_basket)


def wages_by_trade(economy):
    """Last year's wages per hour, as a list of market wages for each trade."""
    rows = {}
    for key, wage in economy.record.memory.wages.items():
        rows.setdefault(key.split(_KEY_SEPARATOR, 1)[0], []).append(wage)
    return rows


def interest_rate(economy):
    """The economy's own currency's rate from last year's memory, or None when it has none."""
    return economy.record.memory.rates.get(economy.setup.currency_id)


def producers_of(economy):
    """The producers by agent id."""
    return dict(economy.record.producers)


def external_trade_net(economy):
    """Money paid in over the external edge: exports less imports."""
    return economy.record.book.edge_net(EDGE_EXTERNAL, economy.setup.currency_id)


def external_trade_volume(economy):
    """Money moved either way over the external edge: exports plus imports."""
    return economy.record.book.edge_volume(EDGE_EXTERNAL, economy.setup.currency_id)


def account_balance(economy, agent_id):
    """An agent's money balance in the economy's currency."""
    return economy.record.book.balance(agent_id, economy.setup.currency_id)


def account_holdings(economy, agent_id):
    """An agent's holdings in the book, as the book reports them."""
    return economy.record.book.holdings(agent_id)
