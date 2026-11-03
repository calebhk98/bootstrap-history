"""Every employer's staff as standing bids in the agent economy's labour core. Part of the port (it imports `sim.economy.api`).

A seat's one-year orders (`hours_wanted_once`: a commission, the herds' growth labour) are posted with its places as bids for
this year only; the hours hired are delivered as hours (`HoursArrived`), not staff, and the order is spent.

An employer (a seat, a firm, a state) posts places by trade: a seat's `hire` (`staff_posting`), an actor's
`record.staff_wanted`. Each year the places become `LabourBid`s for the employer's staff account at the economy's wage for
the trade; the account is funded from the employer's purse up to what it can spend, the core clears and pays the fills from
that account, and the employer's staff become the people the clearing hired (hours over the working year, not rounded). The money left
in the account goes back to the employer, and what was spent is the wages the clearing charged it. Each hour is paid once, by the clearing.

A seat's own hours (`wage_work_offered`) are offers in the same clearing, for an account `work:<seat>`; the seat is
paid what the clearing hired of them, at the market's one wage, after it. The people a seat trained or was granted since the last clearing
are put into the core before it.
"""
from collections import namedtuple
import math

from sim.actors import api as actors_api
from sim.agents.api import edges
from sim.constants import declare
from sim.economy import api as economy_api
from sim.economy.api import EDGE_EXCHANGE, AgentOrders, LabourBid, LabourOffer, Transfer
from sim.refusal import Refusal
from sim.ledger.api import PayEdge, PayExchange, ReceiveFromEdge, ReceiveFromExchange
from sim.workforce.api import ONCE_STOCK, ClearingSettled, HoursArrived, NewcomersPlaced, NoteClearedWage, StaffArrived

STAFF_PREFIX = "staff:"
WORK_PREFIX = "work:"

# what a seat put into the year's clearing: the trades it bid for, the economy units its staff account was funded with, whether it offered hours of its own
Posted = namedtuple("Posted", "trades funded_units offered")

STAFF_WAGE_CEILING_MULTIPLE = declare(
    "STAFF_WAGE_CEILING_MULTIPLE", 1.5, kind="temporary_heuristic", unit="multiple of last year's wage", source=None, confidence="D",
    retire="Complaints/964: the seat states its own maximum wage",
    why="The most a seat's standing bid offers per hour, as a multiple of the trade's wage last year, so a wage that rose in the "
        "year does not leave the places empty; the clearing pays the market wage, not the ceiling.")


def staff_account(seat_id):
    return STAFF_PREFIX + seat_id


def work_account(seat_id):
    return WORK_PREFIX + seat_id


def employer_bids(economy, employer_id, wanted, tile, affordable_coin):
    """(bids, economy units to fund them with) for one employer's places: each trade's hours at the economy's wage (the opening
    wage before the market has one), the bid's maximum wage being the ceiling over that wage. When the places at the wage cost more
    than `affordable_coin` the hours are scaled down together to what it buys; the account is funded with the ceiling bill of
    those hours or all the employer can afford, whichever is less."""
    view, setup = economy.view(), economy.setup
    account = staff_account(employer_id)
    asked = []
    for trade, people in sorted(wanted.items()):
        if people <= 0.0 or trade not in setup.trades:
            continue
        area = view.area_of(trade, tile)
        wage = view.wage(trade, area) or setup.opening_wages.get(trade)
        if wage and wage > 0.0:
            asked.append((trade, area, people * setup.working_hours_per_year, wage))
    affordable_units = max(0.0, affordable_coin) / setup.coin_per_unit
    bill = math.fsum(hours * wage for _trade, _area, hours, wage in asked)
    share = min(1.0, affordable_units / bill) if bill > 0.0 else 0.0
    bids = [LabourBid(account, trade, area, hours * share, wage * STAFF_WAGE_CEILING_MULTIPLE) for trade, area, hours, wage in asked] if share > 0.0 else []
    return bids, min(affordable_units, math.fsum(bid.hours * bid.maximum_wage for bid in bids))


