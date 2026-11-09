"""The local labour market's reach and people for many trades at once (`labour_supply.Supply.reach_block`).

The ordinary trades (the ones that are not absent, literate or drawn from the unskilled pool) are worked out as columns: the core's
people in the base tile's labour area, the staff, the hours offered, then the same arithmetic as `Supply.market_supply` and
`Supply.people_who_exist` over whole arrays. The few other trades ask the per-trade methods, which hold their own rules."""
import numpy

from . import legacy_trade_defaults, trade_data
from .labour_wage_schedule import person_year_hours


def _ordinary(supply, names: numpy.ndarray) -> numpy.ndarray:
    """Which of the trades are ordinary: not absent, not literate (as the supply or the registry reads it), not drawn from the pool."""
    world = supply._world
    special = set(world.trades.trades_absent) | set(supply.trades.LITERATE_TRADES) | set(legacy_trade_defaults.DRAWN_FROM_UNSKILLED_POOL)
    special |= trade_data.literate_trades(trade_data.registry_of(world), names.tolist())
    return ~numpy.isin(names, list(special))


def _core_people(supply, names: numpy.ndarray) -> numpy.ndarray:
    """The core's people of each trade in the base tile's labour area, zero for a trade it holds nobody of or before the core opens."""
    by_tile = supply._world.economy.agent_people_by_tile_and_trade()
    row = {} if by_tile is None else by_tile.get(supply.settlement.base_tile(), {})
    return numpy.fromiter((row.get(trade, 0.0) for trade in names.tolist()), dtype=numpy.float64, count=len(names))


def reach_block(supply, trades):
    """(reachable, existing) per trade, as `Supply.reachable_trade_population` and `Supply.people_who_exist` give them one at a time."""
    names = numpy.asarray(list(trades), dtype=str)
    reachable, existing = numpy.zeros(len(names)), numpy.zeros(len(names))
    plain = _ordinary(supply, names)
    ordinary = names[plain].tolist()
    if ordinary:
        world = supply._world
        hours_per_person = person_year_hours(world)
        fallback = supply._fallback_people()
        core = _core_people(supply, names[plain])
        employees = supply.book.employed_by_trade()
        existing[plain] = numpy.maximum(numpy.where(core != 0.0, core, fallback),
                                        numpy.fromiter((employees.get(trade, 0.0) for trade in ordinary), dtype=numpy.float64, count=len(ordinary)))
        tile = supply.settlement.base_tile()
        offered = [world.economy.agent_hours_offered_at(trade, tile) for trade in ordinary]
        known = numpy.array([hours is not None and hours > 0.0 for hours in offered], dtype=bool)
        hours_offered = numpy.where(known, numpy.array([hours if hours is not None else 0.0 for hours in offered]), fallback * hours_per_person)
        staff = numpy.fromiter((world.actors.actor_staff_fte(trade) for trade in ordinary), dtype=numpy.float64, count=len(ordinary))
        hours = numpy.maximum(0.0, hours_offered - staff * hours_per_person)
        reachable[plain] = numpy.minimum(hours, existing[plain] * hours_per_person) / hours_per_person
    for place in numpy.flatnonzero(~plain).tolist():
        reachable[place] = supply.reachable_trade_population(names[place])
        existing[place] = supply.people_who_exist(names[place])
    return reachable, existing
