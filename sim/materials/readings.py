"""The materials module's views that read the seat's saved reading and the commodity a material is held under."""
from typing import Any, Optional, Tuple

from sim.assembly.api import Part


class Readings(Part):

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
        return self.parts.supply.material_pool(material)[0]

    def national_output(self, commodity: str) -> Tuple[float, float]:
        """(tonnes a year the whole society produces of a commodity, the population that figure is stated for)."""
        default = self.needs.default_population()
        reference = default if commodity in self.needs.empire_output() else float(self.needs.civilisation().get("population") or default)
        return self.parts.supply.national_output_tonnes(commodity), reference
