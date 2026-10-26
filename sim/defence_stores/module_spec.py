"""The defence-stores module's spec (sim/assembly)."""
from sim.assembly.api import QUOTE, TABLE, ModuleSpec, PhaseHook, ViewSpec
from sim.living_stock.api import ChangeHeld

from .module import DefenceStores

# not cached: they follow what is held, built and running, all still written outside any module's commands
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "defence_stores", DefenceStores,
    publishes=(
        ViewSpec("venture_garrison", "venture_garrison", kind=QUOTE, **_LIVE),
        ViewSpec("counter_supply_gap", "counter_supply_gap", kind=QUOTE, **_LIVE),
        ViewSpec("relief_kcal_per_day", "relief_kcal_per_day", kind=TABLE, **_LIVE),
    ),
    reads=("tree", "techniques_held", "operating", "is_venture", "staff", "stock_held", "year", "live_hazard_kinds",
           "running_mechanics", "hours_per_person_year", "institution_units", "effects_in_force"),
    sends=(ChangeHeld,),
    phases=(PhaseHook("defence_stores", "step_defence_stores"),),
),)
