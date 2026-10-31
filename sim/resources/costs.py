"""What sinking and running workings costs: the capital and the yearly running cost of a tonne from the deposits' physical
works at the miner's wage, the land ceiling a working can stand under, and a mine's quote.

Nothing here reads the price of what the mine raises; a material no deposit data describes is worked as a shallow seam of
itself."""
from typing import Any, Dict, Optional, Tuple

from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import deposits as deposit_model, mine_technique

from . import ceilings, rules
from .constants import (GENERIC_MINE_DEPTH_CLASS, GENERIC_MINE_HARDNESS_CLASS, MINE_CEILING_BASE_STRANGER,
                        MINE_CEILING_STATE_SCALE_STRANGER, MINE_LEAD_YEARS, REVENUE_SCALE_CAP_MULTIPLE,
                        REVENUE_SCALE_LABOUR_HOURS)
from .labour_profile import mine_labour_hours_per_tonne


class MineCosts:
    """Needs: deposit_catalogue, wage, material_price, price_index, money_per_labour_hour, revenue_estimate, effect_best,
    effect_terms, running, running_stamp, inspection_reach, mineral_scale, acting_balance, purchase_budget, affordable_units,
    afford_means."""

    def works_materials(self):
        return self.needs.deposit_catalogue()["works_priced_materials"]

    def mine_demand_goods(self, material: str) -> Tuple[str, ...]:
        """The goods whose annual demand a mine of `material` supplies: the catalogue row's list, else the key itself."""
        return self.needs.deposit_catalogue()["demand_goods"].get(material, (material,))

    def mine_trade(self) -> str:
        """The trade whose wage prices mine labour, from the map's parameters."""
        return self.needs.deposit_catalogue()["mining_trade"]

    def reference_deposits(self, material: str):
        """(deposit, weight) pairs describing a typical working of `material`."""
        if material in self.needs.deposit_catalogue()["metals"]:
            pool = deposit_model.load_deposits(material)
            total = sum(deposit.quantity_tonnes_per_year for deposit in pool)
            return [(deposit, deposit.quantity_tonnes_per_year / total) for deposit in pool]
        seam = deposit_model.Deposit(
            name="generic_" + material, metal=material, tile="", material_moved="ore",
            ore_grade_kg_per_tonne=KILOGRAMS_PER_TONNE, depth_class=GENERIC_MINE_DEPTH_CLASS,
            hardness_class=GENERIC_MINE_HARDNESS_CLASS, quantity_tonnes_per_year=1.0, note="")
        return [(seam, 1.0)]

    def mine_works_effects(self):
        """What the running mining techniques change in the physical works, kept while what is running does not change."""
        stamp = self.needs.running_stamp()
        kept = self._works_effects
        if kept is None or kept[0][0] is not stamp[0] or kept[0][1] != stamp[1] or kept[0][2] is not stamp[2]:
            effects = mine_technique.combine(spec for node_id, spec in self.needs.effect_terms("mine_works")
                                             if self.needs.running[node_id])
            kept = self._works_effects = (stamp, effects)
        return kept[1]

    def labour_hours_per_tonne(self, material: str) -> Tuple[float, float]:
        """(build hours per tonne/year, running hours per tonne) of a typical working of `material`, output-weighted across
        its deposits, under the running techniques' effects on the works."""
        return mine_labour_hours_per_tonne(self.reference_deposits(material), self.mine_works_effects())

    def capex_opex(self, material: str) -> Tuple[Optional[float], Optional[float]]:
        """(capital per t/yr to sink, running cost per t/yr) for standing production of `material`, from the deposits'
        physical works at the miner's wage. (None, None) for a name nothing prices."""
        if material not in self.works_materials():
            price = self.needs.material_price[material]
            if price is None or price <= 0:
                return None, None
        wage = self.needs.wage[self.mine_trade()]
        build_hours, running_hours = self.labour_hours_per_tonne(material)
        return build_hours * wage, running_hours * wage

    def mine_capex(self, material: str) -> Optional[float]:
        capex, _opex = self.capex_opex(material)
        return capex

    def mine_opex(self, material: str) -> float:
        _capex, opex = self.capex_opex(material)
        return 0.0 if opex is None else opex

    def mineable(self, material: str) -> bool:
        """Can standing production capacity be sunk in this material at all: any name something prices."""
        return self.mine_capex(self.needs.normalized_material[material]) is not None

    def mine_catalog_hint(self) -> str:
        return rules.catalog_hint(self.works_materials())

    def operating_cost_of(self, working: Dict[str, Any]) -> float:
        """What this working costs to run this year, whether or not its output is used."""
        return (working["capacity"] * self.mine_opex(working["material"]) * self.needs.price_index()
                * self.cost_scale_of(working))

    def mine_operating_cost(self) -> float:
        """The workings' running costs together, charged every year they stand."""
        return sum(self.operating_cost_of(working) for working in self.seat.mines)

    def operating_cost_new(self, material: str, tonnes: float) -> float:
        """What a freshly commissioned working of `tonnes` will be charged a year."""
        return self.operating_cost_of({"material": material, "capacity": tonnes, "intensity_yrs": 0.0})

    def revenue_scale(self) -> float:
        return REVENUE_SCALE_LABOUR_HOURS * self.needs.money_per_labour_hour()

    def mine_land_ceiling(self, material: str) -> float:
        """The largest standing capacity of this material that can be organised, in tonnes a year: what the state can run
        times whether the ore is under the ground held."""
        inspection_share = self.needs.inspection_reach()
        favour = self.needs.effect_best("mine_ceiling")
        return ceilings.mine_ceiling_tonnes(
            favour[1] if favour is not None else None, inspection_share, MINE_CEILING_BASE_STRANGER,
            MINE_CEILING_STATE_SCALE_STRANGER,
            ceilings.revenue_scale_multiple(self.needs.revenue_estimate(), self.revenue_scale(), REVENUE_SCALE_CAP_MULTIPLE),
            self.needs.mineral_scale[material])

    def mine_quote(self, material: str, tonnes_per_year: float) -> Optional[Dict[str, Any]]:
        """What a mine would cost before it is committed to; None for a name nothing prices."""
        material = self.needs.normalized_material[material]
        capex, _opex_per_tonne = self.capex_opex(material)
        if capex is None:
            return None
        tonnes = max(0.0, float(tonnes_per_year))
        scale = self.cost_scale_for_material(material)
        price_index = self.needs.price_index()
        sink = tonnes * capex * price_index * scale
        opex = self.operating_cost_new(material, tonnes)
        ceiling = self.mine_land_ceiling(material)
        room = max(0.0, ceiling - self.mine_capacity().get(material, 0.0) - self.seat.mine_pending.get(material, 0.0))
        depletion = self.mine_depletion(material)
        deposit_room = self.mine_room_in_deposits(material)
        if deposit_room is not None:
            room = min(room, deposit_room)
        note = ("The yearly cost is charged whether or not you use the "
                "output, and goes on until you close it. Mothballing is "
                "not free to reverse: the shaft floods and the crew "
                "disperses, so reopening means sinking it again.")
        if scale > 1.05:
            note += (" This costs %.0f%% of the book price: the easy ore "
                     "here is going." % (scale * 100))
        return {"material": material,
                "tonnes_per_year": round(tonnes, 3),
                "to_sink_it": round(sink, 1),
                "every_year_it_stands": round(opex, 1),
                "years_before_it_produces": MINE_LEAD_YEARS,
                "you_have": round(self.needs.acting_balance(), 1),
                "you_could_raise": round(self.needs.purchase_budget(), 1),
                "you_can_afford_about": min(room, self.needs.affordable_units(capex * price_index * scale, decimals=3)),
                "afford_means": self.needs.afford_means(),
                "the_ground_here_could_ever_support": round(ceiling, 1),
                "room_left_before_geology_stops_you": round(room, 1),
                "deposits_you_have_found": [
                    {"id": row["id"], "tile": row["tile_id"], "room_t_per_year": round(row["room_tonnes_per_year"], 1),
                     "left_t": round(row["remaining_tonnes"])} for row in self.found_deposits(material)],
                "current_yield_is_this_fraction_of_day_one": round(depletion, 3),
                "note": note}
