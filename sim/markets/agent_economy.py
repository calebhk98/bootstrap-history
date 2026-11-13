"""The live agent economy of a game and the record it is rebuilt from. Part of the port (with port.py and port_setup.py,
the only engine modules that import `sim.economy`).

Its whole state lives in the markets module's `agent_economy` record (`stored`), so a saved game resumes the same
economy. Everything the port reads across years is in that record or rebuilt from it:

- "opening", "record": the economy's opening values and its state, brought up to date by `flush_record` on each save;
- "years_run": the years the port has run (the producers' stamp);
- "techniques_admitted": the held nodes the economy's recipes were last matched to;
- "volume_baseline", "health_rows", "sales", "purchases" and the seats' notes: see the modules that write them.

The parts that read and run the economy (reads_*.py, port_year.py, port_actor_trade.py, port_seat_concerns.py) ask this
object for the economy and the record.
"""
from sim.economy import api as economy_api
from sim.economy.api import Economy
from sim.agents.api import PURSE_CURRENCY
from sim.rekey import rekey

from . import port_late, spin_up_run
from .port_coin import priced_at_the_margin
from .port_setup import build_setup, opening_values
from .year_figures import YearFigures

NOTED_PER_SEAT = ("seat_sales", "seat_orders", "seat_trades", "trades_lacking_logged", "sales", "purchases")


class AgentEconomy:
    """One game's agent economy. Not saved itself: it rebuilds from the markets module's `agent_economy` record."""

    def __init__(self, world):
        self._world = world
        self._economy = None
        self._built_from = None          # the stored dict the live economy belongs to; a load replaces it
        self.figures = YearFigures()

    def production_catalog(self):
        return self._world.production_catalog()

    def tonnes_per_unit(self, material):
        return self._world.tonnes_per_unit(material)

    @property
    def stored(self):
        return self._world.agent_record()

    def current(self) -> bool:
        """Whether the live economy was built from the record the game holds now."""
        return self._built_from is self.stored

    def opened(self) -> bool:
        return self._economy is not None or "record" in self.stored

    def economy(self) -> Economy:
        if self._built_from is not self.stored:
            self._economy = None
            self.figures.forget()
        if self._economy is None:
            if "record" in self.stored:
                setup = build_setup(self._world, self.stored["opening"])
                self._economy = economy_api.economy_from_record(setup, self.stored["record"])
            else:
                opening = priced_at_the_margin(self._world, opening_values(self._world))
                setup = build_setup(self._world, opening)
                record = spin_up_run.record_for(setup)
                self._economy = economy_api.economy_from_record(setup, record)
                self.stored["opening"] = opening
                self.save()
            self._built_from = self.stored
            economy_api.note_memory_changed()     # a new memory: what was read from the old one is read again
            purses = self._world.state.actors.purses
            purses.adopt_book(economy_api.economy_book(self._economy), economy_api.economy_contracts(self._economy))
            economy = self._economy
            purses.unit_observer = lambda lender, units, label: economy_api.note_pool_posting(economy, lender, units)
            self.sync_ways()
        return self._economy

    def sync_ways(self):
        """Give the live economy the ways the game has built so far; its hauls are priced over them from now on."""
        self.figures.forget()
        if self._economy is not None:
            economy_api.set_improvements(self._economy, self._world.state.economy.improvements)

    def admit_techniques(self):
        """Give the economy the entries the society's techniques now allow, when its held nodes changed since
        it last looked: they enter the saved opening (so a resumed game rebuilds them) and the live economy."""
        held = sorted(port_late.techniques_held(self._world))
        if held == self.stored.get("techniques_admitted"):
            return
        self.stored["techniques_admitted"] = held
        production = self._world.production_catalog()
        grown = port_late.opening_with_techniques(self._world, self.stored["opening"], frozenset(held), production,
                                                  economy_api.opening_wage_level(self._economy))
        if grown is None:
            return
        self.stored["opening"] = grown
        economy_api.admit_recipes(self._economy, build_setup(self._world, grown, production))
        self.figures.forget()

    def tile_in_economy(self, tile):
        """The tile asked about, or the capital when the economy does not hold it."""
        return economy_api.tile_in_economy(self.economy(), tile)

    def actor_tile(self, actor_id):
        """The tile an actor buys and sells on: where it is, else the capital."""
        actor = self._world.scenario.actors.actors.get(actor_id)
        place = actor.location() if actor is not None else None
        economy = self.economy()
        return place if place in economy_api.economy_tiles(economy) else economy_api.capital_tile(economy)

    # ---- the record ---------------------------------------------------------------------------
    def save(self):
        self.stored["record"] = economy_api.export_record(self._economy, (PURSE_CURRENCY,))

    def flush_record(self):
        """Bring the stored record up to the live economy; the game's save calls this, so a year does not pay for it."""
        if self._economy is not None and self._built_from is self.stored:
            self.save()

    def spin_up_result(self):
        """The saved opening's first-stage result (see spin_up_run.final_result); empty before the opening is saved."""
        return dict((self.stored.get("record") or {}).get("spin_up_result") or {})

    def carried_last_year(self):
        """Last year's goods carried between the economy's tiles, {origin: {destination: tonnes}}; empty until
        the economy has run a year."""
        if self._economy is not None and self._built_from is self.stored:
            return economy_api.carried_last_year(self._economy)
        return ((self.stored.get("record") or {}).get("carriage") or {}).get("carried") or {}

    def years_run(self):
        """Years the port has run this game: the producers change when one closes."""
        return int(self.stored.get("years_run", 0))

    def note_year_run(self):
        self.stored["years_run"] = self.years_run() + 1

    def rename_agent(self, old, new):
        """`old` becomes `new` in the economy's records and in the year's stored notes (a seat handed over)."""
        if self.opened():
            economy_api.rename_agent(self.economy(), old, new)
        for kind in NOTED_PER_SEAT:
            if kind in self.stored:
                rekey(self.stored[kind], old, new)
