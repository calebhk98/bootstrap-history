"""People: hiring them, teaching them, buying them, paying them.

`Labour` is the set of parts that make up the labour of one simulation. It holds no rule and no state of its own:
each part owns one concern and is built here with the world it reads (the workforce module's `WorkforceWorld`,
sim/workforce/world.py) and the other parts it asks, passed in explicitly.

    book         the founder's staff and the reservations against the labour core's people     (staff_book.py)
    hours        the founder's own hour pool and what is spoken for                           (labour_hours.py)
    trades       literate and craft trades, the literacy to fill them, presence here           (labour_trades.py)
    schedule     the opening wage schedule priced at the present level                        (labour_wage_schedule.py)
    settlement   the base tile, its town, and how far a hire travels                          (labour_settlement.py)
    market       the one labour market every employer asks                                    (labour_market_api.py)
    pools        the `art`/`sch` pools rebuilt from the books, and grants of trained people    (labour_pools.py)
    capacity     institutional and supervisory ceilings, and the room left                    (labour_capacity.py)
    supply       how many people of a trade exist, are in reach, and offer hours              (labour_supply.py)
    report       the 'population' command's figures                                           (labour_population_report.py)
    hands        the hands and hours a project can draw on                                    (labour_hands.py)
    advice       what to tell a player who hit a wall on people                               (labour_advice.py)
    hiring       hire and fire                                                                (labour_hiring.py)
    training     teaching trades into existence                                               (labour_training.py)
    commissions  buying a job rather than a person                                            (labour_commissions.py)
    wages        the wage bill, the founder's own hours sold, the standing job                (labour_wages.py)
    relocation   moving the base                                                              (labour_relocation.py)
    bondage      buying and freeing people                                                    (labour_bondage.py)
    ledger       who left the payroll and why                                                 (labour_staff_ledger.py)
    controls     staffing policies: keep concerns staffed, hold a reserve                     (labour_staff_controls.py)
    allocation   the society's labour need by trade and its farming technique                 (labour_allocation.py)
"""
from .labour_advice import Advice
from .labour_allocation import Allocation
from .labour_bondage import Bondage
from .labour_capacity import Capacity
from .labour_commissions import Commissions
from .labour_hands import Hands
from .labour_hiring import Hiring
from .labour_hours import FounderHours
from .labour_market_api import LabourMarket
from .labour_pools import StaffPools
from .labour_population_report import PopulationReport
from .labour_relocation import Relocation
from .labour_settlement import Settlement
from .labour_staff_controls import StaffControls
from .labour_staff_ledger import StaffLedger
from .labour_supply import Supply
from .labour_trades import Trades
from .labour_training import Training
from .labour_wage_schedule import WageScheduleReader
from .labour_wages import Wages
from .staff_book import StaffBook


class Labour:
    """The parts of one simulation's labour. `world` is what they read of it."""

    def __init__(self, world):
        self.book = StaffBook(world)
        self.hours = FounderHours(world)
        self.trades = Trades(world)
        self.settlement = Settlement(world)
        self.schedule = WageScheduleReader(world, self.settlement)
        self.market = LabourMarket(world, self.schedule, self.settlement, self.book)
        self.pools = StaffPools(world, self.book, self.trades)
        self.capacity = Capacity(world, self.book, self.market, self.schedule, self.trades)
        self.supply = Supply(world, self.book, self.capacity, self.settlement, self.trades)
        self.report = PopulationReport(world, self.book, self.settlement, self.supply, self.trades)
        self.hands = Hands(world, self.supply, self.trades)
        self.advice = Advice(world, self.capacity, self.hands)
        self.hiring = Hiring(world, self.advice, self.book, self.capacity, self.market, self.pools, self.supply, self.trades)
        self.training = Training(world, self.advice, self.book, self.capacity, self.hours, self.market, self.supply, self.trades)
        self.commissions = Commissions(world, self.hands, self.market, self.schedule, self.supply, self.trades)
        self.wages = Wages(world, self.book, self.hours, self.market, self.trades)
        self.relocation = Relocation(world, self.book, self.hours, self.market, self.pools, self.settlement)
        self.bondage = Bondage(world, self.advice, self.capacity, self.pools, self.schedule)
        self.ledger = StaffLedger(world, self.book, self.market)
        self.controls = StaffControls(world, self.book, self.capacity, self.hiring, self.market)
        self.allocation = Allocation(world, self.schedule)
