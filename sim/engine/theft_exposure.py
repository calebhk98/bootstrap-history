"""What a thief can take from a holding: how it is kept, how it is guarded, how visible its holder is and how
well the state keeps order.

Theft is not a share of the money held. The same value kept as coin is easy to carry and to spend unasked; kept
as goods it needs carts and a buyer; kept as land it cannot be lifted at all; kept as a loan it is lost only if
the debtor defaults. Guarding (guard hours per tonne a year) and the state's order both cut it, and the more
visible the holder is, the more thieves know to come. Pure functions: callers pass the facts.
"""
from typing import Mapping

from sim.constants import declare

# How much of a holding's value a thief can carry off and turn into money, per kind of holding.
PORTABILITY = {
    "coin": declare(
        "THEFT_PORTABILITY_COIN", 1.0, kind="temporary_heuristic", unit="dimensionless (0..1)", source=None,
        confidence="D", why="Coin is value in the form a thief spends without being asked who he took it from. "
        "The reference the other kinds are scaled against; not measured."),
    "precious_metal": declare(
        "THEFT_PORTABILITY_PRECIOUS_METAL", 0.9, kind="temporary_heuristic", unit="dimensionless (0..1)",
        source=None, confidence="D", why="Bullion and plate are dense and sell anywhere, but a fence must melt or "
        "weigh them first. Not measured."),
    "goods": declare(
        "THEFT_PORTABILITY_GOODS", 0.25, kind="temporary_heuristic", unit="dimensionless (0..1)", source=None,
        confidence="D", why="Bulk goods need carts and a buyer for each load, so a thief gets little per unit of "
        "value. Stands in for per-good bulk and resale, which the model does not yet read. Not measured."),
    "loans": declare(
        "THEFT_PORTABILITY_LOANS", 0.02, kind="temporary_heuristic", unit="dimensionless (0..1)", source=None,
        confidence="D", why="A loan is a claim on a debtor, so a thief takes nothing; the small figure stands for "
        "a debtor defaulting. Not measured."),
    "shares": declare(
        "THEFT_PORTABILITY_SHARES", 0.02, kind="temporary_heuristic", unit="dimensionless (0..1)", source=None,
        confidence="D", why="A share is a claim on a company's profit like a loan is on a debtor; a thief takes "
        "the dividends, not the firm. Not measured."),
    "land": declare(
        "THEFT_PORTABILITY_LAND", 0.0, kind="temporary_heuristic", unit="dimensionless (0..1)", source=None,
        confidence="D", why="Land cannot be carried off; losing it is seizure by a state or an army, a different "
        "event (confiscation, sack). Not measured."),
}
# Kinds a guard can watch because they are carried or stored; a claim or a field is not guarded by a watch.
GUARDABLE_KINDS = ("coin", "precious_metal", "goods")

THEFT_SHARE_PER_YEAR_AT_FULL_EXPOSURE = declare(
    "THEFT_SHARE_PER_YEAR_AT_FULL_EXPOSURE", 0.03, kind="temporary_heuristic",
    unit="dimensionless (share of value per year)", source=None, confidence="D",
    why="Yearly share of fully portable, unguarded, fully visible wealth stolen in a place with no order. "
        "A stand-in for the rate at which a district's thieves find and empty a hoard; not measured.")

GUARD_HOURS_THAT_HALVE_EXPOSURE = declare(
    "GUARD_HOURS_THAT_HALVE_EXPOSURE", 60.0, kind="temporary_heuristic",
    unit="labour hours per tonne per year", source=None, confidence="D",
    why="Guard hours per tonne a year at which exposure falls to half. A saturating relation: the first "
        "watchmen matter most. Stands in for a model of guards against thieves; not measured.")

UNSEEN_EXPOSURE_FLOOR = declare(
    "THEFT_UNSEEN_EXPOSURE_FLOOR", 0.2, kind="temporary_heuristic", unit="dimensionless (0..1)", source=None,
    confidence="D", why="Exposure of a holder nobody has heard of, as a share of a fully visible one's: "
    "thieves still find the unremarkable. Not measured.")

