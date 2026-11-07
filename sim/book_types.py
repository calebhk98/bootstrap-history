"""The book's posting types, refusals and constants: what a caller builds to post and what it catches."""
import sys
from dataclasses import dataclass
from typing import Dict, Tuple

AgentId = str
CurrencyId = str
GoodId = str
TileId = str

# Accounts that are the edge of the model: money and goods enter or leave through one of these, so every
# other agent's holdings change only by a transfer with a counterparty.
EDGE_PREFIX = "edge:"
EDGE_EXCHANGE = "edge:exchange"   # the actors' coin turned into the economy's unit and back


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


def _share(residual: float, gross: float) -> float:
    return abs(residual) / gross if gross > 0.0 else abs(residual)


def delivery_tile(move: GoodsMove) -> TileId:
    return getattr(move, "receiver_tile", "") or move.tile


# Floating-point arithmetic leaves a payer a hair short of what it computed it could pay; a shortfall
# no bigger than this share of what moves is rounding, not an overdraft.
ROUNDING_SHARE = 1e-9
UNDERFLOW = sys.float_info.min   # below the smallest normal float a balance is rounding residue
