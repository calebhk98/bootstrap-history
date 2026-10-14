"""How a material reaches the founder: held, from the market, imported, makeable or unavailable.

The supply throttle counts what the market brings (deposits worked, producers' plants) and what a partner
imports. A good with none of these used to throttle work to the floor with no word on why. Each material is
placed on one route, so a shortage names its cause: nobody runs a producer of it yet, or no one in reach makes
or sells it at all (such work cannot start; see material_availability.py)."""
import math

from .goods_market_imports import HOME_SELLER

ROUTE_HELD = "held"
ROUTE_MARKET = "market"
ROUTE_IMPORTED = "imported"
ROUTE_MAKEABLE = "makeable"
ROUTE_UNAVAILABLE = "unavailable"


class MaterialReachMixin:

    def _material_import_tonnes(self, emp_key):
        """Tonnes a year a trading partner can still bring of `emp_key`; zero when the home society is its
        seller or no one is. A route with no lift limit brings what the partner makes."""
        market = self.goods_market
        seller = market.offered_by(emp_key)
        if seller is None or seller == HOME_SELLER:
            return 0.0
        left = market.import_tonnes_available(emp_key, seller)
        if left is None:
            return 0.0
        if not math.isfinite(left):
            left = self.foreign_supply_tonnes(seller, emp_key)
        return left if math.isfinite(left) else 0.0

    def _makers_of(self, material):
        """Ids of the technology-tree concerns whose output includes `material`, sorted."""
        return sorted(node_id for node_id, node in self.nodes.items()
                      if material in (node.get("_output_per_year") or {}))

    def material_supply_route(self, material):
        """{"route", "makers"} for a material key: how the founder gets it today.

        held: stock or the founder's own workings supply it. market: deposits or producers bring tonnes
        to the market. imported: a partner brings it. makeable: a seller is priced (a technique the
        society holds makes it) but no producer runs it yet. unavailable: no one in reach makes or sells
        it. `makers` lists the concerns of the tree that would make it."""
        emp_key, tag = self._material_tag(material)
        makers = self._makers_of(material)
        if self.material_stock_t(emp_key) > 0.0 or self._own_material_supply(tag) > 0.0:
            return {"route": ROUTE_HELD, "makers": makers}
        if self._material_market_tonnes(emp_key) - self._material_import_tonnes(emp_key) > 0.0:
            return {"route": ROUTE_MARKET, "makers": makers}
        if self._material_import_tonnes(emp_key) > 0.0:
            return {"route": ROUTE_IMPORTED, "makers": makers}
        if self.goods_market.can_be_bought(material):
            return {"route": ROUTE_MAKEABLE, "makers": makers}
        return {"route": ROUTE_UNAVAILABLE, "makers": makers}

    def material_unsupplied_sentence(self, material):
        """One sentence on why nothing of `material` reaches the founder, or "" when something does."""
        reach = self.material_supply_route(material)
        route = reach["route"]
        makers = [node_id for node_id in reach["makers"] if self.is_visible(node_id)]  # fog: name only known concerns
        if route == ROUTE_MAKEABLE:
            held = [node_id for node_id in makers if node_id in self.state.projects.done]
            if held:
                return ("No producer runs %s yet, though %s can make it: open it, or wait for a producer to "
                        "start." % (material, ", ".join(held[:3])))
            if makers:
                return ("No producer runs %s yet; %s would make it." % (material, ", ".join(makers[:3])))
            return ("No producer runs %s yet: a technique you hold makes it, but nothing is set up to, so "
                    "the work waits for a producer to start." % material)
        if route == ROUTE_UNAVAILABLE:
            return ("No one in reach makes or sells %s: it cannot be bought until a technique that makes it "
                    "is reached, a route opens to a partner that does, or a partner gains it." % material)
        return ""
