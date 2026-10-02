"""What happened to each agent this year, gathered from the postings as the year runs.

Agents close their year from this: a producer from what it took in and paid out, a cohort from what
it received and earned, a merchant from what it bought where. It is rebuilt every year and not saved.
"""
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

from .types import EDGE_EXTERNAL, AgentId, ClearingResult, Fill, GoodId, GoodsMove, LabourResult, Transfer

SALE_PREFIX = "sale of "    # settlement's purpose for a goods sale


@dataclass
class YearLedger:
    money_in: Dict[AgentId, float] = field(default_factory=dict)
    money_out: Dict[AgentId, float] = field(default_factory=dict)
    wages_in: Dict[AgentId, float] = field(default_factory=dict)
    sales_in: Dict[AgentId, float] = field(default_factory=dict)
    received: Dict[AgentId, Dict[GoodId, float]] = field(default_factory=dict)
    hours_hired: Dict[AgentId, Dict[str, float]] = field(default_factory=dict)
    hours_sold: Dict[AgentId, float] = field(default_factory=dict)
    grown: Dict[AgentId, Dict[GoodId, float]] = field(default_factory=dict)       # made for itself
    grown_units: Dict[AgentId, Dict[str, float]] = field(default_factory=dict)    # need units of that
    buy_fills: Dict[AgentId, List[Fill]] = field(default_factory=dict)
    sold: Dict[Tuple[AgentId, GoodId], float] = field(default_factory=dict)
    output: Dict[Tuple[AgentId, GoodId], float] = field(default_factory=dict)
    clearings: List[ClearingResult] = field(default_factory=list)
    labour_results: List[LabourResult] = field(default_factory=list)
    unpaid: Dict[AgentId, float] = field(default_factory=dict)
    imports_paid: Dict[Tuple[AgentId, GoodId], float] = field(default_factory=dict)       # money paid to foreign partners
    exports_received: Dict[Tuple[AgentId, GoodId], float] = field(default_factory=dict)   # money received from them
    plant_spend: Dict[AgentId, float] = field(default_factory=dict)    # paid for plant goods, a build not a running cost
    unmet_demand: Dict[Tuple[GoodId, str], float] = field(default_factory=dict)   # (good, area): quantity

    def note_postings(self, postings: Iterable[object], purpose_kind: str = "") -> None:
        for posting in postings:
            if isinstance(posting, Transfer):
                self.money_in[posting.payee] = self.money_in.get(posting.payee, 0.0) + posting.amount
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

    def note_plant_purchases(self, moves: Iterable[object], price: float, plant_goods: Dict[AgentId, Iterable[GoodId]]) -> None:
        """Money producers paid this clearing for goods their own plant is built from."""
        for move in moves:
            if isinstance(move, GoodsMove) and move.good in plant_goods.get(move.receiver, ()):
                self.plant_spend[move.receiver] = self.plant_spend.get(move.receiver, 0.0) + move.quantity * price

    def running_costs(self, agent: AgentId) -> float:
        """Money the agent paid out this year other than for building plant."""
        return max(0.0, self.money_out.get(agent, 0.0) - self.plant_spend.get(agent, 0.0))

    def _note_foreign(self, transfer: Transfer) -> None:
        """Money through the external edge, by the domestic party and the good named in the purpose."""
        good = transfer.purpose[len(SALE_PREFIX):] if transfer.purpose.startswith(SALE_PREFIX) else transfer.purpose
        if transfer.payee == EDGE_EXTERNAL and transfer.payer != EDGE_EXTERNAL:
            key = (transfer.payer, good)
            self.imports_paid[key] = self.imports_paid.get(key, 0.0) + transfer.amount
        elif transfer.payer == EDGE_EXTERNAL and transfer.payee != EDGE_EXTERNAL:
            key = (transfer.payee, good)
            self.exports_received[key] = self.exports_received.get(key, 0.0) + transfer.amount

    def note_clearing(self, result: ClearingResult) -> None:
        self.clearings.append(result)
        for fill in result.fills:
            if fill.side == "buy":
                self.buy_fills.setdefault(fill.agent, []).append(fill)

    def note_labour(self, result: LabourResult, postings: Iterable[object] = ()) -> None:
        """Hours count as hired and sold in proportion to the wages actually paid: hours an employer
        could not pay for are not delivered, so the workers keep them. Without postings the fills count in full."""
        self.labour_results.append(result)
        postings = list(postings)
        paid_by: Dict[AgentId, float] = {}
        paid_to: Dict[AgentId, float] = {}
        for posting in postings:
            if isinstance(posting, Transfer):
                paid_by[posting.payer] = paid_by.get(posting.payer, 0.0) + posting.amount
                paid_to[posting.payee] = paid_to.get(posting.payee, 0.0) + posting.amount
        settled = bool(postings) and result.wage > 0.0
        for fill in result.fills:
            quantity = fill.quantity
            if settled:
                paid = paid_by if fill.side == "buy" else paid_to
                quantity = min(quantity, paid.get(fill.agent, 0.0) / result.wage)
                paid[fill.agent] = paid.get(fill.agent, 0.0) - quantity * result.wage
            if fill.side == "buy":
                trades = self.hours_hired.setdefault(fill.agent, {})
                trades[result.trade] = trades.get(result.trade, 0.0) + quantity
            else:
                self.hours_sold[fill.agent] = self.hours_sold.get(fill.agent, 0.0) + quantity

    def note_output(self, agent: AgentId, moves: Iterable[GoodsMove]) -> None:
        for move in moves:
            if move.receiver == agent:
                key = (agent, move.good)
                self.output[key] = self.output.get(key, 0.0) + move.quantity
