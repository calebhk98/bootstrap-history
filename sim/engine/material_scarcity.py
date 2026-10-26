"""The price rules of a bought material, as plain functions: the freight markup on its book price and the
scarcity factor from how hard demand leans on the supply."""

from sim.unit_conversions import KILOGRAMS_PER_TONNE


def freight_markup(book_price_per_kg, haul_cost_per_tonne, cargo_cost_share):
    """Multiplier on a material's book price for carrying it here: one plus the haul per kilogram over the price
    plus the cargo's own interest and spoilage share. One for a material with no price or no haul."""
    if not book_price_per_kg or book_price_per_kg <= 0:
        return 1.0
    freight_per_kg = (haul_cost_per_tonne or 0.0) / KILOGRAMS_PER_TONNE
    if freight_per_kg <= 0:
        return 1.0
    return 1.0 + freight_per_kg / book_price_per_kg + cargo_cost_share


def scarcity_factor(needs_and_own_supplies, market_tonnes, share_cap, pressure_scale):
    """The dearest pressure among a material's demands. Each demand is (need, own supply) in tonnes; its share
    of the supply (own plus market) is capped, and the price rises by the pressure scale times the share squared.
    One when nothing is needed."""
    worst = 1.0
    for need, own_supply in needs_and_own_supplies:
        if need <= 0:
            continue
        supply = max(1e-9, own_supply + market_tonnes)
        share = min(share_cap, need / supply)
        worst = max(worst, 1.0 + pressure_scale * share * share)
    return worst
