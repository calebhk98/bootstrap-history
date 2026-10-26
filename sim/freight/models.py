"""The carrier each mode prices with and what a tonne-km costs by it, at this society's prices, wages and market rate.

Mode costs come from the physical models (`sim/geography/transport.py` for cart, pack string and towed barge;
`sim/geography/sea_freight.py` for a sailing hull), priced with the feed price, wages, carrier prices and market rate,
with the empty return where flows are one-sided (`sim/geography/freight_cost.py`)."""
import functools

from sim.geography.api import droving_carrier, dues_hours_per_tonne, freight_cost, modes_carrying, sea_freight, train_carrier
from sim.geography.api import transport as freight_physics
from sim.geography.api import walking_cargo_modes

from . import rules
from .constants import (CANAL_MODE, CARAVAN_STRING_SIZE, FREIGHT_DRIVER_WAGE_TRADE, FREIGHT_FEED_PRICE_MATERIAL,
                        FREIGHT_VEHICLE_MATERIAL, LAND_FREIGHT_TEAM_SIZE, RAIL_MODE, SEA_CREW_WAGE_TRADE, SEA_MODE)


@functools.lru_cache(maxsize=None)
def _river_inputs():
    return freight_physics.barge_freight_physical_inputs(freight_physics.OX, 2, freight_physics.BARGE)


@functools.lru_cache(maxsize=None)
def _paved_road_inputs(team_size):
    return freight_physics.draught_freight_physical_inputs(
        freight_physics.OX, team_size, freight_physics.CART, freight_physics.PAVED_ROAD)


@functools.lru_cache(maxsize=None)
def _caravan_inputs():
    return freight_physics.pack_freight_physical_inputs(freight_physics.MULE, int(CARAVAN_STRING_SIZE))


@functools.lru_cache(maxsize=None)
def _land_freight_inputs(team_size):
    """FreightPhysicalInputs for `team_size` oxen pulling a two-wheeled cart on an ordinary dirt track."""
    return freight_physics.draught_freight_physical_inputs(
        freight_physics.OX, team_size, freight_physics.CART, freight_physics.DIRT_TRACK)


