"""The agent economy inside a game: opening it, its year, and what the engine's seams read.

Part of the port (with economy_port.py and port_setup.py, the only engine modules that import
`sim.economy`). Its whole state lives in the markets module's `agent_economy` record, so a saved game resumes the
same economy. The engine's own price, wage and rate code asks `answers()`; while the economy opens (it
reads the engine's own opening figures to build its setup) those figures answer instead.
"""
import collections
import math
import os

from sim.actors import api as actors_api
from sim.agents.api import COIN_RESTRIKE_SHARE_PER_YEAR, PURSE_CURRENCY
from sim.ledger.api import PayExchange, ReceiveFromExchange
from sim.constants import declare
from sim.economy import api as economy_api
from sim.rekey import rekey
from sim.world.demography_turnover import working_age_turnover
from sim.economy.api import (EDGE_EXTERNAL, EDGE_LEGACY, AgentOrders, Economy, GoodsMove, Offer, Producer,
                             YearInputs, expected_output_prices, external_orders, live_input_prices, live_wages,
                             trade_premium, variable_cost_per_run)

from sim.foreign_trade.api import SettleFlow, country_trade_years
from . import trade_duty, port_bondage, port_levy, port_actors, port_cargo, port_cropland, port_flight, port_institutions, port_land, port_late, port_seats, port_sites
from sim.materials.api import ProducerCapacityCache
from .port_key import spin_up_key
from .port_coin import priced_at_the_margin
from .port_setup import build_setup, opening_values
from .port_tiles import TilePricesMixin
from sim.world.material_units import tonnes_per_unit
from sim.prices.api import prices as price_solver, solve_cache
from .spin_up import (SPIN_UP_CACHE_DIRECTORY, SPIN_UP_MAXIMUM_YEARS, SPIN_UP_MEASURED_YEARS, SPIN_UP_TOLERANCE,  # noqa: F401
                      SPIN_UP_TRIMMED_YEARS, SPIN_UP_YEARS_ENV, spin_up_years)
from .spin_up_gap import SPIN_UP_RATE_FLOOR, change_gap, price_gap, window_gaps

OUTCOMES_KEPT = 100   # yearly outcomes held in memory for the health figures
SPIN_UP_WATCHED_GOODS = 12


def _spin_up_cache_key(setup):
    years = spin_up_years()
    return spin_up_key(setup, None if years == (int(SPIN_UP_MAXIMUM_YEARS), int(SPIN_UP_TRIMMED_YEARS)) else years)
FOREIGN_TRADE_SHARE = declare(
    "FOREIGN_TRADE_SHARE", 0.1, kind="temporary_heuristic",
    unit="share of the home market a good's imports or exports can reach in a year", source=None, confidence="D",
    why="How much can cross a border in a year is set by ships, carts and merchants on the routes; the "
        "engine's carrier fleet (sim/foreign_trade, OPENING_CARRIERS_PER_ROUTE) is not yet the economy's. "
        "A share of the home market stands in so trade is bounded.")
PARTNER_SPEND_SHARE_PER_YEAR = declare(
    "PARTNER_SPEND_SHARE_PER_YEAR", 0.05, kind="temporary_heuristic",
    unit="share of a partner's coin it can spend on this society's goods in a year", source=None, confidence="D",
    why="A partner pays for what it buys from the coin it holds, so its purchases fall as it pays coin out "
        "(price-specie flow). How much of its money a partner spends abroad a year is not measured; the "
        "partner as a full economy (Complaint 382) would decide it.")


