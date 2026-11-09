"""Which tiles and cohorts the home country's state and the unqualified questions about 'the economy' are about."""
from typing import Dict, Optional

import numpy as np

from .cohort_people import total_by_tile
from .cohort_store import table_of


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


def home_cohort_ids(setup, record) -> list:
    """The ids, in table order, of the cohorts living on home tiles (the tile of each cohort is asked once per tile)."""
    partners = has_partners(setup)
    return table_of(record.cohorts).ids_on_tiles(lambda tile: on_home_tile(setup, tile, partners))


def home_working_by_tile(setup, record) -> Dict[str, float]:
    """{tile: working people of the home cohorts on it, added in table order}, in tile name order."""
    store = table_of(record.cohorts)
    partners = has_partners(setup)
    names = store.names["tiles"].name_list
    home = np.array([on_home_tile(setup, name, partners) for name in names], dtype=np.bool_)
    totals = total_by_tile(store, "working_people", home[store.tile_numbers()]).tolist()
    present = np.unique(store.tile_numbers()[home[store.tile_numbers()]]).tolist()
    return {name: total for name, total in sorted((names[number], totals[number]) for number in present)}
