"""The diffusion module: how techniques and knowledge spread through the society and abroad, literacy, disclosure."""
from typing import Any, Dict, List, Optional, Tuple

from sim.assembly.api import Module

from . import rules
from .disclosure import Disclosure
from .foreign import Foreign
from .literacy import Literacy
from .relief import Relief
from .spread import Spread
from .tech_effects import TechEffects
from .techniques import Techniques
from .trades import TradeAbsorption


class Diffusion(Techniques, Disclosure, Foreign, Relief, Spread, TechEffects, TradeAbsorption, Literacy, Module):

    def setup(self) -> None:
        self._diffusible: Optional[Dict[str, Tuple[str, ...]]] = None   # category -> node ids, built on first ask
        self._foreign_only_memo: Dict[str, bool] = {}
        self._noted: Optional[tuple] = None      # (techniques in use, year) last stamped
        self._spread: Optional[tuple] = None     # the last answer of techniques_spread and what it was computed from

    def tree_node(self, node_id: str) -> Dict[str, Any]:
        """The tree's record of `node_id`; KeyError for an id the tree lacks."""
        node = self.needs.tree[node_id]
        if node is None:
            raise KeyError(node_id)
        return node

    def advance_society(self, command: Any) -> None:
        """Once a year, on the society's own slow clock rather than a project's."""
        self.advance_literacy(command.year)
        self.advance_trade_absorption(command.year)

    def staff_hire_advice(self, kind: str, count: Optional[int] = None) -> str:
        """The first answer to "I have no staff": hire somebody."""
        return rules.staff_hire_advice(kind, count)

    def staff_sources(self) -> Dict[str, List[Tuple[str, str]]]:
        return rules.staff_sources(self.needs.effect_terms("staff_advice"))
