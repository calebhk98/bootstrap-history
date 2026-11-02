"""Every employer's staff as standing bids in the agent economy's labour core. Part of the port (it imports `sim.economy.api`).

A seat's one-year orders (`hours_wanted_once`: a commission, the herds' growth labour) are posted with its places as bids for
this year only; the hours hired are delivered as hours (`HoursArrived`), not staff, and the order is spent.

An employer (a seat, a firm, a state) posts places by trade: a seat's `hire` (`sim.labour.staff_posting()`), an actor's
`record.staff_wanted`. Each year the places become `LabourBid`s for the employer's staff account at the economy's wage for
the trade; the account is funded from the employer's purse up to what it can spend, the core clears and pays the fills from
that account, and the employer's staff become the people the clearing hired (hours over the working year, not rounded). The money left
in the account goes back to the employer. Each hour is paid once, by the clearing.
"""
import math

from sim.actors import api as actors_api
from sim.agents.api import edges
from sim.constants import declare
from sim.economy import api as economy_api
from sim.economy.api import EDGE_EXCHANGE, AgentOrders, LabourBid, Transfer
from sim.refusal import Refusal
from sim.ledger.api import PayEdge, PayExchange, ReceiveFromEdge, ReceiveFromExchange
from sim.workforce.api import HoursArrived, StaffArrived

STAFF_PREFIX = "staff:"

STAFF_WAGE_CEILING_MULTIPLE = declare(
    "STAFF_WAGE_CEILING_MULTIPLE", 1.5, kind="temporary_heuristic", unit="multiple of last year's wage", source=None, confidence="D",
    retire="Complaints/964: the seat states its own maximum wage",
    why="The most a seat's standing bid offers per hour, as a multiple of the trade's wage last year, so a wage that rose in the "
        "year does not leave the places empty; the clearing pays the market wage, not the ceiling.")


def staff_account(seat_id):
    return STAFF_PREFIX + seat_id


def employer_bids(economy, employer_id, wanted, tile, affordable_coin):
    """(bids, economy units the bids can cost at most) for one employer's places: each trade's hours at the economy's wage
    (the opening wage before the market has one), scaled down together when the ceiling bill exceeds `affordable_coin`."""
    view, setup = economy.view(), economy.setup
    account = staff_account(employer_id)
    bids = []
    for trade, people in sorted(wanted.items()):
        if people <= 0.0 or trade not in setup.trades:
            continue
        area = view.area_of(trade, tile)
        wage = view.wage(trade, area) or setup.opening_wages.get(trade)
        if wage and wage > 0.0:
            bids.append(LabourBid(account, trade, area, people * setup.working_hours_per_year,
                                  wage * STAFF_WAGE_CEILING_MULTIPLE))
    bill = math.fsum(bid.hours * bid.maximum_wage for bid in bids)
    share = min(1.0, max(0.0, affordable_coin) / setup.coin_per_unit / bill) if bill > 0.0 else 0.0
    bids = [LabourBid(bid.employer, bid.trade, bid.area, bid.hours * share, bid.maximum_wage) for bid in bids] if share > 0.0 else []
    return bids, math.fsum(bid.hours * bid.maximum_wage for bid in bids)


def staff_of(hired, working_hours):
    """People per trade for the hours the clearing hired: the hours over the working year, not rounded, the same for a
    seat, a firm and a state."""
    return {trade: hours / working_hours for trade, hours in hired.items() if hours > 0.0}


def places_with_once(standing, once, working_hours):
    """{trade: people} the standing places and the one-year orders ({purpose: {trade: hours}}) together, as one bid per trade."""
    wanted = dict(standing)
    for orders in once.values():
        for trade, hours in orders.items():
            wanted[trade] = wanted.get(trade, 0.0) + hours / working_hours
    return wanted


def split_hired(hired, standing, once, working_hours):
    """(hours hired for the standing places by trade, {purpose: {trade: hours}} hired for the one-year orders): the hours
    the clearing hired of a trade are shared between the places and the orders in proportion to what each asked."""
    asked_once = {trade: math.fsum(orders.get(trade, 0.0) for orders in once.values()) for trade in {t for o in once.values() for t in o}}
    standing_hired, once_hired = {}, {purpose: {} for purpose in once}
    for trade, hours in hired.items():
        order_hours = asked_once.get(trade, 0.0)
        asked = standing.get(trade, 0.0) * working_hours + order_hours
        order_share = order_hours / asked if asked > 0.0 else 0.0
        standing_hired[trade] = hours * (1.0 - order_share)
        for purpose, orders in once.items():
            if orders.get(trade, 0.0) > 0.0:
                once_hired[purpose][trade] = hours * order_share * orders[trade] / order_hours
    return standing_hired, once_hired


