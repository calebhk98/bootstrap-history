"""A project cannot start on a material no one in reach makes or sells.

A price needs a seller. A material with none has no price and cannot be bought, so work that needs more of it than the actor
holds waits for a seller to appear: a technique reached, a route opened, a partner that gains it."""
from typing import Any, Callable, List, Optional, Tuple

from sim.agents.api import research_gate
from sim.world.material_units import tonnes_per_unit


class Availability:
    """Needs: tree_nodes, can_be_bought, goods_stock."""

    def materials_without_a_seller(self, node_id: str, held_tonnes: Optional[Callable[[str], float]] = None) -> List[str]:
        """[material] the project would buy and no one in reach sells, sorted. Stock in hand covers a need;
        `held_tonnes(material)` says how much a buyer other than the seat holds."""
        node = self.needs.tree_nodes()[node_id]
        can_be_bought = self.needs.can_be_bought
        if not node.get("req_any") and all(can_be_bought[material] for material in node["mat"]):
            return []       # the common case, answered without working out the fuel substitution
        needs = self.project_material_needs(node_id)
        held = held_tonnes or (lambda material: self.needs.goods_stock[self.material_pool(material)[0]])
        return research_gate.materials_short_of_stock(
            {material: needs[material] * tonnes_per_unit(material) for material in needs},
            lambda material: can_be_bought[material], held)

    def start_gate_material_seller(self, node_id: str, node: Any, ignore_trade: bool, memo: Any, why: bool
                                   ) -> Optional[Tuple[bool, Optional[str]]]:
        """The start check that a project's materials have a seller: None when they do, else (False, the reason)."""
        unsold = self.materials_without_a_seller(node_id)
        if not unsold:
            return None
        return False, (("it needs %s, and no one in reach makes or sells it: it cannot be bought until a technique "
                        "that makes it is reached, a route opens to a partner that does, or a partner gains it"
                        % ", ".join(unsold)) if why else None)
