"""Coin is metal: what a purse of it weighs, and what keeping that weight costs.

The mass is the money held times the metal in one coin (the civilisation's coin standard). Keeping it costs guards'
hours by the tonne, priced at the unskilled hour like every other labour cost.
"""
from sim.constants import declare

from sim.labour.api import wage_provider

COIN_GUARD_HOURS_PER_TONNE_YEAR = declare(
    "COIN_GUARD_HOURS_PER_TONNE_YEAR", 60.0, kind="temporary_heuristic",
    unit="labour hours per tonne of coin per year", source=None, confidence="D",
    why="Watch-keeping and strongroom upkeep for a hoard, by its mass. Stands in for a vault built "
        "from stone, doors and a guard roster (a vault has no model yet), and is not measured. "
        "It is shown, not yet charged against the purse.")

KEEPING_BASIS = ("guard hours per tonne of coin per year, a labelled heuristic "
                 "(COIN_GUARD_HOURS_PER_TONNE_YEAR), at the unskilled hour")


class CoinHoardMixin:
    """Mixed into `Sim`."""

    def coin_kg_per_unit(self):
        return wage_provider.coin_standard(self.civ)["kg_per_unit"]

    def coin_hoard(self):
        """The money held as physical coin: its metal, mass and the yearly cost of keeping it."""
        tonnes = max(0.0, self.capital) * self.coin_kg_per_unit() / 1000.0
        return {"metal": wage_provider.coin_standard(self.civ)["material"],
                "tonnes": tonnes,
                "keeping_cost_per_year": (tonnes * COIN_GUARD_HOURS_PER_TONNE_YEAR
                                          * self.labour.money_per_labour_hour()),
                "basis": KEEPING_BASIS}

    def coin_hoard_report(self):
        """`coin_hoard` rounded for a screen."""
        hoard = self.coin_hoard()
        return {"metal": hoard["metal"], "tonnes": round(hoard["tonnes"], 3),
                "keeping_cost_per_year": round(hoard["keeping_cost_per_year"], 1),
                "basis": hoard["basis"]}
