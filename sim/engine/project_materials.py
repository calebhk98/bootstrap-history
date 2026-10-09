"""What a project pays for materials: quantities in, current market price out.

A node declares only physical quantities. This module asks the material
market what the part you do not already hold would cost today, through the
same price pressure `quote material` and `buy material` use, and lets the
project pay that money at the start so the tonnes arrive in stock.
"""
import collections

from . import purchase_rule
from .material_units import tonnes_per_unit

# Integration points across a purchase, so a large order is priced along the
# whole price curve instead of at its first tonne.
_PRICE_SLICES = 24



class ProjectMaterialsMixin:
    def project_material_needs(self, node_id):
        """{material key: units} the project physically consumes, with the
        same fuel substitution the supply throttle applies."""
        needs = collections.Counter()
        coke = self.chosen_fuel(node_id) == "coke"
        for material, quantity in sorted(self.nodes[node_id]["mat"].items()):
            if coke and material in ("charcoal_kg", "firewood_kg"):
                needs["coal_kg"] += float(quantity) * self.COKE_PER_CHARCOAL
            else:
                needs[material] += float(quantity)
        return needs

    def _price_factor_across_purchase(self, emp_key, tag, already, tonnes):
        """Mean material_price_factor while buying `tonnes` more of a tag's
        commodity, after `already` tonnes bought in the same bill. Demand
        from the purchase is added to the tag's yearly demand, so it climbs
        the same capped quadratic curve as any other demand."""
        market = self._material_market_tonnes(emp_key)
        demand, worst_other = 0.0, 1.0
        for other_tag, need in self._demand_by_emp_key().get(emp_key, ()):
            if need <= 0:
                continue
            if other_tag == tag:
                demand += need
                continue
            supply = max(1e-9, self._own_material_supply(other_tag) + market)
            share = min(self.MATERIAL_PRICE_DEMAND_SHARE_CAP, need / supply)
            worst_other = max(worst_other, 1.0 + self.MATERIAL_PRICE_PRESSURE_SCALE * share * share)
        supply = max(1e-9, self._own_material_supply(tag) + market)
        cap = self.MATERIAL_PRICE_DEMAND_SHARE_CAP
        slices = _PRICE_SLICES if tonnes > 0 else 1
        total = 0.0
        for i in range(slices):
            bought = already + (tonnes * (i + 0.5) / slices if tonnes > 0 else 0.0)
            share = min(cap, (demand + bought) / supply) if demand + bought > 0 else 0.0
            total += 1.0 + self.MATERIAL_PRICE_PRESSURE_SCALE * share * share
        own_factor = total / slices
        return max(worst_other, own_factor) * self.material_freight_factor(emp_key)

    def material_purchase_cost(self, material, tonnes, already=0.0):
        """(money, mean money per tonne) to buy `tonnes` of a material now, the price rising as
        the order is filled. None when it has no price (see GoodsMarket.quote_buy)."""
        return self.goods_market.quote_buy(material, tonnes, already)

    def project_material_bill(self, node_id):
        """Per material: needed, held (stock and own output over the build),
        missing, and the market cost of the missing part. Callers must not
        change the returned dict: inside a view's bill scope it is shared."""
        return self._shared_bill(node_id, lambda: self._compute_material_bill(node_id))

    def _unclaimed_own_supply(self, tag, node_id):
        """Yearly own output of a material tag that no other running project has claimed."""
        claimed = sum(record.get("own_output_claim", {}).get(tag, 0.0)
                      for other, record in self.state.projects.active.items() if other != node_id)
        return max(0.0, self._own_material_supply(tag) - claimed)

    def project_own_output_claim(self, node_id):
        """{tag: tonnes a year} of the founder's own output this project draws, so the next
        project to start counts only what is left."""
        span = max(1.0, float(self.nodes[node_id].get("build_yrs")
                              or self.nodes[node_id].get("yrs") or 1.0))
        claim = collections.Counter()
        for row in self.project_material_bill(node_id)["rows"]:
            if row["held_from_own_output_tonnes"] > 0:
                claim[self._material_tag(row["material"])[1]] += row["held_from_own_output_tonnes"] / span
        return dict(claim)

    def _compute_material_bill(self, node_id):
        span = max(1.0, float(self.nodes[node_id].get("build_yrs")
                              or self.nodes[node_id].get("yrs") or 1.0))
        stock_left, own_left, headroom_left = {}, {}, {}
        bought = collections.Counter()
        rows, total = [], 0.0
        for material, units in sorted(self.project_material_needs(node_id).items()):
            emp_key, tag = self._material_tag(material)
            needed = units * tonnes_per_unit(material)
            stock_left.setdefault(emp_key, self.material_stock_t(emp_key))
            own_left.setdefault(tag, self._unclaimed_own_supply(tag, node_id) * span)
            from_stock = min(needed, stock_left[emp_key])
            stock_left[emp_key] -= from_stock
            from_own = min(needed - from_stock, own_left[tag])
            own_left[tag] -= from_own
            missing = needed - from_stock - from_own
            quoted = self.material_purchase_cost(material, missing, bought[emp_key, tag])
            cost, mean_price = quoted if quoted else (0.0, 0.0)
            bought[emp_key, tag] += missing
            deliverable_cost = cost
            lab_scale = material.endswith(self.LAB_SCALE_SUFFIX) and not material.endswith("_kg")
            headroom_left.setdefault(emp_key, self._material_market_tonnes(emp_key))
            deliverable = missing if lab_scale else min(missing, headroom_left[emp_key])
            if not lab_scale:
                headroom_left[emp_key] -= deliverable
            if quoted and missing > deliverable:
                # past a year's market supply the rest is bought over the following years at today's
                # quote, not all at once up the scarcity curve
                spot = self.material_purchase_cost(material, 0.0)
                deliverable_cost = (self.material_purchase_cost(material, deliverable, bought[emp_key, tag] - missing)[0]
                                    if deliverable > 0 else 0.0)
                cost = deliverable_cost + (missing - deliverable) * spot[1]
                mean_price = cost / missing
            total += cost
            rows.append({"material": material, "needed_tonnes": needed,
                         "held_tonnes": from_stock + from_own,
                         "held_from_stock_tonnes": from_stock,
                         "held_from_own_output_tonnes": from_own,
                         "missing_tonnes": missing,
                         "price_per_tonne": mean_price, "cost_of_missing": cost,
                         "cost_of_deliverable": deliverable_cost,
                         "deliverable_now_tonnes": deliverable,
                         "own_supply_tonnes_per_year": self._own_material_supply(tag),
                         "years_of_supply_it_takes": (
                             None if lab_scale or missing <= 0 else missing / max(
                                 1e-9, self._material_market_tonnes(emp_key)
                                 + self._own_material_supply(tag))),
                         "priced": quoted is not None})
        return {"rows": rows, "cost_of_missing": total}

    def _up_front_materials_money(self, node_id):
        """Money the start would spend now on the materials the market can
        deliver, or zero when the start could not pay it."""
        _total, up_front = self.project_material_parts(node_id)
        up_front *= self.opposition_factor(node_id) * self.geography.material_cost_factor(node_id)
        if up_front <= 0 or not purchase_rule.can_pay(self, up_front):
            return 0.0
        return up_front

    def settle_project_materials(self, node_id):
        """Buy the materials the market can deliver now (when the money can
        be raised) and return what is left to pay in instalments."""
        full = self.project_cost_now(node_id)
        if self._up_front_materials_money(node_id) <= 0:
            return full
        return full - self.buy_project_materials(node_id)

    def failure_bill(self, node_id):
        """The money bill the player bears for this project: the frozen bill
        once it runs, else what a start today would leave to pay after the
        up-front materials (which stay in stock and are not at risk)."""
        if node_id in self.state.projects.active:
            return self.project_cost(node_id)
        return self.project_cost_now(node_id) - self._up_front_materials_money(node_id)

    def failure_loss(self, node_id):
        """Money a failed attempt costs; the one figure `why` quotes and
        `_complete` charges."""
        if not self.nodes[node_id]["risk"]:
            return 0.0
        return max(0.0, self.failure_bill(node_id)) * self.FAILURE_RESET_SHARE

    def project_material_parts(self, node_id):
        """(cost of the missing materials, of which paid for at the start),
        both before the geography and opposition factors."""
        bill = self.project_material_bill(node_id)
        up_front = 0.0
        for row in bill["rows"]:
            if row["missing_tonnes"] > 0 and row["priced"]:
                up_front += row["cost_of_deliverable"]
        return bill["cost_of_missing"], up_front

    def project_cost_without_materials(self, node_id):
        """Labour and capital, with every factor except the material ones."""
        node = self.nodes[node_id]
        return ((node["_total_cost"] - node["_material_cost"]) * self.cost_money_factor()
                * self.civ_cost_factor(node_id) * self.rebuild_work_factor(node_id))

    def bounty_price(self, node_id):
        """A prize for the whole project: the multiplier times what this
        society would pay to build it today, before opposition."""
        return (self.project_cost_now(node_id) / self.opposition_factor(node_id)
                * self.BOUNTY_PRICE_MULTIPLIER)

    def buy_project_materials(self, node_id):
        """Pay for what the market can deliver now of the missing materials
        and bank it as stock. Returns the money paid."""
        factor = self.opposition_factor(node_id) * self.geography.material_cost_factor(node_id)
        market = self.goods_market
        paid = 0.0
        for row in self.project_material_bill(node_id)["rows"]:
            tonnes = row["deliverable_now_tonnes"]
            if tonnes <= 0 or not row["priced"]:
                continue
            money = row["cost_of_deliverable"] * factor
            market.settle_purchase(market.acting,self._material_tag(row["material"])[0], tonnes, money,
                                   "materials bought for projects")
            paid += money
        return paid

    def project_material_upfront_refusal(self, node_id):
        """Why the money for the materials due at the start cannot be raised."""
        _total, up_front = self.project_material_parts(node_id)
        up_front *= self.opposition_factor(node_id) * self.geography.material_cost_factor(node_id)
        if purchase_rule.can_pay(self, up_front):
            return None
        return purchase_rule.refusal_text(
            self, "the materials this project needs bought now", up_front)
