"""Every employer's staff as standing bids in the agent economy's labour core. Part of the port (it imports `sim.economy.api`).

A seat's one-year orders (`hours_wanted_once`: a commission, the herds' growth labour) are posted with its places as bids for
this year only; the hours hired are delivered as hours (`HoursArrived`), not staff, and the order is spent. An order the seat did
not post (no affordable bid, or its wage payment refused) stays queued, except the herds' growing labour, which is worked out again each year.

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
from sim.reporting.api import RecordEvent
from sim.workforce.api import ONCE_STOCK, ClearingSettled, HoursArrived, NewcomersPlaced, NoteClearedWage, StaffArrived

STAFF_PREFIX = "staff:"
WORK_PREFIX = "work:"

# what a seat put into the year's clearing: the trades it bid for, the economy units its staff account was funded with, whether it
# offered hours of its own and the cause when it had places that no bid carried (None otherwise)
Posted = namedtuple("Posted", "trades funded_units offered unposted_cause")

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
    """(bids, economy units to fund them with) for one employer's places: each trade's hours at the economy's wage (the one rule, sim/economy/trade_wages.py), the bid's maximum wage
    being the ceiling over that wage. A trade the economy has no market for is not bid for (`trades_lacking` names it). When the places
    at the wage cost more than `affordable_coin` the hours are scaled down together to what it buys; the account is funded with the
    ceiling bill of those hours or all the employer can afford, whichever is less."""
    view, trades = economy.view(), economy_api.economy_trades(economy)
    account = staff_account(employer_id)
    asked = []
    for trade, people in sorted(wanted.items()):
        if people <= 0.0 or trade not in trades:
            continue
        area = view.area_of(trade, tile)
        asked.append((trade, area, people * economy_api.working_hours_per_year(economy), economy_api.trade_wage_at(economy, trade, tile)))
    affordable_units = max(0.0, affordable_coin) / economy_api.coin_per_unit(economy)
    bill = math.fsum(hours * wage for _trade, _area, hours, wage in asked)
    share = min(1.0, affordable_units / bill) if bill > 0.0 else 0.0
    bids = [LabourBid(account, trade, area, hours * share, wage * STAFF_WAGE_CEILING_MULTIPLE) for trade, area, hours, wage in asked] if share > 0.0 else []
    return bids, min(affordable_units, math.fsum(bid.hours * bid.maximum_wage for bid in bids))


def trades_lacking(economy, wanted):
    """{trade: people} of the places asked of a trade the economy has no market for: no bid carries them."""
    trades = economy_api.economy_trades(economy)
    return {trade: float(people) for trade, people in sorted(wanted.items()) if people > 0.0 and trade not in trades}


def unposted_cause(economy, wanted):
    """Why places that made no bid were not posted: "trade_not_in_economy" when every trade asked for is one the economy has no
    market for, else "no_affordable_bid" (the employer could not pay for any hour)."""
    asked = {trade for trade, people in wanted.items() if people > 0.0}
    return "trade_not_in_economy" if asked and asked == set(trades_lacking(economy, wanted)) else "no_affordable_bid"


def seat_places(sim, economy):
    """{trade: people} the acting seat's places and one-year orders ask for."""
    return places_with_once(sim.labour.staff_posting(), sim.labour.once_posting(), economy_api.working_hours_per_year(economy))


def seat_staff_bids(sim, economy, seat_id, tile):
    """(bids, economy units to fund them with) for the acting seat's places and one-year orders on `tile`; the one figure the
    seat's committed money (`port_goods_orders.staff_funding_coin`) and the year's posting (`post`) both draw. Call it inside
    `sim.scenario.act_as(seat_id)`. The figure can still move between the two: the wage it reads is the economy's current one, and the
    wages change at the clearing and when `place_newcomers` adds workers, which `post` does first."""
    wanted = seat_places(sim, economy)
    if not wanted:
        return [], 0.0
    return employer_bids(economy, seat_id, wanted, tile, sim.finance.spending_power("buy"))


def work_offers(economy, seat_id, offered, tile):
    """(offers, hours not offered by trade): the hours of a trade a seat offers of its own, as offers for its work account at no
    reservation wage (it sells at the market's); an hour of a trade the economy lacks is not offered, and is returned."""
    view, trades = economy.view(), economy_api.economy_trades(economy)
    offers = tuple(LabourOffer(work_account(seat_id), trade, view.area_of(trade, tile), hours, 0.0)
                   for trade, hours in sorted(offered.items()) if hours > 0.0 and trade in trades)
    dropped = {trade: hours for trade, hours in sorted(offered.items()) if hours > 0.0 and trade not in trades}
    return offers, dropped


