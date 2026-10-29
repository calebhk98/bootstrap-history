"""The stores module's spec (sim/assembly).

It reads the declarations held as data (the base game's `data/world/stores.json`, the mods' `data/stores.json`) through
two views of the content module, and answers its own `store_declarations` point with them; a mod's code adds its stores by providing to the point."""
from sim.assembly.api import KEYED, LIST, ExtensionPoint, ModuleSpec, Provision, ViewSpec

from .commands import WriteStore
from .module import Stores
from .state import StoresWorld

MODULE_SPECS = (ModuleSpec(
	"stores", Stores, world_state=StoresWorld,
	publishes=(
		# not cached: the values are written through the book's views, which bump no channel
		ViewSpec("store_book", "store_book", cached=False),
		ViewSpec("store", "store", kind=KEYED, cached=False),
	),
	applies=((WriteStore, "write_store"),),
	reads=("base_store_declarations", "data_store_declarations"),
	extension_points=(ExtensionPoint("store_declarations", LIST),),   # () -> [StoreSpec]: the stores a provider declares
	provides=(Provision("store_declarations", "provide_base_stores", "base"),
	          Provision("store_declarations", "provide_data_stores", "data")),
),)
