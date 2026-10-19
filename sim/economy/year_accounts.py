"""The year's accounts: what was made, used up in making, eaten, built and left in stock, good by good, and
how well each cohort ate and was paid. Read from the year's own book flows, stocks and ledger, not from the
engine's real-output measure (Complaint 554). Nothing here changes the economy."""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Mapping

from .types import EDGE_CONSUMPTION, EDGE_PRODUCTION, EDGE_SPOILAGE

# the purposes the economy books goods under (producers.py, households_close.py, inventory.py, economy.py)
GROWN_PURPOSE = "grown for itself"
INPUT_PURPOSE = "input"
CONSUMPTION_PURPOSE = "consumption"
WEAR_PURPOSE = "wear"
PLANT_PURPOSE = "built into plant"
STATE_PURPOSE_PREFIX = "state "


@dataclass(frozen=True)
class GoodAccount:
    production: float = 0.0                  # made this year, grown for itself included
    production_grown: float = 0.0            # the part households grew for themselves
    intermediate_use: float = 0.0            # used up as an input of production
    final_consumption_bought: float = 0.0    # eaten or used by households, bought on the market
    final_consumption_grown: float = 0.0     # the same, grown on their own plots
    durable_wear: float = 0.0                # households' durables worn through use
    state_use: float = 0.0                   # used up by the state
    investment: float = 0.0                  # built into plant
    other_use: float = 0.0                   # used up by other actors, outside the purposes above
    spoilage: float = 0.0
    other_net_inflow: float = 0.0            # net over the other edges: across the border, the mint, wear, cargo
    stock_at_start: float = 0.0
    stock_change: float = 0.0                # held by agents at the end less at the start
    market_turnover: float = 0.0             # quantity the year's markets cleared

    @property
    def final_consumption(self) -> float:
        return self.final_consumption_bought + self.final_consumption_grown + self.durable_wear

    def residual(self) -> float:
        """What the flows leave unexplained of the stock change: zero when the accounts close."""
        return (self.production + self.other_net_inflow - self.intermediate_use - self.final_consumption
                - self.state_use - self.investment - self.other_use - self.spoilage - self.stock_change)


@dataclass(frozen=True)
class CohortAccount:
    cohort: str
    tile: str
    income_class: int
    people: float
    need_per_head: float            # the hunger need's units a person needs a year (calories in the data)
    eaten_per_head: float
    bought_per_head: float
    own_plot_per_head: float
    real_income_per_head: float     # last year's income per head over the opening basket's cost per head

    @property
    def eaten_over_need(self) -> float:
        return self.eaten_per_head / self.need_per_head if self.need_per_head > 0.0 else math.nan


@dataclass(frozen=True)
class TileAccount:
    tile: str
    people: float
    need_per_head: float
    eaten_per_head: float

    @property
    def eaten_over_need(self) -> float:
        return self.eaten_per_head / self.need_per_head if self.need_per_head > 0.0 else math.nan


@dataclass(frozen=True)
class RealWage:
    trade: str
    wage_per_hour: float
    wage_per_hour_opening: float
    basket_cost_per_head: float             # the opening's basket per head at this year's prices
    basket_cost_per_head_opening: float     # the same at the prices the price level is based on
    working_hours_per_year: float

    @property
    def real_wage_index(self) -> float:
        """Baskets a wage buys over the baskets the opening's wage bought: one at the opening."""
        if min(self.basket_cost_per_head, self.wage_per_hour_opening, self.basket_cost_per_head_opening) <= 0.0:
            return math.nan
        return (self.wage_per_hour / self.basket_cost_per_head) / (
            self.wage_per_hour_opening / self.basket_cost_per_head_opening)

    @property
    def baskets_per_working_year(self) -> float:
        return (self.wage_per_hour * self.working_hours_per_year / self.basket_cost_per_head
                if self.basket_cost_per_head > 0.0 else math.nan)


@dataclass(frozen=True)
class YearAccounts:
    year: int
    goods: Dict[str, GoodAccount] = field(default_factory=dict)
    plant_wear: Dict[str, float] = field(default_factory=dict)   # goods the plant that wore out this year is made of
    cohorts: List[CohortAccount] = field(default_factory=list)
    tiles: List[TileAccount] = field(default_factory=list)
    real_wages: Dict[str, RealWage] = field(default_factory=dict)


def stocks(book) -> Dict[str, float]:
    """Quantity of each good the agents hold (edge accounts excluded)."""
    return book.goods_totals()


def build(setup, record, ledger, stocks_at_start: Mapping[str, float], prices: Mapping[str, float],
          wages: Mapping[str, float]) -> YearAccounts:
    cohorts = _cohorts(setup, record, ledger, prices)
    return YearAccounts(year=record.memory.year, goods=_goods(setup, record, ledger, stocks_at_start),
                        plant_wear=_plant_wear(setup, record, ledger), cohorts=cohorts, tiles=_tiles(cohorts),
                        real_wages=_real_wages(setup, record, prices, wages))


