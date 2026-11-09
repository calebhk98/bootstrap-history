"""Which tiles and cohorts the home country's state and the unqualified questions about 'the economy' are about."""
from typing import Optional


def has_partners(setup) -> bool:
    """Whether the economy holds more than the home country. Tile ownership changes during a game, so this is read
    afresh; hot callers ask once and pass the answer on."""
    return len(setup.countries()) > 1


def on_home_tile(setup, tile: str, partners: Optional[bool] = None) -> bool:
    """Whether the home country holds `tile` (always, with one country): the home state taxes and hires only there.
    `partners` is the caller's own `has_partners(setup)` when it has asked already."""
    if setup.country_of(tile) == setup.civ_id:
        return True
    return not (has_partners(setup) if partners is None else partners)


def home_cohorts(setup, record) -> list:
    """The cohorts living on home tiles."""
    partners = has_partners(setup)
    home_tiles = {tile for tile in {cohort.tile for cohort in record.cohorts.values()} if on_home_tile(setup, tile, partners)}
    return [cohort for cohort in record.cohorts.values() if cohort.tile in home_tiles]
