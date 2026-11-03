"""The prices module: the calculator-backed price tables, cost books, the commodity catalogue and the memos keyed on what
is built and run. It owns no saved state; its caches are rebuilt on demand."""
from typing import Any, Dict, Optional, Tuple

from sim.assembly.api import Module

from .calculated import CalculatedViews
from .cost_books import CostBooks
from .memos import Memos
from .tables import Tables


class Prices(Module):

    PARTS = {
        "calculated_views": CalculatedViews,
        "tables": Tables,
        "cost_books": CostBooks,
        "memos": Memos,
    }
