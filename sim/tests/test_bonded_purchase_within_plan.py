"""Complaint 644: an employer buys bonded people only within the room its year plan leaves. Rules called on built
inputs (the labour core's buying, the economy's room, the settlement); no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.economy import bonded_purchase, outlay_room
from sim.economy.accounts import Book
from sim.economy.producers import Plan
from sim.economy.state_budget import StateBudget
from sim.economy.types import Bid, EDGE_MINT, Transfer
from sim.labour.market import formation as core_formation
from sim.labour.market.bonded_worth import BondedLot
from sim.labour.market.records import Bid as CoreBid, Clearing, MarketState, YearInputs, YearReport

HOURS = 2000.0
FLOOR = 100.0


def market(trade, vacant_by_employer, wage=1.0):
    bids = [CoreBid(employer, trade, "dale", hours, wage) for employer, hours in sorted(vacant_by_employer.items())]
    clearing = Clearing(trade=trade, area="dale", wage=wage, hours_offered=0.0, hours_wanted=sum(vacant_by_employer.values()),
                        hours_hired=0.0, hired_by_employer={}, paid_by_employer={}, average_wage=wage)
    return bids, clearing


def year_inputs(bids, room, trades=("fitter",)):
    return YearInputs(trades={}, bids=bids, subsistence_per_worker_year={}, hours_per_worker_year=HOURS,
                      discount_rate=0.05, career_years=40.0, bondage_allowed=frozenset({"dale"}),
                      bonded_for_sale={"dale": {trade: 50.0 for trade in trades}}, ask_floor_per_worker_year={"dale": FLOOR},
                      outlay_room=room)


def buy(vacant, room, wage=1.0):
    bids, clearing = market("fitter", vacant, wage)
    report = YearReport()
    core_formation.form_trades(MarketState(), year_inputs(bids, room), [clearing], report)
    return report


def cost_of(report):
    return sum(lot.people * lot.price for lot in report.bonded_lots)


def paid_by(report, employer):
    return sum(lot.people * lot.price * dict(lot.payers).get(employer, 0.0) for lot in report.bonded_lots)


# an employer whose plan leaves no room buys none
report = buy({"forge": 10.0 * HOURS}, {}, wage=0.0)
check("a vacancy whose wage line is nothing, with no free cash, buys none", not report.bonded_lots, report.bonded_lots)
report = buy({}, {"forge": 1.0e9})
check("free cash with no vacancy buys none", not report.bonded_lots, report.bonded_lots)

# a purchase never passes the room
people = 100.0
line = people * HOURS * 0.1
report = buy({"forge": people * HOURS}, {}, wage=0.1)
check("with no free cash only the wage line of the vacancy is spent", 0.0 < cost_of(report) <= line + 1e-6, (cost_of(report), line))
report = buy({"forge": people * HOURS}, {"forge": 5.0e4}, wage=0.1)
check("free cash adds to the room, and the purchase stays inside it",
      line < cost_of(report) <= line + 5.0e4 + 1e-6, (cost_of(report), line))
report = buy({"forge": 10.0 * HOURS}, {"forge": 1.0e12})
check("room for more than the vacancies still buys no more than the vacancies",
      sum(lot.people for lot in report.bonded_lots) <= 10.0 + 1e-9, report.bonded_lots)

# the cost is shared by vacancy and no employer pays past its own room
report = buy({"forge": 6.0 * HOURS, "mill": 2.0 * HOURS}, {"forge": 1.0e9})
check("the poorer employer's room caps what it pays", paid_by(report, "mill") <= 2.0 * HOURS * 1.0 + 1e-6,
      (paid_by(report, "mill"), report.bonded_lots))
check("the shares paid add to the whole", all(abs(sum(share for _, share in lot.payers) - 1.0) < 1e-9 for lot in report.bonded_lots),
      report.bonded_lots)
report = buy({"forge": 4.0 * HOURS, "mill": 4.0 * HOURS}, {"mill": 1.0e9}, wage=0.0)
check("an employer with a vacancy and no room at all is not charged", paid_by(report, "forge") == 0.0, report.bonded_lots)

# free cash is spent once across one employer's markets
bids_a, clearing_a = market("fitter", {"forge": 5.0 * HOURS}, wage=0.0)
bids_b, clearing_b = market("smith", {"forge": 5.0 * HOURS}, wage=0.0)
report = YearReport()
core_formation.form_trades(MarketState(), year_inputs(bids_a + bids_b, {"forge": 3.0e4}, ("fitter", "smith")),
                           [clearing_a, clearing_b], report)
check("one employer's free cash is spent once across its markets", 0.0 < cost_of(report) <= 3.0e4 + 1e-6, cost_of(report))

# the plan figure of each kind of employer
check("free cash is cash less the plan's lines", outlay_room.free_cash(1000.0, [300.0, 200.0, 100.0]) == 400.0)
check("a plan that assigns all the cash leaves no room", outlay_room.free_cash(500.0, [300.0, 300.0]) == 0.0)
budget = StateBudget(wage_budget=1030.0, goods_budget=1030.0, held_back=1000.0)
plans = {"forge": Plan(1.0, bids=(Bid("forge", "iron", "dale", "t1", 1.0, 0.0, 1.0, 1.0, 150.0),), wage_line=300.0)}
balances = {"forge": 1000.0, "state": 3290.0}
room = outlay_room.by_employer(plans, "state", budget, balances.get)
check("a producer's room and the state's are read from their plans the same way", room == {"forge": 550.0, "state": 230.0}, room)
budget = StateBudget(wage_budget=1030.0, goods_budget=1030.0, held_back=1230.0)
check("a state whose plan assigns all its cash has no room", "state" not in outlay_room.by_employer({}, "state", budget, balances.get))

# settlement: the employers the core named pay, and nobody else is charged
book = Book()
for employer, cash in (("forge", 600.0), ("mill", 100.0), ("state", 1000.0)):
    book.transfer(Transfer(EDGE_MINT, employer, "coin", cash, "opening"))
lots = [BondedLot("work@t1", "smith", "work@t2", 4.0, 10.0, 2.0, payers=(("forge", 0.75), ("mill", 0.25)))]
bought, paid, paid_lots, held = bonded_purchase.settle(book, "coin", lots)
check("the named employers pay their shares and hold the people", abs(paid - 48.0) < 1e-9 and
      abs(held[("t1", "smith")]["forge"] - 3.0) < 1e-9 and abs(held[("t1", "smith")]["mill"] - 1.0) < 1e-9, (paid, held))
check("an employer the core did not name keeps its cash", book.balance("state", "coin") == 1000.0)
check("the book still sums to nothing", abs(book.total("coin")) < 1e-9)
