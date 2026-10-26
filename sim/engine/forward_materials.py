"""One-line forwarders from `Sim` to the materials module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself.
`wire_chain_report` is not a forwarder: it needs the commodity catalogue's propagation, which stays in the engine."""
from sim.prices.api import commodities as _commod


class ForwardMaterialsMixin:

    # ---- the catalogue and the supply ----

    def _material_tag(self, material):
        return self.view("material_pool")[material]

    def material_shortfall_t(self, material, by_tag=None):
        return self.view("material_shortfall")(material, by_tag)

    def _society_output_tonnes(self, commodity):
        return self.view("society_output")[commodity]

    def _material_market_tonnes(self, commodity):
        return self.view("material_market_tonnes")[commodity]

    def _own_material_supply(self, tag):
        return self.view("material_own_supply")[tag]

    def _own_production_tags(self):
        return self.view("own_production_tags")()

    def _demand_by_supply_tag(self, demand):
        return self.view("demand_by_supply_tag")(demand)

    def demand_and_own_supply_by_material(self, by_tag):
        return self.view("own_supply_by_commodity")(by_tag)

    @property
    def MATERIAL_CHECKS(self):
        return self.view("material_checks")()

    def annual_material_demand(self):
        return self.view("material_demand")()

    def material_price_factor(self, commodity):
        return self.view("material_price_factor")[commodity]

    def material_market_summary(self):
        return self.view("material_market_summary")()

    def material_unsupplied_sentence(self, material):
        return self.view("material_unsupplied_sentence")[material]

    def materials_report(self):
        return self.view("materials_report")()

    def wire_chain_report(self, wire_t_per_yr):
        """Would this shortfall in copper wire be a copper shortage, or is the wire-drawing bench the bottleneck? The
        catalogue's propagation, handed this seat's reachable copper in place of the national estimate."""
        supply_t = self._own_material_supply("mine:copper") + self._material_market_tonnes("copper")
        ledger = _commod.CommodityLedger(supply_override={"copper": supply_t})
        return ledger.propagate_demand("copper_wire", max(0.0, float(wire_t_per_yr)))

    # ---- the tonnes ledger ----

    def _material_stock(self):
        return self.view("held_goods")()

    def material_stock_t(self, commodity):
        return self.view("goods_stock")[commodity]

    # ---- the throttle and electricity ----

    def peek_resource_throttle(self):
        return self.view("resource_throttle")()

    def peek_project_resource_throttle(self, node_id):
        return self.view("resource_throttle")(node_id)

    def generation_breakdown_kw(self):
        return self.view("generation_breakdown")()

    def installed_generation_kw_by_tier(self):
        return self.view("generation_by_tier")()

    def _electricity_demand_kw(self):
        return self.view("electricity_demand")()

    # ---- what a project pays for materials ----

    def project_material_needs(self, node_id):
        return self.view("project_material_needs")[node_id]

    def project_material_bill(self, node_id):
        return self.view("project_material_bill")[node_id]

    def project_material_parts(self, node_id):
        return self.view("project_material_parts")[node_id]

    def project_cost_without_materials(self, node_id):
        return self.view("project_cost_without_materials")(node_id)

    def failure_loss(self, node_id):
        return self.view("failure_loss")(node_id)

    def bounty_price(self, node_id):
        return self.view("bounty_price")(node_id)
