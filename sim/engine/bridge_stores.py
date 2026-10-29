"""Bridge entries the stores module reads: the store declarations the engine loads from data files."""
from sim.content import api as content

from .bridge import bridge_view


@bridge_view("base_store_declarations")
def base_store_declarations(sim):
    """[StoreSpec] the base game declares (data/world/stores.json)."""
    return content.base_store_declarations()
