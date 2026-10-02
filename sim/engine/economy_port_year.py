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
from sim.economy.types import EDGE_LEGACY, GoodsMove, Offer, Transfer
from sim.economy.record import EconomyRecord
from sim.economy.year_close import national_prices

from .economy_port_setup import build_setup, opening_values

SWITCH_ENVIRONMENT = "ROME_AGENT_ECONOMY"
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
FOUNDER_AGENT = "founder"


def switch_requested(cfg) -> bool:
    return bool(cfg.get("agent_economy")) or os.environ.get(SWITCH_ENVIRONMENT) == "1"


class AgentEconomy:
    """One game's agent economy. Not saved itself: it rebuilds from `state.economy.agent_economy`."""

    def __init__(self, sim):
        self._sim = sim
        self._economy = None
        self._answers = None

    @property
    def stored(self):
        return self._sim.state.economy.agent_economy

    def on(self) -> bool:
        return bool(self.stored.get("on"))

    def opened(self) -> bool:
        return self._economy is not None or "record" in self.stored

    def economy(self) -> Economy:
        if self._economy is None:
            if "record" in self.stored:
                setup = build_setup(self._sim, self.stored["opening"])
                self._economy = Economy(setup, EconomyRecord.from_record(self.stored["record"]))
            else:
                opening = opening_values(self._sim)
                self._economy = Economy(build_setup(self._sim, opening))
                self.stored["opening"] = opening
                self._spin_up()
                self._save()
        return self._economy

    # ---- the year -----------------------------------------------------------------------------
    def run_year(self):
        economy = self.economy()
        orders = self._founder_orders()
        outcome = economy.step(self._inputs(orders))
        self._settle_founder()
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
                cost = sim.concern_cost_ratio(node_id, material) * old_prices.get(material, 0.0)
                offers.append(Offer(FOUNDER_AGENT, material, area_map.area_of(material, tile), tile, quantity, cost))
        book.move_many(moves)
        return {FOUNDER_AGENT: AgentOrders(offers=tuple(offers))} if offers else {}

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
        self.stored["founder_takings"] = proceeds

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
                          yield_factor_by_producer=yields, engine_orders=engine_orders)

    def _spin_up(self):
        """Hidden years from the opening until prices settle; then the price level is rebased to one."""
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
            now = [outcome.price_level] + [outcome.prices.get(good, 0.0) for good in watched]
            if before is not None and max(abs(new / old - 1.0) for new, old in zip(now, before) if old > 0.0) < SPIN_UP_TOLERANCE:
                break
            before = now
        money = economy.setup.currency_id
        record.index_base_prices = national_prices(record)
        record.memory.price_levels[money] = 1.0
        record.memory.expected_inflation[money] = 0.0
        record.memory.year = 0

    def _save(self):
        self.stored["record"] = self._economy.record.to_record()

    # ---- what the seams read ------------------------------------------------------------------
    def answers(self):
        """(prices by good, mean wage per hour by trade, rate), for this year; built once a year."""
        if self._answers is None:
            record = self.economy().record
            wages = {}
            for key, wage in record.memory.wages.items():
                trade = key.split("|", 1)[0]
                wages.setdefault(trade, []).append(wage)
            self._answers = (national_prices(record),
                             {trade: sum(rows) / len(rows) for trade, rows in wages.items()},
                             record.memory.rates.get(self._economy.setup.currency_id))
        return self._answers

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
        return self.answers()[1].get(trade)

    def rate(self):
        return self.answers()[2]
