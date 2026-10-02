"""The double-entry book: every agent's money (per currency) and goods (per good per tile).

Money and goods change hands only through `transfer` and `move` (or the batch forms), so each
posting has a counterparty. Edge accounts (types.is_edge) are the only ones that may go negative;
they are where the model meets what it does not simulate, and the sum over all accounts stays zero.
"""
import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from .types import EDGE_PREFIX, AgentId, CurrencyId, GoodId, GoodsMove, TileId, Transfer, is_edge


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
        for (agent, currency), value in money_after.items():
            _nested(self._money, agent)[currency] = value
        for (agent, good, tile), value in goods_after.items():
            self._set_stock(agent, good, tile, value)
        for transfer in transfers:
            self._record_money(transfer)
        for move in moves:
            self._record_goods(move)

    def _money_after(self, transfers: Sequence[Transfer]) -> Dict[Tuple[AgentId, CurrencyId], float]:
        after: Dict[Tuple[AgentId, CurrencyId], float] = {}
        moved: Dict[Tuple[AgentId, CurrencyId], float] = {}
        for transfer in transfers:
            amount = transfer.amount
            if not amount >= 0.0:
                raise NegativeAmount("transfer of %r %s (%s) is negative" % (amount, transfer.currency, transfer.purpose))
            for agent, signed in ((transfer.payer, -amount), (transfer.payee, amount)):
                key = (agent, transfer.currency)
                current = after[key] if key in after else self.balance(agent, transfer.currency)
                after[key] = current + signed
                moved[key] = moved.get(key, 0.0) + amount
        for (agent, currency), value in sorted(after.items()):
            if value < -ROUNDING_SHARE * moved[(agent, currency)] and not is_edge(agent):
                raise InsufficientFunds("%s would hold %.6g %s after the batch" % (agent, value, currency))
        return after

    def _goods_after(self, moves: Sequence[GoodsMove]) -> Dict[Tuple[AgentId, GoodId, TileId], float]:
        after: Dict[Tuple[AgentId, GoodId, TileId], float] = {}
        moved: Dict[Tuple[AgentId, GoodId, TileId], float] = {}
        for move in moves:
            quantity = move.quantity
            if not quantity >= 0.0:
                raise NegativeAmount("move of %r %s (%s) is negative" % (quantity, move.good, move.purpose))
            for agent, tile, signed in ((move.giver, move.tile, -quantity), (move.receiver, _delivery_tile(move), quantity)):
                key = (agent, move.good, tile)
                current = after[key] if key in after else self.stock(agent, move.good, tile)
                after[key] = current + signed
                moved[key] = moved.get(key, 0.0) + quantity
        for (agent, good, tile), value in sorted(after.items()):
            if value < -ROUNDING_SHARE * moved[(agent, good, tile)] and not is_edge(agent):
                raise InsufficientGoods("%s would hold %.6g %s on %s after the batch" % (agent, value, good, tile))
        return after

    def _set_stock(self, agent: AgentId, good: GoodId, tile: TileId, value: float) -> None:
        _nested(_nested(self._goods, agent), good)[tile] = value
        holders = self._holders.get(good)
        if holders is None:
            holders = self._holders[good] = set()
        holders.add(agent)

    def _record_money(self, transfer: Transfer) -> None:
        amount, currency = transfer.amount, transfer.currency
        self._gross_money[currency] = self._gross_money.get(currency, 0.0) + amount
        by_purpose = _nested(self._money_by_purpose, currency)
        by_purpose[transfer.purpose] = by_purpose.get(transfer.purpose, 0.0) + amount
        for agent, signed in ((transfer.payer, amount), (transfer.payee, -amount)):
            if agent.startswith(EDGE_PREFIX):
                volume = _nested(self._edge_money_volume, agent)
                volume[currency] = volume.get(currency, 0.0) + amount
                net = _nested(self._edge_money_net, agent)
                net[currency] = net.get(currency, 0.0) + signed

    def _record_goods(self, move: GoodsMove) -> None:
        quantity, good = move.quantity, move.good
        self._gross_goods[good] = self._gross_goods.get(good, 0.0) + quantity
        by_purpose = _nested(self._goods_by_purpose, good)
        by_purpose[move.purpose] = by_purpose.get(move.purpose, 0.0) + quantity
        for agent, signed in ((move.giver, quantity), (move.receiver, -quantity)):
            if agent.startswith(EDGE_PREFIX):
                volume = _nested(self._edge_goods_volume, agent)
                volume[good] = volume.get(good, 0.0) + quantity
                net = _nested(self._edge_goods_net, agent)
                net[good] = net.get(good, 0.0) + signed

    # ---- reads ---------------------------------------------------------------------------------

    def balance(self, agent: AgentId, currency: CurrencyId) -> float:
        purse = self._money.get(agent)
        return purse.get(currency, 0.0) if purse else 0.0

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
        return math.fsum(value for by_good in self._goods.values() for value in by_good.get(good, {}).values())

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

    def start_year(self) -> None:
        """Reset the yearly flow records; holdings carry."""
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

    def to_record(self) -> dict:
        return {
            "money": _sorted_nested(self._money),
            "goods": {agent: _sorted_nested(by_good) for agent, by_good in sorted(self._goods.items())},
            "gross_money": dict(sorted(self._gross_money.items())),
            "gross_goods": dict(sorted(self._gross_goods.items())),
            "money_by_purpose": _sorted_nested(self._money_by_purpose),
            "goods_by_purpose": _sorted_nested(self._goods_by_purpose),
            "edge_money_volume": _sorted_nested(self._edge_money_volume),
            "edge_money_net": _sorted_nested(self._edge_money_net),
            "edge_goods_volume": _sorted_nested(self._edge_goods_volume),
            "edge_goods_net": _sorted_nested(self._edge_goods_net),
        }

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
        return book
