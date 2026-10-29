"""The content module's spec (sim/assembly).

It owns which mods directory the game is over (sent as `OpenContent` when the assembly is built) and publishes what the mods
installed there contribute as data: their ids, the map overlays, the household needs, the actor kinds, the stores, the trade registry, the technology effects and the
foreign economies. It reads no view. Not cached: the answers come from files, and the directory is the only input."""
from sim.assembly.api import KEYED, ModuleSpec, ViewSpec

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
		ViewSpec("trade_records", "trade_records", **_FILES),
		ViewSpec("trade_notes", "trade_notes", **_FILES),
		ViewSpec("trades_absent", "trades_absent", **_FILES),
		ViewSpec("trade_family", "trade_family", kind=KEYED, **_FILES),
		ViewSpec("tech_effects", "tech_effects", kind=KEYED, **_FILES),
		ViewSpec("foreign_economy_records", "foreign_economy_records", **_FILES),
		ViewSpec("not_traded_materials", "not_traded_materials", **_FILES),
	),
	applies=((OpenContent, "open_content"),),
),)
