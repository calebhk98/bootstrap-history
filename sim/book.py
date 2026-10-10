"""The double-entry book: every agent's money (per currency) and goods (per good per tile).

It is a top-level module because both the economy's agents and the actors' purses (`sim/agents/purses.py`)
keep their holdings in a book of this one class.

Money and goods change hands only through `transfer` and `move` (or the batch forms), so each
posting has a counterparty. Edge accounts (`is_edge`) are the only ones that may go negative;
they are where the model meets what it does not simulate, and the sum over all accounts stays zero.
"""
import math
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

AgentId = str
CurrencyId = str
GoodId = str
TileId = str

# Accounts that are the edge of the model: money and goods enter or leave through one of these, so every
# other agent's holdings change only by a transfer with a counterparty.
EDGE_PREFIX = "edge:"


def is_edge(agent_id: AgentId) -> bool:
    return agent_id.startswith(EDGE_PREFIX)


@dataclass(frozen=True)
class Transfer:
    payer: AgentId
    payee: AgentId
    currency: CurrencyId
    amount: float                    # never negative; reverse payer and payee instead
    purpose: str


@dataclass(frozen=True)
class GoodsMove:
    giver: AgentId
    receiver: AgentId
    good: GoodId
    tile: TileId
    quantity: float                  # never negative
    purpose: str


class BookError(Exception):
    """Base class for a refused posting."""


class NegativeAmount(BookError, ValueError):
    pass


class InsufficientFunds(BookError):
    pass


class InsufficientGoods(BookError):
    pass


@dataclass(frozen=True)
class DeliveredMove(GoodsMove):
    """A goods move whose receiver takes delivery on another tile (`tile` is where the giver holds it)."""
    receiver_tile: TileId = ""


@dataclass(frozen=True)
class ConservationReport:
    money: Dict[CurrencyId, float]      # |sum of all balances| / gross volume booked, per currency
    goods: Dict[GoodId, float]          # likewise per good
    breaches: Tuple[str, ...]           # the entries above the tolerance

    @property
    def ok(self) -> bool:
        return not self.breaches


def _nested(mapping: dict, key):
    inner = mapping.get(key)
    if inner is None:
        inner = mapping[key] = {}
    return inner


def _sorted_nested(mapping: dict) -> dict:
    return {key: dict(sorted(inner.items())) for key, inner in sorted(mapping.items())}


def _share(residual: float, gross: float) -> float:
    return abs(residual) / gross if gross > 0.0 else abs(residual)


def _delivery_tile(move: GoodsMove) -> TileId:
    return getattr(move, "receiver_tile", "") or move.tile


# Floating-point arithmetic leaves a payer a hair short of what it computed it could pay; a shortfall
# no bigger than this share of what moves is rounding, not an overdraft.
ROUNDING_SHARE = 1e-9
UNDERFLOW = sys.float_info.min   # below the smallest normal float a balance is rounding residue


