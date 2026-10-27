"""Bridge entries the stores module reads: the store declarations the engine loads from data files."""
from . import bridge_land, mod_stores
from .bridge import bridge_view


@bridge_view("base_store_declarations")
def base_store_declarations(sim):
    """[StoreSpec] the base game declares (data/world/stores.json)."""
    return mod_stores.base_declarations()


@bridge_view("data_store_declarations")
def data_store_declarations(sim):
    """[StoreSpec] the installed mods declare in their data/stores.json, in mod load order."""
    return mod_stores.data_declarations(bridge_land.MODS_DIR)
