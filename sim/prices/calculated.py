"""The calculated-goods views: what the solver says the goods cost at a set of held techniques, in labour hours, and what a
partner's own society makes and charges at its own opening techniques."""
from typing import Any, Dict, FrozenSet, Mapping

from sim.assembly.api import Part

from . import prices as price_solver
from . import rules


class CalculatedViews(Part):

    def __init__(self, module):
        super().__init__(module)
        self._partner_economies: Dict[str, Any] = {}         # what each partner makes and charges at its own opening

    def opening_schedule(self, civilisation: Mapping[str, Any]) -> Any:
        """The opening wage schedule of a civilisation record: the workforce module's, which builds it once per record."""
        return self.needs.wage_schedule_for(civilisation)

    def held_civilisation(self) -> Dict[str, Any]:
        """The home civilisation's record with the tiles it holds now as its home tiles, so the solve prices the ground the
        country has, not the ground its file opened with."""
        return {**self.needs.civilisation(), "home_tiles": list(self.needs.home_tiles_held())}

    def held_goods_prices_in_hours(self, held: FrozenSet[str]) -> Dict[str, float]:
        """{material: labour-hour price} of every material the solver prices when the techniques `held` are known, at the
        farming the civilisation opens with (one solve per set)."""
        hours, _provenance = price_solver.goods_in_hours(
            held, self.opening_schedule(self.needs.civilisation()).document(), self.held_civilisation(),
            unskilled_trade=self.needs.unskilled_trade(), mods_dir=self.needs.mods_directory())
        return hours

    def partner_own_economy(self, civilization_id: str) -> Dict[str, Any]:
        """What a civilisation makes and charges at its own opening technologies, frozen for the game: {solved_materials, the
        prices in its own coin, money_per_labour_hour}."""
        found = self._partner_economies.get(civilization_id)
        if found is None:
            record = self.needs.civilisation_record[civilization_id]
            schedule = self.opening_schedule(record)
            hours, provenance = price_solver.goods_in_hours(
                frozenset(record["starting_techs"]), schedule.document(), record,
                unskilled_trade=self.needs.unskilled_trade(), mods_dir=self.needs.mods_directory())
            found = self._partner_economies[civilization_id] = {
                "solved_materials": rules.solved_materials(provenance),
                "prices_in_own_coin": rules.money_prices(hours, schedule.money_per_labour_hour),
                "money_per_labour_hour": schedule.money_per_labour_hour}
        return found
