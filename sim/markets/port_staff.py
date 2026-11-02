"""The seats' staff as standing bids in the agent economy's labour core. Part of the port (it imports `sim.economy.api`).

A seat's `hire` posts places by trade (`sim.labour.staff_posting()`). Each year the places become `LabourBid`s for the seat's
staff account at the economy's wage for the trade; the account is funded from the seat's purse up to what it can spend, the
core clears and pays the fills from that account, and the seat's staff become the people the clearing hired (hours over the
working year). The money left in the account goes back to the seat. Each hour is paid once, by the clearing.
"""
import math

from sim.agents.api import edges
from sim.constants import declare
from sim.economy import api as economy_api
from sim.economy.api import EDGE_EXCHANGE, AgentOrders, LabourBid, Transfer
from sim.ledger.api import PayEdge, ReceiveFromEdge
from sim.workforce.api import StaffArrived

STAFF_PREFIX = "staff:"

STAFF_WAGE_CEILING_MULTIPLE = declare(
    "STAFF_WAGE_CEILING_MULTIPLE", 1.5, kind="temporary_heuristic", unit="multiple of last year's wage", source=None, confidence="D",
    retire="Complaints/964: the seat states its own maximum wage",
    why="The most a seat's standing bid offers per hour, as a multiple of the trade's wage last year, so a wage that rose in the "
        "year does not leave the places empty; the clearing pays the market wage, not the ceiling.")


def staff_account(seat_id):
    return STAFF_PREFIX + seat_id


def seat_bids(economy, seat_id, wanted, tile, affordable_coin):
    """(bids, economy units the bids can cost at most) for one seat's places: each trade's hours at the economy's wage
    (the opening wage before the market has one), scaled down together when the ceiling bill exceeds `affordable_coin`."""
    view, setup = economy.view(), economy.setup
    account = staff_account(seat_id)
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


def post(sim, economy, seat_ids, tile_of):
    """({account: AgentOrders}, {seat id: the trades it posted}) for the year; each posting seat's money goes into its
    staff account."""
    orders, posted = {}, {}
    setup = economy.setup
    for seat_id in seat_ids:
        with sim.act_as(seat_id):
            wanted = sim.labour.staff_posting()
            if not wanted:
                continue
            bids, units = seat_bids(economy, seat_id, wanted, tile_of(sim.labour.base_tile()), sim.view("spending_power")("buy"))
            if not bids:
                continue
            sim.send(PayEdge(edges.EDGE_WORKERS, units * setup.coin_per_unit, "wages offered in the labour market"))
        economy_api.post_transfers(economy, [Transfer(EDGE_EXCHANGE, staff_account(seat_id), setup.currency_id, units, "wages offered")])
        orders[staff_account(seat_id)] = AgentOrders(labour_bids=tuple(bids))
        posted[seat_id] = sorted({bid.trade for bid in bids})
    return orders, posted


def settle(sim, economy, posted):
    """After the clearing: the money left in each posting seat's account goes back to it, and its staff in each trade it
    posted are the people the clearing hired (whole people; a trade it did not post keeps its people)."""
    setup = economy.setup
    for seat_id, trades in sorted(posted.items()):
        account = staff_account(seat_id)
        hired = economy_api.hours_hired_by_employer(economy, account)
        unspent = economy_api.settle_agent_takings(economy, account, EDGE_EXCHANGE)
        with sim.act_as(seat_id):
            if unspent > 0.0:
                sim.send(ReceiveFromEdge(edges.EDGE_WORKERS, unspent * setup.coin_per_unit, "wage offers unspent"))
            for trade in trades:
                sim.send(StaffArrived(trade, float(round(hired.get(trade, 0.0) / setup.working_hours_per_year))))
