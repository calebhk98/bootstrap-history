"""The agent economy's year: what the port posts to it, the step, and what settles back into the game. Part of the port.

The year only sequences work the port's modules own: the cargo legs (port_cargo), the staff (port_staff), the goods orders
(port_goods_orders), the levy and dues (port_dues), the bondage purchases (port_bondage), the sites (port_sites), the actors'
trade (port_actor_trade), the seats' concerns (port_seat_concerns) and the inputs the engine hands over (port_year_inputs)."""
from sim.agents.api import COIN_RESTRIKE_SHARE_PER_YEAR
from sim.demography.api import MovePeople
from sim.economy import api as economy_api
from .unit_mass import tonnes_per_unit

from . import (port_bondage, port_cargo, port_cropland, port_dues, port_duty, port_goods_orders, port_health, port_sites,
               port_staff, trade_duty)
from .port_year_inputs import recipe_outputs


class YearRun:

    def __init__(self, world, agent, seats, trade, inputs):
        self._world = world
        self._agent = agent
        self._seats = seats
        self._trade = trade
        self._inputs = inputs
        # The last year this process ran, for the tools that print its accounts. Nothing in the game reads it; the health
        # figures are in the stored record. None until a year has run here (a loaded game has run none yet).
        self.last_outcome = None

    def run_year(self):
        world, agent = self._world, self._agent
        economy = agent.economy()
        legs = world.foreign.cargo_legs()
        # the year's working day is set before any hours are posted, so posting and settling convert people and hours alike;
        # the tariff the home state holds is read now, as the landed goods are priced
        economy.change_setup(**port_cropland.follow_farm_sites(world, economy_api.economy_tiles(economy),
                                                                      economy_api.crop_site_inputs(economy)[0]),
                             working_hours_per_year=float(world.scenario.HOURS_PER_PERSON_YEAR),
                             carried_tariff=port_duty.carried_tariffs(
                                 economy_api.economy_countries(economy), economy_api.home_country(economy),
                                 lambda country: trade_duty.import_terms(world, country)[0]))
        agent.sync_ways()
        agent.admit_techniques()
        orders, offered, seat_inputs = self._seats.orders()
        moves, cargo_orders, fundings = port_cargo.cargo_orders(economy, legs, tonnes_per_unit)
        economy_api.move_goods(economy, moves)
        economy_api.post_transfers(economy, fundings)
        orders.update(cargo_orders)
        self.strike_state_coin(economy)
        sales, purchases = self._trade.post_orders(orders)
        staff_orders, staff_posted = port_staff.post(world, economy, world.state.seats_playing(),
                                                     agent.tile_in_economy, agent.stored.setdefault("trades_lacking_logged", {}))
        orders.update(staff_orders)
        actor_staff_orders, actor_staff_posted = port_staff.post_actors(world, economy, agent.actor_tile)
        orders.update(actor_staff_orders)
        goods_orders, goods_posted = port_goods_orders.post(world, economy, agent.stored.get("seat_orders", {}),
                                                            agent.tile_in_economy)
        orders.update(goods_orders)
        economy_api.watch_tiles(economy, self._seats.seat_tiles())
        outcome = economy.step(self._inputs.build(orders, port_cargo.border_accounts(economy, legs)))
        agent.stored.pop("seat_orders", None)   # spent only once the step has run; a step that raises keeps the orders
        agent.figures.forget()
        port_bondage.settle_purchases(world, economy, outcome)
        if outcome.migrated_by_tile:   # the labour market's moves go to demography, which owns where people live
            world.send(MovePeople(dict(outcome.migrated_by_tile)))
        port_sites.deplete(world, outcome.extraction, recipe_outputs(economy))
        port_health.note_year(agent.stored, outcome)
        self.last_outcome = outcome
        self._trade.settle(sales, purchases)
        port_staff.settle(world, economy, staff_posted)
        port_staff.settle_actors(world, economy, actor_staff_posted)
        agent.stored["seat_trades"] = port_goods_orders.settle(world, economy, goods_posted)
        port_dues.settle(world, economy)
        self._seats.settle(offered, seat_inputs)
        world.foreign.settle_trader_cargo(port_cargo.close_cargo_accounts(economy, legs, tonnes_per_unit))
        agent.figures.forget()
        agent.note_year_run()
        self.note_volume_baseline(economy)
        return outcome

    def strike_state_coin(self, economy):
        """The cut the home state decided on this year lowers the metal in the coin it issues."""
        cut = self._world.finance.state_treasury().record.coin_cut_share
        self._agent.figures.forget()
        economy.strike_lighter_coin(cut, COIN_RESTRIKE_SHARE_PER_YEAR)

    def note_volume_baseline(self, economy):
        """The first year a good clears any quantity in a country's markets is the quantity later years are
        measured against there."""
        baseline = self._agent.stored.setdefault("volume_baseline", {})
        for country in economy_api.economy_countries(economy):
            noted = baseline.setdefault(country, {})
            for good, volume in economy_api.country_traded_volumes(economy, country).items():
                if volume > 0.0 and good not in noted:
                    noted[good] = volume