def note_refusals(sim, refusal, dropped):
    """The acting seat's log says why its places or its own hours did not reach the clearing: the refused payment of its wages
    (its places hire no one this year) and the trades the economy lacks (their hours are not offered)."""
    if refusal is not None:
        sim.send(RecordEvent.of("staff_wages_unfunded", "The wages for your places could not be paid into the labour market (%s), so "
                                "hire no one this year: your staff are the people the labour market hired for you, none." % refusal, cause=refusal.cause))
    if dropped:
        sim.send(RecordEvent.of("wage_work_not_offered", "The labour market has no such trade, so these hours of your own work were "
                                "not offered: %s." % ", ".join("%s %.0f" % (trade, hours) for trade, hours in sorted(dropped.items())),
                                hours_by_trade={trade: float(hours) for trade, hours in dropped.items()}))


def note_trades_lacking(sim, lacking, logged):
    """The acting seat's log names the places no bid carried because the economy has no market for their trade, once for
    each trade (`logged` is the seat's list of trades already named, kept in the save)."""
    lacking = {trade: people for trade, people in lacking.items() if trade not in logged}
    logged.extend(lacking)
    if lacking:
        sim.send(RecordEvent.of("staff_trades_not_posted", "The labour market has no such trade, so these places were not posted: %s." % ", ".join(
            "%s %.1f" % (trade, people) for trade, people in lacking.items()), cause="trade_not_in_economy", people_by_trade=lacking))


def place_newcomers(sim, economy, tile):
    """The people the acting seat trained or was granted since the last clearing join the labour core on its tile, as workers of their
    trade, where its places hire them like anyone; the list is spent."""
    newcomers = sim.labour.newcomers()
    if not newcomers:
        return
    lacking, trades = {}, economy_api.economy_trades(economy)
    for trade, people in sorted(newcomers.items()):
        if trade in trades:
            economy_api.add_workers(economy, tile, trade, people)
        elif people > 0.0:
            lacking[trade] = float(people)
    if lacking:
        sim.send(RecordEvent.of("newcomers_not_placed", "The labour market has no such trade, so these newly trained or granted people "
                                "did not join it: %s." % ", ".join("%s %.1f" % (trade, people) for trade, people in sorted(lacking.items())),
                                cause="trade_not_in_economy", people_by_trade=lacking))
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


def wanted_places_exist(sim):
    """Whether the acting seat has places or one-year orders to post."""
    return bool(sim.labour.staff_posting()) or any(hours > 0.0 for orders in sim.labour.once_posting().values() for hours in orders.values())


def post(sim, economy, seat_ids, tile_of, trades_logged):
    """({account: AgentOrders}, {seat id: Posted}) for the year; each posting seat's money goes into its staff account. Every seat is
    a key: one whose places were not posted for want of an affordable bid has no trades and so no staff this year. A wage payment
    the seat's purse refuses is tried once more with what the seat can spend after the refusal; if that is refused too, nothing is
    posted for the seat, which its log states. A refusal never creates free labour: the core rehires the seat's people elsewhere
    when the seat has no bids, so the seat's staff follow what the core hired (none) and its commission orders stay queued.
    `trades_logged` is {seat id: trades its log has named as missing from the economy}, so each is named once."""
    orders, posted = {}, {}
    for seat_id in seat_ids:
        posted[seat_id] = Posted((), 0.0, False, None)
        with sim.scenario.act_as(seat_id):
            tile = tile_of(sim.labour.base_tile())
            place_newcomers(sim, economy, tile)
            trades, funded, offered, unposted = [], 0.0, False, None
            wanted = seat_places(sim, economy)
            note_trades_lacking(sim, trades_lacking(economy, wanted), trades_logged.setdefault(seat_id, []))
            bids, units = seat_staff_bids(sim, economy, seat_id, tile)
            refusal = None
            if bids:
                paid = sim.send(PayEdge(edges.EDGE_WORKERS, units * economy_api.coin_per_unit(economy), "wages offered in the labour market"))
                if isinstance(paid, Refusal):
                    bids, units = seat_staff_bids(sim, economy, seat_id, tile)
                    if bids:
                        paid = sim.send(PayEdge(edges.EDGE_WORKERS, units * economy_api.coin_per_unit(economy), "wages offered in the labour market"))
                    refusal = paid if isinstance(paid, Refusal) else None
                if refusal is None:
                    economy_api.post_transfers(economy, [Transfer(EDGE_EXCHANGE, staff_account(seat_id), economy_api.currency_id(economy), units, "wages offered")])
                    orders[staff_account(seat_id)] = AgentOrders(labour_bids=tuple(bids))
                    trades, funded = sorted({bid.trade for bid in bids}), units
            elif wanted_places_exist(sim):
                unposted = unposted_cause(economy, wanted)
            offers, dropped = work_offers(economy, seat_id, sim.labour.wage_work_offered(), tile)
            note_refusals(sim, refusal, dropped)
            if offers:
                orders[work_account(seat_id)] = AgentOrders(labour_offers=offers)
                offered = True
        posted[seat_id] = Posted(trades, funded, offered, unposted)
    return orders, posted