ORDER_SUPPRESSION = declare(
    "THEFT_ORDER_SUPPRESSION", 0.9, kind="temporary_heuristic", unit="dimensionless (0..1)", source=None,
    confidence="D", why="Share of theft a perfectly ordered state (patrols, alarm, courts) removes. Stands "
    "in for the protection and alarm mechanics, which the model does not yet read per district. Not measured.")


def portability_of(kind):
    """How much of a holding of this kind a thief can take, 0..1; an unknown kind counts as bulk goods."""
    return PORTABILITY.get(kind, PORTABILITY["goods"])


def guarding_factor(guard_hours_per_tonne_year):
    """Exposure left after guarding: 1 with no guard, falling toward 0 as the hours a tonne rise."""
    hours = max(0.0, guard_hours_per_tonne_year)
    return GUARD_HOURS_THAT_HALVE_EXPOSURE / (GUARD_HOURS_THAT_HALVE_EXPOSURE + hours)


def visibility_factor(visible_scale):
    """Exposure by how visible the holder is (the engine's visible scale, 0..1)."""
    scale = min(1.0, max(0.0, visible_scale))
    return UNSEEN_EXPOSURE_FLOOR + (1.0 - UNSEEN_EXPOSURE_FLOOR) * scale


def order_factor(state_capacity, protection):
    """Exposure left under the state's order and the holder's own protection (each 0..1, independent covers)."""
    uncovered = (1.0 - min(1.0, max(0.0, state_capacity))) * (1.0 - min(1.0, max(0.0, protection)))
    return 1.0 - ORDER_SUPPRESSION * (1.0 - uncovered)


def guard_hours_for(kind, guard_hours_per_tonne_year):
    """Guard hours per tonne a year that watch this kind: a number applies to every guardable kind, a mapping
    names them (a kind it leaves out is unwatched)."""
    if isinstance(guard_hours_per_tonne_year, Mapping):
        return guard_hours_per_tonne_year.get(kind, 0.0)
    return guard_hours_per_tonne_year


def share_taken(kind, strength, guard_hours_per_tonne_year, visible_scale, state_capacity, protection):
    """Share of a holding of this kind that a theft of this strength takes: what is portable, unguarded, visible
    and outside the state's order. Strength 1 is the share of a fully exposed holding taken by the event."""
    guarded = (guarding_factor(guard_hours_for(kind, guard_hours_per_tonne_year))
               if kind in GUARDABLE_KINDS else 1.0)
    around = visibility_factor(visible_scale) * order_factor(state_capacity, protection)
    return min(1.0, max(0.0, strength) * portability_of(kind) * guarded * around)


def theft_shares_by_kind(kinds, strength, guard_hours_per_tonne_year, visible_scale, state_capacity, protection):
    """Share taken of each kind named, for a theft of this strength."""
    return {kind: share_taken(kind, strength, guard_hours_per_tonne_year, visible_scale, state_capacity,
                              protection) for kind in kinds}


def theft_loss_by_kind(holdings, guard_hours_per_tonne_year, visible_scale, state_capacity, protection,
                       strength=THEFT_SHARE_PER_YEAR_AT_FULL_EXPOSURE):
    """Expected value stolen in a year from each kind of holding (kind -> value held); a debt is not stolen from.
    A larger `strength` prices an event (a sack, a bandit year) by the same exposure."""
    shares = theft_shares_by_kind(holdings, strength, guard_hours_per_tonne_year, visible_scale, state_capacity,
                                  protection)
    return {kind: max(0.0, value) * shares[kind] for kind, value in holdings.items()}


def expected_theft_loss(holdings, guard_hours_per_tonne_year, visible_scale, state_capacity, protection):
    """Total expected value stolen in a year across the holdings."""
    return sum(theft_loss_by_kind(holdings, guard_hours_per_tonne_year, visible_scale, state_capacity,
                                  protection).values())
