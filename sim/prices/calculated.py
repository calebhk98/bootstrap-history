"""The calculated-goods views: what the solver says the goods cost at a set of held techniques, in labour hours, and what a
partner's own society makes and charges at its own opening techniques."""
import json
from typing import Any, Dict, FrozenSet, Mapping

from . import prices as price_solver
from . import rules


class CalculatedViews:

    def opening_schedule(self, civilisation: Mapping[str, Any]) -> Any:
        """The opening wage schedule of a civilisation record, remembered by the record's whole content so a variant is
        never served another's."""
        key = json.dumps(civilisation, sort_keys=True, default=str)
        schedule = self._schedule_by_content.get(key)
        if schedule is None:
            schedule = self._schedule_by_content[key] = self.needs.wage_schedule_for(civilisation)
        return schedule

    def calculated_goods_prices(self, held: FrozenSet[str], farmed_hectares: float) -> Dict[str, float]:
        """{material: labour-hour price} of every material the solver prices when `held` techniques are known and
        `farmed_hectares` are farmed (banded), from one solve."""
        civilisation = self.needs.civilisation()
        document = self.opening_schedule(civilisation).document()
        goods, _provenance = price_solver.priced_goods_table(
            held, document, civilization_id=civilisation.get("id"), civilization=civilisation,
            farmed_hectares=price_solver.band_farmed_hectares(farmed_hectares), interest_rate=None)
        return rules.goods_in_coin(goods, document["money_per_labour_hour"], 1.0)

    def held_goods_prices_in_hours(self, held: FrozenSet[str]) -> Dict[str, float]:
        """{material: labour-hour price} of every material the solver prices when the techniques `held` are known, at the
        farming the civilisation opens with (one solve per set)."""
        civilisation = self.needs.civilisation()
        document = self.opening_schedule(civilisation).document()
        goods, _provenance = price_solver.priced_goods_table(
            held, document, civilization_id=civilisation.get("id"), civilization=civilisation)
        return rules.goods_in_coin(goods, document["money_per_labour_hour"], 1.0)

    def partner_own_economy(self, civilization_id: str) -> Dict[str, Any]:
        """What a civilisation makes and charges at its own opening technologies, frozen for the game: {solved_materials, the
        prices in its own coin, money_per_labour_hour}."""
        found = self._partner_economies.get(civilization_id)
        if found is None:
            record = self.needs.civilisation_record[civilization_id]
            schedule = self.opening_schedule(record)
            document = schedule.document()
            goods, provenance = price_solver.priced_goods_table(
                frozenset(record["starting_techs"]), document, civilization_id=civilization_id)
            found = self._partner_economies[civilization_id] = {
                "solved_materials": rules.solved_materials(provenance),
                "prices_in_own_coin": rules.goods_in_coin(
                    goods, document["money_per_labour_hour"], schedule.money_per_labour_hour),
                "money_per_labour_hour": schedule.money_per_labour_hour}
        return found
