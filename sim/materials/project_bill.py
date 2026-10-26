"""What a project pays for materials: quantities in, current market price out.

A node declares only physical quantities. The bill asks the market what the part the seat does not already hold would cost
today, at the economy's price on the founder's tile plus carriage, the price climbing over the order, and lets the project
pay that money at the start so the tonnes arrive in stock."""
import collections
from typing import Any, Dict, Optional, Tuple

from sim.agents.api import edges
from sim.ledger.api import ChangeStock, PayEdge
from sim.markets.api import NotePurchase
from sim.projects.api import constants as project_constants
from sim.world.material_units import tonnes_per_unit

from . import rules


class ProjectBill:
    """Needs: tree_nodes, legacy_projects, goods_stock, purchase_quote, shared_bill, opposition_factor,
    material_cost_factor, can_pay, purchase_refusal, project_cost, project_cost_now, cost_money_factor, civ_cost_factor,
    rebuild_work_factor, failure_reset_share. Sends PayEdge, NotePurchase, ChangeStock."""

    def project_material_needs(self, node_id: str) -> collections.Counter:
        """{material key: units} the project physically consumes, with the fuel substitution the throttle applies."""
        return rules.project_needs(self.needs.tree_nodes()[node_id], self.uses_coke(node_id))

    def project_material_bill(self, node_id: str) -> Dict[str, Any]:
        """Per material: needed, held (stock and own output over the build), missing, and the market cost of the missing
        part. Callers must not change the returned dict: inside a view's bill scope it is shared."""
        return self.needs.shared_bill(node_id, lambda: self.compute_material_bill(node_id))

    def compute_material_bill(self, node_id: str) -> Dict[str, Any]:
        needs = self.needs
        span = rules.build_span(needs.tree_nodes()[node_id])
        return rules.material_bill(self.project_material_needs(node_id), span, tonnes_per_unit, self.material_pool,
                                   lambda commodity: needs.goods_stock[commodity],
                                   lambda tag: self.unclaimed_own_supply(tag, node_id), needs.purchase_quote,
                                   self.market_tonnes, self.own_material_supply)

    def unclaimed_own_supply(self, tag: str, node_id: str) -> float:
        """Yearly own output of a supply pool that no other running project has claimed."""
        claimed = sum(record.get("own_output_claim", {}).get(tag, 0.0)
                      for other, record in self.needs.legacy_projects().active.items() if other != node_id)
        return rules.unclaimed(self.own_material_supply(tag), claimed)

    def project_own_output_claim(self, node_id: str) -> Dict[str, float]:
        """{tag: tonnes a year} of the seat's own output this project draws, so the next project to start counts only what
        is left."""
        span = rules.build_span(self.needs.tree_nodes()[node_id])
        claim: collections.Counter = collections.Counter()
        for row in self.project_material_bill(node_id)["rows"]:
            if row["held_from_own_output_tonnes"] > 0:
                claim[self.material_pool(row["material"])[1]] += row["held_from_own_output_tonnes"] / span
        return dict(claim)

    def project_material_parts(self, node_id: str) -> Tuple[float, float]:
        """(cost of the missing materials, of which paid for at the start), both before the geography and opposition factors."""
        return rules.bill_parts(self.project_material_bill(node_id))

    def project_cost_without_materials(self, node_id: str) -> float:
        """Labour and capital, with every factor except the material ones."""
        node = self.needs.tree_nodes()[node_id]
        needs = self.needs
        return ((node["_total_cost"] - node["_material_cost"]) * needs.cost_money_factor()
                * needs.civ_cost_factor(node_id) * needs.rebuild_work_factor(node_id))

    def up_front_materials_money(self, node_id: str) -> float:
        """Money the start would spend now on the materials the market can deliver, or zero when the start could not pay it."""
        _total, up_front = self.project_material_parts(node_id)
        up_front *= self.needs.opposition_factor(node_id) * self.needs.material_cost_factor(node_id)
        if up_front <= 0 or not self.needs.can_pay(up_front):
            return 0.0
        return up_front

    def settle_project_materials(self, command: Any) -> Tuple[float, float]:
        """Buy the materials the market can deliver now (when the money can be raised): (what is left to pay in
        instalments, the materials money paid now)."""
        node_id = command.node_id
        full = self.needs.project_cost_now(node_id)
        if self.up_front_materials_money(node_id) <= 0:
            return full, 0.0
        paid_now = self.buy_project_materials(node_id)
        return full - paid_now, paid_now

    def buy_project_materials(self, node_id: str) -> float:
        """Pay for what the market can deliver now of the missing materials and bank it as stock. Returns the money paid."""
        needs = self.needs
        factor = needs.opposition_factor(node_id) * needs.material_cost_factor(node_id)
        paid = 0.0
        for row in self.project_material_bill(node_id)["rows"]:
            tonnes = row["deliverable_now_tonnes"]
            if tonnes <= 0 or not row["priced"]:
                continue
            money = row["cost_of_deliverable"] * factor
            commodity = self.material_pool(row["material"])[0]
            needs.send(PayEdge(edges.EDGE_MARKET, money, "materials bought for projects"))
            needs.send(NotePurchase(commodity, tonnes))
            needs.send(ChangeStock(commodity, tonnes))
            paid += money
        return paid

    def failure_bill(self, node_id: str) -> float:
        """The money bill the player bears for this project: the frozen bill once it runs, else what a start today would
        leave to pay after the up-front materials (which stay in stock and are not at risk)."""
        if node_id in self.needs.legacy_projects().active:
            return self.needs.project_cost(node_id)
        return self.needs.project_cost_now(node_id) - self.up_front_materials_money(node_id)

    def failure_loss(self, node_id: str) -> float:
        """Money a failed attempt costs; the one figure `why` quotes and `_complete` charges."""
        if not self.needs.tree_nodes()[node_id]["risk"]:
            return 0.0
        return max(0.0, self.failure_bill(node_id)) * self.needs.failure_reset_share()

    def bounty_price(self, node_id: str) -> float:
        """A prize for the whole project: the multiplier times what this society would pay to build it today, before opposition."""
        return (self.needs.project_cost_now(node_id) / self.needs.opposition_factor(node_id)
                * project_constants.BOUNTY_PRICE_MULTIPLIER)

    def material_upfront_refusal(self, node_id: str) -> Optional[Any]:
        """Why the money for the materials due at the start cannot be raised, or None when it can."""
        _total, up_front = self.project_material_parts(node_id)
        up_front *= self.needs.opposition_factor(node_id) * self.needs.material_cost_factor(node_id)
        if self.needs.can_pay(up_front):
            return None
        return self.needs.purchase_refusal("the materials this project needs bought now", up_front)
