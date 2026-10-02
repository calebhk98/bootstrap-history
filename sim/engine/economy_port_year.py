"""The agent economy inside a game: the switch, opening it, its year, and what the engine's seams read.

Part of the port (with economy_port.py and economy_port_setup.py, the only engine modules that import
`sim.economy`). Its whole state lives in `state.economy.agent_economy`, so a saved game resumes the
same economy. The engine's own price, wage and rate code asks `answers()` and falls back to its old
figures while the switch is off or before the economy has opened.
"""
import os

from sim.constants import declare
from sim.economy.economy import Economy
from sim.economy.protocols import AgentOrders, YearInputs
from sim.economy.foreign import external_orders
from sim.economy.types import EDGE_EXTERNAL, EDGE_LEGACY, GoodsMove, Offer, Transfer
from sim.economy.record import EconomyRecord
from sim.economy.notional import shown_prices
from sim.economy.year_close import rebase_price_level
from sim.economy.year_labour import trade_premium

from . import solve_cache
from .data import load_civ
from .economy_port_setup import build_setup, in_units, opening_values

SWITCH_ENVIRONMENT = "ROME_AGENT_ECONOMY"
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
FOUNDER_AGENT = "founder"


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
                self._economy = Economy(setup, EconomyRecord.from_record(self.stored["record"]))
            else:
                opening = opening_values(self._sim)
                setup = build_setup(self._sim, opening)
                record = solve_cache.cached_json(
                    solve_cache.solve_key({"agent_economy_spin_up": in_units(opening), "civ": self._sim.civ["id"]}),
                    lambda: self._spun_up(setup), cache_dir=SPIN_UP_CACHE_DIRECTORY)
                self._economy = Economy(setup, EconomyRecord.from_record(record))
                self.stored["opening"] = opening
                self._save()
            self._built_from = self.stored
        return self._economy

    def _spun_up(self, setup):
        """The record after the hidden years; the same opening always gives the same one, so it is cached
        on disk with the price solver's results (keyed on the data files and the source)."""
        self._economy = Economy(setup)
        self._spin_up()
        return self._economy.record.to_record()

    # ---- the year -----------------------------------------------------------------------------
    def run_year(self):
        economy = self.economy()
        orders = self._founder_orders()
        orders.update(self._external_orders())
        outcome = economy.step(self._inputs(orders))
        self._settle_founder()
        self._settle_foreign_coin()
        self._answers = None
        self._save()
        return outcome

    # ---- the founder's concerns sell in the same market ----------------------------------------
    def _founder_orders(self):
        """The founder's running concerns' output for the year, handed over from the engine through the
        legacy edge (the engine's purse is not yet an account in the book: Complaint 382) and offered at
        what the concern costs to make it."""
        sim, economy = self._sim, self._economy
        book, area_map = economy.record.book, economy.area_map
        tile = sim.base_tile() if sim.base_tile() in economy.setup.tiles else economy.setup.capital_tile
        projects = sim.state.projects
        old_prices = sim._material_prices()
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
                moves.append(GoodsMove(EDGE_LEGACY, FOUNDER_AGENT, material, tile, quantity, "concern output"))
                cost = (sim.concern_cost_ratio(node_id, material) * old_prices.get(material, 0.0)
                        / economy.setup.coin_per_unit)
                offers.append(Offer(FOUNDER_AGENT, material, area_map.area_of(material, tile), tile, quantity, cost))
        book.move_many(moves)
        return {FOUNDER_AGENT: AgentOrders(offers=tuple(offers))} if offers else {}

    # ---- foreign partners trade at the port -----------------------------------------------------
    def _external_orders(self):
        """Imports offered at the cheapest partner's landed price and exports bid for at the partner's
        own price less carriage, on the port tile (sim/economy/foreign.py). How much can cross is a
        share of the home market, standing in for the carriers' capacity (FOREIGN_TRADE_SHARE)."""
        sim, economy = self._sim, self._economy
        partners = sim.foreign_economies()
        if not partners:
            return {}
        from .project_materials import tonnes_per_unit
        offers_api = sim.goods_market
        routes = {partner: offers_api._route_from(partner) for partner in partners}
        volumes = {}
        for key, volume in economy.record.volumes.items():
            good = key.split("|", 1)[0]
            volumes[good] = volumes.get(good, 0.0) + volume
        landed, export_prices, available, wanted = {}, {}, {}, {}
        for good in economy.area_map.goods():
            market = max(volumes.get(good, 0.0), economy.record.opening_basket.get(good, 0.0))
            if market <= 0.0:
                continue
            for partner in partners:
                route = routes[partner]
                price = offers_api.landed_price(good, partner, route)
                if price is not None and price > 0.0 and price < landed.get(good, float("inf")):
                    landed[good] = price
                facts = sim._foreign_economy_facts(partner)
                partner_price = facts["prices_in_home_money"].get(good)
                if route is not None and partner_price:
                    net = (partner_price * offers_api.partner_price_level(partner)
                           - route.cost_per_tonne * tonnes_per_unit(good))
                    if net > export_prices.get(good, 0.0):
                        export_prices[good] = net
            available[good] = wanted[good] = market * FOREIGN_TRADE_SHARE
        coin = economy.setup.coin_per_unit
        landed = {good: price / coin for good, price in landed.items()}
        export_prices = {good: price / coin for good, price in export_prices.items()}
        return {EDGE_EXTERNAL: external_orders(landed, export_prices, available, wanted,
                                               economy.area_map.area_of, economy.setup.port_tile,
                                               export_budget=self._partner_spending(partners) / coin)}

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
        book, money = economy.record.book, economy.setup.currency_id
        coin = economy.setup.coin_per_unit
        paid_in = book.edge_net(EDGE_EXTERNAL, money)            # exports less imports
        volume = book.edge_volume(EDGE_EXTERNAL, money)
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

    def _settle_founder(self):
        """What the founder's goods fetched goes back to the engine; what did not sell goes back too."""
        record = self._economy.record
        money = self._economy.setup.currency_id
        book = record.book
        proceeds = book.balance(FOUNDER_AGENT, money)
        if proceeds > 0.0:
            book.transfer(Transfer(FOUNDER_AGENT, EDGE_LEGACY, money, proceeds, "founder's takings"))
        returns = [GoodsMove(FOUNDER_AGENT, EDGE_LEGACY, good, tile, quantity, "unsold concern output")
                   for good, tiles in book.holdings(FOUNDER_AGENT)["goods"].items()
                   for tile, quantity in tiles.items() if quantity > 0.0]
        book.move_many(returns)
        self.stored["founder_takings"] = proceeds * self._economy.setup.coin_per_unit

    def _inputs(self, engine_orders) -> YearInputs:
        sim = self._sim
        population = sim.population
        total = float(population.total)
        weather = sim._pooled_farm_weather_multiplier(sim.state.scenario.year)
        economy = self._economy
        yields = {producer_id: weather for producer_id, producer in economy.record.producers.items()
                  if economy.setup.land_per_run.get(producer.recipe_id, 0.0) > 0.0}
        return YearInputs(year=sim.state.scenario.year, population_by_tile=sim.settlement_tiles(),
                          working_age_share=population.working_age / total if total > 0.0 else 0.0,
                          yield_factor_by_producer=yields, engine_orders=engine_orders, harvest_factor=weather)

    def _spin_up(self):
        """Hidden years from the opening until prices and the interest rate settle; then the price level
        is rebased to one."""
        economy = self._economy
        record = economy.record
        basket = record.opening_basket
        prices = economy.setup.opening_prices
        watched = sorted(basket, key=lambda good: -basket[good] * prices.get(good, 0.0))[:SPIN_UP_WATCHED_GOODS]
        inputs = YearInputs(year=0, population_by_tile={}, working_age_share=economy.setup.working_share,
                            yield_factor_by_producer={}, engine_orders={})
        before = None
        for _year in range(int(SPIN_UP_MAXIMUM_YEARS)):
            outcome = economy.step(inputs)
            now = ([outcome.price_level, record.memory.rates.get(economy.setup.currency_id, 0.0)]
                   + [outcome.prices.get(good, 0.0) for good in watched])
            if before is not None and max(abs(new / old - 1.0) for new, old in zip(now, before) if old > 0.0) < SPIN_UP_TOLERANCE:
                break
            before = now
        rebase_price_level(economy.setup, record)
        record.memory.year = 0

    def _save(self):
        self.stored["record"] = self._economy.record.to_record()

    # ---- what the seams read ------------------------------------------------------------------
    def answers(self):
        """(prices by good, mean wage per hour by trade, rate), for this year; built once a year. A good
        whose markets have not cleared lately shows what it costs to make at today's prices and wages, or
        its last price when nothing makes it; `stale_goods()` names those."""
        if self._answers is None or self._built_from is not self.stored:
            record = self.economy().record
            wages = {}
            for key, wage in record.memory.wages.items():
                trade = key.split("|", 1)[0]
                wages.setdefault(trade, []).append(wage)
            coin = self._economy.setup.coin_per_unit
            prices, self._stale = shown_prices(self._economy.setup, record)
            self._answers = ({good: price * coin for good, price in prices.items()},
                             {trade: sum(rows) / len(rows) * coin for trade, rows in wages.items()},
                             record.memory.rates.get(self._economy.setup.currency_id))
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

    def rate(self):
        return self.answers()[2]
