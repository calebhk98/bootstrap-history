"""What a project pays for materials: quantities in, current market price out.

A node declares only physical quantities. This module asks the material
market what the part you do not already hold would cost today, through the
same price pressure `quote material` and `buy material` use, and lets the
project pay that money at the start so the tonnes arrive in stock.
"""
import collections

from . import purchase_rule
from sim.unit_conversions import KILOGRAMS_PER_TONNE

# Integration points across a purchase, so a large order is priced along the
# whole price curve instead of at its first tonne.
_PRICE_SLICES = 24
_GRAMS_PER_TONNE = 1.0e6


def tonnes_per_unit(material):
    """Tonnes in one unit of a material key: the tree's gram keys are grams,
    every other key is counted in thousands of units to the tonne."""
    if material.endswith("_g") and not material.endswith("_kg"):
        return 1.0 / _GRAMS_PER_TONNE
    return 1.0 / KILOGRAMS_PER_TONNE


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
        """(money, mean money per tonne) to buy `tonnes` of a material now,
        the price rising as the order is filled. None when it has no price."""
        unit_price = self._book_price_per_kg(material)
        if unit_price is None:
            return None
        emp_key, tag = self._material_tag(material)
        per_tonne = unit_price / tonnes_per_unit(material) * self.price_index
        factor = self._price_factor_across_purchase(emp_key, tag, already, max(0.0, tonnes))
        return per_tonne * factor * max(0.0, tonnes), per_tonne * factor

    def project_material_bill(self, node_id):
        """Per material: needed, held (stock and own output over the build),
        missing, and the market cost of the missing part."""
        span = max(1.0, float(self.nodes[node_id].get("build_yrs")
                              or self.nodes[node_id].get("yrs") or 1.0))
        stock_left, own_left, headroom_left = {}, {}, {}
        bought = collections.Counter()
        rows, total = [], 0.0
        for material, units in sorted(self.project_material_needs(node_id).items()):
            emp_key, tag = self._material_tag(material)
            needed = units * tonnes_per_unit(material)
            stock_left.setdefault(emp_key, self.material_stock_t(emp_key))
            own_left.setdefault(tag, self._own_material_supply(tag) * span)
            from_stock = min(needed, stock_left[emp_key])
            stock_left[emp_key] -= from_stock
            from_own = min(needed - from_stock, own_left[tag])
            own_left[tag] -= from_own
            missing = needed - from_stock - from_own
            quoted = self.material_purchase_cost(material, missing, bought[emp_key, tag])
            cost, mean_price = quoted if quoted else (0.0, 0.0)
            bought[emp_key, tag] += missing
            lab_scale = material.endswith(self.LAB_SCALE_SUFFIX) and not material.endswith("_kg")
            headroom_left.setdefault(emp_key, self._material_market_tonnes(emp_key))
            deliverable = missing if lab_scale else min(missing, headroom_left[emp_key])
            if not lab_scale:
                headroom_left[emp_key] -= deliverable
            total += cost
            rows.append({"material": material, "needed_tonnes": needed,
                         "held_tonnes": from_stock + from_own,
                         "held_from_stock_tonnes": from_stock,
                         "held_from_own_output_tonnes": from_own,
                         "missing_tonnes": missing,
                         "price_per_tonne": mean_price, "cost_of_missing": cost,
                         "deliverable_now_tonnes": deliverable,
                         "priced": quoted is not None})
        return {"rows": rows, "cost_of_missing": total}

    def settle_project_materials(self, node_id):
        """Buy the materials the market can deliver now (when the money can
        be raised) and return what is left to pay in instalments."""
        full = self.project_cost_now(node_id)
        _total, up_front = self.project_material_parts(node_id)
        up_front *= self.opposition_factor(node_id) * self.material_cost_factor(node_id)
        if up_front <= 0 or not purchase_rule.can_pay(self, up_front):
            return full
        return full - self.buy_project_materials(node_id)

    def project_material_parts(self, node_id):
        """(cost of the missing materials, of which paid for at the start),
        both before the geography and opposition factors."""
        bill = self.project_material_bill(node_id)
        up_front = 0.0
        for row in bill["rows"]:
            if row["missing_tonnes"] > 0 and row["priced"]:
                up_front += row["cost_of_missing"] * (
                    row["deliverable_now_tonnes"] / row["missing_tonnes"])
        return bill["cost_of_missing"], up_front

    def project_cost_without_materials(self, node_id):
        """Labour and capital, with every factor except the material ones."""
        node = self.nodes[node_id]
        return ((node["_total_cost"] - node["_material_cost"]) * self.cost_money_factor()
                * self.civ_cost_factor(node_id))

    def buy_project_materials(self, node_id):
        """Pay for what the market can deliver now of the missing materials
        and bank it as stock. Returns the money paid."""
        factor = self.opposition_factor(node_id) * self.material_cost_factor(node_id)
        household = self.state.household
        opening = self._material_opening_stock()
        stock = self._material_stock()
        paid = 0.0
        for row in self.project_material_bill(node_id)["rows"]:
            tonnes = row["deliverable_now_tonnes"]
            if tonnes <= 0 or not row["priced"]:
                continue
            money = row["price_per_tonne"] * tonnes * factor
            emp_key = self._material_tag(row["material"])[0]
            household.capital -= money
            stock[emp_key] += tonnes
            opening[emp_key] = opening.get(emp_key, 0.0) + tonnes
            paid += money
        household._stock_throttle_sig = None
        return paid

    def project_material_upfront_refusal(self, node_id):
        """Why the money for the materials due at the start cannot be raised."""
        _total, up_front = self.project_material_parts(node_id)
        up_front *= self.opposition_factor(node_id) * self.material_cost_factor(node_id)
        if purchase_rule.can_pay(self, up_front):
            return None
        return purchase_rule.refusal_text(
            self, "the materials this project needs bought now", up_front)
