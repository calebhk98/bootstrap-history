"""What happened to each agent this year, gathered from the postings as the year runs.

Agents close their year from this: a producer from what it took in and paid out, a cohort from what
it received and earned, a merchant from what it bought where. It is rebuilt every year and not saved.
"""
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from .clearing_totals import MarketKey, market_totals
from .types import AgentId, ClearingResult, Fill, GoodId, GoodsMove, LabourResult, Transfer, EDGE_MINT, is_external_edge

SALE_PREFIX = "sale of "    # settlement's purpose for a goods sale


@dataclass
class YearLedger:
    money_out: Dict[AgentId, float] = field(default_factory=dict)
    wages_in: Dict[AgentId, float] = field(default_factory=dict)
    sales_in: Dict[AgentId, float] = field(default_factory=dict)
    received: Dict[AgentId, Dict[GoodId, float]] = field(default_factory=dict)
    hours_hired: Dict[AgentId, Dict[str, float]] = field(default_factory=dict)
    hours_hired_by_market: Dict[Tuple[AgentId, str, str], Tuple[float, float]] = field(default_factory=dict)   # (employer, trade, area): (hours paid for, money paid)
    crew_hours_bought: Dict[AgentId, Dict[Tuple[str, str], float]] = field(default_factory=dict)   # merchants that bid for crew: hours sold them by (trade, area)
    hours_sold: Dict[AgentId, float] = field(default_factory=dict)
    spare_hours: Dict[AgentId, float] = field(default_factory=dict)   # hours a household had left once its own plot took what the land it holds could
    grown: Dict[AgentId, Dict[GoodId, float]] = field(default_factory=dict)       # made for itself
    own_plot_hours: Dict[AgentId, Dict[str, float]] = field(default_factory=dict)   # hours worked on its own plot, by recipe
    grown_units: Dict[AgentId, Dict[str, float]] = field(default_factory=dict)    # need units of that
    buy_fills: Dict[AgentId, List[Fill]] = field(default_factory=dict)
    sold: Dict[Tuple[AgentId, GoodId], float] = field(default_factory=dict)
    output: Dict[Tuple[AgentId, GoodId], float] = field(default_factory=dict)
    clearings: List[ClearingResult] = field(default_factory=list)
    delivered_by_market: Dict[Tuple[GoodId, str], float] = field(default_factory=dict)   # (good, area): goods settlement moved
    totals_cache: Optional[Tuple[Dict[MarketKey, float], Dict[MarketKey, Optional[float]]]] = field(default=None, repr=False, compare=False)
    mint_takes: List[Tuple[ClearingResult, Dict[Tuple[AgentId, str], float]]] = field(default_factory=list)   # clearing, units delivered to the mint by (seller, tile)
    pending_mint_takes: Dict[Tuple[AgentId, str], float] = field(default_factory=dict, repr=False)
    labour_results: List[LabourResult] = field(default_factory=list)
    imports_paid: Dict[Tuple[AgentId, GoodId], float] = field(default_factory=dict)       # money paid to foreign partners
    carried_in: Dict[Tuple[AgentId, str], float] = field(default_factory=dict)   # (carrier, source country): value at the source of what it carried into the home country (the tariff rides on it)
    exports_received: Dict[Tuple[AgentId, GoodId], float] = field(default_factory=dict)   # money received from them
    plant_spend: Dict[AgentId, float] = field(default_factory=dict)    # paid for plant goods, a build not a running cost
    plant_worn: Dict[AgentId, float] = field(default_factory=dict)     # runs of capacity that wore out this year
    unmet_demand: Dict[Tuple[GoodId, str], float] = field(default_factory=dict)   # (good, area): quantity
    bids_by_market: Dict[Tuple[GoodId, str], list] = field(default_factory=dict)  # (good, area): the year's bids
    import_accounts: frozenset = frozenset()   # accounts whose sales are goods that crossed the border (customs)
    export_accounts: frozenset = frozenset()   # accounts whose purchases leave over the border
    migrated_by_tile: Dict[str, float] = field(default_factory=dict)   # net working people the labour market moved, by tile
    bonded_lots: list = field(default_factory=list)   # the lots as paid (bonded_purchase.settle)
    wage_floor_per_hour: float = 0.0       # what a worker's household costs less its plot, per hour, over the areas
    state_capacity: float = 1.0            # the year's share of its assessments the state's officials collect (`EconomyYearInputs.state_capacity`)

    def note_postings(self, postings: Iterable[object], purpose_kind: str = "") -> None:
        for posting in postings:
            if isinstance(posting, Transfer):
                self.money_out[posting.payer] = self.money_out.get(posting.payer, 0.0) + posting.amount
                self._note_foreign(posting)
                if purpose_kind == "wages":
                    self.wages_in[posting.payee] = self.wages_in.get(posting.payee, 0.0) + posting.amount
                elif purpose_kind == "sales":
                    self.sales_in[posting.payee] = self.sales_in.get(posting.payee, 0.0) + posting.amount
            elif isinstance(posting, GoodsMove) and purpose_kind == "sales":
                goods = self.received.setdefault(posting.receiver, {})
                goods[posting.good] = goods.get(posting.good, 0.0) + posting.quantity
                key = (posting.giver, posting.good)
                self.sold[key] = self.sold.get(key, 0.0) + posting.quantity
                if posting.receiver == EDGE_MINT:
                    taken = (posting.giver, posting.tile)
                    self.pending_mint_takes[taken] = self.pending_mint_takes.get(taken, 0.0) + posting.quantity

    def note_paid_outside_markets(self, postings: Iterable[Transfer]) -> None:
        """Money paid out in no market (rent, a bonded household's payments, the keep of bonded people): a cost of the payer's
        year, though it takes nothing from the payee's receipts."""
        for posting in postings:
            self.money_out[posting.payer] = self.money_out.get(posting.payer, 0.0) + posting.amount

    def note_wages_outside_markets(self, postings: Iterable[Transfer]) -> None:
        """Pay for work that was not bought in the labour market (a steward's pay): the payer's cost, the payee's wages."""
        postings = list(postings)
        self.note_paid_outside_markets(postings)
        for posting in postings:
            self.wages_in[posting.payee] = self.wages_in.get(posting.payee, 0.0) + posting.amount

    def note_plant_purchases(self, postings: Iterable[object], good: GoodId, plant_goods: Dict[AgentId, Iterable[GoodId]]) -> None:
        """Money producers paid, in the clearing of `good`, for goods their own plant is built from: what they paid the sellers. A seller paid
        nothing but paying to be rid of a negative-priced good is not a buyer, so only receivers of the goods count."""
        postings = list(postings)
        buyers = {posting.receiver for posting in postings if isinstance(posting, GoodsMove)}
        for posting in postings:
            if isinstance(posting, Transfer) and posting.payer in buyers and good in plant_goods.get(posting.payer, ()):
                self.plant_spend[posting.payer] = self.plant_spend.get(posting.payer, 0.0) + posting.amount

    def running_costs(self, agent: AgentId) -> float:
        """Money the agent paid out this year other than for building plant."""
        return max(0.0, self.money_out.get(agent, 0.0) - self.plant_spend.get(agent, 0.0))

    def _note_foreign(self, transfer: Transfer) -> None:
        """Money across the border, by the domestic party and the good named in the purpose: paid to a foreign edge,
        received from one, taken for a landed cargo's sale, or paid for a cargo bound abroad."""
        good = transfer.purpose[len(SALE_PREFIX):] if transfer.purpose.startswith(SALE_PREFIX) else transfer.purpose
        if is_external_edge(transfer.payee) and not is_external_edge(transfer.payer):
            key = (transfer.payer, good)
            self.imports_paid[key] = self.imports_paid.get(key, 0.0) + transfer.amount
        elif is_external_edge(transfer.payer) and not is_external_edge(transfer.payee):
            key = (transfer.payee, good)
            self.exports_received[key] = self.exports_received.get(key, 0.0) + transfer.amount
        elif transfer.payee in self.import_accounts and transfer.purpose.startswith(SALE_PREFIX):
            key = (transfer.payee, good)
            self.imports_paid[key] = self.imports_paid.get(key, 0.0) + transfer.amount
        elif transfer.payer in self.export_accounts and transfer.purpose.startswith(SALE_PREFIX):
            key = (transfer.payer, good)
            self.exports_received[key] = self.exports_received.get(key, 0.0) + transfer.amount

    def note_clearing(self, result: ClearingResult, delivered: float) -> None:
        """Keep a clearing and the goods its settlement delivered (less than it matched when a buyer could not pay)."""
        self.clearings.append(result)
        self.mint_takes.append((result, self.pending_mint_takes))
        self.pending_mint_takes = {}
        self.totals_cache = None
        market = (result.good, result.area)
        self.delivered_by_market[market] = self.delivered_by_market.get(market, 0.0) + delivered
        for fill in result.fills:
            if fill.side == "buy":
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
            self.totals_cache = market_totals(self.clearings, self.delivered_by_market)
        return self.totals_cache

    def note_labour(self, result: LabourResult, postings: Iterable[object] = (), settled: bool = True) -> None:
        """Hours count as hired and sold in proportion to the wages actually paid: hours an employer
        could not pay for are not delivered, so the workers keep them, and a settlement that paid nothing
        delivers no hours. A caller with no settlement passes `settled=False` and the fills count in full."""
        self.labour_results.append(result)
        postings = list(postings)
        paid_by: Dict[AgentId, float] = {}
        paid_to: Dict[AgentId, float] = {}
        for posting in postings:
            if isinstance(posting, Transfer):
                paid_by[posting.payer] = paid_by.get(posting.payer, 0.0) + posting.amount
                paid_to[posting.payee] = paid_to.get(posting.payee, 0.0) + posting.amount
        settled = settled and result.wage > 0.0
        for fill in result.fills:
            quantity = fill.quantity
            if settled:
                paid = paid_by if fill.side == "buy" else paid_to
                quantity = min(quantity, paid.get(fill.agent, 0.0) / result.wage)
                paid[fill.agent] = paid.get(fill.agent, 0.0) - quantity * result.wage
            if fill.side == "buy":
                trades = self.hours_hired.setdefault(fill.agent, {})
                trades[result.trade] = trades.get(result.trade, 0.0) + quantity
                market = (fill.agent, result.trade, result.area)
                bought, paid_money = self.hours_hired_by_market.get(market, (0.0, 0.0))
                self.hours_hired_by_market[market] = (bought + quantity, paid_money + quantity * fill.price)
            else:
                self.hours_sold[fill.agent] = self.hours_sold.get(fill.agent, 0.0) + quantity

    def note_output(self, agent: AgentId, moves: Iterable[GoodsMove]) -> None:
        for move in moves:
            if move.receiver == agent:
                key = (agent, move.good)
                self.output[key] = self.output.get(key, 0.0) + move.quantity
