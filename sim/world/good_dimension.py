"""What a good's unit measures: mass, volume, energy, ground area, length or a count of pieces.

A good's id may carry the unit token (`_kg`, `_m3`, `_mj`, `hectare_`); a production entry states the
dimension in `unit_dimension` for every good, and the two must agree where the id speaks.

Standalone: no engine imports.
"""
from typing import Optional

MASS, VOLUME, ENERGY, AREA, LENGTH, COUNT = "mass", "volume", "energy", "area", "length", "count"
DIMENSIONS = (MASS, VOLUME, ENERGY, AREA, LENGTH, COUNT)
# Dimensions whose unit is not a quantity of matter that can be put on a cart.
IMMOBILE_DIMENSIONS = (ENERGY, AREA)

_SUFFIX_DIMENSIONS = (("_kg", MASS), ("_g", MASS), ("_t", MASS), ("_tons", MASS), ("_m3", VOLUME),
                      ("_m2", AREA), ("_mj", ENERGY), ("_m", LENGTH))
_PREFIX_DIMENSIONS = (("hectare_", AREA),)


def dimension_from_id(good: str) -> Optional[str]:
    """The dimension a good's id spells out, or None when the id carries no unit token."""
    for prefix, dimension in _PREFIX_DIMENSIONS:
        if good.startswith(prefix):
            return dimension
    for suffix, dimension in _SUFFIX_DIMENSIONS:
        if good.endswith(suffix):
            return dimension
    return None
