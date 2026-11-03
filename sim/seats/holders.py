"""Which seats hold or built a node."""
from typing import Any, List

from sim.assembly.api import Part

from . import builds


class Holders(Part):

    def seat_holders(self, node_id: str) -> List[str]:
        """Ids of the seats that hold `node_id` at all, built or granted."""
        return builds.holders_of(self.needs.techniques_by_seat(), node_id)

    def built_by_any_seat(self, among: Any) -> set:
        """Every node of `among` some seat built itself."""
        return builds.built_by_any(self.needs.techniques_by_seat(), among)