def work_offers(economy, seat_id, offered, tile):
    """The hours of a trade a seat offers of its own, as offers for its work account at no reservation wage (it sells at the market's);
    an hour of a trade the economy lacks is not offered."""
    view, setup = economy.view(), economy.setup
    return tuple(LabourOffer(work_account(seat_id), trade, view.area_of(trade, tile), hours, 0.0)
                 for trade, hours in sorted(offered.items()) if hours > 0.0 and trade in setup.trades)


def place_newcomers(sim, economy, tile):
    """The people the acting seat trained or was granted since the last clearing join the labour core on its tile, as workers of their
    trade, where its places hire them like anyone; the list is spent."""
    newcomers = sim.labour.newcomers()
    if not newcomers:
        return
    for trade, people in sorted(newcomers.items()):
        if trade in economy.setup.trades:
            economy_api.add_workers(economy, tile, trade, people)
    sim.send(NewcomersPlaced())


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
    """({account: AgentOrders}, {seat id: Posted}) for the year; each posting seat's money goes into its staff account. Every seat is
    a key: one whose places were not posted (no places, or no affordable bid) has no trades."""
    orders, posted = {}, {}
    setup = economy.setup
    for seat_id in seat_ids:
        posted[seat_id] = Posted((), 0.0, False)
        with sim.act_as(seat_id):
            tile = tile_of(sim.labour.base_tile())
            place_newcomers(sim, economy, tile)
            trades, funded, offered = [], 0.0, False
            wanted = places_with_once(sim.labour.staff_posting(), sim.labour.once_posting(), setup.working_hours_per_year)
            bids, units = employer_bids(economy, seat_id, wanted, tile, sim.spending_power("buy")) if wanted else ([], 0.0)
            if bids and not isinstance(sim.send(PayEdge(edges.EDGE_WORKERS, units * setup.coin_per_unit, "wages offered in the labour market")), Refusal):
                economy_api.post_transfers(economy, [Transfer(EDGE_EXCHANGE, staff_account(seat_id), setup.currency_id, units, "wages offered")])
                orders[staff_account(seat_id)] = AgentOrders(labour_bids=tuple(bids))
                trades, funded = sorted({bid.trade for bid in bids}), units
            offers = work_offers(economy, seat_id, sim.labour.wage_work_offered(), tile)
            if offers:
                orders[work_account(seat_id)] = AgentOrders(labour_offers=offers)
                offered = True
        posted[seat_id] = Posted(trades, funded, offered)
    return orders, posted


def settle(sim, economy, posted):
    """After the clearing: the money left in each posting seat's account goes back to it (what was spent is the wages the clearing
    charged), the seat is paid what the clearing hired of the hours it offered of its own, and every seat's staff are the people the
    clearing hired for it (none for a seat whose places were not posted)."""
    setup = economy.setup
    sim.send(NoteClearedWage(economy_api.wages_by_trade_weighted(economy).get(setup.unskilled_trade)))
    for seat_id, seat_posted in sorted(posted.items()):
        hired, charged, earned = {}, 0.0, 0.0
        with sim.act_as(seat_id):
            standing, once = sim.labour.staff_posting(), sim.labour.once_posting()
        if seat_posted.trades:
            account = staff_account(seat_id)
            hired = economy_api.hours_hired_by_employer(economy, account)
            unspent = economy_api.settle_agent_takings(economy, account, EDGE_EXCHANGE)
            charged = max(0.0, seat_posted.funded_units - unspent) * setup.coin_per_unit
            with sim.act_as(seat_id):
                if unspent > 0.0:
                    sim.send(ReceiveFromEdge(edges.EDGE_WORKERS, unspent * setup.coin_per_unit, "wage offers unspent"))
        if seat_posted.offered:
            earned = economy_api.settle_agent_takings(economy, work_account(seat_id), EDGE_EXCHANGE) * setup.coin_per_unit
        standing_hired, once_hired = split_hired(hired, standing, once, setup.working_hours_per_year)
        staff = staff_of(standing_hired, setup.working_hours_per_year)
        with sim.act_as(seat_id):
            if earned > 0.0:
                sim.send(ReceiveFromEdge(edges.EDGE_EMPLOYERS, earned, "wages for your own work"))
            sim.send(ClearingSettled(charged, earned))
            for purpose in sorted(set(once_hired) | {ONCE_STOCK}):
                sim.send(HoursArrived(purpose, once_hired.get(purpose, {})))
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
