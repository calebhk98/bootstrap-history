"""What happened to each agent this year, gathered from the postings as the year runs.

Agents close their year from this: a producer from what it took in and paid out, a cohort from what
it received and earned, a merchant from what it bought where. It is rebuilt every year and not saved.

The figures live in tables (`year_ledger_tables.py`) keyed by the book's agent, good and purpose numbers and the market memory's
market numbers; `year_ledger_views.py` shows them as the dicts they used to be (`ledger.money_out["farm"]`), so a reader not yet
on the tables is unchanged. A converted caller hands the `note_*_arrays` entry points whole arrays of numbers instead. What the
tables do not hold yet is kept as before: the clearings, fills and bids (objects the goods side owns), the labour results, the
mint takes, and the small per-agent dicts nobody adds to in a loop (`crew_hours_bought`, `own_plot_hours`, `grown_units`,
`carried_in`)."""
from typing import Dict, Iterable, List, Optional, Tuple

import numpy

from .clearing_totals import MarketKey
from .goods_year_results import ArrayClearing
from .types import AgentId, ClearingResult, Fill, GoodId, GoodsMove, LabourResult, Transfer
from . import year_ledger_arrays as arrays
from .year_ledger_note_kernels import round_totals
from .year_ledger_store import LedgerTables
from .year_ledger_pair_views import NestedView, PairView
from .year_ledger_postings import PostingNotes
from .year_ledger_subs import ForeignSub, GoodSub, LabourMarketSub, TradeSub
from .year_ledger_tables import (HOURS, HOURS_SOLD, MONEY_OUT, OTHER_PURPOSE, OUTPUT, PAIR_KIND, PLANT_SPEND, PLANT_WORN, ROUNDS, SALES_IN,
                                 SALES_PURPOSE, SETTLEMENTS, SPARE_HOURS, WAGES_IN, WAGES_PURPOSE)
from .year_ledger_views import AgentFigureView, MarketFigureView


def _floats(values) -> numpy.ndarray:
    return numpy.asarray(values, dtype=numpy.float64)


def _flags(values) -> numpy.ndarray:
    return numpy.asarray(values, dtype=numpy.bool_)


