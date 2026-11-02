"""What kind of trade a trade is, and whether it can be had here at all: literate or craft, the literacy
this society has to fill it, and its presence in the society."""
from sim.constants import declare

from . import legacy_trade_defaults, trade_data
from .hire_outcome import craft_trades_report
from .wage_provider import reference_civilisation


class _LiterateTrades:
    """The trades whose practice is reading: this world's own on an instance, the shipped set on the class."""

    def __get__(self, instance, owner=None):
        if instance is None:
            return frozenset()
        return trade_data.literate_trades(trade_data.registry_of(instance._world), instance._world.wages)


class Trades:
    def __init__(self, world):
        self._world = world

    # ---- literacy bounds who you can hire ----------------------------------
    # FINDINGS_ROUND2 section Q: every civ file carries literacy_general and
    # literacy_elite, and apply_tech_effects (society.py) raises them when
    # paper, printing, schools and libraries are built. Nothing else reading
    # either number would let a scribe cost the same to hire in a society
    # where two people in a hundred could read as in one where nine could.
    #
    # `scholar` is drawn from the lettered, propertied class - literacy_elite
    # in the civ file, "fraction of the propertied class that can read". The
    # rest - `scribe`, and the trades taught into being from ordinary
    # craftsmen (`engineer`, `chemist`, `machinist`, `optician`) - draw on the
    # wider literacy_general pool of anyone who can read at all. `merchant` is
    # left out on purpose: an agent working on commission is not, in this
    # period, chiefly a reader.
    # electrician belongs in this set too: it is a taught trade that reads
    # drawings, exactly like the other four, so excluding it would let it
    # bypass the literacy ceiling that caps machinists, chemists,
    # engineers and opticians.
    LITERATE_TRADES = _LiterateTrades()

    def is_craft_trade(self, trade):
        return self._world.trade_family(trade) == legacy_trade_defaults.CRAFT_FAMILY

    def craft_trades_report(self):
        """The trades that supervise as craft and those that do not, by the same test `is_craft_trade` applies."""
        return craft_trades_report(self._world.wages, self.is_craft_trade)

    # The literacy this file's trade shares and staff ceilings were already
    # tuned against, before literacy was read anywhere: the default
    # civilisation's own numbers, because every other constant in this economy -
    # price index, cost multipliers - is calibrated relative to it. Below
    # its own reference literacy stays 1.0 and NOTHING changes for it; a
    # civilization with less of either number gets a genuinely smaller pool,
    # in proportion, and a civilization with more (a higher elite literacy
    # than the reference) is not penalised for having read more.
    LITERACY_REFERENCE_GENERAL = declare(
        "LITERACY_REFERENCE_GENERAL", reference_civilisation()["literacy_general"], kind="initial_condition",
        unit="fraction of population able to read (general)",
        source="the default civilisation file's own literacy_general field.",
        confidence="B",
        why="The default civilisation's starting literacy_general, read here as the "
            "denominator every OTHER civilisation's literate-trade capacity "
            "is measured against, because every other constant in this "
            "economy (price index, cost multipliers) is calibrated "
            "relative to that civilisation. A real starting condition, "
            "read from its file, not an invented number.")

    LITERACY_REFERENCE_ELITE = declare(
        "LITERACY_REFERENCE_ELITE", reference_civilisation()["literacy_elite"], kind="initial_condition",
        unit="fraction of the propertied class able to read (elite)",
        source="the default civilisation file's own literacy_elite field.", confidence="B",
        why="As LITERACY_REFERENCE_GENERAL, for the lettered, propertied "
            "pool `scholar` is drawn from.")

    LITERACY_FACTOR_CAP = declare(
        "LITERACY_FACTOR_CAP", 4.0, kind="temporary_heuristic",
        unit="dimensionless multiple of the Rome-reference pool",
        source=None, confidence="D",
        why="How far a literacy_factor may rise above 1.0 for a society "
            "that has read PAST Rome's own reference literacy. Bounded so "
            "a civilisation is never treated as though it could staff an "
            "unbounded number of literate trades just because a handful of "
            "technologies nudged literacy above 0.9; the figure 4.0 is "
            "tuned headroom, not a measured ceiling on how literate a "
            "pre-modern society can get.")

    def literacy_factor(self, trade):
        """0..1: how much of this trade's usual pool this society's literacy
        can actually fill. 1.0 for anything that is not a literate trade."""
        if trade not in self.LITERATE_TRADES:
            return 1.0
        if trade == trade_data.scholar_trade():
            lit, ref = self._world.literacy("literacy_elite"), self.LITERACY_REFERENCE_ELITE
        else:
            lit, ref = self._world.literacy("literacy_general"), self.LITERACY_REFERENCE_GENERAL
        # NOT CLAMPED AT ONE: Rome starts AT the reference, so clamping here
        # would return exactly 1.0 for Rome for ever, no matter how much
        # printing, movable type, schools and academies raise
        # literacy_general above it - moving the specialist ceiling not at
        # all. It is the one thing the argument for printing rests on: a
        # society that reads more can staff more.
        #
        # Bounded at four, because a lettered pool cannot outgrow the town
        # without the town growing, and because the tech effects that feed it
        # are deliberately small.
        return max(0.0, min(self.LITERACY_FACTOR_CAP, float(lit) / ref))

    def trade_available(self, trade):
        """Can this trade be had here at all, at any price?

        Rome has masons and plumbers in abundance and no machinists whatever.
        An absent trade is not expensive, it is absent, and the only way to have
        one is to teach somebody the trade yourself.
        """
        if trade not in self._world.trades_absent:
            return True
        workforce = self._world.workforce
        return (trade in workforce.trades_created
                or (workforce.trade_schools or {}).get(trade, 0.0) > 0)

    def available_trades(self):
        """Every trade this society has that the labour market can supply."""
        return [trade for trade in sorted(self._world.wages) if self.trade_available(trade)]
