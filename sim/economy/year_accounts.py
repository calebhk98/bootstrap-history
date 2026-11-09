"""The year's accounts: what was made, used up in making, eaten, built and left in stock, good by good, and
how well each cohort ate and was paid. Read from the year's own book flows, stocks and ledger, not from the
engine's real-output measure (Complaint 554). Nothing here changes the economy."""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional

from .year_accounts_columns import column, row_columns, sum_across, summed_by_key
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
    wage_per_hour_opening: Optional[float]      # None when the opening paid this trade no wage
    basket_cost_per_head: Optional[float]       # the opening's basket per head at this year's prices; None when a good is unpriced
    basket_cost_per_head_opening: Optional[float]   # the same at the prices the price level is based on
    working_hours_per_year: float

    @property
    def real_wage_index(self) -> float:
        """Baskets a wage buys over the baskets the opening's wage bought: one at the opening."""
        figures = (self.basket_cost_per_head, self.wage_per_hour_opening, self.basket_cost_per_head_opening)
        if None in figures or min(figures) <= 0.0:
            return math.nan
        return (self.wage_per_hour / self.basket_cost_per_head) / (
            self.wage_per_hour_opening / self.basket_cost_per_head_opening)

    @property
    def baskets_per_working_year(self) -> float:
        return (self.wage_per_hour * self.working_hours_per_year / self.basket_cost_per_head
                if self.basket_cost_per_head is not None and self.basket_cost_per_head > 0.0 else math.nan)


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


def plain_rows(view) -> Dict[str, Dict[str, float]]:
    """A ledger's agent -> (sub -> amount) view as plain dicts, read from its table in one pass (a plain mapping in a test is copied)."""
    block = getattr(view, "as_plain", None)
    return block() if block is not None else {name: dict(rows.items()) for name, rows in view.items()}


def _goods(setup, record, ledger, stocks_at_start) -> Dict[str, GoodAccount]:
    book = record.book
    stocks_now = stocks(book)
    other_edges = [edge for edge in book.edge_goods_agents()
                   if edge not in (EDGE_PRODUCTION, EDGE_CONSUMPTION, EDGE_SPOILAGE)]
    cohort_ids = list(record.cohorts)
    bought = summed_by_key(*row_columns(plain_rows(ledger.received), cohort_ids))
    grown = summed_by_key(*row_columns(plain_rows(ledger.grown), cohort_ids))
    delivered = ledger.delivered_by_market.items()     # what traded is what was delivered
    turnover = summed_by_key([good for (good, _area), _quantity in delivered], [quantity for _market, quantity in delivered])
    names = sorted(set(stocks_now) | set(stocks_at_start) | set(turnover) | set(setup.specs))
    nets = {edge: column(book.edge_goods_net_by_good(edge), names)
            for edge in (EDGE_PRODUCTION, EDGE_CONSUMPTION, EDGE_SPOILAGE, *other_edges)}
    inputs, household_flows = book.flow_by_purpose(INPUT_PURPOSE, names), book.flow_by_purpose(CONSUMPTION_PURPOSE, names)
    wear, plant = book.flow_by_purpose(WEAR_PURPOSE, names), book.flow_by_purpose(PLANT_PURPOSE, names)
    grown_flows, state_flows = book.flow_by_purpose(GROWN_PURPOSE, names), book.flow_by_prefix(STATE_PURPOSE_PREFIX, names)
    others = sum_across([nets[edge] for edge in other_edges], len(names))
    columns = zip(names, nets[EDGE_PRODUCTION], nets[EDGE_CONSUMPTION], nets[EDGE_SPOILAGE], others, inputs, household_flows, wear, plant,
                  grown_flows, state_flows, column(grown, names), column(bought, names), column(stocks_at_start, names),
                  column(stocks_now, names), column(turnover, names))
    accounts = {}
    for (good, produced, consumed, spoiled, other_net, intermediate, household, worn, built, grown_flow, state, own, bought_here,
         start, now, traded) in columns:
        known = intermediate + household + worn + built + state
        share_grown = own / (own + bought_here) if own > 0.0 else 0.0
        accounts[good] = GoodAccount(
            production=produced, production_grown=grown_flow, intermediate_use=intermediate,
            final_consumption_bought=household * (1.0 - share_grown), final_consumption_grown=household * share_grown,
            durable_wear=worn, state_use=state, investment=built, other_use=-consumed - known, spoilage=-spoiled,
            other_net_inflow=other_net, stock_at_start=start, stock_change=now - start, market_turnover=traded)
    return accounts


