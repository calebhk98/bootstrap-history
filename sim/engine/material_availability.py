"""A project cannot start on a material no one in reach makes or sells.

A price needs a seller (goods_market_offers.py). A material with none has no price and cannot be
bought, so work that needs more of it than the actor holds waits for a seller to appear: a technique
reached, a route opened, a partner that gains it."""
from sim.agents.api import research_gate

from .blockers import blocker_kind


def materials_without_a_seller(self, node_id, held_tonnes=None):
    """[material] the project would buy and no one in reach sells, sorted. Stock in hand covers a need;
    `held_tonnes(material)` says how much a buyer other than the founder holds."""
    from .material_units import tonnes_per_unit
    node = self.nodes[node_id]
    market = self.goods_market
    if not node.get("req_any") and all(market.can_be_bought(material) for material in node["mat"]):
        return []       # the common case, answered without working out the fuel substitution
    needs = self.project_material_needs(node_id)
    held = held_tonnes or (lambda material: self.material_stock_t(self._material_tag(material)[0]))
    return research_gate.materials_short_of_stock(
        {material: needs[material] * tonnes_per_unit(material) for material in needs}, market.can_be_bought, held)


@blocker_kind("supply")
def check_materials_have_a_seller(self, node_id, node, ignore_trade, _memo, _why):
    unsold = materials_without_a_seller(self, node_id)
    if not unsold:
        return None
    return False, (("it needs %s, and no one in reach makes or sells it: it cannot be bought until a technique "
                    "that makes it is reached, a route opens to a partner that does, or a partner gains it"
                    % ", ".join(unsold)) if _why else None)
