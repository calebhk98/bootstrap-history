"""The sharing module's spec (sim/assembly).

It publishes the three ways to ask for a shared answer and reads exactly the views its stamp confirms an answer by."""
from sim.assembly.api import QUOTE, ModuleSpec, ViewSpec

from .module import Sharing

READS_BY_OWNER = {
	"scenario": ("year",),
	"knowledge": ("techniques_version", "techniques_held"),
	"ventures": ("operating_version", "operating"),
	"resources": ("forest_hectares", "nitre_beds", "mine_workings"),
	"demography": ("population",),
	"reporting": ("real_output_per_head",),
	"prices": ("material_prices", "done_memo"),
	"materials": ("material_demand_held", "material_pool", "project_material_needs"),
	"markets": ("others_trade_stamp",),
	"ledger": ("goods_stock",),
}

MODULE_SPECS = (ModuleSpec(
	"sharing", Sharing,
	publishes=(
		ViewSpec("shared_answers", "shared_answers", kind=QUOTE),
		ViewSpec("shared_answer", "shared_answer", kind=QUOTE),
		ViewSpec("shared_bill", "shared_bill", kind=QUOTE),
	),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
),)
