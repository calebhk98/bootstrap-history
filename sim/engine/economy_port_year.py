"""The agent economy inside a game: the switch, opening it, its year, and what the engine's seams read.

Part of the port (with economy_port.py and economy_port_setup.py, the only engine modules that import
`sim.economy`). Its whole state lives in `state.economy.agent_economy`, so a saved game resumes the
same economy. The engine's own price, wage and rate code asks `answers()` and falls back to its old
figures while the switch is off or before the economy has opened.
"""
import collections
import math
import os

from sim.agents.api import COIN_RESTRIKE_SHARE_PER_YEAR
from sim.constants import declare
from sim.economy import api as economy_api
from sim.world.demography_turnover import working_age_turnover
from sim.economy.api import (EDGE_EXTERNAL, EDGE_LEGACY, AgentOrders, Economy, GoodsMove, Offer, Producer,
                             YearInputs, expected_output_prices, external_orders, live_input_prices, live_wages,
                             trade_premium, variable_cost_per_run)

from . import economy_port_cargo, solve_cache
from .data import load_civ
from .economy_port_key import spin_up_key
from .economy_port_setup import build_setup, opening_values

SWITCH_ENVIRONMENT = "ROME_AGENT_ECONOMY"
OUTCOMES_KEPT = 100   # yearly outcomes held in memory for the health figures
SPIN_UP_CACHE_DIRECTORY = os.path.join(os.path.dirname(solve_cache.DEFAULT_CACHE_DIRECTORY), "agent_economy")
SPIN_UP_TOLERANCE = declare(
    "SPIN_UP_TOLERANCE", 0.02, kind="temporary_heuristic",
    unit="largest yearly relative change of the price level and the main prices", source=None, confidence="D",
    why="The hidden years before a game run until the economy stops moving more than this a year, so the "
        "first year the player sees is the economy's own and not the price solver's. A looser figure "
        "starts sooner and further from settled.")
SPIN_UP_MAXIMUM_YEARS = declare(
    "SPIN_UP_MAXIMUM_YEARS", 30, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="A bound on the hidden years, so a economy that keeps moving still starts in a known time.")
SPIN_UP_TRIMMED_YEARS = declare(
    "SPIN_UP_TRIMMED_YEARS", 15, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="After the workforce is trimmed to the hours employers want, the skilled trades need a few years for "
        "wages to leave the market's ceiling and for entry to fill the thinned trades. Their wages swing by "
        "multiples a year in thin labour markets and never meet a tolerance, so the stage is a fixed length, "
        "as long as that takes and no longer (shorter lengths left trades glutted or the staffing wage "
        "reference too high in some civilisations; found by trying lengths against the opening-workforce tests). "
        "A model of hiring and training would derive it per trade.")
SPIN_UP_WATCHED_GOODS = 12
FOREIGN_TRADE_SHARE = declare(
    "FOREIGN_TRADE_SHARE", 0.1, kind="temporary_heuristic",
    unit="share of the home market a good's imports or exports can reach in a year", source=None, confidence="D",
    why="How much can cross a border in a year is set by ships, carts and merchants on the routes; the "
        "engine's carrier fleet (foreign_payments, OPENING_CARRIERS_PER_ROUTE) is not yet the economy's. "
        "A share of the home market stands in so trade is bounded.")
PARTNER_SPEND_SHARE_PER_YEAR = declare(
    "PARTNER_SPEND_SHARE_PER_YEAR", 0.05, kind="temporary_heuristic",
    unit="share of a partner's coin it can spend on this society's goods in a year", source=None, confidence="D",
    why="A partner pays for what it buys from the coin it holds, so its purchases fall as it pays coin out "
        "(price-specie flow). How much of its money a partner spends abroad a year is not measured; the "
        "partner as a full economy (Complaint 382) would decide it.")


def switch_requested(cfg) -> bool:
    """On unless config `agent_economy` is explicitly False; the environment variable overrides
    the config either way ("1" forces on, "0" forces off)."""
    override = os.environ.get(SWITCH_ENVIRONMENT)
    if override in ("0", "1"):
        return override == "1"
    return cfg.get("agent_economy") is not False


