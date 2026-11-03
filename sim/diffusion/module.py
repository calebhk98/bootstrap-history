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


class Diffusion(Module):

    PARTS = {
        "techniques": Techniques,
        "disclosure": Disclosure,
        "foreign": Foreign,
        "relief": Relief,
        "spread": Spread,
        "tech_effects": TechEffects,
        "trade_absorption": TradeAbsorption,
        "literacy": Literacy,
    }

    def advance_society(self, command: Any) -> None:
        """Once a year, on the society's own slow clock rather than a project's."""
        self.parts.literacy.advance_literacy(command.year)
        self.parts.trade_absorption.advance_trade_absorption(command.year)

    def staff_hire_advice(self, kind: str, count: Optional[int] = None) -> str:
        """The first answer to "I have no staff": hire somebody."""
        return rules.staff_hire_advice(kind, count)

    def staff_sources(self) -> Dict[str, List[Tuple[str, str]]]:
        return rules.staff_sources(self.needs.effect_terms("staff_advice"))
