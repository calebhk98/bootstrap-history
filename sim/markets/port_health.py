"""The agent economy's health figures for a game in progress (Complaint 445), through sim/economy/diagnostics.

Part of the port. The staple is the good the hunger need's basket buys most of; metals default to the
good that backs the currency, and a caller may name others.

The figures are read from `health_rows`, one row per year played, kept in the agent economy's stored record (so a saved
game carries its years) and cut to the last OUTCOMES_KEPT. A row holds the fields of the year's outcome the diagnostics read.
"""
from types import SimpleNamespace

from sim.constants import declare
from sim.economy.api import backing_good, health_figures, hunger_goods, opening_quantities

OUTCOMES_KEPT = declare(
    "OUTCOMES_KEPT", 100, kind="temporary_heuristic", unit="years of rows", source=None, confidence="D",
    retire="no complaint covers it; a save-size bound, retired when the health figures are kept as running sums in sim/economy/diagnostics, not as the yearly rows they are cut from",
    why="The health figures are read from the stored yearly rows; a game longer than this forgets its first years, so the "
        "save does not grow with the game.")


def health_row(outcome):
    """What the health figures read of one year's outcome, as plain JSON values."""
    return {"prices": dict(outcome.prices), "wages": dict(outcome.wages),
            "hired_hours": outcome.hired_hours, "idle_hours": outcome.idle_hours,
            "wage_floor_per_hour": outcome.wage_floor_per_hour,
            "hunger_by_tile": dict(outcome.hunger_by_tile)}


def note_year(stored, outcome):
    """Add the year's row to the stored record, keeping the last OUTCOMES_KEPT."""
    rows = stored.setdefault("health_rows", [])
    rows.append(health_row(outcome))
    del rows[:-OUTCOMES_KEPT]


def staple_good(agent, stale=()):
    """The good of the hunger need with the largest opening basket quantity, leaving out the `stale` goods (those whose markets
    have not cleared lately: a good nobody trades shows what it would cost to make, not a price); None when none is left."""
    economy = agent.economy()
    opening = opening_quantities(economy)
    goods = [good for good in hunger_goods(economy) if good not in stale]
    return max(goods, key=lambda good: opening.get(good, 0.0), default=None)


def health_report(agent, metals=(), staple=None):
    """{"years", "staple", "metals", "figures"} over the yearly rows kept since this game began."""
    economy = agent.economy()
    if not metals and backing_good(economy):
        metals = (backing_good(economy),)
    staple = staple or staple_good(agent)
    rows = list(agent.stored.get("health_rows", []))
    outcomes = [SimpleNamespace(**row) for row in rows]
    figures = health_figures(economy, outcomes, staple, metals) if outcomes and staple else {}
    return {"years": len(outcomes), "staple": staple, "metals": list(metals), "figures": figures}
