"""Campaigns' module spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (bridge_shared.py) under the name the owner will publish. Grouped by the owner each is catalogued under
(docs/architecture/catalogue)."""
from sim.actors.api import RecordConquestContact
from sim.assembly.api import KEYED, ModuleSpec, PhaseHook, ViewSpec
from sim.demography.api import AddCaptives
from sim.hazards.api import RecordWorldEvent
from sim.land.api import TransferTile
from sim.polity.api import (CloseSuccessionDispute, RecordRising, RegisterPeople, ReplaceRuler, ResetStateUnrest,
                            SetGrievanceReference, SetLandTakenMemory, SetTileReading, StrikeFromForce)
from sim.stores.api import WriteStore

from .armies import ARMIES
from .commands import DisbandArmy, OrderArmy, RaiseArmy, RecallArmy
from .module import Campaigns
from .state import CampaignsWorld

READS_BY_OWNER = {
	"land": ("tile_owner", "tiles_owned_by", "tile_owner_map", "tile_facts", "route_between", "reach_from", "home_modes"),
	"actors": ("has_state", "country_world", "countries"),
	"polity": ("organised_factions",),
	"seats": ("played_countries",),
	"demography": ("food_eaten",),
	"stores": ("store",),
	"core": ("civilisation", "year"),
}

MODULE_SPECS = (ModuleSpec(
	"campaigns", Campaigns, channels=(ARMIES,), world_state=CampaignsWorld,
	publishes=(
		# not cached: the free soldiers come from the state's army line, which polity code still writes outside its commands
		ViewSpec("armies", "armies_of_owner", kind=KEYED, channels=(ARMIES,), cached=False),
	),
	applies=((RaiseArmy, "apply_raise_army"), (OrderArmy, "apply_order_army"), (RecallArmy, "apply_recall_army"),
	         (DisbandArmy, "apply_disband_army")),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(TransferTile, StrikeFromForce, AddCaptives, RecordWorldEvent, RecordConquestContact, WriteStore, SetLandTakenMemory,
	       RegisterPeople, SetGrievanceReference, ResetStateUnrest, SetTileReading, RecordRising, ReplaceRuler,
	       CloseSuccessionDispute),
	phases=(PhaseHook("campaigns", "step_campaigns"), PhaseHook("revolts", "step_revolts")),
),)
