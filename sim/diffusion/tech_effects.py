"""What a finished technique does to the society as a whole: its values, its reading, its disease burden.

Needs: tech_effects, coverage, disease_burden, disease_burden_held, disease_burden_weights, literacy, ceilings, send (TeachLiteracy)."""
from typing import Any, Dict, List, Tuple

from sim.actors.api import TeachLiteracy
from sim.polity.api import ShiftValueWeight
from sim.refusal import Refusal
from sim.reporting.api import RecordEvent

from . import literacy_rules, rules

LITERACY_FIELDS = ("literacy_elite", "literacy_general")


class TechEffects:

    def apply_tech_effects(self, command: Any) -> None:
        """Building something changes what this society is like: printing raises literacy, the scientific method
        reduces the fear of the inexplicable. The effects table (_TECH_EFFECTS.json) says how much."""
        node_id = command.node_id
        effects = self.needs.tech_effects[node_id]
        if not effects:
            return
        changed: List[str] = []
        changed_fields: List[str] = []
        changes: Dict[str, Tuple[float, float]] = {}
        literacy_before = ({field: self.literacy(field) for field in LITERACY_FIELDS}
                           if any(field in effects for field in LITERACY_FIELDS) else {})
        for field, delta in effects.items():
            if field.startswith("_") or not isinstance(delta, (int, float)):
                continue
            shifted = self.needs.send(ShiftValueWeight(field, delta))
            if not isinstance(shifted, Refusal):
                before, after = shifted
                changed.append(rules.value_weight_change_text(field, before, after))
                changed_fields.append(field)
                changes[field] = (before, after)
            elif field == "population" and node_id not in self.needs.coverage():
                # only the disease technologies carry this weight; the disease burden reads it live from the tree
                burden = self.needs.disease_burden()
                weights = self.needs.disease_burden_weights()
                total_weight = sum(weights.values())
                burden_before = rules.burden_before_effect(burden, delta, lambda: self.needs.disease_burden_held[node_id],
                                                           total_weight, node_id in weights)
                changed.append(rules.burden_change_text(burden_before, burden))
                changed_fields.append(field)
                changes[field] = (burden_before, burden)
        self._teach_literacy(effects, literacy_before, changed, changed_fields, changes)
        if changed:
            self.needs.send(RecordEvent.of("society_changed", rules.society_changed_text(self.needs.tree[node_id]["name"], changed),
                                           project=node_id, fields=sorted(changed_fields), changes=changes))

    def _teach_literacy(self, effects: Dict[str, Any], literacy_before: Dict[str, float], changed: List[str],
                        changed_fields: List[str], changes: Dict[str, Tuple[float, float]]) -> None:
        for field in LITERACY_FIELDS:
            delta = effects.get(field)
            if isinstance(delta, (int, float)):
                ceiling = self.literacy_ceiling(field)
                before = self.literacy(field)
                target = literacy_rules.literacy_after_effect(before, delta, ceiling)
                learners_ceiling = self.literacy_ceiling("common") if field == "literacy_general" else ceiling
                self.needs.send(TeachLiteracy(field, target, learners_ceiling))
        for field, before in literacy_before.items():
            after = self.literacy(field)
            if before != after or field in effects:
                changes[field] = (before, after)
                changed_fields.append(field)
                changed.append(rules.literacy_change_text(field, before, after))
