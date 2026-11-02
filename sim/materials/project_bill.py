"""What a project pays for materials: quantities in, current market price out.

A node declares only physical quantities. The bill asks the market what the part the seat does not already hold would cost
today, at the economy's price on the founder's tile plus carriage, the price climbing over the order, and posts the buy
orders for it at the start; the tonnes arrive in stock at the year's clearing, and the project waits for them (sim/projects)."""
import collections
from typing import Any, Dict, Optional, Tuple

from sim.markets.api import BuyMaterial
from sim.refusal import Refusal
from sim.projects.api import constants as project_constants
from sim.world.material_units import tonnes_per_unit

from . import rules


class ProjectBill:
    """Needs: tree_nodes, active_projects, goods_stock, purchase_quote, shared_bill, opposition_factor,
    material_cost_factor, can_pay, purchase_refusal, project_cost, project_cost_now, cost_money_factor, civ_cost_factor,
    rebuild_work_factor, failure_reset_share. Sends BuyMaterial."""

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
                      for other, record in self.needs.active_projects().items() if other != node_id)
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
        """Money the start would put in orders for the materials the market can deliver, or zero when the start could not pay it."""
        _total, up_front = self.project_material_parts(node_id)
        up_front *= self.needs.opposition_factor(node_id) * self.needs.material_cost_factor(node_id)
        if up_front <= 0 or not self.needs.can_pay(up_front):
            return 0.0
        return up_front

    def settle_project_materials(self, command: Any) -> Tuple[float, float, list]:
        """Order the materials the market can deliver (when the money can be raised) for the year's clearing: (what is left to
        pay in instalments, the money of the orders posted at the full quote, one entry per order: {"material", "stock_key",
        "tonnes", "quoted"}, or the same with "refused" (a cause) for an order the market refused). The project's bill falls by
        the quoted money; the project settles it against what the clearing bought (sim/projects/materials_wait.py)."""
        node_id = command.node_id
        full = self.needs.project_cost_now(node_id)
        if self.up_front_materials_money(node_id) <= 0:
            return full, 0.0, []
        ordered, awaited = self.order_project_materials(node_id)
        return full - ordered, ordered, awaited

    def order_project_materials(self, node_id: str) -> Tuple[float, list]:
        """Post a buy order, tagged with the project, for the part of each missing material the market can deliver, at the
        quote as the limit. Returns (the money of the orders posted, with carriage and the geography and opposition factors,
        the entries ordered or refused)."""
        needs = self.needs
        factor = needs.opposition_factor(node_id) * needs.material_cost_factor(node_id)
        wanted = []
        for row in self.project_material_bill(node_id)["rows"]:
            tonnes = row["deliverable_now_tonnes"]
            if tonnes > 0 and row["priced"]:
                wanted.append((row["material"], tonnes, row["cost_of_deliverable"] / tonnes))
        return self.post_project_orders(node_id, wanted, factor)

    def post_project_orders(self, node_id: str, wanted: list, factor: float) -> Tuple[float, list]:
        """Post (material, tonnes, quoted money per tonne with carriage) as the project's orders; (money quoted, entries)."""
        ordered, entries = 0.0, []
        for material, tonnes, per_tonne in wanted:
            posted = self.needs.send(BuyMaterial(material, tonnes, per_tonne, node_id, factor, True))
            stock_key = self.material_pool(material)[0]
            if isinstance(posted, Refusal):
                entries.append({"material": material, "stock_key": stock_key, "tonnes": tonnes, "quoted": 0.0,
                                "refused": posted.cause, "refused_text": str(posted)})
                continue
            ordered += posted["committed_money"]
            entries.append({"material": material, "stock_key": stock_key, "tonnes": posted["tonnes"],
                            "quoted": posted["committed_money"]})
        return ordered, entries

    def reorder_project_materials(self, command: Any) -> Tuple[float, list]:
        """Order again what the clearing left short for a project: `command.shortfalls` is ((material, tonnes), ...), each
        priced at today's quote. Answers (the money quoted, the entries ordered or refused)."""
        needs = self.needs
        factor = needs.opposition_factor(command.node_id) * needs.material_cost_factor(command.node_id)
        wanted, entries = [], []
        for material, tonnes in command.shortfalls:
            quoted = needs.purchase_quote(material, tonnes)
            if quoted is None:
                entries.append({"material": material, "stock_key": self.material_pool(material)[0], "tonnes": tonnes, "quoted": 0.0,
                                "refused": "no_price", "refused_text": "%s has no price here, so it cannot be ordered." % material})
            else:
                wanted.append((material, tonnes, quoted[1]))
        ordered, posted = self.post_project_orders(command.node_id, wanted, factor)
        return ordered, entries + posted

    def failure_bill(self, node_id: str) -> float:
        """The money bill the player bears for this project: the frozen bill once it runs, else what a start today would
        leave to pay after the up-front materials (which stay in stock and are not at risk)."""
        if node_id in self.needs.active_projects():
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