class Book:
    def __init__(self):
        self._money: Dict[AgentId, Dict[CurrencyId, float]] = {}
        self._goods: Dict[AgentId, Dict[GoodId, Dict[TileId, float]]] = {}
        self._holders: Dict[GoodId, set] = {}                 # agents that have ever held the good
        self._gross_money: Dict[CurrencyId, float] = {}       # all postings ever, for conservation
        self._gross_goods: Dict[GoodId, float] = {}
        self._money_by_purpose: Dict[CurrencyId, Dict[str, float]] = {}   # this year
        self._goods_by_purpose: Dict[GoodId, Dict[str, float]] = {}
        self._edge_money_volume: Dict[AgentId, Dict[CurrencyId, float]] = {}
        self._edge_money_net: Dict[AgentId, Dict[CurrencyId, float]] = {}
        self._edge_goods_volume: Dict[AgentId, Dict[GoodId, float]] = {}
        self._edge_goods_net: Dict[AgentId, Dict[GoodId, float]] = {}
        self._supply_at_start: Dict[CurrencyId, float] = {}   # money supply when the year began

    # ---- postings ------------------------------------------------------------------------------

    def transfer(self, transfer: Transfer) -> None:
        amount = transfer.amount
        if not amount >= 0.0:
            raise NegativeAmount("transfer of %r %s (%s) is negative; reverse payer and payee"
                                 % (amount, transfer.currency, transfer.purpose))
        if amount == 0.0:
            return
        payer = transfer.payer
        if not is_edge(payer):
            balance = self.balance(payer, transfer.currency)
            if balance < amount * (1.0 - ROUNDING_SHARE):
                raise InsufficientFunds("%s holds %.6g %s but must pay %.6g (%s)"
                                        % (payer, balance, transfer.currency, amount, transfer.purpose))
        purses = self._money
        for agent, signed in ((payer, -amount), (transfer.payee, amount)):
            purse = purses.get(agent)
            if purse is None:
                purse = purses[agent] = {}
            purse[transfer.currency] = purse.get(transfer.currency, 0.0) + signed
        self._record_money(transfer)

    def move(self, move: GoodsMove) -> None:
        quantity = move.quantity
        if not quantity >= 0.0:
            raise NegativeAmount("move of %r %s (%s) is negative; reverse giver and receiver"
                                 % (quantity, move.good, move.purpose))
        if quantity == 0.0:
            return
        giver = move.giver
        held = self.stock(giver, move.good, move.tile)
        if not is_edge(giver) and held < quantity * (1.0 - ROUNDING_SHARE):
            raise InsufficientGoods("%s holds %.6g %s on %s but must give %.6g (%s)"
                                    % (giver, held, move.good, move.tile, quantity, move.purpose))
        self._set_stock(giver, move.good, move.tile, held - quantity)
        delivery = _delivery_tile(move)
        self._set_stock(move.receiver, move.good, delivery, self.stock(move.receiver, move.good, delivery) + quantity)
        self._record_goods(move)

    def transfer_many(self, transfers: Iterable[Transfer]) -> None:
        self.post(transfers, ())

    def move_many(self, moves: Iterable[GoodsMove]) -> None:
        self.post((), moves)

    def post(self, transfers: Iterable[Transfer], moves: Iterable[GoodsMove]) -> None:
        """Apply money transfers and goods moves together: all of them or none."""
        transfers, moves = list(transfers), list(moves)
        money_after = self._money_after(transfers)
        goods_after = self._goods_after(moves)
        purses = self._money
        for (agent, currency), value in money_after.items():
            purse = purses.get(agent)
            if purse is None:
                purse = purses[agent] = {}
            purse[currency] = value
        for (agent, good, tile), value in goods_after.items():
            self._set_stock(agent, good, tile, value)
        for transfer in transfers:
            self._record_money(transfer)
        for move in moves:
            self._record_goods(move)

    def _money_after(self, transfers: Sequence[Transfer]) -> Dict[Tuple[AgentId, CurrencyId], float]:
        after: Dict[Tuple[AgentId, CurrencyId], float] = {}
        before: Dict[Tuple[AgentId, CurrencyId], float] = {}
        moved: Dict[Tuple[AgentId, CurrencyId], float] = {}
        purses = self._money
        for transfer in transfers:
            amount = transfer.amount
            currency = transfer.currency
            if not amount >= 0.0:
                raise NegativeAmount("transfer of %r %s (%s) is negative" % (amount, currency, transfer.purpose))
            key = (transfer.payer, currency)
            if key in after:
                after[key] -= amount
                moved[key] += amount
            else:
                purse = purses.get(key[0])
                start = purse.get(currency, 0.0) if purse else 0.0
                before[key] = start
                after[key] = start - amount
                moved[key] = amount
            key = (transfer.payee, currency)
            if key in after:
                after[key] += amount
                moved[key] += amount
            else:
                purse = purses.get(key[0])
                start = purse.get(currency, 0.0) if purse else 0.0
                before[key] = start
                after[key] = start + amount
                moved[key] = amount
        # only an overdraft this batch makes or deepens fails: a residue an earlier, larger batch
        # was allowed to leave is not this batch's doing
        failing = [key for key, value in after.items()
                   if value < min(0.0, before[key]) - max(ROUNDING_SHARE * moved[key], UNDERFLOW) and not is_edge(key[0])]
        if failing:
            agent, currency = min(failing)
            raise InsufficientFunds("%s would hold %.6g %s after the batch" % (agent, after[(agent, currency)], currency))
        return after

    def _goods_after(self, moves: Sequence[GoodsMove]) -> Dict[Tuple[AgentId, GoodId, TileId], float]:
        after: Dict[Tuple[AgentId, GoodId, TileId], float] = {}
        before: Dict[Tuple[AgentId, GoodId, TileId], float] = {}
        moved: Dict[Tuple[AgentId, GoodId, TileId], float] = {}
        for move in moves:
            quantity = move.quantity
            good = move.good
            if not quantity >= 0.0:
                raise NegativeAmount("move of %r %s (%s) is negative" % (quantity, good, move.purpose))
            key = (move.giver, good, move.tile)
            if key in after:
                after[key] -= quantity
                moved[key] += quantity
            else:
                start = self.stock(*key)
                before[key] = start
                after[key] = start - quantity
                moved[key] = quantity
            key = (move.receiver, good, _delivery_tile(move))
            if key in after:
                after[key] += quantity
                moved[key] += quantity
            else:
                start = self.stock(*key)
                before[key] = start
                after[key] = start + quantity
                moved[key] = quantity
        failing = [key for key, value in after.items()
                   if value < min(0.0, before[key]) - max(ROUNDING_SHARE * moved[key], UNDERFLOW) and not is_edge(key[0])]
        if failing:
            agent, good, tile = min(failing)
            raise InsufficientGoods("%s would hold %.6g %s on %s after the batch" % (agent, after[(agent, good, tile)], good, tile))
        return after

    def _set_stock(self, agent: AgentId, good: GoodId, tile: TileId, value: float) -> None:
        by_good = self._goods.get(agent)
        if by_good is None:
            by_good = self._goods[agent] = {}
        by_tile = by_good.get(good)
        if by_tile is None:
            by_tile = by_good[good] = {}
        by_tile[tile] = value
        holders = self._holders.get(good)
        if holders is None:
            holders = self._holders[good] = set()
        holders.add(agent)

    def _record_money(self, transfer: Transfer) -> None:
        amount, currency, payer, payee = transfer.amount, transfer.currency, transfer.payer, transfer.payee
        gross = self._gross_money
        gross[currency] = gross.get(currency, 0.0) + amount
        by_purpose = self._money_by_purpose.get(currency)
        if by_purpose is None:
            by_purpose = self._money_by_purpose[currency] = {}
        purpose = transfer.purpose
        by_purpose[purpose] = by_purpose.get(purpose, 0.0) + amount
        if payer.startswith(EDGE_PREFIX):
            self._record_edge_money(payer, currency, amount, amount)
        if payee.startswith(EDGE_PREFIX):
            self._record_edge_money(payee, currency, amount, -amount)

    def _record_edge_money(self, agent: AgentId, currency: CurrencyId, amount: float, signed: float) -> None:
        volume = _nested(self._edge_money_volume, agent)
        volume[currency] = volume.get(currency, 0.0) + amount
        net = _nested(self._edge_money_net, agent)
        net[currency] = net.get(currency, 0.0) + signed

    def _record_goods(self, move: GoodsMove) -> None:
        quantity, good, giver, receiver = move.quantity, move.good, move.giver, move.receiver
        gross = self._gross_goods
        gross[good] = gross.get(good, 0.0) + quantity
        by_purpose = self._goods_by_purpose.get(good)
        if by_purpose is None:
            by_purpose = self._goods_by_purpose[good] = {}
        purpose = move.purpose
        by_purpose[purpose] = by_purpose.get(purpose, 0.0) + quantity
        if giver.startswith(EDGE_PREFIX):
            self._record_edge_goods(giver, good, quantity, quantity)
        if receiver.startswith(EDGE_PREFIX):
            self._record_edge_goods(receiver, good, quantity, -quantity)

    def _record_edge_goods(self, agent: AgentId, good: GoodId, quantity: float, signed: float) -> None:
        volume = _nested(self._edge_goods_volume, agent)
        volume[good] = volume.get(good, 0.0) + quantity
        net = _nested(self._edge_goods_net, agent)
        net[good] = net.get(good, 0.0) + signed

    # ---- reads ---------------------------------------------------------------------------------

    def balance(self, agent: AgentId, currency: CurrencyId) -> float:
        purse = self._money.get(agent)
        return purse.get(currency, 0.0) if purse else 0.0

    def knows(self, agent: AgentId) -> bool:
        """Whether the agent has ever held or paid anything in this book."""
        return agent in self._money or agent in self._goods

    def stock(self, agent: AgentId, good: GoodId, tile: TileId) -> float:
        by_good = self._goods.get(agent)
        if not by_good:
            return 0.0
        by_tile = by_good.get(good)
        return by_tile.get(tile, 0.0) if by_tile else 0.0

    def holdings(self, agent: AgentId) -> dict:
        money = {currency: value for currency, value in sorted(self._money.get(agent, {}).items()) if value != 0.0}
        goods = {}
        for good, by_tile in sorted(self._goods.get(agent, {}).items()):
            tiles = {tile: value for tile, value in sorted(by_tile.items()) if value != 0.0}
            if tiles:
                goods[good] = tiles
        return {"money": money, "goods": goods}

    def agents(self) -> List[AgentId]:
        return sorted(set(self._money) | set(self._goods))

    def holders_of(self, good: GoodId) -> List[AgentId]:
        """Agents (not edge accounts) holding some of the good."""
        return sorted(agent for agent in self._holders.get(good, ()) if not is_edge(agent)
                      if any(value != 0.0 for value in self._goods[agent][good].values()))

    def money_supply(self, currency: CurrencyId) -> float:
        return math.fsum(purse.get(currency, 0.0) for agent, purse in self._money.items() if not is_edge(agent))

    def total(self, currency: CurrencyId) -> float:
        return math.fsum(purse.get(currency, 0.0) for purse in self._money.values())

    def goods_total(self, good: GoodId) -> float:
        # fsum is exact, so visiting only the agents that ever held the good gives the same total
        goods = self._goods
        return math.fsum(value for agent in self._holders.get(good, ()) for value in goods[agent][good].values())

    # ---- flows this year -----------------------------------------------------------------------

    def money_flow(self, currency: CurrencyId) -> Dict[str, float]:
        """Gross money booked this year, by purpose."""
        return dict(sorted(self._money_by_purpose.get(currency, {}).items()))

    def goods_flow(self, good: GoodId) -> Dict[str, float]:
        return dict(sorted(self._goods_by_purpose.get(good, {}).items()))

    def edge_volume(self, edge_id: AgentId, currency: CurrencyId) -> float:
        """Gross money in and out through an edge account this year."""
        return self._edge_money_volume.get(edge_id, {}).get(currency, 0.0)

    def edge_net(self, edge_id: AgentId, currency: CurrencyId) -> float:
        """Money the edge paid into the economy this year, less what it took out."""
        return self._edge_money_net.get(edge_id, {}).get(currency, 0.0)

    def edge_goods_volume(self, edge_id: AgentId, good: GoodId) -> float:
        return self._edge_goods_volume.get(edge_id, {}).get(good, 0.0)

    def edge_goods_net(self, edge_id: AgentId, good: GoodId) -> float:
        return self._edge_goods_net.get(edge_id, {}).get(good, 0.0)

    def currencies(self) -> List[CurrencyId]:
        return sorted({currency for purse in self._money.values() for currency in purse})

    def supply_at_start(self, currency: CurrencyId) -> float:
        """The money supply (edge accounts excluded) when the year's flow records were last reset."""
        return self._supply_at_start.get(currency, 0.0)

    def edge_agents(self) -> List[AgentId]:
        """Edge accounts that carried money this year."""
        return sorted(self._edge_money_net)

    def start_year(self) -> None:
        """Reset the yearly flow records and note the supply; holdings carry."""
        self._supply_at_start = {currency: self.money_supply(currency) for currency in self.currencies()}
        self._money_by_purpose = {}
        self._goods_by_purpose = {}
        self._edge_money_volume = {}
        self._edge_money_net = {}
        self._edge_goods_volume = {}
        self._edge_goods_net = {}

    def check_conservation(self, tolerance_share: float) -> ConservationReport:
        """Residual of each currency and good, as a share of everything ever booked in it."""
        money = {currency: _share(self.total(currency), gross) for currency, gross in sorted(self._gross_money.items())}
        goods = {good: _share(self.goods_total(good), gross) for good, gross in sorted(self._gross_goods.items())}
        breaches = tuple(["money %s: %.3g" % item for item in money.items() if item[1] > tolerance_share]
                         + ["goods %s: %.3g" % item for item in goods.items() if item[1] > tolerance_share])
        return ConservationReport(money, goods, breaches)

    # ---- save file -----------------------------------------------------------------------------

    def to_record(self, only: Iterable[CurrencyId] = None, skip: Iterable[CurrencyId] = ()) -> dict:
        """The book as plain data; `only` keeps just those currencies (goods are left out then), `skip` drops some."""
        if only is None and not skip:
            return self._record_of(lambda currency: True, True, False)
        wanted = None if only is None else set(only)
        dropped = set(skip)
        return self._record_of(lambda currency: (wanted is None or currency in wanted) and currency not in dropped,
                               wanted is None, True)

    def _record_of(self, keep, with_goods: bool, filtered: bool) -> dict:
        def by_agent(mapping: dict) -> dict:
            out = {}
            for agent, by_currency in sorted(mapping.items()):
                kept = {currency: value for currency, value in sorted(by_currency.items()) if keep(currency)}
                if kept or not filtered:
                    out[agent] = kept
            return out

        def by_currency(mapping: dict) -> dict:
            return {currency: value for currency, value in sorted(mapping.items()) if keep(currency)}

        def purposes(mapping: dict) -> dict:
            return {currency: dict(sorted(inner.items())) for currency, inner in sorted(mapping.items()) if keep(currency)}

        return {
            "money": by_agent(self._money),
            "goods": {agent: _sorted_nested(by_good) for agent, by_good in sorted(self._goods.items())} if with_goods else {},
            "gross_money": by_currency(self._gross_money),
            "gross_goods": dict(sorted(self._gross_goods.items())) if with_goods else {},
            "money_by_purpose": purposes(self._money_by_purpose),
            "goods_by_purpose": _sorted_nested(self._goods_by_purpose) if with_goods else {},
            "edge_money_volume": by_agent(self._edge_money_volume),
            "edge_money_net": by_agent(self._edge_money_net),
            "edge_goods_volume": _sorted_nested(self._edge_goods_volume) if with_goods else {},
            "edge_goods_net": _sorted_nested(self._edge_goods_net) if with_goods else {},
            "supply_at_start": by_currency(self._supply_at_start),
        }

    def absorb(self, other: "Book") -> None:
        """Take over everything `other` holds and has booked, its currencies added to this book's."""
        def add_nested(into: dict, source: dict) -> None:
            for key, inner in source.items():
                held = _nested(into, key)
                for name, value in inner.items():
                    held[name] = held.get(name, 0.0) + value

        add_nested(self._money, other._money)
        for agent, by_good in other._goods.items():
            for good, by_tile in by_good.items():
                for tile, value in by_tile.items():
                    self._set_stock(agent, good, tile, self.stock(agent, good, tile) + value)
        for mine, theirs in ((self._gross_money, other._gross_money), (self._gross_goods, other._gross_goods),
                             (self._supply_at_start, other._supply_at_start)):
            for key, value in theirs.items():
                mine[key] = mine.get(key, 0.0) + value
        for mine, theirs in ((self._money_by_purpose, other._money_by_purpose),
                             (self._goods_by_purpose, other._goods_by_purpose),
                             (self._edge_money_volume, other._edge_money_volume),
                             (self._edge_money_net, other._edge_money_net),
                             (self._edge_goods_volume, other._edge_goods_volume),
                             (self._edge_goods_net, other._edge_goods_net)):
            add_nested(mine, theirs)

    @classmethod
    def from_record(cls, record: dict) -> "Book":
        book = cls()
        book._money = _sorted_nested(record["money"])
        book._goods = {agent: _sorted_nested(by_good) for agent, by_good in record["goods"].items()}
        for agent, by_good in book._goods.items():
            for good in by_good:
                book._holders.setdefault(good, set()).add(agent)
        book._gross_money = dict(record["gross_money"])
        book._gross_goods = dict(record["gross_goods"])
        book._money_by_purpose = _sorted_nested(record["money_by_purpose"])
        book._goods_by_purpose = _sorted_nested(record["goods_by_purpose"])
        book._edge_money_volume = _sorted_nested(record["edge_money_volume"])
        book._edge_money_net = _sorted_nested(record["edge_money_net"])
        book._edge_goods_volume = _sorted_nested(record["edge_goods_volume"])
        book._edge_goods_net = _sorted_nested(record["edge_goods_net"])
        book._supply_at_start = dict(record["supply_at_start"])
        return book
