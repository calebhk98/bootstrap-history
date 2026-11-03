"""Once a year on the society's own clock, and the advice the society gives about staff."""
from typing import Any, Dict, List, Optional, Tuple

from sim.assembly.api import Part

from . import rules


class Society(Part):

    def advance_society(self, command: Any) -> None:
        """Once a year, on the society's own slow clock rather than a project's."""
        self.parts.literacy.advance_literacy(command.year)
        self.parts.trade_absorption.advance_trade_absorption(command.year)

    def staff_hire_advice(self, kind: str, count: Optional[int] = None) -> str:
        """The first answer to "I have no staff": hire somebody."""
        return rules.staff_hire_advice(kind, count)

    def staff_sources(self) -> Dict[str, List[Tuple[str, str]]]:
        return rules.staff_sources(self.needs.effect_terms("staff_advice"))
