"""The content module's spec (sim/assembly).

It owns which mods directory the game is over (sent as `OpenContent` when the assembly is built) and publishes what the mods
installed there contribute as data: their ids, the map overlays, the household needs, the actor kinds and the stores. It reads no
view. Not cached: the answers come from files, and the directory is the only input."""
from sim.assembly.api import ModuleSpec, ViewSpec

from .commands import OpenContent
from .module import Content

_FILES = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
	"content", Content,
	publishes=(
		ViewSpec("mods_directory", "mods_directory", **_FILES),
		ViewSpec("installed_mod_ids", "installed_mod_ids", **_FILES),
		ViewSpec("map_overlays", "map_overlays", **_FILES),
		ViewSpec("household_need_data", "household_need_data", **_FILES),
		ViewSpec("declared_actor_kinds", "declared_actor_kinds", **_FILES),
		ViewSpec("data_store_declarations", "data_store_declarations", **_FILES),
	),
	applies=((OpenContent, "open_content"),),
),)
