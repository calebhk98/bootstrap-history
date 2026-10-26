"""The ledger package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the legacy state it still needs

from .commands import ChangeStock, PayEdge, PayWages, ReceiveFromEdge
from . import rules
