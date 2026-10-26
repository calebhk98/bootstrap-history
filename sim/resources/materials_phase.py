"""The year's step that supplies the materials the economy is short of: commission the workings that are ready, then, when
the throttle shows a shortage the automatic policies may answer, buy woodland, sink a mine or lay nitre beds before the
shortage bites (a competent manager's answer, and the one the old model never made).

The phase is `materials` of sim/engine/year_phases.py. What a shortage tells the player is the engine's step after it."""
from typing import Any

from sim.agents.api import edges
from sim.ledger.api import PayEdge
from sim.materials.api import ApplyThrottle
from sim.reporting.api import RecordAutomation, RecordAutomationSkip, RecordEvent, order_id
from sim.unit_conversions import KILOGRAMS_PER_TONNE

from . import sizing
from .channels import NITRE
from .commands import BuyForest, OpenMine
from .constants import AUTO_FOREST_CAPITAL_LABOUR_HOURS_PER_HA, NITRE_BED_SPEND_CEILING_LABOUR_HOURS

AUTO_FOREST_SHARE_OF_PURCHASE_BUDGET = 0.35     # of what the seat could raise, the most one charcoal answer spends
AUTO_FOREST_HECTARES_PER_YEAR = 400.0           # the most woodland one charcoal answer buys
AUTO_FOREST_WITH_SMELTING_HECTARES = 200.0      # the most woodland bought beside an ore order for a metal smelted with charcoal
CHARCOAL_SMELTED_METALS = ("iron", "copper", "lead")   # smelted with charcoal, so the ore is only half the answer


class MaterialsPhase:
    """Needs: spending_power, automatic_policy, material_binding, material_demand, material_checks,
    charcoal_per_hectare, price_index, money_per_labour_hour, acting_balance, area_text, mass_rate_text, money_text.
    Sends ApplyThrottle, PayEdge, RecordAutomation, RecordAutomationSkip, RecordEvent."""

    def step_materials(self, seat_id: Any = None) -> None:
        needs = self.needs
        self.commission_mines()
        throttle = needs.send(ApplyThrottle())
        # What coppice is gated on is whether the seat can raise the price of some, which is what spending power says;
        # below that `buy_forest` refuses what cannot be paid for anyway.
        can_raise = needs.spending_power("buy")
        if (throttle < 0.9 and can_raise > self.forest_price_per_hectare()
                and (needs.automatic_policy("auto_mine") or needs.automatic_policy("auto_forest"))):
            binding = needs.material_binding()
            if binding == "charcoal":
                # charcoal is grown, so the answer is woodland
                if needs.automatic_policy("auto_forest"):
                    self.auto_forest(can_raise)
            elif binding in self.works_materials() and needs.automatic_policy("auto_mine"):
                self.auto_mine(binding)
            elif binding == "saltpetre" and needs.automatic_policy("auto_mine"):
                self.auto_nitre()

    def auto_forest(self, can_raise: float) -> None:
        """Buy woodland sized from the charcoal shortfall, not from a flat share of cash."""
        needs = self.needs
        per_hectare = needs.charcoal_per_hectare()
        need_tonnes = (needs.material_demand().get("charcoal_kg", 0.0) / KILOGRAMS_PER_TONNE) - self.seat.forest_ha * per_hectare
        want_hectares = max(0.0, need_tonnes) / max(per_hectare, 1e-9)
        afford_hectares = (can_raise * AUTO_FOREST_SHARE_OF_PURCHASE_BUDGET / self.forest_price_per_hectare())
        before = needs.acting_balance()
        hectares_before = self.seat.forest_ha
        self.buy_forest(BuyForest(min(AUTO_FOREST_HECTARES_PER_YEAR, want_hectares, afford_hectares)))
        if self.seat.forest_ha > hectares_before:
            needs.send(RecordAutomation(
                "auto_forest", "forest", "%s of coppice" % needs.area_text(self.seat.forest_ha - hectares_before),
                "charcoal demand exceeds what %s yield by %s" % (
                    needs.area_text(hectares_before), needs.mass_rate_text(max(0.0, need_tonnes), short=False)), before))

    def auto_mine(self, binding: str) -> None:
        """Sink a mine sized from all the material keys that feed the bucket that binds, not from one of them; shafts
        already sinking count, so a tranche about to commission is not ordered twice."""
        needs = self.needs
        demand = needs.material_demand()
        keys = tuple(sorted(material for material, (bucket, _tag) in needs.material_checks().items() if bucket == binding))
        short = sum(demand.get(material, 0.0) for material in keys)
        before = needs.acting_balance()
        pending = self.seat.mine_pending.get(binding, 0.0)
        ordered = sizing.auto_mine_order_tonnes(short, self.mine_capacity().get(binding, 0.0), pending,
                                                needs.acting_balance(), self.mine_capex(binding))
        order = order_id("auto_mine", binding, needs.year())
        self.auto_prospect(binding)
        self.open_mine(OpenMine(binding, ordered, order=order))
        active = self.mine_capacity().get(binding, 0.0)
        if ordered > 0:
            needs.send(RecordAutomation(
                "auto_mine", "mine", "%s of %s ordered" % (needs.mass_rate_text(ordered), binding),
                "demand %s > active %s; pending capacity considered %s" % (
                    needs.mass_rate_text(short), needs.mass_rate_text(active), needs.mass_rate_text(pending)), before,
                dict(order=order, reason_kind="mine_ordered", demand=short, active_capacity=active, pending_capacity=pending,
                     ordered=ordered)))
        else:
            needs.send(RecordAutomationSkip(
                "auto_mine", "mine for %s" % binding,
                "nothing ordered: shortfall %s against %s active and %s pending, a quarter of capital buys %s" % (
                    needs.mass_rate_text(short), needs.mass_rate_text(active), needs.mass_rate_text(pending),
                    needs.mass_rate_text(sizing.auto_mine_affordable_tonnes(needs.acting_balance(), self.mine_capex(binding))))))
        if binding in CHARCOAL_SMELTED_METALS:
            capital_per_hectare = AUTO_FOREST_CAPITAL_LABOUR_HOURS_PER_HA * needs.money_per_labour_hour()
            self.buy_forest(BuyForest(min(AUTO_FOREST_WITH_SMELTING_HECTARES, needs.acting_balance() / capital_per_hectare)))

    def auto_nitre(self) -> None:
        """Lay nitre beds with a flat yearly ceiling, not sized to a shortfall that beds cannot close at any affordable
        scale: sizing it would starve everything else and pin the household in arrears. The shortage stays real."""
        needs = self.needs
        ceiling = NITRE_BED_SPEND_CEILING_LABOUR_HOURS * needs.money_per_labour_hour()
        spend = sizing.nitre_bed_yearly_spend(needs.acting_balance(), ceiling)
        needs.send(PayEdge(edges.EDGE_BUILDERS, spend, "nitre beds laid down"))
        square_metres = spend / self.nitre_base_cost()
        self.seat.nitre_bed_m2 += square_metres
        self.bump_seat(NITRE)
        needs.send(RecordAutomation("auto_mine", "nitre", "%s of nitre bed" % needs.area_text(square_metres, unit="square_metre"),
                                    "saltpetre is the binding shortage; the yearly spend is capped, not sized to the gap",
                                    needs.acting_balance() + spend))
        needs.send(RecordEvent.of("nitre_bed_laid", "laid down %s of nitre bed for %s (auto_mine)" % (
            needs.area_text(square_metres, unit="square_metre"), needs.money_text(spend))))
