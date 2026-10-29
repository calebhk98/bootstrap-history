"""The prices module: the calculator-backed price tables, cost books, the commodity catalogue and the memos keyed on what
is built and run. It owns no saved state; its caches are rebuilt on demand."""
from typing import Any, Dict, Optional, Tuple

from sim.assembly.api import Module

from .calculated import CalculatedViews
from .cost_books import CostBooks
from .memos import Memos
from .tables import Tables


class Prices(CalculatedViews, Tables, CostBooks, Memos, Module):
    def setup(self) -> None:
        self._schedule_by_content: Dict[str, Any] = {}       # opening wage schedule of a civilisation record, by its content
        self._partner_economies: Dict[str, Any] = {}         # what each partner makes and charges at its own opening
        self._reading_market_rate = False                    # set while the market rate is asked for: it may need these prices
        self._price_tables_cache: Optional[Tuple] = None     # (granted, in use, tables, granted count, (farmed, rate))
        self._incumbent_table_cache: Optional[Tuple] = None  # ((granted, farmed, rate), hours, basis)
        self._material_prices_cache: Optional[Tuple] = None  # (hours table, money per hour, prices)
        self._cost_book_cache: Optional[Tuple] = None        # (stamp, cost book, {ratios})
        self._done_store: Optional[Tuple] = None             # (stamp, done set, answers)
        self._producers_store: Optional[Tuple] = None        # (stamp, answers)
