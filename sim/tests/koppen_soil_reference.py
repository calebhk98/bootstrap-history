"""The old Koppen-keyed table of arable share and fertility, kept as a REFERENCE for tests only (Complaint 543).

Tile arable share and fertility are now derived from the water balance, growing months and ruggedness
(sim/geography/soil_derivation.py). Under CLAUDE.md 4.2 the derived values are validated against this table's
distribution by class, not equal to it: the table was agronomic judgement (confidence D). Nothing outside sim/tests reads it.
Values are (arable_fraction, fertility_quality_multiplier).
"""

KOPPEN_ARABLE_AND_FERTILITY = {
    # ---- A: tropical -------------------------------------------------
    "Af": (0.30, 0.65),  # rainforest, no dry season: leaches soil; clearing is limited by the forest layer in sim/geography/food_land.py
    "Am": (0.30, 0.90),  # monsoon: a real dry season aids clearing; rice country
    "Aw": (0.30, 0.75),  # savanna, dry winter: workable but thinner, erodible soils
    "As": (0.30, 0.75),  # savanna, dry summer: same treatment as Aw
    # ---- B: arid -------------------------------------------------------
    "BWh": (0.02, 0.55),  # hot desert: almost nothing arable outside oases (see LIMITS)
    "BWk": (0.02, 0.45),  # cold desert: same, shorter growing season where anything grows
    "BSh": (0.20, 0.60),  # hot semi-arid steppe: dryland grain, thin soils
    "BSk": (0.22, 0.55),  # cold semi-arid steppe: same, cooler
    # ---- C: temperate ----------------------------------------------------
    "Csa": (0.35, 1.00),  # Mediterranean, hot summer - THE ANCHOR (Italy's own class)
    "Csb": (0.32, 0.95),  # Mediterranean, warm summer: cooler/wetter than Csa
    "Csc": (0.25, 0.85),  # Mediterranean, cold summer: rare, montane
    "Cwa": (0.32, 0.95),  # dry-winter subtropical, hot summer: monsoon-adjacent, good grain land
    "Cwb": (0.28, 0.85),  # dry-winter subtropical, warm summer: highland version of the above
    "Cwc": (0.20, 0.70),  # dry-winter subtropical, cold summer: montane, marginal
    "Cfa": (0.35, 1.05),  # humid subtropical, no dry season: the Yangtze basin's own class, rice country
    "Cfb": (0.30, 0.90),  # oceanic: Britain and Gaul's own class, temperate lowland
    "Cfc": (0.22, 0.75),  # subpolar oceanic: short cool summer
    # ---- D: continental --------------------------------------------------
    "Dsa": (0.28, 0.80), "Dsb": (0.24, 0.75), "Dsc": (0.10, 0.55), "Dsd": (0.08, 0.50),
    "Dwa": (0.28, 0.85), "Dwb": (0.24, 0.80), "Dwc": (0.10, 0.55), "Dwd": (0.06, 0.45),
    "Dfa": (0.30, 0.90), "Dfb": (0.26, 0.85), "Dfc": (0.08, 0.45), "Dfd": (0.04, 0.35),
    # ---- E: polar ----------------------------------------------------------
    "ET": (0.005, 0.05),  # tundra - matches sim/world/agriculture.py's ARCTIC_TUNDRA exactly
    "EF": (0.0, 0.0),     # permanent ice
}


def arable_and_fertility_from_mix(sample_mix):
    """(arable_fraction, fertility) of a tile from its {climate class: sample
    count} mix. Arable fraction is the plain mean over samples; fertility is
    the mean over the ARABLE ground, so a tundra corner of a Mediterranean
    tile does not dilute the fertility of the land that is actually farmed."""
    samples = sum(sample_mix.values())
    arable_total = 0.0
    fertile_total = 0.0
    plain_fertility_total = 0.0
    for koppen_class, count in sample_mix.items():
        arable, fertility = KOPPEN_ARABLE_AND_FERTILITY[koppen_class]
        arable_total += arable * count
        fertile_total += arable * fertility * count
        plain_fertility_total += fertility * count
    arable_fraction = arable_total / samples
    if arable_total > 0.0:
        return arable_fraction, fertile_total / arable_total
    return arable_fraction, plain_fertility_total / samples