def _plant_wear(setup, record, ledger) -> Dict[str, float]:
    wear: Dict[str, float] = {}
    for producer_id, runs in sorted(ledger.plant_worn.items()):
        recipe_id = record.producers.recipe_id_of(producer_id)
        recipe = setup.recipes[recipe_id] if recipe_id is not None else None
        if recipe is None or recipe.plant_life_years <= 0.0:
            continue
        for good, per_run in recipe.plant_goods.items():
            wear[good] = wear.get(good, 0.0) + per_run * runs
    return dict(sorted(wear.items()))


def basket_cost_per_head(goods, prices: Mapping[str, float], people: float) -> Optional[float]:
    """What the opening's basket (national quantities) costs per person at `prices`; None with no people or a
    basket good that has no price."""
    if people <= 0.0 or any(prices.get(good) is None for good in goods.opening_basket):
        return None
    return math.fsum(quantity * prices[good] for good, quantity in goods.opening_basket.items()) / people


def _hunger_need_units(need, specs):
    """The hunger need's (good, need units per unit of the good) for the goods that are used up, and what no good at all is worth
    (the sum of the zero terms)."""
    kept = [(good, effect) for good, effect in need.goods if not specs[good].service_life_years > 0.0]
    return kept, math.fsum(0.0 * effect for _good, effect in kept)


def _need_units(kept, nothing, quantities: Mapping[str, float]) -> float:
    """The need units of the goods a cohort got (`quantities` by good) over the `kept` goods of its need; `nothing` for no goods."""
    if not quantities:
        return nothing
    return math.fsum(quantities.get(good, 0.0) * effect for good, effect in kept)


def _cohorts(setup, record, ledger, prices) -> List[CohortAccount]:
    cost = basket_cost_per_head(record.goods, prices, math.fsum(setup.opening_population_by_tile.values()))
    received_by_cohort, grown_by_cohort = plain_rows(ledger.received), plain_rows(ledger.grown)
    needs_by_tile: Dict[str, tuple] = {}     # tile -> (hunger need or None, its kept goods, its zero); the basket is the tile's
    rows = []
    for cohort_id, cohort in sorted(record.cohorts.items()):
        if cohort.tile not in needs_by_tile:
            need = next((spec for spec in setup.basket_for(cohort.tile).needs if spec.need_id == setup.hunger_need), None)
            needs_by_tile[cohort.tile] = (need, None, None)
        need, kept, nothing = needs_by_tile[cohort.tile]
        if need is None or cohort.people <= 0.0:
            continue
        if kept is None:
            kept, nothing = _hunger_need_units(need, setup.specs)
            needs_by_tile[cohort.tile] = (need, kept, nothing)
        bought = _need_units(kept, nothing, received_by_cohort.get(cohort_id, {}))
        own = _need_units(kept, nothing, grown_by_cohort.get(cohort_id, {}))
        rows.append(CohortAccount(
            cohort=cohort_id, tile=cohort.tile, income_class=cohort.income_class, people=cohort.people,
            need_per_head=need.subsistence_per_person, eaten_per_head=(bought + own) / cohort.people,
            bought_per_head=bought / cohort.people, own_plot_per_head=own / cohort.people,
            real_income_per_head=cohort.last_year_income / cohort.people / cost if cost is not None and cost > 0.0 else math.nan))
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


def opening_wage_at_index_base(setup, record, trade: str) -> Optional[float]:
    """The setup's opening wage of `trade` in the money the index base prices stand in: the base is the prices when the
    spin-up was rebased, so the opening-year wage is scaled by the level the rebase kept (one before any rebase); None for a trade
    the setup opened with no wage."""
    wage = setup.opening_wages.get(trade)
    if wage is None:
        return None
    return wage * record.memory.opening_wage_levels.get(setup.currency_id, 1.0)


def _real_wages(setup, record, prices, wages) -> Dict[str, RealWage]:
    people = math.fsum(setup.opening_population_by_tile.values())
    now = basket_cost_per_head(record.goods, prices, people)
    then = basket_cost_per_head(record.goods, record.goods.index_base_prices or setup.opening_prices, people)
    return {trade: RealWage(trade, wage, opening_wage_at_index_base(setup, record, trade), now, then, setup.working_hours_per_year)
            for trade, wage in sorted(wages.items())}
