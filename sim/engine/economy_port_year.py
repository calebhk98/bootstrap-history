"""The agent economy inside a game: the switch, opening it, its year, and what the engine's seams read.

Part of the port (with economy_port.py and economy_port_setup.py, the only engine modules that import
`sim.economy`). Its whole state lives in `state.economy.agent_economy`, so a saved game resumes the
same economy. The engine's own price, wage and rate code asks `answers()` and falls back to its old
figures while the switch is off or before the economy has opened.
"""
import os

from sim.constants import declare
from sim.economy.economy import Economy
from sim.economy.protocols import YearInputs
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
        outcome = economy.step(self._inputs())
        self._answers = None
        self._save()
        return outcome

    def _inputs(self) -> YearInputs:
        sim = self._sim
        population = sim.population
        total = float(population.total)
        weather = sim._pooled_farm_weather_multiplier(sim.state.scenario.year)
        economy = self._economy
        yields = {producer_id: weather for producer_id, producer in economy.record.producers.items()
                  if economy.setup.land_per_run.get(producer.recipe_id, 0.0) > 0.0}
        return YearInputs(year=sim.state.scenario.year, population_by_tile=sim.settlement_tiles(),
                          working_age_share=population.working_age / total if total > 0.0 else 0.0,
                          yield_factor_by_producer=yields, engine_orders={})

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
