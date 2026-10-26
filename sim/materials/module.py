"""The materials module: the supply and demand of raw materials, the resource throttle, electricity, how a material reaches
the seat, and what a project pays for its materials."""
from typing import Any, Dict, Optional, Tuple

from sim.assembly.api import Module

from .availability import Availability
from .demand import Demand
from .electricity import Electricity
from .project_bill import ProjectBill
from .supply import Supply
from .throttle import Throttle


class Materials(Supply, Demand, Electricity, Throttle, ProjectBill, Availability, Module):
    def setup(self) -> None:
        self._readings: Dict[Any, Any] = {}        # seat id -> what is remembered for that seat (demand tables, last reading)
        self._annual_keys: Optional[Tuple] = None   # (active projects, done version) the last annual demand was worked out for
        self._standing: Optional[Tuple] = None      # (done version, done set, what the finished installations keep drawing)
        self._done_memo: Optional[Tuple] = None     # (stamp, done set, answers) while the techniques held are unchanged
        self._running_tables: Optional[Tuple] = None   # (projects, stamp, tree, tables) while what is built and run is unchanged
        self._coppice: Optional[Tuple] = None       # (tiles held, mean stem wood increment of them)
        self._load_ids: Any = None                  # nodes that need generated electricity; the tree does not change in a run

    # ---- views that read the seat's saved reading ----

    def binding(self) -> Optional[str]:
        """The pool that limited the seat's work in the last reading, or None."""
        return self.seat.binding

    def last_throttle(self) -> float:
        """The share of planned work the last reading let run."""
        return self.seat.throttle

    def shortages(self) -> Any:
        """Readings in which each pool bound the pace (the live counter)."""
        return self.seat.shortages

    def material_commodity(self, material: str) -> str:
        """The commodity key a material is held under in the tonnes ledger."""
        return self.material_pool(material)[0]

    def national_output(self, commodity: str) -> Tuple[float, float]:
        """(tonnes a year the whole society produces of a commodity, the population that figure is stated for)."""
        default = self.needs.default_population()
        reference = default if commodity in self.needs.empire_output() else float(self.needs.civilisation().get("population") or default)
        return self.national_output_tonnes(commodity), reference