class AgentEconomy:
    """One game's agent economy. Not saved itself: it rebuilds from `state.economy.agent_economy`."""

    def __init__(self, sim):
        self._sim = sim
        self._economy = None
        self._answers = None
        self._stale = set()
        self.outcomes = collections.deque(maxlen=OUTCOMES_KEPT)   # recent yearly outcomes, for health figures; not saved
        self._built_from = None          # the stored dict the live economy belongs to; a load replaces it

    @property
    def stored(self):
        return self._sim.state.economy.agent_economy

    def on(self) -> bool:
        return bool(self.stored.get("on"))

    def opened(self) -> bool:
        return self._economy is not None or "record" in self.stored

    def economy(self) -> Economy:
        if self._built_from is not self.stored:
            self._economy, self._answers = None, None
        if self._economy is None:
            if "record" in self.stored:
                setup = build_setup(self._sim, self.stored["opening"])
                self._economy = economy_api.economy_from_record(setup, self.stored["record"])
            else:
                opening = opening_values(self._sim)
                setup = build_setup(self._sim, opening)
                record = solve_cache.cached_json(
                    spin_up_key(setup),
                    lambda: self._spun_up(setup), cache_dir=SPIN_UP_CACHE_DIRECTORY)
                self._economy = economy_api.economy_from_record(setup, record)
                self.stored["opening"] = opening
                self._save()
            self._built_from = self.stored
            self.sync_ways()
        return self._economy

    def sync_ways(self):
        """Give the live economy the ways the game has built so far; its hauls are priced over them from now on."""
        if self._economy is not None:
            economy_api.set_improvements(self._economy, self._sim.state.economy.improvements)

    def _spun_up(self, setup):
        """The record after the hidden years; the same opening always gives the same one, so it is cached
        on disk with the price solver's results (keyed on the data files and the source)."""
        self._economy = economy_api.blank_economy(setup)
        self._spin_up()
        return economy_api.export_record(self._economy)

    def cohort_incomes(self):
        return economy_api.cohort_incomes(self.economy())

    # ---- the year -----------------------------------------------------------------------------
    def run_year(self):
        economy = self.economy()
        self.sync_ways()
        orders = self._seat_orders()
        orders.update(self._external_orders())
        from .project_materials import tonnes_per_unit
        legs = self._sim.cargo_legs()
        moves, cargo_orders, fundings = economy_port_cargo.cargo_orders(economy, legs, tonnes_per_unit)
        economy_api.move_goods(economy, moves)
        economy_api.post_transfers(economy, fundings)
        orders.update(cargo_orders)
        self._strike_state_coin(economy)
        outcome = economy.step(self._inputs(orders))
        self.outcomes.append(outcome)
        self._settle_seats()
        self._sim.settle_trader_cargo(economy_port_cargo.close_cargo_accounts(economy, legs, tonnes_per_unit))
        self._settle_foreign_coin()
        self._answers = None
        self._save()
        return outcome

    def _strike_state_coin(self, economy):
        """The cut the home state decided on this year lowers the metal in the coin it issues."""
        cut = self._sim.state_treasury().record.coin_cut_share
        economy.strike_lighter_coin(cut, COIN_RESTRIKE_SHARE_PER_YEAR)

    # ---- each seat's concerns sell in the same market ----------------------------------------
    def _seat_orders(self):
        """Every seat's running concerns' output for the year, one agent per seat named by its seat id."""
        sim = self._sim
        orders = {}
        for seat_id in sorted(sim.state.seats):
            with sim.act_as(seat_id):
                orders.update(self._acting_seat_orders(seat_id))
        return orders

    def _acting_seat_orders(self, agent_id):
        """The acting seat's running concerns' output for the year, handed over from the engine through the
        legacy edge (the engine's purse is not yet an account in the book: Complaint 382) and offered at
        what the concern costs to make it at the economy's own prices and wages (_concern_reservation)."""
        sim, economy = self._sim, self._economy
        area_map = economy.area_map
        tile = sim.labour.base_tile() if sim.labour.base_tile() in economy.setup.tiles else economy.setup.capital_tile
        projects = sim.state.projects
        view = economy.view()
        moves, offers = [], []
        for node_id in sorted(projects.operating):
            if node_id in projects.granted or not sim.is_venture(node_id):
                continue
            baskets = sim.concern_baskets_now(node_id)
            if baskets is None:
                continue
            ramp = sim.venture_ramp(node_id)
            for material, units in sorted(baskets.outputs.items()):
                quantity = units * ramp
                if quantity <= 0.0 or material not in area_map.goods():
                    continue
                moves.append(GoodsMove(EDGE_LEGACY, agent_id, material, tile, quantity, "concern output"))
                cost = self._concern_reservation(node_id, material, tile, view, agent_id)
                offers.append(Offer(agent_id, material, area_map.area_of(material, tile), tile, quantity, cost))
        economy_api.move_goods(economy, moves)
        return {agent_id: AgentOrders(offers=tuple(offers))} if offers else {}

    def _concern_reservation(self, node_id, material, tile, view, agent_id) -> float:
        """The least the seat takes for a unit of a concern's output: the unit's share, by value, of
        the variable cost of the cheapest technique the concern holds that the economy knows, at the
        economy's live prices and wages. With no such technique it sells at what the market pays."""
        from .prices import default_production_entries
        from .producer_costs import entry_keys_held_for
        recipes = self._economy.setup.recipes
        keys = entry_keys_held_for(node_id, default_production_entries(), self._sim.techniques_in_use())
        best = None
        for key in sorted(keys):
            recipe = recipes.get(key)
            if recipe is None or material not in recipe.outputs:
                continue
            probe = Producer(agent_id, agent_id, key, tile, 1.0)
            prices = expected_output_prices(probe, recipe, view) or {}
            revenue = sum(recipe.outputs[good] * prices.get(good, 0.0) for good in recipe.outputs)
            cost = variable_cost_per_run(recipe, live_input_prices(probe, recipe, view),
                                         live_wages(probe, recipe, view))
            if revenue > 0.0 and math.isfinite(cost) and prices.get(material):
                per_unit = cost * prices[material] / revenue
                best = per_unit if best is None else min(best, per_unit)
        return best if best is not None else 0.0

    # ---- foreign partners trade at the port -----------------------------------------------------
    def _external_orders(self):
        """Imports offered at the cheapest partner's landed price and exports bid for at the partner's
        own price less carriage, on the port tile (sim/economy/foreign.py). How much can cross is a
        share of the home market, standing in for the carriers' capacity (FOREIGN_TRADE_SHARE). A good the
        trader actors carry in a direction this year is theirs to carry that way (foreign_actor_trade.py)."""
        sim, economy = self._sim, self._economy
        partners = sim.foreign_economies()
        if not partners:
            return {}
        from .project_materials import tonnes_per_unit
        offers_api = sim.goods_market
        routes = {partner: offers_api._route_from(partner) for partner in partners}
        volumes = economy_api.traded_volumes(economy)
        opening = economy_api.opening_quantities(economy)
        landed, export_prices, available, wanted = {}, {}, {}, {}
        for good in economy.area_map.goods():
            market = max(volumes.get(good, 0.0), opening.get(good, 0.0))
            if market <= 0.0:
                continue
            for partner in partners:
                route = routes[partner]
                price = offers_api.landed_price(good, partner, route)
                if (price is not None and price > 0.0 and price < landed.get(good, float("inf"))
                        and not sim.actors_carry(good, False, partner)):
                    landed[good] = price
                partner_price = sim.partner_price_per_unit(partner, good)
                if route is not None and partner_price and not sim.actors_carry(good, True, partner):
                    net = partner_price - route.cost_per_tonne * tonnes_per_unit(good)
                    if net > export_prices.get(good, 0.0):
                        export_prices[good] = net
            available[good] = wanted[good] = market * FOREIGN_TRADE_SHARE
        coin = economy.setup.coin_per_unit
        landed = {good: price / coin for good, price in landed.items()}
        export_prices = {good: price / coin for good, price in export_prices.items()}
        stand_in = external_orders(landed, export_prices, available, wanted,
                                   economy.area_map.area_of, economy.setup.port_tile,
                                   export_budget=self._partner_spending(partners) / coin)
        return {EDGE_EXTERNAL: stand_in}

    def price_response(self, material, landed_tonnes, taken_tonnes):
        """Factor on a material's price at the port once more tonnes land there or are taken out, from the book the
        market last cleared; None when the market has none."""
        from .project_materials import tonnes_per_unit
        per_unit = tonnes_per_unit(material)
        if not per_unit or per_unit <= 0.0 or material not in self.economy().area_map.goods():
            return None
        return economy_api.price_response(self.economy(), material, landed_tonnes / per_unit, taken_tonnes / per_unit)

    def _partner_spending(self, partners) -> float:
        """What the partners can spend on this society's goods this year, in home money: a share of the
        coin each still holds (its opening stock and what the ledger says it gained or paid out)."""
        sim = self._sim
        total = 0.0
        for partner in partners:
            standard = load_civ(partner)["coin_standard"]
            metal_price = sim._coin_metal_price(standard["material"])
            if not metal_price:
                continue
            held = (sim._partner_coin_opening_units(partner)
                    + sim._foreign_ledger(partner)["partner_coin_units"])
            total += max(0.0, held) * standard["kg_per_unit"] * metal_price
        return total * PARTNER_SPEND_SHARE_PER_YEAR

    def _settle_foreign_coin(self):
        """The year's foreign trade paid for in the partners' ledgers (foreign_payments): imports pay coin
        to them and exports draw coin from them, so a partner paying out coin sees its price level fall
        and buys less (price-specie flow). Trade with several partners is split evenly among them; the
        economy's external edge does not yet say which partner each good went to."""
        sim, economy = self._sim, self._economy
        partners = sim.foreign_economies()
        if not partners:
            return
        coin = economy.setup.coin_per_unit
        paid_in = economy_api.external_trade_net(economy)            # exports less imports
        volume = economy_api.external_trade_volume(economy)
        imports, exports = (volume - paid_in) / 2.0 * coin, (volume + paid_in) / 2.0 * coin
        for partner in partners:
            standard = load_civ(partner)["coin_standard"]
            metal_price = sim._coin_metal_price(standard["material"])
            if not metal_price:
                continue
            per_partner_coin = standard["kg_per_unit"] * metal_price
            if imports > 0.0:
                sim._settle_flow(partner, 1.0, imports / len(partners), per_partner_coin)
            if exports > 0.0:
                sim._settle_flow(partner, -1.0, exports / len(partners), per_partner_coin)

    def _settle_seats(self):
        """What each seat's goods fetched goes back to the engine; what did not sell goes back too."""
        coin = self._economy.setup.coin_per_unit
        self.stored["seat_takings"] = {
            seat_id: economy_api.settle_agent_takings(self._economy, seat_id, EDGE_LEGACY) * coin
            for seat_id in sorted(self._sim.state.seats)}

    def _inputs(self, engine_orders) -> YearInputs:
        sim = self._sim
        population = sim.population
        total = float(population.total)
        weather = sim._pooled_farm_weather_multiplier(sim.state.scenario.year)
        economy = self._economy
        yields = {producer_id: weather for producer_id, producer in economy_api.producers_of(economy).items()
                  if economy.setup.land_per_run.get(producer.recipe_id, 0.0) > 0.0}
        entrant_share, attrition_share = working_age_turnover(population)
        return YearInputs(year=sim.state.scenario.year, population_by_tile=sim.labour.settlement_tiles(),
                          working_age_share=population.working_age / total if total > 0.0 else 0.0,
                          entrant_share=entrant_share, attrition_share=attrition_share,
                          yield_factor_by_producer=yields, engine_orders=engine_orders, harvest_factor=weather)

    def _spin_up(self):
        """Hidden years from the opening until prices and the interest rate settle; then the price level
        is rebased to one."""
        economy = self._economy
        basket = economy_api.opening_quantities(economy)
        prices = economy.setup.opening_prices
        watched = sorted(basket, key=lambda good: -basket[good] * prices.get(good, 0.0))[:SPIN_UP_WATCHED_GOODS]
        inputs = YearInputs(year=0, population_by_tile={}, working_age_share=economy.setup.working_share,
                            yield_factor_by_producer={}, engine_orders={})
        self._settle(economy, inputs, watched)
        economy_api.trim_workforce_to_expected_hours(economy)
        self._settle_trimmed(economy, inputs)
        economy_api.finish_spin_up(economy)

    @staticmethod
    def _settle(economy, inputs, watched):
        """Hidden years until the price level, the rate and the main prices move less than the tolerance a year."""
        before = None
        for _year in range(int(SPIN_UP_MAXIMUM_YEARS)):
            outcome = economy.step(inputs)
            now = ([outcome.basket_price_level, economy_api.interest_rate(economy) or 0.0]
                   + [outcome.prices.get(good, 0.0) for good in watched])
            if before is not None and max(
                    abs(new / old - 1.0) for new, old in zip(now, before) if old > 0.0) < SPIN_UP_TOLERANCE:
                break
            before = now

    @staticmethod
    def _settle_trimmed(economy, inputs):
        """The few further years, from the state the first stage left, in which the trimmed trades' wages and
        entry settle."""
        for _year in range(int(SPIN_UP_TRIMMED_YEARS)):
            economy.step(inputs)

    def _save(self):
        self.stored["record"] = economy_api.export_record(self._economy)

    # ---- what the seams read ------------------------------------------------------------------
    def answers(self):
        """(prices by good, hours-weighted wage per hour by trade, rate), for this year; built once a year. A good
        whose markets have not cleared lately shows what it costs to make at today's prices and wages, or
        its last price when nothing makes it; `stale_goods()` names those."""
        if self._answers is None or self._built_from is not self.stored:
            self.economy()
            wages = economy_api.wages_by_trade_weighted(self._economy)
            coin = self._economy.setup.coin_per_unit
            prices, self._stale = economy_api.shown_prices_of(self._economy)
            self._answers = ({good: price * coin for good, price in prices.items()},
                             {trade: wage * coin for trade, wage in wages.items()},
                             economy_api.interest_rate(self._economy))
        return self._answers

    def stale_goods(self):
        """Goods whose shown price is not a market's: not cleared within notional.RECENT_TRADE_YEARS."""
        self.answers()
        return set(self._stale)

    def price_ratio(self, materials, old_prices):
        """The new price over the engine's own cost, for the first of `materials` both price; None if none."""
        prices = self.answers()[0]
        for material in materials:
            old = old_prices.get(material, 0.0)
            new = prices.get(material)
            if new is not None and old > 0.0:
                return new / old
        return None

    def people_by_trade(self):
        """The labour core's people by trade, or None before the economy has been opened."""
        if self._economy is None and "record" not in self.stored:
            return None
        return economy_api.people_by_trade(self.economy())

    def worker_years_by_recipe(self):
        """Worker-years a year the economy's producers can put into each recipe at full capacity."""
        economy = self.economy()
        years = {}
        for producer in economy_api.producers_of(economy).values():
            recipe = economy.setup.recipes.get(producer.recipe_id)
            if recipe is not None:
                years[producer.recipe_id] = years.get(producer.recipe_id, 0.0) + (
                    producer.capacity_runs * sum(recipe.labour_hours.values()) / economy.setup.working_hours_per_year)
        return years

    def wage_per_hour(self, trade):
        """The trade's wage in its labour markets; a trade no producer hires (soldiers, scribes) is paid
        what its training adds to the unskilled wage, so every wage stands on the same market."""
        wages = self.answers()[1]
        if trade in wages:
            return wages[trade]
        setup = self._economy.setup
        unskilled = wages.get(setup.unskilled_trade)
        if unskilled is None:
            return None
        return unskilled * (1.0 + trade_premium(setup, trade))

    def land_rent_per_hectare(self):
        """Mean rent per hectare-year the land market let land at last year, in coin."""
        return economy_api.land_rent_per_hectare(self.economy()) * self._economy.setup.coin_per_unit

    def land_rent_at_tile(self, tile):
        """Rent per hectare-year on one tile in coin (the mean where none was let there)."""
        return economy_api.land_rent_at_tile(self.economy(), tile) * self._economy.setup.coin_per_unit

    def land_rent_paid_by_tile(self):
        """Rent producers paid on each tile where land was let last year, in coin."""
        coin = self._economy.setup.coin_per_unit
        return {tile: rent * coin for tile, rent in economy_api.land_rent_paid_by_tile(self.economy()).items()}

    def rate(self):
        return self.answers()[2]

    def credit_room(self, borrower_id):
        """What the credit market will still advance one borrower; None before lenders have met."""
        self.answers()
        return economy_api.credit_room(self._economy, borrower_id)
