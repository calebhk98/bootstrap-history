"""What would end a material shortage, in things the player can type: woodland for charcoal, nitre beds for saltpetre, a
working for what is dug, and a plain statement for what nothing the seat owns supplies."""
from typing import Any, Dict, Optional

from sim.unit_conversions import KILOGRAMS_PER_TONNE

from . import sizing
from .constants import NITRE_SHORTAGE_SAFETY_BUFFER, NITRE_YIELD_T_PER_M2


class Remedies:
    """Needs: material_demand, charcoal_per_hectare, material_shortfall, material_market_tonnes, goods_stock,
    material_unsupplied_sentence, price_index, area_text, mass_rate_text, mass_per_area_text, money_text."""

    def shortage_remedy_plan(self, binding: Optional[str], shortfall_t: Optional[float] = None) -> Dict[str, Any]:
        """{"text", "commands"} for what would end the shortage of `binding`; every command's size comes from
        `shortfall_t`, the tonnes a year still uncovered (the materials' own figure when omitted), so the suggestion covers
        the shortfall the capacity screen reports."""
        if not binding:
            return {"text": "", "commands": []}
        needs = self.needs
        if binding == "charcoal":
            return self.charcoal_remedy()
        if shortfall_t is None:
            shortfall_t = needs.material_shortfall(binding)
        if binding == "saltpetre":
            return self.saltpetre_remedy(shortfall_t)
        if binding in self.works_materials():
            return self.dig_remedy(binding, shortfall_t)
        return {"text": (
            needs.material_unsupplied_sentence[binding]
            or "Nothing you own supplies %s and the market is out of it; the work waits until something "
               "upstream of it is built." % binding), "commands": []}

    def charcoal_remedy(self) -> Dict[str, Any]:
        needs = self.needs
        per_hectare = needs.charcoal_per_hectare()
        need = max(0.0, needs.material_demand().get("charcoal_kg", 0.0) / KILOGRAMS_PER_TONNE - self.seat.forest_ha * per_hectare)
        hectares_needed = max(1.0, round(need / max(per_hectare, 1e-9)))
        return {"text": (
            "Charcoal is grown, not bought: about %s more of "
            "coppice would cover it ('buy forest %d', roughly %s"
            "). Ask the price first with 'quote forest %d'."
            % (needs.area_text(hectares_needed, grouped=True), hectares_needed,
               needs.money_text(hectares_needed * self.forest_base_cost() * needs.price_index(), True), hectares_needed)),
            "commands": ["quote forest %d" % hectares_needed, "buy forest %d" % hectares_needed]}

    def saltpetre_remedy(self, shortfall_t: float) -> Dict[str, Any]:
        needs = self.needs
        demand = needs.material_demand().get("saltpetre_kg", 0.0) / KILOGRAMS_PER_TONNE
        deficit = sizing.nitre_deficit_tonnes(
            shortfall_t, demand, self.seat.nitre_bed_m2, NITRE_YIELD_T_PER_M2, needs.material_market_tonnes["saltpetre"],
            needs.goods_stock["saltpetre"])
        # twenty per cent headroom keeps a tiny change in the portfolio from putting the player straight back into shortage
        square_meters = sizing.nitre_bed_square_metres(deficit, NITRE_SHORTAGE_SAFETY_BUFFER, NITRE_YIELD_T_PER_M2)
        return {"text": (
            "Saltpetre is made in nitre beds, not mined: you are about "
            "%s short. With a 20%% safety buffer, 'buy "
            "nitre %d' lays enough bed at %s "
            "per year (about %s)."
            % (needs.mass_rate_text(deficit, digits=2, short=False), square_meters,
               needs.mass_per_area_text(NITRE_YIELD_T_PER_M2, digits=4),
               needs.money_text(square_meters * self.nitre_base_cost() * needs.price_index(), True))),
            "commands": ["buy nitre %d" % square_meters]}

    def dig_remedy(self, binding: str, shortfall_t: float) -> Dict[str, Any]:
        needs = self.needs
        sinking_tonnes, ready_year, shortfall_t = sizing.mine_shortfall_after_sinking(binding, shortfall_t, self.seat.mine_tranches)
        if sinking_tonnes > 0.0:
            sinking_text = ("A working of %s is already being sunk, ready in %d. "
                            % (needs.mass_rate_text(sinking_tonnes, grouped=True, short=False), ready_year))
            if shortfall_t < 1.0:
                return {"text": sinking_text + "It covers the shortfall; wait for it.", "commands": []}
        else:
            sinking_text = ""
        tonnes_short = sizing.mine_size_tonnes(shortfall_t)
        has_working = self.mine_capacity().get(binding, 0.0) > 0.0
        return {"text": sinking_text + (
            "The market will not sell you enough %s, so you have to dig "
            "it: %s. 'quote mine %s %d' for the price, then 'buy mine "
            "%s %d'. A shaft takes a few years to come into production."
            % (binding,
               ("you are about %s short"
                % needs.mass_rate_text(shortfall_t, grouped=True, short=False)) if shortfall_t >= 1.0
               else "your own workings already cover the demand you have "
                    "today, so this is the market, not you"
               if has_working
               else "you have no working of it yet, so sink one",
               binding, tonnes_short, binding, tonnes_short)),
            "commands": ["quote mine %s %d" % (binding, tonnes_short),
                         "buy mine %s %d" % (binding, tonnes_short)],
            "kind": "dig_mine", "has_working": has_working,
            "short_tonnes": shortfall_t}
