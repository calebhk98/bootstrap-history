"""What the engine hands the agent economy for its year: the `YearInputs`. Part of the port.

Each figure is read from the game through the port's world (the weather, the people, the state, the land, the credit lines)
or from the port's rule modules (port_land, port_flight, port_bondage, port_institutions, port_sites, port_levy)."""
from sim.economy import api as economy_api
from sim.economy.api import YearInputs
from sim.world.material_units import tonnes_per_unit

from . import port_actors, port_bondage, port_flight, port_institutions, port_land, port_levy, port_sites


def recipe_outputs(economy):
    """{recipe id: {good: quantity a run}} of the recipes the economy runs."""
    return {recipe_id: recipe.outputs for recipe_id, recipe in economy_api.recipes_of(economy).items()}


class YearInputsBuilder:

    def __init__(self, world, agent, seats):
        self._world = world
        self._agent = agent
        self._seats = seats

    def build(self, engine_orders, border_accounts=((), ())) -> YearInputs:
        sim = self._world
        weather = sim._pooled_farm_weather_multiplier(sim.year, harmed=False)   # harm is applied per producer below
        economy = self._agent.economy()
        harmed = sim.externality_yield_factors(sim.year)
        yields = port_sites.crop_yields(economy, weather, sim.farm_weather_by_tile(sim.year))
        yields = port_sites.harmed_yields(yields, harmed, economy_api.producers_of(economy))
        people = sim.labour.settlement_tiles()
        bands = sim.view("regional_people_by_band")()    # demography's (children, working age, elderly) by tile
        return YearInputs(year=sim.year, population_by_tile=people,
                          working_people_by_tile={tile: bands[tile][1] for tile in people if tile in bands},
                          working_hours_per_year=sim.view("hours_per_person_year")(),
                          yield_factor_by_producer=yields, engine_orders=engine_orders, harvest_factor=weather,
                          state_capacity=sim.state_reach(),
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
                                              for buyer in sorted(sim.actors.actors)),
                          bondage_tiles=port_bondage.bondage_tiles(sim, economy),
                          bonded_for_sale=port_bondage.bonded_for_sale(sim, economy),
                          standing_bids=self.founder_standing_bids(), credit_asks=self.credit_asks(),
                          site_limits=tuple(port_sites.site_limits(sim, recipe_outputs(economy), economy_api.economy_tiles(economy))))

    def credit_asks(self):
        """Each playing seat's credit line, as a request for the year's clearing: the line its name and earning
        give (the market's room not yet applied) in the economy's money."""
        sim, economy = self._world, self._agent.economy()
        coin, currency = economy_api.coin_per_unit(economy), economy_api.currency_id(economy)
        rate = sim.market_rate()
        asks = []
        for seat_id in sorted(sim.playing_seats() or sim.state.seats):
            with sim.act_as(seat_id):
                base, _floor, serviceable = sim.credit_line_sought()
                line = max(0.0, min(base, serviceable)) * sim.price_index / coin
            if line > 0.0:
                asks.append(economy_api.credit_line_request(seat_id, currency, line, rate))
        return tuple(asks)

    def founder_standing_bids(self):
        """The founder's running works' draws on materials, as bids for firm entry to read (port_actors.standing_bids)."""
        sim = self._world
        tiles = sorted(self._seats.seat_tiles())
        if not tiles:
            return ()
        return port_actors.standing_bids(self._agent.economy(), sim._market_flows(), tiles[0], tonnes_per_unit,
                                         sim.economy.materials_in)
