"""The yearly phase that tells the player what a material shortage costs.

A part of the year's phases (core_step_phases.py); Sim inherits it through StepPhasesMixin. The step before it, which
commissions the workings and buys the woodland, mines and nitre beds that answer a shortage, is the resources module's
phase `materials` (sim/resources/materials_phase.py); this one reads what that step's throttle reading left."""
from sim.reporting.api import RecordEvent
from . import shortage_conditions


class MaterialsPhaseMixin:

    def _step_material_shortage_notes(self):
        holdings = self.state.holdings
        throttle = holdings.throttle
        slowed = shortage_conditions.slowed_projects(self) if throttle < 0.6 and holdings.binding else []
        if slowed:
            # SAY WHAT TO DO ABOUT IT: a bare "SHORT OF SALTPETRE: work at
            # 5% of plan" with no remedy attached reads as the game being
            # stuck rather than as something actionable.
            # One standing condition; the full message only when it is new or has moved materially.
            # Only said while a running project draws the material: a shortage nothing running needs slows nothing.
            if shortage_conditions.note_shortage(self, holdings.binding, throttle):
                names = ", ".join(self.nodes[node_id]["name"] for node_id in slowed[:3])
                self.send(RecordEvent.of("material_shortage", "SHORT OF %s: %s running at %d%% of plan. %s"
                                 % (shortage_conditions.material_words(holdings.binding).upper(), names,
                                    throttle * 100, self.shortage_remedy(holdings.binding))))
        else:
            shortage_conditions.clear_shortage(self)
