"""What the engine hands the agent economy for its year: the `EconomyYearInputs`. Part of the port.

Each figure is read from the game through the port's world (the weather, the people, the state, the land, the credit lines)
or from the port's rule modules (port_land, port_flight, port_bondage, port_institutions, port_sites, port_levy)."""
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.labour import api as labour_api
from .unit_mass import tonnes_per_unit

from . import port_actors, port_bondage, port_flight, port_institutions, port_land, port_levy, port_sites


def recipe_outputs(economy):
    """{recipe id: {good: quantity a run}} of the recipes the economy runs."""
    return {recipe_id: recipe.outputs for recipe_id, recipe in economy_api.recipes_of(economy).items()}


class YearInputsBuilder:

    def __init__(self, world, agent, seats):
        self._world = world
        self._agent = agent
        self._seats = seats

    def build(self, engine_orders, border_accounts=((), ())) -> EconomyYearInputs:
        sim = self._world
        weather = sim.farm.pooled_weather_multiplier(sim.scenario.year, harmed=False)   # harm is applied per producer below
        economy = self._agent.economy()
        harmed = sim.farm.externality_yield_factors(sim.scenario.year)
        yields = port_sites.crop_yields(economy, weather, sim.farm.weather_by_tile(sim.scenario.year))
        yields = port_sites.harmed_yields(yields, harmed, economy_api.producers_of(economy))
        people = sim.labour.settlement_tiles()
        bands = sim.state.regional_people_by_band()    # demography's (children, working age, elderly) by tile
        return EconomyYearInputs(year=sim.scenario.year, population_by_tile=people,
                          working_people_by_tile={tile: bands[tile][1] for tile in people if tile in bands},
                          yield_factor_by_producer=yields, engine_orders=engine_orders, harvest_factor=weather,
                          state_capacity=sim.finance.state_reach(),
                          import_accounts=border_accounts[0], export_accounts=border_accounts[1],
                          labour_levy_hours_per_worker=port_levy.levy_hours_per_worker(sim),
                          debt_relief_tiles=port_land.debt_relief_tiles(sim, economy),
                          title_moves=port_land.title_moves(sim, economy),
                          farmed_forms=port_land.farmed_forms(sim, economy),
                          tax_rates=port_land.tax_rates(sim),
                          land_tax_share_of_rent=port_land.land_tax_share_of_rent(sim),
                          **port_flight.flight_values(sim, economy),
                          institutions=port_institutions.held(sim),
                          durable_users=tuple(port_actors.held_account(buyer)
                                              for buyer in sorted(sim.scenario.actors.actors)),
                          bondage_tiles=port_bondage.bondage_tiles(sim, economy),
                          bonded_for_sale=port_bondage.bonded_for_sale(sim, economy),
                          schools=self.seat_schools(),
                          standing_bids=self.seats_standing_bids(), credit_asks=self.credit_asks(),
                          site_limits=tuple(port_sites.site_limits(sim, recipe_outputs(economy), economy_api.economy_tiles(economy))))

    def seat_schools(self):
        """The trade schools of every playing seat, each in the labour area of the seat's base tile: what the labour core trains
        through (`labour.api.schools_of_actor`)."""
        sim = self._world
        schools = []
        for seat_id in sim.state.seats_playing():
            with sim.scenario.act_as(seat_id):
                seats = sim.labour.trade_schools()
                tile = self._agent.tile_in_economy(sim.labour.base_tile())
            if seats:
                schools.extend(labour_api.schools_of_actor(seat_id, economy_api.labour_area(tile), seats))
        return tuple(schools)

    def credit_asks(self):
        """Each playing seat's credit line, as a request for the year's clearing: the line its name and earning
        give (the market's room not yet applied) in the economy's money."""
        sim, economy = self._world, self._agent.economy()
        coin, currency = economy_api.coin_per_unit(economy), economy_api.currency_id(economy)
        rate = sim.finance.market_rate()
        asks = []
        for seat_id in sim.state.seats_playing():
            with sim.scenario.act_as(seat_id):
                base, floor, serviceable = sim.finance.credit_line_sought()
                # the running-cost floor is asked of the lenders too: the seat's ceiling is what they grant
                line = max(0.0, min(base, serviceable), floor) * sim.scenario.price_index / coin
            if line > 0.0:
                asks.append(economy_api.credit_line_request(seat_id, currency, line, rate))
        return tuple(asks)

    def seats_standing_bids(self):
        """Each playing seat's running works' draws on materials, as bids on that seat's tile for firm entry to read
        (port_actors.standing_bids)."""
        sim, economy = self._world, self._agent.economy()
        drawn = sim.market_flows()["drawn"]
        bids = []
        for seat_id in sorted(sim.state.seats_playing()):
            if not drawn.get(seat_id):
                continue
            with sim.scenario.act_as(seat_id):
                tile = self._agent.tile_in_economy(sim.labour.base_tile())
            bids.extend(port_actors.standing_bids(economy, seat_id, drawn[seat_id], tile, tonnes_per_unit,
                                                  sim.economy.materials_in))
        return tuple(bids)
