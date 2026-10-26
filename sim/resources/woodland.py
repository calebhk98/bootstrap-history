"""Coppice woodland and nitre beds: what the seat holds of each, what a hectare or a square metre costs, and buying them.

Charcoal is grown, so the answer to a charcoal shortage is woodland; saltpetre is made, so the answer to a saltpetre
shortage is a bed. Both are bought once and yield every year after, and neither can be sold back."""
from typing import Any, Dict

from sim.agents.api import edges
from sim.ledger.api import PayEdge
from sim.refusal import Refusal
from sim.reporting.api import RecordEvent

from . import ceilings
from .channels import FOREST, NITRE
from .commands import BuyForest, LayNitreBeds
from .constants import (FOREST_HA_PER_MILLION_KM2_BASE, FOREST_HA_PER_MILLION_KM2_PER_SC, FOREST_LABOUR_HOURS_PER_HA,
                        NITRE_LABOUR_HOURS_PER_M2, NITRE_YIELD_T_PER_M2, REVENUE_SCALE_CAP_MULTIPLE)


class Woodland:
    """Needs: legacy_world_map, civilisation, price_index, money_per_labour_hour, revenue_estimate, forest_reach, can_pay,
    area_text. Sends PayEdge, RecordEvent."""

    def forest_hectares(self) -> float:
        """Hectares of coppice the acting seat holds."""
        return self.seat.forest_ha

    def forest_base_cost(self) -> float:
        """What a hectare of coppice costs before the price index."""
        return FOREST_LABOUR_HOURS_PER_HA * self.needs.money_per_labour_hour()

    def forest_holding(self) -> Dict[str, float]:
        """{hectares, base_cost_per_hectare, price_index}: the forest held and what a hectare costs, before the price index."""
        return {"hectares": self.seat.forest_ha, "base_cost_per_hectare": self.forest_base_cost(),
                "price_index": self.needs.price_index()}

    def forest_price_per_hectare(self) -> float:
        """What a hectare of coppice costs now: the one price `buy forest` charges and `quote forest` shows."""
        return self.forest_base_cost() * self.needs.price_index()

    def nitre_beds(self) -> Dict[str, float]:
        """{square_metres, tonnes_per_square_metre}: the nitre bed the acting seat holds and what a square metre yields a year."""
        return {"square_metres": self.seat.nitre_bed_m2, "tonnes_per_square_metre": NITRE_YIELD_T_PER_M2}

    def nitre_base_cost(self) -> float:
        """What a square metre of nitre bed costs before the price index."""
        return NITRE_LABOUR_HOURS_PER_M2 * self.needs.money_per_labour_hour()

    def home_land_area_km2(self) -> float:
        """Total land area of the tiles the civilisation holds, not counted by how many region labels the ground is filed under."""
        return ceilings.held_land_area_km2(self.needs.civilisation(), self.needs.legacy_world_map())

    def forest_land_ceiling(self) -> float:
        """The largest standing coppice that could ever be held, in hectares."""
        state_reach = self.needs.forest_reach()
        return ceilings.forest_ceiling_hectares(
            self.home_land_area_km2(), state_reach, FOREST_HA_PER_MILLION_KM2_BASE, FOREST_HA_PER_MILLION_KM2_PER_SC,
            ceilings.revenue_scale_multiple(self.needs.revenue_estimate(), self.revenue_scale(), REVENUE_SCALE_CAP_MULTIPLE))

    def buy_forest(self, command: BuyForest) -> Any:
        """Coppice woodland, bought outright; the hectares bought are cut to the room under the ceiling."""
        hectares = command.hectares
        room = ceilings.room_under_ceiling(self.forest_land_ceiling(), self.seat.forest_ha)
        if hectares > room:
            # a log line, which the player sees, is the honest way to say why fewer hectares were bought than asked
            self.needs.send(RecordEvent.of("coppice_limit", "you can hold at most %s of coppice here; "
                                           "bought %s, not %s" % (self.needs.area_text(self.forest_land_ceiling()),
                                                                  self.needs.area_text(room), self.needs.area_text(hectares))))
            hectares = room
        if hectares <= 0:
            return Refusal("no_room", "there is no room for more coppice under the ceiling", hectares=hectares)
        cost = hectares * self.forest_price_per_hectare()
        if cost > 0 and not self.needs.can_pay(cost):
            return Refusal("cannot_afford", "the coppice costs more than the purchase budget covers", cost=cost)
        self.needs.send(PayEdge(edges.EDGE_LANDOWNERS, cost, "forest bought"))
        self.seat.forest_ha += hectares
        self.bump_seat(FOREST)
        return hectares

    def lay_nitre(self, command: LayNitreBeds) -> Any:
        """Lay down nitre beds: saltpetre is not dug and not grown, it is made."""
        square_metres = float(command.square_metres)
        if square_metres <= 0:
            return Refusal("nothing_asked", "say how many square metres of nitre bed to lay")
        cost = square_metres * self.nitre_base_cost() * self.needs.price_index()
        if not self.needs.can_pay(cost):
            return Refusal("cannot_afford", "the nitre beds cost more than the purchase budget covers", cost=cost)
        self.needs.send(PayEdge(edges.EDGE_BUILDERS, cost, "nitre beds laid down"))
        self.seat.nitre_bed_m2 += square_metres
        self.bump_seat(NITRE)
        return square_metres