class YearLedger(PostingNotes):
    def __init__(self, import_accounts: frozenset = frozenset(), export_accounts: frozenset = frozenset(), state_capacity: float = 1.0,
                 book=None, markets=None) -> None:
        """`book` and `markets` are the game's book and market memory tables (`record.book`, `record.memory.tables`), whose
        numberings the ledger's tables use; a ledger made without them numbers on its own, which is for a test."""
        self.tables = tables = LedgerTables(book, markets)
        figure = lambda name, number: AgentFigureView(tables, number, name)       # noqa: E731
        self.money_out = figure("money_out", MONEY_OUT)
        self.wages_in = figure("wages_in", WAGES_IN)
        self.sales_in = figure("sales_in", SALES_IN)
        self.plant_spend = figure("plant_spend", PLANT_SPEND)     # paid for plant goods, a build not a running cost
        self.plant_worn = figure("plant_worn", PLANT_WORN)        # runs of capacity that wore out this year
        self.hours_sold = figure("hours_sold", HOURS_SOLD)
        self.spare_hours = figure("spare_hours", SPARE_HOURS)     # hours a household had left once its own plot took what the land it holds could
        pairs = tables.pairs
        self.received = NestedView(tables, pairs["received"], GoodSub(tables))
        self.grown = NestedView(tables, pairs["grown"], GoodSub(tables))                 # made for itself
        self.hours_hired = NestedView(tables, pairs["hours_hired"], TradeSub(tables))
        self.sold = PairView(tables, pairs["sold"], GoodSub(tables))
        self.output = PairView(tables, pairs["output"], GoodSub(tables))
        self.imports_paid = PairView(tables, pairs["imports_paid"], ForeignSub(tables))      # money paid to foreign partners
        self.exports_received = PairView(tables, pairs["exports_received"], ForeignSub(tables))   # money received from them
        self.hours_hired_by_market = PairView(tables, pairs["hours_hired_by_market"], LabourMarketSub(tables))   # (employer, trade, area): (hours paid for, money paid)
        self.delivered_by_market = MarketFigureView(tables, 0, "delivered")     # (good, area): goods settlement moved
        self.unmet_demand = MarketFigureView(tables, 1, "unmet")              # (good, area): quantity
        self.crew_hours_bought: Dict[AgentId, Dict[Tuple[str, str], float]] = {}   # merchants that bid for crew: hours sold them by (trade, area)
        self.own_plot_hours: Dict[AgentId, Dict[str, float]] = {}   # hours worked on its own plot, by recipe
        self.grown_units: Dict[AgentId, Dict[str, float]] = {}    # need units of that
        self.buy_fills: Dict[AgentId, List[Fill]] = {}
        self.fill_watchers: Optional[frozenset] = None   # the buyers whose buy fills are kept (merchants and the state read them); None: all
        self.clearings: List[ClearingResult] = []
        self.totals_cache: Optional[Tuple[Dict[MarketKey, float], Dict[MarketKey, Optional[float]]]] = None
        self.mint_takes: List[Tuple[ClearingResult, Dict[Tuple[AgentId, str], float]]] = []   # clearing, units delivered to the mint by (seller, tile)
        self.pending_mint_takes: Dict[Tuple[AgentId, str], float] = {}
        self.labour_results: List[LabourResult] = []
        self.carried_in: Dict[Tuple[AgentId, str], float] = {}   # (carrier, source country): value at the source of what it carried into the home country (the tariff rides on it)
        self.bids_by_market: Dict[Tuple[GoodId, str], list] = {}  # (good, area): the year's bids
        self.import_accounts = import_accounts   # accounts whose sales are goods that crossed the border (customs)
        self.export_accounts = export_accounts   # accounts whose purchases leave over the border
        self.migrated_by_tile: Dict[str, float] = {}   # net working people the labour market moved, by tile
        self.bonded_lots: list = []   # the lots as paid (bonded_purchase.settle)
        self.wage_floor_per_hour = 0.0       # what a worker's household costs less its plot, per hour, over the areas
        self.state_capacity = state_capacity   # the year's share of its assessments the state's officials collect (`EconomyYearInputs.state_capacity`)

    # ---- whole arrays in: the entry points a converted caller uses (`year_ledger_arrays.py` says what each takes) ---------------

    def add_money_out(self, agents, amounts, positive_only: bool = False) -> None:
        self.tables.flush(SETTLEMENTS)
        arrays.add_money_out(self.tables, agents, amounts, positive_only)

    def add_pair_amounts(self, name: str, agents, subkeys, amounts, extras=arrays.NO_WHOLES, positive_only: bool = False) -> None:
        self.tables.flush(PAIR_KIND[name])
        arrays.add_pair_amounts(self.tables, name, agents, subkeys, amounts, extras, positive_only)

    def note_settlement_rows(self, *columns) -> None:
        """`arrays.note_settlement_rows` after the pending notes."""
        self.tables.flush(SETTLEMENTS)
        arrays.note_settlement_rows(self.tables, *columns)

    def note_hours_rows(self, *columns) -> None:
        """`arrays.note_hours_rows` after the pending notes."""
        self.tables.flush(HOURS)
        arrays.note_hours_rows(self.tables, *columns)

    def note_round_rows(self, markets, quantities, prices, moved) -> None:
        """`arrays.note_round_rows` after the pending notes; the market totals are worked out again."""
        self.tables.flush(ROUNDS)
        arrays.note_round_rows(self.tables, markets, quantities, prices, moved)
        self.totals_cache = None

    def note_settlement(self, settled, purpose_kind: str,
                        plant_goods: Optional[Dict[AgentId, Iterable[GoodId]]] = None) -> None:
        """`note_postings(settled.postings, purpose_kind)` from the settlement's per-agent sums: money paid out, wages or
        sales received, the foreign-money figures, and for a sale the goods received and sold and what the mint took. With
        `plant_goods`, also `note_plant_purchases` for the good sold. The rows wait in `tables.pending` until a read."""
        item, agents, pending = settled.item, settled.agents, self.tables.pending
        count = len(agents)
        sales = purpose_kind == "sales"
        pending.agents.extend(agents)
        pending.paid.extend(settled.paid)
        pending.received.extend(settled.received)
        pending.imports.extend(settled.imports)
        pending.exports.extend(settled.exports)
        pending.got_goods.extend(settled.got_goods)
        pending.goods_in.extend(settled.goods_in)
        pending.goods_out.extend(settled.goods_out)
        pending.purpose_kind.extend([WAGES_PURPOSE if purpose_kind == "wages" else SALES_PURPOSE if sales else OTHER_PURPOSE] * count)
        pending.good.extend([self.tables.book.good_number(item) if sales else -1] * count)
        template = reference = 0
        if any(settled.imports) or any(settled.exports):
            template, reference = self.tables.purpose_code(settled.purpose)
        pending.template.extend([template] * count)
        pending.reference.extend([reference] * count)
        if plant_goods is None:
            pending.plant_bought.extend([False] * count)
        else:
            pending.plant_bought.extend([bool(out > 0.0 and got and item in plant_goods.get(agent, ()))
                                         for agent, out, got in zip(agents, settled.paid, settled.got_goods)])
        pending.counts[SETTLEMENTS] += count
        if sales and settled.key_to_mint and max(settled.key_to_mint) > 0.0:
            for key, taken in zip(settled.keys, settled.key_to_mint):
                if taken > 0.0:
                    self.pending_mint_takes[key] = self.pending_mint_takes.get(key, 0.0) + taken

    def running_costs(self, agent: AgentId) -> float:
        """Money the agent paid out this year other than for building plant."""
        tables = self.tables
        tables.flush(SETTLEMENTS)
        number = tables.book.agent_ids.numbers.get(agent)
        if number is None:
            return 0.0
        figures = tables.figures
        try:
            paid = figures.money_out.item(number) if figures.order_money_out.item(number) else 0.0
            plant = figures.plant_spend.item(number) if figures.order_plant_spend.item(number) else 0.0
        except IndexError:
            return 0.0
        return max(0.0, paid - plant)

    def note_clearing(self, result: ClearingResult, delivered: float) -> None:
        """Keep a clearing and the goods its settlement delivered (less than it matched when a buyer could not pay)."""
        self.clearings.append(result)
        self.mint_takes.append((result, self.pending_mint_takes))
        self.pending_mint_takes = {}
        price, pending = result.price, self.tables.pending
        key = result.good + "|" + result.area
        market = self.tables.markets.goods_numbers.get(key)
        pending.round_market.append(self.tables.market_number(result.good, result.area) if market is None else market)
        pending.round_quantity.append(result.quantity)
        pending.round_price.append(numpy.nan if price is None else price)
        pending.round_moved.append(delivered)
        pending.counts[ROUNDS] += 1
        self.totals_cache = None
        watchers = self.fill_watchers
        if watchers is not None and isinstance(result, ArrayClearing):
            for agent, fills in result.bought_by(watchers).items():
                self.buy_fills.setdefault(agent, []).extend(fills)
            return
        for fill in result.fills:
            if fill.side == "buy" and (watchers is None or fill.agent in watchers):
                self.buy_fills.setdefault(fill.agent, []).append(fill)

    def settled_to_mint(self, result: ClearingResult) -> Optional[Dict[Tuple[AgentId, str], float]]:
        """Units the settlement of this clearing delivered to the mint, by (seller, tile); None for a clearing not noted."""
        for noted, takes in self.mint_takes:
            if noted is result:
                return takes
        return None

    def market_totals(self):
        """`clearing_totals.market_totals` of the year's clearings, worked out once until another clearing is noted."""
        if self.totals_cache is None:
            tables = self.tables
            tables.flush(ROUNDS)
            markets, quantity, price = round_totals(tables.rounds.market, tables.rounds.quantity, tables.rounds.price,
                                                    int(tables.rounds.row_count[0]), tables.market_figures.delivered,
                                                    tables.market_figures.order_delivered, int(tables.market_figures.row_count[0]))
            names = tables.markets.goods_markets.name_list
            keys = [(names[market].partition("|")[0], names[market].partition("|")[2]) for market in markets.tolist()]
            self.totals_cache = (dict(zip(keys, quantity.tolist())),
                                 {key: None if value != value else value for key, value in zip(keys, price.tolist())})
        return self.totals_cache

    def note_labour(self, result: LabourResult, postings: Iterable[object] = (), settled: bool = True) -> None:
        """Hours count as hired and sold in proportion to the wages actually paid: hours an employer
        could not pay for are not delivered, so the workers keep them, and a settlement that paid nothing
        delivers no hours. A caller with no settlement passes `settled=False` and the fills count in full."""
        paid_by: Dict[AgentId, float] = {}
        paid_to: Dict[AgentId, float] = {}
        for posting in postings:
            if isinstance(posting, Transfer):
                paid_by[posting.payer] = paid_by.get(posting.payer, 0.0) + posting.amount
                paid_to[posting.payee] = paid_to.get(posting.payee, 0.0) + posting.amount
        self.note_hours(result, paid_by, paid_to, settled)

    def note_labour_settled(self, result: LabourResult, done) -> None:
        """`note_labour` of a labour settlement (`settlement.settle_labour`), from its per-agent sums."""
        self.note_hours(result, done.paid_by, done.paid_to, True)

    def note_hours(self, result: LabourResult, paid_by: Dict[AgentId, float], paid_to: Dict[AgentId, float],
                   settled: bool) -> None:
        """The hours of a labour result as hired and sold, given the wages paid by each employer and to each worker."""
        self.labour_results.append(result)
        fills = result.fills
        if not fills:
            return
        pending, tables = self.tables.pending, self.tables
        settled = settled and result.wage > 0.0
        count = len(fills)
        slot_of: Dict[AgentId, int] = {}
        offset = len(pending.paid_by_slot)
        pending.fill_agents.extend([fill.agent for fill in fills])
        pending.fill_slot.extend([offset + slot_of.setdefault(fill.agent, len(slot_of)) for fill in fills])
        pending.fill_quantity.extend([fill.quantity for fill in fills])
        pending.fill_price.extend([fill.price for fill in fills])
        pending.fill_is_buy.extend([fill.side == "buy" for fill in fills])
        pending.fill_trade.extend([tables.trade_number(result.trade)] * count)
        pending.fill_market.extend([tables.labour_market_number(result.trade, result.area)] * count)
        pending.fill_wage.extend([result.wage] * count)
        pending.fill_settled.extend([settled] * count)
        pending.paid_by_slot.extend([paid_by.get(name, 0.0) for name in slot_of])
        pending.paid_to_slot.extend([paid_to.get(name, 0.0) for name in slot_of])
        pending.counts[HOURS] += count

    def note_output(self, agent: AgentId, moves: Iterable[GoodsMove]) -> None:
        pending = self.tables.pending
        for move in moves:
            if move.receiver == agent:
                pending.output_agents.append(agent)
                pending.output_goods.append(move.good)
                pending.output_quantity.append(move.quantity)
                pending.counts[OUTPUT] += 1