class AgentEconomy(TilePricesMixin):
    """One game's agent economy. Not saved itself: it rebuilds from the markets module's `agent_economy` record."""

    def __init__(self, sim):
        self._sim = sim
        self._economy = None
        self._answers = None
        self._country_answers = {}
        self._stale = set()
        self._kinds = None               # (the answers they belong to, {good: kind of its shown price})
        self._capacity_cache = ProducerCapacityCache()
        self._floor_costs = {}           # need floors by country scope, valid until the economy next changes
        self._floor_costs_of = None      # the economy object they were read from
        self.outcomes = collections.deque(maxlen=OUTCOMES_KEPT)   # recent yearly outcomes, for health figures; not saved
        self._built_from = None          # the stored dict the live economy belongs to; a load replaces it
        self._years_run = 0              # years this object has run: the producers change when one closes
        self._techniques_admitted = None   # the held nodes the economy's recipes were last matched to; not saved
        self._record_stale = False       # the live economy has moved on since `stored["record"]` was exported

    @property
    def stored(self):
        return self._sim.agent_record()

    def spin_up_result(self):
        """The saved opening's first-stage result (see `_settle`); empty before the opening is saved."""
        return dict((self.stored.get("record") or {}).get("spin_up_result") or {})

    def producer_capacities(self):
        if not self.opened():
            return []
        return [(producer.recipe_id, producer.capacity_runs) for producer in economy_api.all_producers(self.economy())]

    def fugitive_share_by_tile(self):
        """{tile: share of the people who belonged to it that are away having fled the state's take}; empty before the economy opens."""
        return economy_api.fugitive_share_by_tile(self.economy()) if self.opened() else {}

    def opened(self) -> bool:
        return self._economy is not None or "record" in self.stored

    def economy(self) -> Economy:
        if self._built_from is not self.stored:
            self._economy, self._answers, self._country_answers = None, None, {}
        if self._economy is None:
            if "record" in self.stored:
                setup = build_setup(self._sim, self.stored["opening"])
                self._economy = economy_api.economy_from_record(setup, self.stored["record"])
            else:
                opening = priced_at_the_margin(self._sim, opening_values(self._sim))
                setup = build_setup(self._sim, opening)
                record = solve_cache.cached_json(
                    _spin_up_cache_key(setup),
                    lambda: self._spun_up(setup), cache_dir=SPIN_UP_CACHE_DIRECTORY)
                self._economy = economy_api.economy_from_record(setup, record)
                self.stored["opening"] = opening
                self._save()
            self._built_from = self.stored
            self._sim.state.actors.purses.adopt_book(economy_api.economy_book(self._economy),
                                                         economy_api.economy_contracts(self._economy))
            self.sync_ways()
        return self._economy

    def sync_ways(self):
        """Give the live economy the ways the game has built so far; its hauls are priced over them from now on."""
        self._floor_costs = {}
        if self._economy is not None:
            economy_api.set_improvements(self._economy, self._sim.state.economy.improvements)

    def admit_techniques(self):
        """Give the economy the entries the society's techniques now allow, when its held nodes changed since
        it last looked: they enter the saved opening (so a resumed game rebuilds them) and the live economy."""
        held = port_late.techniques_held(self._sim)
        if held == self._techniques_admitted:
            return
        self._techniques_admitted = held
        production = price_solver.default_production_entries()
        grown = port_late.opening_with_techniques(self._sim, self.stored["opening"], held, production)
        if grown is None:
            return
        self.stored["opening"] = grown
        economy_api.admit_recipes(self._economy, build_setup(self._sim, grown, production))
        self._floor_costs = {}
        self._answers = None
        self._country_answers = {}
        self._record_stale = True

    def _note_volume_baseline(self):
        """The first year a good clears any quantity in a country's markets is the quantity later years are
        measured against there."""
        baseline = self.stored.setdefault("volume_baseline", {})
        for country in self._economy.setup.countries():
            noted = baseline.setdefault(country, {})
            for good, volume in economy_api.country_traded_volumes(self._economy, country).items():
                if volume > 0.0 and good not in noted:
                    noted[good] = volume

    def volume_baseline(self, country=None):
        return dict(self.stored.get("volume_baseline", {}).get(country or self._economy.setup.civ_id, {}))

    def traded_volumes(self, country=None):
        return economy_api.country_traded_volumes(self.economy(), country)

    def opening_basket(self, country=None):
        """(units a year of each good in the country's opening basket, opening price of each in labour hours)."""
        economy = self.economy()
        return economy_api.country_opening_basket(economy, country), economy_api.opening_prices_in_hours(economy)

    def producers_stamp(self):
        return self._years_run

    def _spun_up(self, setup):
        """The record after the hidden years; the same opening always gives the same one, so it is cached
        on disk with the price solver's results (keyed on the data files and the source)."""
        self._economy = economy_api.blank_economy(setup)
        economy_api.begin_spin_up(self._economy)
        self._spin_up()
        return economy_api.export_record(self._economy, (PURSE_CURRENCY,))

    def cohort_incomes(self):
        """(people, yearly income in coin) of the household cohorts, poorest per head first."""
        coin = self._economy.setup.coin_per_unit
        return [(people, income * coin) for people, income in economy_api.cohort_incomes(self.economy())]

    def cohort_land_rents(self, tiles=None):
        """(people, rent received last year in coin) in the order of `cohort_incomes`; only rent paid on `tiles` when given."""
        coin = self._economy.setup.coin_per_unit
        return [(people, rent * coin) for people, rent in economy_api.cohort_land_rents(self.economy(), tiles)]

    # ---- the year -----------------------------------------------------------------------------
    def run_year(self):
        economy = self.economy()
        port_cropland.follow_farm_sites(self._sim, economy.setup)
        economy.setup.state_capacity = self._sim.state_reach()
        self.sync_ways()
        self.admit_techniques()
        orders = self._seat_orders()
        orders.update(self._external_orders())
        from sim.world.material_units import tonnes_per_unit
        legs = self._sim.cargo_legs()
        moves, cargo_orders, fundings = port_cargo.cargo_orders(economy, legs, tonnes_per_unit)
        economy_api.move_goods(economy, moves)
        economy_api.post_transfers(economy, fundings)
        orders.update(cargo_orders)
        self._strike_state_coin(economy)
        sales, purchases = self._actor_trade_orders(orders)
        economy_api.watch_tiles(economy, self._seat_tiles())
        outcome = economy.step(self._inputs(orders, port_cargo.border_accounts(economy, legs)))
        self._floor_costs = {}
        port_bondage.settle_purchases(self._sim, economy, outcome)
        port_sites.deplete(self._sim, outcome.extraction, self._recipe_outputs())
        self.outcomes.append(outcome)
        self._settle_actor_trade(sales, purchases)
        self._settle_seats()
        self._sim.settle_trader_cargo(port_cargo.close_cargo_accounts(economy, legs, tonnes_per_unit))
        self._note_off_map_trade(*self._settle_foreign_coin())
        self._answers = None
        self._country_answers = {}
        self._floor_costs = {}
        self._record_stale = True        # exported when the game is saved (flush_record)
        self._years_run += 1
        self._note_volume_baseline()
        return outcome

    # ---- firms', states' and traders' sales and purchases (port_actors.py) ------------------
    def held_units(self, buyer, material):
        return port_actors.held_units(self.economy(), buyer, material)

    def fleet_goods(self, buyer):
        economy = self.economy()
        production = price_solver.default_production_entries()
        return [{"material": good, "life": economy.setup.specs[good].service_life_years,
                 "held": self.held_units(buyer, good), "crew": entry["naval_crew"]}
                for good, entry in sorted(production.items()) if entry.get("naval_crew")
                and good in economy.setup.recipes and good in economy.setup.specs
                and economy.setup.recipe_allowed(good, self._actor_tile(buyer))]

    def note_sale(self, seller, material, tonnes, from_concerns):
        port_actors.note_sale(self.stored.setdefault("sales", []), seller, material, tonnes, from_concerns,
                                      self.__dict__.setdefault("_sale_index", [None, 0, {}]))

    def note_purchase(self, buyer, commodity, tonnes, budget):
        port_actors.note_purchase(self.stored.setdefault("purchases", []), buyer, commodity, tonnes, budget)

    def forget_orders(self, actor_id):
        for kind, key in (("sales", "seller"), ("purchases", "buyer")):
            if kind in self.stored:
                kept = [order for order in self.stored[kind] if order[key] != actor_id]
                if len(kept) != len(self.stored[kind]):   # a list nothing left keeps its identity, and its index
                    self.stored[kind] = kept

    def rename_agent(self, old, new):
        """`old` becomes `new` in the economy's records and in the year's stored notes (a seat handed over)."""
        if self.opened():
            economy_api.rename_agent(self.economy(), old, new)
            self._record_stale = True
        for kind in ("seat_takings", "seat_sales", "sales", "purchases"):
            if kind in self.stored:
                rekey(self.stored[kind], old, new)

    def trades_good(self, material):
        """Whether the economy has a market for the material."""
        return material in self.economy().area_map.goods()

    def _actor_tile(self, actor_id):
        actor = self._sim.view("cast")().actors.get(actor_id)
        place = actor.location() if actor is not None else None
        return place if place in self._economy.setup.tiles else self._economy.setup.capital_tile

    def _actor_trade_orders(self, orders):
        """Put the year's noted sales and purchases of the actors in the book as orders; (the sales and the purchases
        that entered, as dicts)."""
        economy, sim = self._economy, self._sim
        known = sim.view("cast")().actors
        sales = [sale for sale in self.stored.pop("sales", []) if sale["seller"] in known]
        purchases = [purchase for purchase in self.stored.pop("purchases", []) if purchase["buyer"] in known]
        from sim.world.material_units import tonnes_per_unit
        view = economy.view()

        def reservation(seller, node_id, material, tile):
            return self._concern_reservation(node_id, material, tile, view, seller)

        moves, sale_orders = port_actors.sale_orders(economy, sales, tonnes_per_unit, self._actor_tile, reservation)
        coin = economy.setup.coin_per_unit
        purchase_orders, funding = port_actors.purchase_orders(
            economy, purchases, tonnes_per_unit, self._actor_tile, sim.economy.materials_in, coin)
        economy_api.move_goods(economy, moves)
        for buyer, coin_spent, _units in funding:
            sim.send(PayExchange(buyer, coin_spent, "market purchases"))
        port_actors.fund(economy, funding)
        orders.update(sale_orders)
        orders.update(purchase_orders)
        return sales, purchases

    def _settle_actor_trade(self, sales, purchases):
        """What the actors' sales fetched and their budgets left over turn back into their coin; the goods unsold go
        back out. Bought capital assets stay with their buyer and materials are used up."""
        proceeds, refunds, _bought, delivered = port_actors.close(self._economy, sales, purchases)
        self._keep_deliveries(delivered)
        coin = self._economy.setup.coin_per_unit
        for amounts, label in ((proceeds, "market sales"), (refunds, "market purchases returned")):
            for actor_id, units in sorted(amounts.items()):
                self._sim.send(ReceiveFromExchange(actor_id, units * coin, label))

    def _keep_deliveries(self, delivered):
        """Goods a buyer that keeps its purchases bought at the market join its stores, in tonnes."""
        actors_api.keep_deliveries(self._sim.view("cast")().actors, delivered)

    def _strike_state_coin(self, economy):
        """The cut the home state decided on this year lowers the metal in the coin it issues."""
        cut = self._sim.view("state_treasury")().record.coin_cut_share
        self._floor_costs = {}
        economy.strike_lighter_coin(cut, COIN_RESTRIKE_SHARE_PER_YEAR)

    # ---- each seat's concerns sell in the same market ----------------------------------------
    def _seat_orders(self):
        """Every seat's running concerns' output for the year, one agent per seat named by its seat id."""
        sim = self._sim
        orders = {}
        for seat_id in sorted(sim.playing_seats() or sim.state.seats):   # a seat whose run ended sells nothing
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
        offered = self.__dict__.setdefault("_seat_offered", {}).setdefault(agent_id, (tile, {}))[1]
        inputs = self.__dict__.setdefault("_seat_inputs", {})
        for node_id in sorted(projects.operating):
            quantities = sim.concern_book_offer(node_id)
            if not quantities:
                continue
            inputs[agent_id] = inputs.get(agent_id, 0.0) + sim.concern_book_inputs_cost(node_id)
            for material, quantity in sorted(quantities.items()):
                offered[material] = offered.get(material, 0.0) + quantity
                moves.append(GoodsMove(EDGE_LEGACY, agent_id, material, tile, quantity, "concern output"))
                cost = self._concern_reservation(node_id, material, tile, view, agent_id)
                offers.append(Offer(agent_id, material, area_map.area_of(material, tile), tile, quantity, cost))
        economy_api.move_goods(economy, moves)
        return {agent_id: AgentOrders(offers=tuple(offers))} if offers else {}

    def _concern_reservation(self, node_id, material, tile, view, agent_id) -> float:
        """The least the seat takes for a unit of a concern's output: the unit's share, by value, of
        the variable cost of the cheapest technique the concern holds that the economy knows, at the
        economy's live prices and wages. With no such technique it sells at what the market pays."""
        from sim.prices.api import prices as price_solver, rules as price_rules
        recipes = self._economy.setup.recipes
        keys = price_rules.entry_keys_held_for(node_id, price_solver.default_production_entries(), self._sim.techniques_spread())
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
        trader actors carry in a direction this year is theirs to carry that way (sim/foreign_trade/actor_trade.py)."""
        sim, economy = self._sim, self._economy
        partners = sim.foreign_economies()
        if not partners:
            return {}
        from sim.world.material_units import tonnes_per_unit
        offers_api = sim.goods_market
        routes = {partner: offers_api._route_from(partner) for partner in partners}
        volumes = economy_api.traded_volumes(economy)
        opening = economy_api.opening_quantities(economy)
        landed, export_prices, available, wanted = {}, {}, {}, {}
        duty_share = economy.setup.import_duty_share
        duty_share.clear()
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
                    duty_share[good] = 1.0 - offers_api.landed_price(good, partner, route, with_duty=False) / price
                partner_price = sim.partner_price_per_unit(partner, good)
                tariff, embargoed = trade_duty.export_terms(sim, partner)
                if route is not None and partner_price and not embargoed and not sim.actors_carry(good, True, partner):
                    net = partner_price * (1.0 - tariff) - route.cost_per_tonne * tonnes_per_unit(good)
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

    def market_record(self, material):
        """Tonnes the material's markets sold, left unsold and left unmet last year."""
        per_unit = tonnes_per_unit(material)
        return {name: quantity * per_unit for name, quantity in economy_api.market_record(self.economy(), material).items()}

    def price_response(self, material, landed_tonnes, taken_tonnes, tile=None):
        """Factor on a material's price once more tonnes land in its market or are taken out, from the book the
        market last cleared: at the port when no tile is named (the price the economy shows nationally), else on the
        tile's own area. None when the market has none."""
        from sim.world.material_units import tonnes_per_unit
        per_unit = tonnes_per_unit(material)
        if not per_unit or per_unit <= 0.0 or material not in self.economy().area_map.goods():
            return None
        return economy_api.price_response(self.economy(), material, landed_tonnes / per_unit, taken_tonnes / per_unit,
                                          tile=None if tile is None else self._tile_in_economy(tile))

    def _partner_spending(self, partners) -> float:
        """What the partners can spend on this society's goods this year, in home money: a share of the
        coin each still holds (its opening stock and what the ledger says it gained or paid out)."""
        sim = self._sim
        total = 0.0
        for partner in partners:
            standard = sim.partner_civ(partner)["coin_standard"]
            metal_price = sim._material_prices().get(standard["material"])   # the metal at its cost: its market price (Complaint 519) would size a partner's spending by the opening's mispriced metals
            if not metal_price:
                continue
            held = (sim._partner_coin_opening_units(partner)
                    + sim.foreign_coin_partner_units(partner))
            total += max(0.0, held) * standard["kg_per_unit"] * metal_price
        return total * PARTNER_SPEND_SHARE_PER_YEAR

    def _settle_foreign_coin(self):
        """The year's foreign trade paid for in the partners' ledgers (sim/foreign_trade): imports pay coin
        to them and exports draw coin from them, so a partner paying out coin sees its price level fall
        and buys less (price-specie flow). Trade with several partners is split evenly among them; the
        economy's external edge does not yet say which partner each good went to."""
        sim, economy = self._sim, self._economy
        partners = sim.foreign_economies()
        if not partners:
            return 0.0, 0.0
        coin = economy.setup.coin_per_unit
        paid_in = economy_api.external_trade_net(economy)            # exports less imports
        volume = economy_api.external_trade_volume(economy)
        imports, exports = (volume - paid_in) / 2.0 * coin, (volume + paid_in) / 2.0 * coin
        for partner in partners:
            standard = sim.partner_civ(partner)["coin_standard"]
            metal_price = sim.goods_market.home_unit_price(standard["material"])
            if not metal_price:
                continue
            if imports > 0.0:
                sim.send(SettleFlow(partner, 1.0, imports / len(partners)))
            if exports > 0.0:
                sim.send(SettleFlow(partner, -1.0, exports / len(partners)))
        return imports, exports

    def _note_off_map_trade(self, imports, exports):
        """The year's trade over the external edge goes into the book of the country whose tile the port stands on."""
        setup = self._economy.setup
        country_trade_years.note(self.stored.setdefault("country_trade_by_year", {}), setup.country_of(setup.port_tile),
                                 self._sim.state.scenario.year, imports, exports)

    def _settle_seats(self):
        """What each seat's goods fetched goes to its ledger, less what its concerns' inputs cost; what did not sell goes
        back to the engine (port_seats.settle_seats)."""
        offered = self.__dict__.pop("_seat_offered", {})
        inputs = self.__dict__.pop("_seat_inputs", {})
        sold, takings = port_seats.settle_seats(self._sim, self._economy, offered, inputs, EDGE_LEGACY)
        self.stored["seat_sales"] = {**self.stored.get("seat_sales", {}), **sold}
        self.stored["seat_takings"] = takings

    def seat_sale_outlook(self, seat_id, material, quantity):
        """What the seat may count as sold of `quantity` units of a material it makes: its last clearing's share and
        price, else what the market's buyers took last year (concern_sales.outlook); None when the economy is not open."""
        if not self.opened():
            return None
        return port_seats.outlook(self.economy(), self.stored.get("seat_sales", {}), seat_id, material, quantity)

    def _inputs(self, engine_orders, border_accounts=((), ())) -> YearInputs:
        sim = self._sim
        population = sim.population
        total = float(population.total)
        weather = sim.view("harvest_weather")(sim.state.scenario.year, None, False)   # harm is applied per producer below
        economy = self._economy
        harmed = sim.externality_yield_factors(sim.state.scenario.year)
        yields = port_sites.crop_yields(economy, weather, sim.view("farm_weather")[sim.state.scenario.year])
        yields = port_sites.harmed_yields(yields, harmed, economy_api.producers_of(economy))
        entrant_share, attrition_share = working_age_turnover(population)
        return YearInputs(year=sim.state.scenario.year, population_by_tile=sim.labour.settlement_tiles(),
                          working_age_share=population.working_age / total if total > 0.0 else 0.0,
                          entrant_share=entrant_share, attrition_share=attrition_share,
                          yield_factor_by_producer=yields, engine_orders=engine_orders, harvest_factor=weather,
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
                                              for buyer in sorted(sim.view("cast")().actors)),
                          bondage_tiles=port_bondage.bondage_tiles(sim, economy),
                          bonded_for_sale=port_bondage.bonded_for_sale(sim, economy),
                          standing_bids=self._founder_standing_bids(), credit_asks=self._credit_asks(),
                          site_limits=tuple(port_sites.site_limits(sim, self._recipe_outputs(), self._economy.setup.tiles)))

    def _credit_asks(self):
        """Each playing seat's credit line, as a request for the year's clearing: the line its name and earning
        give (the market's room not yet applied) in the economy's money."""
        sim, setup = self._sim, self._economy.setup
        rate = sim.market_rate()
        asks = []
        for seat_id in sorted(sim.playing_seats() or sim.state.seats):
            with sim.act_as(seat_id):
                base, _floor, serviceable = sim.credit_line_sought()
                line = max(0.0, min(base, serviceable)) * sim.price_index / setup.coin_per_unit
            if line > 0.0:
                asks.append(economy_api.credit_line_request(seat_id, setup.currency_id, line, rate))
        return tuple(asks)

    def _founder_standing_bids(self):
        """The founder's year of draws on materials, as bids for firm entry to read (port_actors.standing_bids)."""
        sim, seats = self._sim, self._sim.state.seats
        tiles = sorted(self._seat_tiles())
        if not tiles:
            return ()
        return port_actors.standing_bids(self._economy, sim._market_flows(), seats, tiles[0], tonnes_per_unit,
                                                 sim.economy.materials_in)

    def _seat_tiles(self):
        """The tiles the playing seats buy and sell on, whose markets' books the economy keeps."""
        sim = self._sim
        tiles = set()
        for seat_id in sim.playing_seats() or sim.state.seats:
            with sim.act_as(seat_id):
                tiles.add(self._tile_in_economy(sim.labour.base_tile()))
        return tiles

    def _recipe_outputs(self):
        """{recipe id: {good: quantity a run}} of the recipes the economy runs."""
        return {recipe_id: recipe.outputs for recipe_id, recipe in self._economy.setup.recipes.items()}

    def _spin_up(self):
        """Hidden years from the opening until prices and the interest rate settle; then the price level
        is rebased to one."""
        economy = self._economy
        basket = economy_api.opening_quantities(economy)
        prices = economy.setup.opening_prices
        watched = sorted(basket, key=lambda good: -basket[good] * prices.get(good, 0.0))[:SPIN_UP_WATCHED_GOODS]
        inputs = YearInputs(year=0, population_by_tile={}, working_age_share=economy.setup.working_share,
                            yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
        first_stage = self._settle(economy, inputs, watched)
        economy_api.trim_workforce_to_expected_hours(economy)
        final_states = self._settle_trimmed(economy, inputs, watched)
        economy_api.trim_workforce_to_expected_hours(economy)   # the trade the settled years left idle does not carry its people into the game
        economy_api.finish_spin_up(economy)
        years = first_stage["years"] + spin_up_years()[1]
        economy_api.note_spin_up_result(economy, self.final_result(first_stage, final_states, years))

    @staticmethod
    def _settle(economy, inputs, watched):
        """The first stage's stop rule (it decides when the stage ends; it is not the opening's reported
        result): hidden years until the price level, the rate (against a floor, see spin_up_gap) and the main
        prices move less than the tolerance a year. Returns {"settled": whether the tolerance was met, "years":
        years run, "gap": the largest change in the last year measured (none measured: infinity is not stored,
        so one)}."""
        before = None
        gap = 1.0
        years = 0
        settled = False
        for _year in range(spin_up_years()[0]):
            outcome = economy.step(inputs)
            years += 1
            now = (outcome.basket_price_level, economy_api.interest_rate(economy) or 0.0,
                   {good: outcome.prices.get(good, 0.0) for good in watched})
            if before is not None:
                gap = max(change_gap(now[0], before[0]) if before[0] > 0.0 else 0.0,
                          change_gap(now[1], before[1], SPIN_UP_RATE_FLOOR) if before[1] > 0.0 else 0.0,
                          price_gap(now[2], before[2]))
                if gap < SPIN_UP_TOLERANCE:
                    settled = True
                    break
            before = now
        return {"settled": settled, "years": years, "gap": gap}

    @staticmethod
    def _settle_trimmed(economy, inputs, watched):
        """The few further years, from the state the first stage left, in which the trimmed trades' wages and
        entry settle. Returns the state (see spin_up_gap) of each of the last SPIN_UP_MEASURED_YEARS years."""
        states = collections.deque(maxlen=int(SPIN_UP_MEASURED_YEARS))
        for _year in range(spin_up_years()[1]):
            outcome = economy.step(inputs)
            state = economy_api.spin_up_state(economy, outcome)
            state.update(price_level=outcome.basket_price_level, rate=economy_api.interest_rate(economy) or 0.0,
                         prices={good: outcome.prices.get(good, 0.0) for good in watched})
            states.append(state)
        return list(states)

    @staticmethod
    def final_result(first_stage, final_states, years):
        """What the saved opening reports, apart from the stop rule: whether the state it opens in (after
        trimming) moved less than the tolerance a year, in every quantity spin_up_gap measures, over the last
        consecutive years. {"settled", "years" (all hidden years), "gap" (largest change; one when fewer than two
        years were measured), "gaps" (by quantity), "measured_years", "final" (the last year's state),
        "first_stage" (the stop rule's own result)}."""
        gaps = window_gaps(final_states)
        gap = 1.0 if gaps is None else max(gaps.values())
        return {"settled": gaps is not None and gap < SPIN_UP_TOLERANCE, "years": years, "gap": gap,
                "gaps": gaps or {}, "measured_years": len(final_states),
                "final": dict(final_states[-1]) if final_states else {}, "first_stage": dict(first_stage)}

    def _save(self):
        self.stored["record"] = economy_api.export_record(self._economy, (PURSE_CURRENCY,))
        self._record_stale = False

    def flush_record(self):
        """Bring the stored record up to the live economy; the game's save calls this, so a year does not pay for it."""
        if self._record_stale and self._economy is not None and self._built_from is self.stored:
            self._save()

    def carried_last_year(self):
        """Last year's goods carried between the economy's tiles, {origin: {destination: tonnes}}; empty until
        the economy has run a year."""
        if self._economy is not None and self._built_from is self.stored:
            return economy_api.carried_last_year(self._economy)
        return (self.stored.get("record") or {}).get("carried") or {}

    # ---- what the seams read ------------------------------------------------------------------
    def answers(self, country=None):
        """(prices by good, hours-weighted wage per hour by trade, rate), for this year; built once a year. A good
        whose markets have not cleared lately shows what it costs to make at today's prices and wages, or
        its last price when nothing makes it; `stale_goods()` names those. For a partner `country` that is part
        of the economy, those of its own markets; any other country is answered as the home country."""
        if country is not None and country != self._sim.civ.get("id"):
            home = self.answers()
            if country not in self._economy.setup.countries():
                return home
            if country not in self._country_answers:
                coin = self._economy.setup.coin_per_unit
                prices, _stale = economy_api.shown_prices_of(self._economy, country)
                wages = economy_api.wages_by_trade_weighted(self._economy, country)
                self._country_answers[country] = ({good: price * coin for good, price in prices.items()},
                                                  {trade: wage * coin for trade, wage in wages.items()}, home[2])
            return self._country_answers[country]
        if self._answers is None or self._built_from is not self.stored:
            self.economy()
            wages = economy_api.wages_by_trade_weighted(self._economy)
            coin = self._economy.setup.coin_per_unit
            prices, self._stale = economy_api.shown_prices_of(self._economy)
            self._answers = ({good: price * coin for good, price in prices.items()},
                             {trade: wage * coin for trade, wage in wages.items()},
                             economy_api.interest_rate(self._economy))
        return self._answers

    def price_kind(self, good):
        """What the shown price of a good is (economy_api.shown_price_kinds_of): traded, a quote named by what it
        is, or an estimate; None for a good the economy shows no price for. Built once a year."""
        self.answers()
        if self._kinds is None or self._kinds[0] is not self._answers:
            self._kinds = (self._answers, economy_api.shown_price_kinds_of(self._economy))
        return self._kinds[1].get(good)

    def stale_goods(self):
        """Goods whose shown price is not a market's: not cleared within notional.RECENT_TRADE_YEARS."""
        self.answers()
        return set(self._stale)

    def people_by_trade(self):
        """The labour core's people by trade, or None before the economy has been opened."""
        if self._economy is None and "record" not in self.stored:
            return None
        return economy_api.people_by_trade(self.economy())

    def people_by_tile_and_trade(self):
        """The labour core's people by tile and trade, or None before the economy has been opened."""
        if self._economy is None and "record" not in self.stored:
            return None
        return economy_api.people_by_tile_and_trade(self.economy())

    def producer_capacity_tonnes(self, material):
        """Tonnes a year the economy's producers can make of a material at full capacity; zero before the
        economy has opened."""
        if not self.opened():
            return 0.0
        economy = self.economy()
        units = self._capacity_cache.units_by_material(
            economy, economy_api.all_producers(economy),
            # summed in id order: a loaded game holds the producers in id order, a live one in the order they entered
            lambda: sorted(economy_api.producers_of(economy).values(), key=lambda each: each.agent_id),
            economy.setup.recipes)
        return units.get(material, 0.0) * tonnes_per_unit(material)

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

    def producers_by_good(self):
        """{good: [(tile, recipe id)]} of the economy's producers for each good their recipes put out."""
        economy = self.economy()
        found = {}
        for producer in sorted(economy_api.producers_of(economy).values(), key=lambda each: each.agent_id):
            recipe = economy.setup.recipes.get(producer.recipe_id)
            for good in (recipe.outputs if recipe is not None else ()):
                found.setdefault(good, []).append((producer.tile, producer.recipe_id))
        return found

    def unskilled_wage_per_hour(self):
        """The home labour markets' wage for an hour of the trade anyone can take up, in coin."""
        wages = self.answers()[1]
        return wages.get(self._economy.setup.unskilled_trade)

    def wage_per_hour(self, trade, country=None):
        """The trade's wage in its labour markets; a trade no producer hires (soldiers, scribes) is paid
        what its training adds to the unskilled wage, so every wage stands on the same market."""
        wages = self.answers(country)[1]
        if trade in wages:
            return wages[trade]
        setup = self._economy.setup
        unskilled = wages.get(setup.unskilled_trade)
        if unskilled is None:
            return None
        return unskilled * (1.0 + trade_premium(setup, trade))

    def country(self, country):
        """What the economy answers for a partner country in it (`CountryAnswers`), or None when the country is
        not in this economy or its labour markets have no wage yet."""
        economy = self.economy()
        if country == economy.setup.civ_id or country not in economy.setup.countries():
            return None
        from .port_country import CountryAnswers
        year = self._sim.state.scenario.year
        book = self.stored.get("country_trade_by_year", {})
        answers = CountryAnswers(economy, country, lambda direction: country_trade_years.value(book, country, year - 1, direction))
        return answers if answers.has_labour_market() else None

    def land_rent_per_hectare(self):
        """Mean rent per hectare-year the land market let land at last year, in coin."""
        return economy_api.land_rent_per_hectare(self.economy()) * self._economy.setup.coin_per_unit

    def need_floor_costs_per_person_year(self, country=None):
        """What a person's floor of each need costs a year at the prices on the home tiles (the mean over the
        people there), in coin; empty before any tile holds people."""
        economy = self.economy()
        scope = economy_api.country_figures.home_when_shared(economy, country)
        if economy is not self._floor_costs_of:
            self._floor_costs, self._floor_costs_of = {}, economy
        if scope not in self._floor_costs:
            costs = economy_api.country_figures.need_floor_costs_per_person_year(economy, scope)
            self._floor_costs[scope] = {need: cost * economy.setup.coin_per_unit for need, cost in costs.items()}
        return dict(self._floor_costs[scope])

    def need_floor_costs_at_tile(self, tile):
        """What a person's floor of each need costs a year at the prices on one tile, in coin."""
        economy = self.economy()
        costs = economy_api.country_figures.tile_need_floor_costs(economy, tile)
        return {need: cost * economy.setup.coin_per_unit for need, cost in costs.items()}

    def land_rent_at_tile(self, tile):
        """Rent per hectare-year on one tile in coin (the mean where none was let there)."""
        return economy_api.land_rent_at_tile(self.economy(), tile) * self._economy.setup.coin_per_unit

    def idle_hours_by_trade(self):
        """(hours offered and not hired, hours offered) of each trade in the home labour markets last year."""
        return economy_api.idle_hours_by_trade(self.economy())

    def land_rent_paid_by_tile(self):
        """Rent producers paid on each tile where land was let last year, in coin."""
        coin = self._economy.setup.coin_per_unit
        return {tile: rent * coin for tile, rent in economy_api.land_rent_paid_by_tile(self.economy()).items()}

    def output_tonnes_by_tile(self):
        """Tonnes of each good the producers made on each tile last year."""
        from sim.world.material_units import tonnes_per_unit
        return {tile: {good: units * tonnes_per_unit(good) for good, units in row.items()}
                for tile, row in economy_api.output_by_tile(self.economy()).items()}

    def rate(self):
        return self.answers()[2]

    def credit_room(self, borrower_id):
        """What the credit market will still advance one borrower, in coin; None before lenders have met."""
        self.answers()
        room = economy_api.credit_room(self._economy, borrower_id)
        return None if room is None else room * self._economy.setup.coin_per_unit
