"""The only door into sim/economy/: what code outside the package may import.

Outside code imports from here and reaches the simulation's economy through an `Economy` (built by
sim/engine/economy_port*.py), never through a submodule or a private name. The accessors below read the
record's internals so that callers do not hold `economy.record.<field>` in their own code.
"""
WALL = "two-way"  # nothing here reaches sim/engine/; the engine hands it what it needs (sim/engine/economy_port.py)

import math

from . import diagnostics, households, labour_state, land_rents, market_curves, taxes, tile_costs, workforce_settle
from .currency import currency_from_coin_standard
from .economy import Economy
from .foreign import external_orders
from .market_memory import market_key
from .notional import shown_prices
from .producers import Producer, expected_output_prices, live_input_prices, live_wages
from .protocols import AgentOrders, YearInputs
from .recipes import recipes_from_production_data
from .record import EconomyRecord
from .setup import EconomySetup, TradeSpec, goods_specs
from .types import EDGE_CARGO, EDGE_EXTERNAL, EDGE_LEGACY, Bid, GoodsMove, Offer, Transfer, external_edge
from .unit_cost import variable_cost_per_run
from .year_close import rebase_basket_price_level
from .year_labour import trade_premium
from sim.world import capital_market

__all__ = [
    "diagnostics", "households", "taxes", "tile_costs", "currency_from_coin_standard", "Economy", "external_orders",
    "price_response",
    "shown_prices", "Producer", "expected_output_prices", "live_input_prices", "live_wages", "AgentOrders",
    "YearInputs", "recipes_from_production_data", "EconomyRecord", "EconomySetup", "TradeSpec",
    "goods_specs", "EDGE_EXTERNAL", "EDGE_LEGACY", "EDGE_CARGO", "external_edge", "Bid", "GoodsMove", "Offer", "Transfer",
    "variable_cost_per_run", "rebase_basket_price_level", "trade_premium",
    "traded_volumes", "opening_quantities", "wages_by_trade", "wages_by_trade_weighted", "interest_rate", "producers_of",
    "external_trade_net", "external_trade_volume", "account_balance", "account_holdings",
    "credit_room", "economy_from_record", "blank_economy", "export_record", "finish_spin_up", "shown_prices_of",
    "settle_agent_takings", "move_goods", "post_transfers", "cohort_incomes", "land_rent_per_hectare",
    "land_rent_paid_by_tile",
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


def people_by_trade(economy):
    """Working people by trade across every labour area, as the labour core's state holds them."""
    return labour_state.people_by_trade_everywhere(economy.record.workforce)


def wages_by_trade(economy):
    """Last year's wages per hour, as a list of market wages for each trade."""
    rows = {}
    for key, wage in economy.record.memory.wages.items():
        rows.setdefault(key.split(_KEY_SEPARATOR, 1)[0], []).append(wage)
    return rows


def land_rent_per_hectare(economy):
    """Mean rent per hectare-year producers paid last year over the tiles where land was let (zero where
    none was)."""
    rents = [rent for rent in economy.record.land_rent.values() if rent > 0.0]
    return sum(rents) / len(rents) if rents else 0.0


def land_rent_paid_by_tile(economy):
    """Rent producers paid on each tile where land was let last year, in the economy's units."""
    return land_rents.rent_paid_by_tile(economy.setup, economy.record)


def wages_by_trade_weighted(economy):
    """Last year's wage per hour of each trade: the remembered wage of each of its labour markets weighted
    by the hours hired there last year. A trade that hired nowhere falls back to the unweighted mean of
    its remembered wages."""
    rows = {}
    for key, wage in economy.record.memory.wages.items():
        rows.setdefault(key.split(_KEY_SEPARATOR, 1)[0], []).append((wage, economy.record.hours_hired.get(key, 0.0)))
    return {trade: (sum(wage * hours for wage, hours in pairs) / sum(hours for _wage, hours in pairs)
                    if sum(hours for _wage, hours in pairs) > 0.0 else sum(wage for wage, _hours in pairs) / len(pairs))
            for trade, pairs in rows.items()}


def interest_rate(economy):
    """The economy's own currency's rate from last year's memory, or None when it has none."""
    return economy.record.memory.rates.get(economy.setup.currency_id)


def credit_room(economy, borrower_id):
    """What lenders will still advance `borrower_id` beyond what others were lent at the last lending: the
    share of the savings on offer that lenders put out, less what the other borrowers took. None before
    lenders have met (no savings were offered yet)."""
    record = economy.record
    if record.funds_offered <= 0.0:
        return None
    others = sum(lent for borrower, lent in record.lent_by_borrower.items() if borrower != borrower_id)
    return capital_market.headroom(capital_market.lendable_capacity(record.funds_offered), others)


def producers_of(economy):
    """The producers by agent id."""
    return dict(economy.record.producers)


def external_trade_net(economy):
    """Money paid in over the external edge: exports less imports."""
    return economy.record.book.edge_net(EDGE_EXTERNAL, economy.setup.currency_id)


def external_trade_volume(economy):
    """Money moved either way over the external edge: exports plus imports."""
    return economy.record.book.edge_volume(EDGE_EXTERNAL, economy.setup.currency_id)


def cohort_incomes(economy):
    """(people, last year's money income) of every household cohort, poorest per head first: the economy's
    own answer to what its bodies of people earn."""
    rows = [(cohort.people, cohort.last_year_income) for cohort in economy.record.cohorts.values()
            if cohort.people > 0.0]
    return sorted(rows, key=lambda row: (row[1] / row[0], row[0]))


def price_response(economy, good, landed_units, taken_units):
    """Factor on a good's national price once `landed_units` more are offered and `taken_units` more are bought at
    the port, from the book the port's market last cleared (the economy's own demand and supply). The national price
    weighs each market area by what it usually trades, so a move at the port shows in it by the port's share of that
    value. None when the port's market has no book or traded nothing."""
    area = market_curves.port_area(economy.area_map, economy.setup.port_tile, good)
    curve = economy.record.curves.get(market_key(good, area)) if area is not None else None
    if curve is None:
        return None
    memory = economy.record.memory
    factor = market_curves.price_response(curve, good, memory.prices.get(market_key(good, area)), landed_units, taken_units)
    if factor is None or not math.isfinite(factor):
        return factor
    return 1.0 + _port_share(economy, good, area) * (factor - 1.0)


def _port_share(economy, good, area):
    """The port area's share of a good's usual traded value, which weighs a move at the port into the national
    price. Kept per economy until its next year, when prices and weights change."""
    cache = economy.__dict__.setdefault("_port_shares", {})
    key = (economy.record.memory.prices is not None and id(economy.record.memory.prices), good, area)
    if key not in cache:
        memory = economy.record.memory
        weights = memory.volume_weights or economy.record.volumes
        total = 0.0
        port_value = 0.0
        port_key = market_key(good, area)
        for market, price in memory.prices.items():
            if market.split(_KEY_SEPARATOR, 1)[0] == good:
                value = price * weights.get(market, 0.0)
                total += value
                if market == port_key:
                    port_value = value
        cache[key] = port_value / total if total > 0.0 else 1.0
    return cache[key]


def account_balance(economy, agent_id):
    """An agent's money balance in the economy's currency."""
    return economy.record.book.balance(agent_id, economy.setup.currency_id)


def account_holdings(economy, agent_id):
    """An agent's holdings in the book, as the book reports them."""
    return economy.record.book.holdings(agent_id)


def economy_from_record(setup, saved):
    """An Economy resumed from a record exported by `export_record`."""
    return Economy(setup, EconomyRecord.from_record(saved))


def blank_economy(setup):
    """An Economy at its opening, before any year has run."""
    return Economy(setup)


def set_improvements(economy, improvements):
    """Give the economy's hauls the built ways `{edge_key: {"road": true}}`; False when nothing changed."""
    return economy.set_improvements(improvements)


def export_record(economy):
    """The economy's record as plain data, for saving."""
    return economy.record.to_record()


def finish_spin_up(economy):
    """Closes the hidden spin-up years: the price level is rebased to one and the clock returns to zero."""
    rebase_basket_price_level(economy.setup, economy.record)
    economy.record.memory.year = 0


def trim_workforce_to_expected_hours(economy):
    """Cuts each skilled trade to the hours employers plan to want; see workforce_settle."""
    workforce_settle.trim_to_expected_hours(economy.setup, economy.record, economy.view())


def shown_prices_of(economy):
    """(prices, stale goods) the game is shown for this economy; see `notional.shown_prices`."""
    return shown_prices(economy.setup, economy.record)


def move_goods(economy, moves):
    """Applies goods moves to the economy's book."""
    economy.record.book.move_many(moves)


def post_transfers(economy, transfers):
    """Applies money transfers to the economy's book."""
    economy.record.book.transfer_many(transfers)


def settle_agent_takings(economy, agent_id, edge_id, tile_note="agent's takings"):
    """Sends an agent's money and every unsold holding back over an edge; returns the money sent."""
    book, money = economy.record.book, economy.setup.currency_id
    proceeds = book.balance(agent_id, money)
    if proceeds > 0.0:
        book.transfer(Transfer(agent_id, edge_id, money, proceeds, tile_note))
    returns = [GoodsMove(agent_id, edge_id, good, tile, quantity, "unsold concern output")
               for good, tiles in book.holdings(agent_id)["goods"].items()
               for tile, quantity in tiles.items() if quantity > 0.0]
    book.move_many(returns)
    return proceeds