def _goods(setup, record, ledger, stocks_at_start) -> Dict[str, GoodAccount]:
    book = record.book
    stocks_now = stocks(book)
    other_edges = [edge for edge in book.edge_goods_agents()
                   if edge not in (EDGE_PRODUCTION, EDGE_CONSUMPTION, EDGE_SPOILAGE)]
    bought: Dict[str, float] = {}
    grown: Dict[str, float] = {}
    for cohort_id in record.cohorts:
        for good, quantity in ledger.received.get(cohort_id, {}).items():
            bought[good] = bought.get(good, 0.0) + quantity
        for good, quantity in ledger.grown.get(cohort_id, {}).items():
            grown[good] = grown.get(good, 0.0) + quantity
    turnover: Dict[str, float] = {}
    for result in ledger.clearings:
        turnover[result.good] = turnover.get(result.good, 0.0) + result.quantity
    goods = set(stocks_now) | set(stocks_at_start) | set(turnover) | set(setup.specs)
    accounts = {}
    for good in sorted(goods):
        purposes = book.goods_flow(good)
        state = math.fsum(quantity for purpose, quantity in purposes.items() if purpose.startswith(STATE_PURPOSE_PREFIX))
        known = (purposes.get(INPUT_PURPOSE, 0.0) + purposes.get(CONSUMPTION_PURPOSE, 0.0)
                 + purposes.get(WEAR_PURPOSE, 0.0) + purposes.get(PLANT_PURPOSE, 0.0) + state)
        household = purposes.get(CONSUMPTION_PURPOSE, 0.0)
        own = grown.get(good, 0.0)
        share_grown = own / (own + bought.get(good, 0.0)) if own > 0.0 else 0.0
        accounts[good] = GoodAccount(
            production=book.edge_goods_net(EDGE_PRODUCTION, good),
            production_grown=purposes.get(GROWN_PURPOSE, 0.0),
            intermediate_use=purposes.get(INPUT_PURPOSE, 0.0),
            final_consumption_bought=household * (1.0 - share_grown), final_consumption_grown=household * share_grown,
            durable_wear=purposes.get(WEAR_PURPOSE, 0.0), state_use=state,
            investment=purposes.get(PLANT_PURPOSE, 0.0),
            other_use=-book.edge_goods_net(EDGE_CONSUMPTION, good) - known,
            spoilage=-book.edge_goods_net(EDGE_SPOILAGE, good),
            other_net_inflow=math.fsum(book.edge_goods_net(edge, good) for edge in other_edges),
            stock_at_start=stocks_at_start.get(good, 0.0),
            stock_change=stocks_now.get(good, 0.0) - stocks_at_start.get(good, 0.0),
            market_turnover=turnover.get(good, 0.0))
    return accounts


def _plant_wear(setup, record, ledger) -> Dict[str, float]:
    wear: Dict[str, float] = {}
    for producer_id, runs in sorted(ledger.plant_worn.items()):
        producer = record.producers.get(producer_id)
        recipe = setup.recipes[producer.recipe_id] if producer is not None else None
        if recipe is None or recipe.plant_life_years <= 0.0:
            continue
        for good, per_run in recipe.plant_goods.items():
            wear[good] = wear.get(good, 0.0) + per_run * runs
    return dict(sorted(wear.items()))


def basket_cost_per_head(record, prices: Mapping[str, float], people: float) -> float:
    """What the opening's basket (national quantities) costs per person at `prices`."""
    if people <= 0.0:
        return 0.0
    return math.fsum(quantity * prices.get(good, 0.0) for good, quantity in record.opening_basket.items()) / people


def _need_units(need, goods: Mapping[str, float], specs) -> float:
    return math.fsum(goods.get(good, 0.0) * effect for good, effect in need.goods
                     if not specs[good].service_life_years > 0.0)


def _cohorts(setup, record, ledger, prices) -> List[CohortAccount]:
    cost = basket_cost_per_head(record, prices, math.fsum(setup.opening_population_by_tile.values()))
    rows = []
    for cohort_id, cohort in sorted(record.cohorts.items()):
        need = next((spec for spec in setup.basket_for(cohort.tile).needs if spec.need_id == setup.hunger_need), None)
        if need is None or cohort.people <= 0.0:
            continue
        bought = _need_units(need, ledger.received.get(cohort_id, {}), setup.specs)
        own = _need_units(need, ledger.grown.get(cohort_id, {}), setup.specs)
        rows.append(CohortAccount(
            cohort=cohort_id, tile=cohort.tile, income_class=cohort.income_class, people=cohort.people,
            need_per_head=need.subsistence_per_person, eaten_per_head=(bought + own) / cohort.people,
            bought_per_head=bought / cohort.people, own_plot_per_head=own / cohort.people,
            real_income_per_head=cohort.last_year_income / cohort.people / cost if cost > 0.0 else math.nan))
    return rows


def _tiles(cohorts: List[CohortAccount]) -> List[TileAccount]:
    by_tile: Dict[str, List[CohortAccount]] = {}
    for cohort in cohorts:
        by_tile.setdefault(cohort.tile, []).append(cohort)
    rows = []
    for tile, members in sorted(by_tile.items()):
        people = math.fsum(member.people for member in members)
        rows.append(TileAccount(
            tile=tile, people=people,
            need_per_head=math.fsum(member.people * member.need_per_head for member in members) / people,
            eaten_per_head=math.fsum(member.people * member.eaten_per_head for member in members) / people))
    return rows


def _real_wages(setup, record, prices, wages) -> Dict[str, RealWage]:
    people = math.fsum(setup.opening_population_by_tile.values())
    now = basket_cost_per_head(record, prices, people)
    then = basket_cost_per_head(record, record.index_base_prices or setup.opening_prices, people)
    return {trade: RealWage(trade, wage, setup.opening_wages.get(trade, 0.0), now, then, setup.working_hours_per_year)
            for trade, wage in sorted(wages.items())}