def post(sim, economy, seat_ids, tile_of):
    """({account: AgentOrders}, {seat id: the trades it posted}) for the year; each posting seat's money goes into its
    staff account. Every seat is a key: one whose places were not posted (no places, no affordable bid, or the purse
    refused) has an empty list."""
    orders, posted = {}, {}
    setup = economy.setup
    for seat_id in seat_ids:
        posted[seat_id] = []
        with sim.act_as(seat_id):
            wanted = places_with_once(sim.labour.staff_posting(), sim.labour.once_posting(), setup.working_hours_per_year)
            if not wanted:
                continue
            bids, units = employer_bids(economy, seat_id, wanted, tile_of(sim.labour.base_tile()), sim.view("spending_power")("buy"))
            if not bids:
                continue
            if isinstance(sim.send(PayEdge(edges.EDGE_WORKERS, units * setup.coin_per_unit, "wages offered in the labour market")), Refusal):
                continue
        economy_api.post_transfers(economy, [Transfer(EDGE_EXCHANGE, staff_account(seat_id), setup.currency_id, units, "wages offered")])
        orders[staff_account(seat_id)] = AgentOrders(labour_bids=tuple(bids))
        posted[seat_id] = sorted({bid.trade for bid in bids})
    return orders, posted


def settle(sim, economy, posted):
    """After the clearing: the money left in each posting seat's account goes back to it, and every seat's staff are the
    people the clearing hired for it (none for a seat whose places were not posted)."""
    setup = economy.setup
    for seat_id, trades in sorted(posted.items()):
        hired = {}
        with sim.act_as(seat_id):
            standing, once = sim.labour.staff_posting(), sim.labour.once_posting()
        if trades:
            account = staff_account(seat_id)
            hired = economy_api.hours_hired_by_employer(economy, account)
            unspent = economy_api.settle_agent_takings(economy, account, EDGE_EXCHANGE)
            with sim.act_as(seat_id):
                if unspent > 0.0:
                    sim.send(ReceiveFromEdge(edges.EDGE_WORKERS, unspent * setup.coin_per_unit, "wage offers unspent"))
        standing_hired, once_hired = split_hired(hired, standing, once, setup.working_hours_per_year)
        staff = staff_of(standing_hired, setup.working_hours_per_year)
        with sim.act_as(seat_id):
            for purpose, hours_by_trade in sorted(once_hired.items()):
                sim.send(HoursArrived(purpose, hours_by_trade))
            for trade in sorted(set(staff) | set(sim.labour.employed_by_trade())):
                sim.send(StaffArrived(trade, staff.get(trade, 0.0)))


def post_actors(sim, economy, tile_of_actor):
    """({account: AgentOrders}, [ids of the actors that posted]) for the year: the firms', states' and players' places become
    bids like a seat's; each posting actor's money goes into its staff account."""
    orders, posted = {}, []
    setup = economy.setup
    for actor_id, actor in sorted(sim.actors.actors.items()):
        if actor.record.exited_year is not None or not actor.record.staff_wanted:
            continue
        bids, units = employer_bids(economy, actor_id, actor.record.staff_wanted, tile_of_actor(actor_id), max(0.0, actor.money))
        if not bids:
            continue
        if isinstance(sim.send(PayExchange(actor_id, units * setup.coin_per_unit, "wages offered in the labour market")), Refusal):
            continue
        economy_api.post_transfers(economy, [Transfer(EDGE_EXCHANGE, staff_account(actor_id), setup.currency_id, units, "wages offered")])
        orders[staff_account(actor_id)] = AgentOrders(labour_bids=tuple(bids))
        posted.append(actor_id)
    return orders, posted


def settle_actors(sim, economy, posted):
    """After the clearing: the money left in each posting actor's account goes back to it, and every actor's staff are the
    people the clearing hired for it (none for an actor that posted nothing)."""
    setup = economy.setup
    staff = {}
    for actor_id in posted:
        account = staff_account(actor_id)
        hired = economy_api.hours_hired_by_employer(economy, account)
        unspent = economy_api.settle_agent_takings(economy, account, EDGE_EXCHANGE)
        if unspent > 0.0:
            sim.send(ReceiveFromExchange(actor_id, unspent * setup.coin_per_unit, "wage offers unspent"))
        staff[actor_id] = staff_of(hired, setup.working_hours_per_year)
    actors_api.set_staff(sim.actors, staff)