class Models:
    """Needs: legacy_world_map, wage, material_price, material_prices, market_rate."""

    def train_carrier(self):
        """Geography's train as a freight carrier ({inputs, fuel_material, stock_material, stock_kg})."""
        return train_carrier(RAIL_MODE, self.needs.legacy_world_map())

    def carrier_feed_material(self, mode):
        """The material whose price a mode's feed (or fuel) is counted at: coal for a train, the draught animals'
        feed otherwise."""
        train = self.train_carrier() if mode == RAIL_MODE else None
        return train["fuel_material"] if train else FREIGHT_FEED_PRICE_MATERIAL

    def sea_crew(self):
        return rules.sea_crew_hands(
            self.needs.wage[SEA_CREW_WAGE_TRADE], self.needs.material_price[FREIGHT_FEED_PRICE_MATERIAL] or 0.0,
            self.needs.material_price[FREIGHT_VEHICLE_MATERIAL] or 0.0)

    def carrier_models(self):
        """{mode: (physical inputs, carrier prices, working days a year, hull loss per 1000 km)}: the carrier unit
        each mode's inputs describe, priced from this society's prices. Kept while the price table, the sea crew's
        wage, the map and the team size are the same."""
        prices = self.needs.material_prices()
        key = (self.needs.wage[SEA_CREW_WAGE_TRADE], self.needs.legacy_world_map(), LAND_FREIGHT_TEAM_SIZE)
        cached = self._models_cache
        if cached is not None and cached[0] is prices and cached[1] == key:
            return cached[2]
        models = self.build_carrier_models()
        self._models_cache = (prices, key, models)
        return models

    def build_carrier_models(self):
        vehicle_wood = self.needs.material_price[FREIGHT_VEHICLE_MATERIAL] or 0.0
        ox_price = self.needs.material_prices().get("ox", 0.0)
        mule_price = self.needs.material_prices().get("mule", 0.0)
        team = float(LAND_FREIGHT_TEAM_SIZE)
        string = int(CARAVAN_STRING_SIZE)
        land_days = freight_cost.LAND_WORKING_DAYS_PER_YEAR
        crew = self.sea_crew()
        hull_inputs = sea_freight.sailing_freight_physical_inputs(crew=crew)
        hull_kg = hull_inputs.cargo_tonnes * sea_freight.HULL_TIMBER_KG_PER_CARGO_TONNE
        train = self.train_carrier()
        stock_price = self.needs.material_price[train["stock_material"]] or 0.0
        world_map = self.needs.legacy_world_map()
        river_boat = (_river_inputs(), freight_cost.CarrierPrices(freight_physics.BARGE.self_mass_kg * vehicle_wood,
                                                                   2.0 * ox_price), land_days, 0.0)
        walking = {mode: (droving_carrier(mode, world_map)["inputs"], freight_cost.CarrierPrices(0.0), land_days, 0.0)
                   for mode in walking_cargo_modes(world_map)}
        return {
            **walking,
            "cart": (_land_freight_inputs(int(LAND_FREIGHT_TEAM_SIZE)),
                     freight_cost.CarrierPrices(freight_physics.CART.self_mass_kg * vehicle_wood,
                                                team * ox_price), land_days, 0.0),
            "road": (_paved_road_inputs(int(LAND_FREIGHT_TEAM_SIZE)),
                     freight_cost.CarrierPrices(freight_physics.CART.self_mass_kg * vehicle_wood,
                                                team * ox_price), land_days, 0.0),
            "pack": (_caravan_inputs(),
                     freight_cost.CarrierPrices(
                         string * freight_physics.PACK_SADDLE.self_mass_kg * vehicle_wood,
                         string * mule_price), land_days, 0.0),
            "river_boat": river_boat,
            CANAL_MODE: river_boat,
            RAIL_MODE: (train["inputs"], freight_cost.CarrierPrices(train["stock_kg"] * stock_price), land_days, 0.0),
            SEA_MODE: (hull_inputs, freight_cost.CarrierPrices(hull_kg * vehicle_wood),
                       sea_freight.SAILING_DAYS_PER_YEAR, sea_freight.hull_loss_per_thousand_km(crew))}

    def freight_mode_costs(self, imbalance=1.0, modes=None, cargo=None):
        """{mode: home money per tonne-km}: feed and crew, the carrier's capital at the market rate, hull losses, and
        the return leg (`imbalance` 0 when flows balance, 1 when the carrier comes back empty). The same function
        prices foreign legs and domestic hauls."""
        land_wage = self.needs.wage[FREIGHT_DRIVER_WAGE_TRADE]
        sea_wage = self.needs.wage[SEA_CREW_WAGE_TRADE]
        rate = self.needs.market_rate()
        world_map = self.needs.legacy_world_map()
        walking = frozenset(walking_cargo_modes(world_map))
        carrying = frozenset(modes_carrying(cargo, world_map)) if cargo else frozenset()
        return {mode: freight_cost.freight_money_per_tonne_km(
                    inputs, self.needs.material_price[self.carrier_feed_material(mode)] or 0.0,
                    sea_wage if mode == SEA_MODE else land_wage, prices, rate, working_days, imbalance, loss,
                    cargo_walks=mode in walking)
                for mode, (inputs, prices, working_days, loss) in self.carrier_models().items()
                if (modes is None or mode in modes) and (cargo is None or mode in carrying)}

    def freight_handling_costs(self):
        """{mode: home money per tonne} charged once per leg of that mode: port handling at sea, and the tolls or port
        dues the geography states for each mode (paid at the carrier's wage)."""
        wage = self.needs.wage[FREIGHT_DRIVER_WAGE_TRADE]
        return rules.handling_money_per_tonne(dues_hours_per_tonne(self.needs.legacy_world_map()), wage, SEA_MODE,
                                              sea_freight.PORT_HANDLING_HOURS_PER_TONNE)
