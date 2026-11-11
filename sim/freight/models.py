"""The carrier each mode prices with and what a tonne-km costs by it, at this society's prices, wages and market rate.

Mode costs come from the physical models (`sim/geography/transport.py` for cart, pack string and towed barge;
`sim/geography/sea_freight.py` for a sailing hull), priced with the feed price, wages, carrier prices and market rate,
with the empty return where flows are one-sided (`sim/geography/freight_cost.py`)."""
import functools

from sim.assembly.api import Part
from sim.geography.api import freight_cost, sea_freight
from sim.labour import api as labour_api
from sim.geography.api import transport as freight_physics

from . import rules
from .constants import (CANAL_MODE, CARAVAN_STRING_SIZE,
                        FREIGHT_VEHICLE_MATERIAL, LAND_FREIGHT_TEAM_SIZE, RAIL_MODE, SEA_MODE)


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


class Models(Part):
    """Needs: mode_carrier, carriage_facts, modes_carrying, labour_quote, material_price, material_prices, market_rate.
    A mode whose feed, vehicle or animals have no price is not offered: `unpriced_modes` names what each lacks."""

    def __init__(self, module):
        super().__init__(module)
        self._models_cache = None        # (price table, key, models, unpriced) while the table, the sea crew's wage and the map hold

    def trade_of_role(self, role):
        """The trade that plays `role` (unskilled: the drivers; sailor: sea crews; merchant), from the trade data."""
        return labour_api.trade_of_role(self.needs.trade_registry(), role)

    def train_carrier(self):
        """Geography's train as a freight carrier ({inputs, fuel_material, stock_material, stock_kg})."""
        return self.needs.mode_carrier(RAIL_MODE)["train"]

    def feed_price_material(self):
        """The material whose book price turns the draught animals' (and the sea crew's) feed kilograms into money: the
        civilisation's staple grain, a stand-in for fodder, dearer per kilogram than fodder, so the feed cost is an upper bound."""
        return labour_api.wage_provider.staple_material(self.needs.civilisation())

    def carrier_feed_material(self, mode):
        """The material whose price a mode's feed (or fuel) is counted at: coal for a train, the draught animals'
        feed otherwise."""
        train = self.train_carrier() if mode == RAIL_MODE else None
        return train["fuel_material"] if train else self.feed_price_material()

    def sea_crew(self):
        """Hands a merchant hull sails with; None while the feed or the timber has no price."""
        grain_price = self.needs.material_price[self.feed_price_material()]
        wood_price = self.needs.material_price[FREIGHT_VEHICLE_MATERIAL]
        if grain_price is None or wood_price is None:
            return None
        return rules.sea_crew_hands(self.needs.labour_quote(self.trade_of_role("sailor")), grain_price, wood_price)

    def carrier_models(self):
        """{mode: (physical inputs, carrier prices, working days a year, hull loss per 1000 km)}: the carrier unit
        each mode's inputs describe, priced from this society's prices; a mode with an unpriced input is left out.
        Kept while the price table, the sea crew's wage and the team size are the same."""
        prices = self.needs.material_prices()
        key = (self.needs.labour_quote(self.trade_of_role("sailor")), LAND_FREIGHT_TEAM_SIZE)
        cached = self._models_cache
        if cached is not None and cached[0] is prices and cached[1] == key:
            return cached[2]
        models, unpriced = self.build_carrier_models()
        self._models_cache = (prices, key, models, unpriced)
        return models

    def unpriced_modes(self):
        """{mode: the materials with no price that keep it from being offered}."""
        self.carrier_models()
        return self._models_cache[3]

    def build_carrier_models(self):
        """(models, unpriced): the carrier of each mode whose inputs are all priced, and what the others lack."""
        prices = self.needs.material_prices()
        vehicle_wood = self.needs.material_price[FREIGHT_VEHICLE_MATERIAL]
        ox_price = prices.get("ox")
        mule_price = prices.get("mule")
        team = float(LAND_FREIGHT_TEAM_SIZE)
        string = int(CARAVAN_STRING_SIZE)
        land_days = freight_cost.LAND_WORKING_DAYS_PER_YEAR
        crew = self.sea_crew()
        train = self.train_carrier()
        stock_price = self.needs.material_price[train["stock_material"]]
        draught = {"wood_kg": vehicle_wood, "ox": ox_price}
        wanted = {"cart": draught, "road": draught, "pack": {"wood_kg": vehicle_wood, "mule": mule_price},
                  "river_boat": draught, CANAL_MODE: draught, RAIL_MODE: {train["stock_material"]: stock_price},
                  SEA_MODE: {self.feed_price_material(): self.needs.material_price[self.feed_price_material()],
                             "wood_kg": vehicle_wood}}
        unpriced = {mode: sorted(material for material, price in needed.items() if price is None)
                    for mode, needed in wanted.items()}
        unpriced = {mode: missing for mode, missing in unpriced.items() if missing}
        models = {mode: (self.needs.mode_carrier(mode)["droving"]["inputs"], freight_cost.CarrierPrices(0.0), land_days, 0.0)
                  for mode in self.needs.carriage_facts()["walking_modes"]}
        if "river_boat" not in unpriced:
            river_boat = (_river_inputs(), freight_cost.CarrierPrices(freight_physics.BARGE.self_mass_kg * vehicle_wood,
                                                                       2.0 * ox_price), land_days, 0.0)
            models["river_boat"] = river_boat
            models[CANAL_MODE] = river_boat
        if "cart" not in unpriced:
            models["cart"] = (_land_freight_inputs(int(LAND_FREIGHT_TEAM_SIZE)),
                              freight_cost.CarrierPrices(freight_physics.CART.self_mass_kg * vehicle_wood,
                                                         team * ox_price), land_days, 0.0)
            models["road"] = (_paved_road_inputs(int(LAND_FREIGHT_TEAM_SIZE)),
                              freight_cost.CarrierPrices(freight_physics.CART.self_mass_kg * vehicle_wood,
                                                         team * ox_price), land_days, 0.0)
        if "pack" not in unpriced:
            models["pack"] = (_caravan_inputs(), freight_cost.CarrierPrices(
                string * freight_physics.PACK_SADDLE.self_mass_kg * vehicle_wood, string * mule_price), land_days, 0.0)
        for mode in self.needs.modes_carrying("goods"):
            porter = self.needs.mode_carrier(mode)["porter"]
            if porter:
                models[mode] = (porter["inputs"], freight_cost.CarrierPrices(0.0), land_days, 0.0)
        if RAIL_MODE not in unpriced:
            models[RAIL_MODE] = (train["inputs"], freight_cost.CarrierPrices(train["stock_kg"] * stock_price), land_days, 0.0)
        if SEA_MODE not in unpriced:
            hull_inputs = sea_freight.sailing_freight_physical_inputs(crew=crew)
            hull_kg = hull_inputs.cargo_tonnes * sea_freight.HULL_TIMBER_KG_PER_CARGO_TONNE
            models[SEA_MODE] = (hull_inputs, freight_cost.CarrierPrices(hull_kg * vehicle_wood),
                                sea_freight.SAILING_DAYS_PER_YEAR, sea_freight.hull_loss_per_thousand_km(crew))
        return models, unpriced

    def freight_mode_costs(self, imbalance=1.0, modes=None, cargo=None):
        """{mode: home money per tonne-km}: feed and crew, the carrier's capital at the market rate, hull losses, and
        the return leg (`imbalance` 0 when flows balance, 1 when the carrier comes back empty). The same function
        prices foreign legs and domestic hauls. A mode whose feed or carrier has no price is absent. With `cargo`,
        only the modes that carry it and whose required nodes this society holds are offered."""
        land_wage = self.needs.labour_quote(self.trade_of_role("unskilled"))
        sea_wage = self.needs.labour_quote(self.trade_of_role("sailor"))
        rate = self.needs.market_rate()
        walking = frozenset(self.needs.carriage_facts()["walking_modes"])
        carrying = frozenset(self.needs.modes_carrying(cargo)) if cargo else frozenset()
        feed_prices = {}

        def feed_price(mode):
            material = self.carrier_feed_material(mode)
            if material not in feed_prices:
                feed_prices[material] = self.needs.material_price[material]
            return feed_prices[material]
        costs = {mode: freight_cost.freight_money_per_tonne_km(
                    inputs, feed_price(mode), sea_wage if mode == SEA_MODE else land_wage, prices, rate, working_days,
                    imbalance, loss, cargo_walks=mode in walking)
                for mode, (inputs, prices, working_days, loss) in self.carrier_models().items()
                if (modes is None or mode in modes) and (cargo is None or mode in carrying) and feed_price(mode) is not None}
        if cargo is None:
            return costs
        return rules.usable_mode_costs(costs, self.needs.modes_usable((self.needs.held_techniques(False),), cargo))

    def freight_handling_costs(self):
        """{mode: home money per tonne} charged once per leg of that mode: port handling at sea, and the tolls or port
        dues the geography states for each mode (paid at the carrier's wage)."""
        wage = self.needs.labour_quote(self.trade_of_role("unskilled"))
        return rules.handling_money_per_tonne(self.needs.carriage_facts()["dues_hours_per_tonne"], wage, SEA_MODE,
                                              sea_freight.PORT_HANDLING_HOURS_PER_TONNE)