def settle(sim, economy, posted):
    """After the clearing: the money left in each posting seat's account goes back to it (what was spent is the wages the clearing
    charged), the seat is paid what the clearing hired of the hours it offered of its own, and every seat's staff are the people the
    clearing hired for it (none for a seat whose places were not posted). A one-year order the seat did not post stays queued for next
    year, except the herds' growth labour, which the herds work out again each year and which is spent."""
    sim.send(NoteClearedWage(economy_api.wages_by_trade_weighted(economy).get(economy_api.unskilled_trade(economy))))
    for seat_id, seat_posted in sorted(posted.items()):
        hired, charged, earned = {}, 0.0, 0.0
        with sim.scenario.act_as(seat_id):
            standing, once = sim.labour.staff_posting(), sim.labour.once_posting()
        if seat_posted.unposted_cause is not None:
            with sim.scenario.act_as(seat_id):
                sim.send(RecordEvent.of("staff_places_not_posted", "Your places and one-year orders for hours were not posted "
                                        "to the labour market (%s), so they hire no one this year; orders for contracted hours stay queued for next year." % seat_posted.unposted_cause.replace("_", " "),
                                        cause=seat_posted.unposted_cause, once_purposes=sorted(purpose for purpose, orders in once.items() if orders)))
        if seat_posted.trades:
            account = staff_account(seat_id)
            hired = economy_api.hours_paid_by_employer(economy, account)
            unspent = economy_api.settle_agent_takings(economy, account, EDGE_EXCHANGE)
            charged = max(0.0, seat_posted.funded_units - unspent) * economy_api.coin_per_unit(economy)
            with sim.scenario.act_as(seat_id):
                if unspent > 0.0:
                    sim.send(ReceiveFromEdge(edges.EDGE_WORKERS, unspent * economy_api.coin_per_unit(economy), "wage offers unspent"))
        if seat_posted.offered:
            earned = economy_api.settle_agent_takings(economy, work_account(seat_id), EDGE_EXCHANGE) * economy_api.coin_per_unit(economy)
        standing_hired, once_hired = split_hired(hired, standing, once, economy_api.working_hours_per_year(economy))
        staff = staff_of(standing_hired, economy_api.working_hours_per_year(economy))
        with sim.scenario.act_as(seat_id):
            if earned > 0.0:
                sim.send(ReceiveFromEdge(edges.EDGE_EMPLOYERS, earned, "wages for your own work"))
            sim.send(ClearingSettled(charged, earned))
            for purpose in sorted(set(once_hired) | {ONCE_STOCK} if seat_posted.trades else {ONCE_STOCK}):
                sim.send(HoursArrived(purpose, once_hired.get(purpose, {})))
            for trade in sorted(set(staff) | set(sim.labour.employed_by_trade())):
                sim.send(StaffArrived(trade, staff.get(trade, 0.0)))


def note_actor_unposted(sim, actor_id, cause):
    """A seat's places that posted nothing are logged in its own log with the cause. A firm or state has no log; its own record
    already shows the gap, `staff_wanted` naming the places and `workforce` holding no one for them."""
    if actor_id in sim.state.seats:
        sim.send(RecordEvent(
            "actor_places_not_posted", "Your places were not posted to the labour market (%s), so they hire no one this year." % cause.replace("_", " "),
            {"cause": cause}, seat=actor_id))


def post_actors(sim, economy, tile_of_actor):
    """({account: AgentOrders}, [ids of the actors that posted]) for the year: the firms', states' and players' places become
    bids like a seat's; each posting actor's money goes into its staff account."""
    orders, posted = {}, []
    for actor_id, actor in sorted(sim.scenario.actors.actors.items()):
        if actor.record.exited_year is not None or not actor.record.staff_wanted:
            continue
        bids, units = employer_bids(economy, actor_id, actor.record.staff_wanted, tile_of_actor(actor_id), max(0.0, actor.money))
        if not bids:
            note_actor_unposted(sim, actor_id, unposted_cause(economy, actor.record.staff_wanted))
            continue
        paid = sim.send(PayExchange(actor_id, units * economy_api.coin_per_unit(economy), "wages offered in the labour market"))
        if isinstance(paid, Refusal):
            note_actor_unposted(sim, actor_id, paid.cause)
            continue
        economy_api.post_transfers(economy, [Transfer(EDGE_EXCHANGE, staff_account(actor_id), economy_api.currency_id(economy), units, "wages offered")])
        orders[staff_account(actor_id)] = AgentOrders(labour_bids=tuple(bids))
        posted.append(actor_id)
    return orders, posted


def settle_actors(sim, economy, posted):
    """After the clearing: the money left in each posting actor's account goes back to it, and every actor's staff are the
    people the clearing hired for it (none for an actor that posted nothing)."""
    staff = {}
    for actor_id in posted:
        account = staff_account(actor_id)
        hired = economy_api.hours_paid_by_employer(economy, account)
        unspent = economy_api.settle_agent_takings(economy, account, EDGE_EXCHANGE)
        if unspent > 0.0:
            sim.send(ReceiveFromExchange(actor_id, unspent * economy_api.coin_per_unit(economy), "wage offers unspent"))
        staff[actor_id] = staff_of(hired, economy_api.working_hours_per_year(economy))
    actors_api.set_staff(sim.scenario.actors, staff)
