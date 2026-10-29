"""The ventures module for a test: built with `module_harness`, every view it reads answering a neutral default unless the test
gives its own.

    module = ventures_host.build(tree_nodes={"a": {...}}, operating={"a"}, staff={"employees": {"smith": 1.0}, "artisans": 0.0})
    module.venture_foreman_free("smith")

A view given as a plain value is that value; as a function, it is called with the view's arguments. A keyed view is given as a dict or a
function of the key. Defaults are the quiet answers (nothing known, nothing running, nobody employed)."""
import types
from typing import Any, Dict

from sim.tests import module_harness
from sim.ventures.module import Ventures
from sim.ventures.state import VenturesSeat


def projects_record(**fields: Any) -> types.SimpleNamespace:
	"""What a test gives with its projects: the held and granted sets (knowledge's), and the works open and shut the plants start with."""
	values = dict(done=set(), granted=set(), operating=set(), mothballed=set())
	values.update(fields)
	return types.SimpleNamespace(**values)


def defaults() -> Dict[str, Any]:
	record = projects_record()
	return {
		"tree_nodes": {}, "projects_record": record, "techniques_held": record.done, "techniques_granted": record.granted,
		"capability_sets": (frozenset(), frozenset(), {}), "venture_garrison": lambda node_id, units=1.0: {},
		"concern_runs_without_founder": lambda node_id: False, "institution_units": lambda node_id: 1.0,
		"institution_unit_ceiling": lambda node_id: 1.0, "institution_unit_cost": lambda node_id, have, add: 0.0,
		"institution_upkeep": lambda node_id, units=None, fully_staffed=False: 0.0, "running": lambda node_id: False,
		"is_venture": lambda node_id: True, "practisable": lambda node_id: False, "venture_ramp": lambda node_id: 1.0,
		"node_output_market_factor": lambda node, seat: 1.0, "concern_takings": lambda node_id, ramp, with_output_factor=True: 0.0,
		"concern_goods_have_market": lambda node_id: True, "concern_sale_basis": lambda node_id: "market",
		"project_cost": lambda node_id: 0.0, "open_refusal": lambda node_id, unit_count=None: None,
		"staff_closure_age": lambda node_id: None,
		"staff": {"scholars": 0.0, "artisans": 0.0, "employees": {}}, "effective_scholars": 0.0,
		"hours_per_person_year": 2000.0, "money_per_labour_hour": 1.0, "unskilled_trade": "labourer",
		"mechanic": lambda name: {}, "founder": {"alive": False, "life_left": 0.0, "dead_reason": None, "policy": {}},
		"seat_party_with_margins": lambda seat_id, margins: types.SimpleNamespace(actor_id=seat_id, margins=margins),
		"actor_world": types.SimpleNamespace(concern_margin=lambda node_id: 0.0),
		"cast": types.SimpleNamespace(of_kind=lambda kind: [], get=lambda actor_id: None),
		"spending_power": lambda kind="buy": 0.0, "acting_balance": 0.0, "price_index": 1.0, "population_total": 1000.0, "year": 100,
		"game_config": {"revenue_ramp_years": 3}, "money_text": lambda amount, grouped=False, short=False: "%d money" % round(amount),
	}


def build(answers: Dict[type, Any] = None, seat: VenturesSeat = None, **views: Any) -> Ventures:
	"""The module with `views` (and `answers`, the replies of owners to commands, keyed by command class). Its seat state is `seat`, or
	one with a plant running (or shut) for each work the test lists as `operating` (or in the projects record's `mothballed`)."""
	every_view = defaults()
	every_view.update(views)
	record = every_view.pop("projects_record")
	seat = seat or VenturesSeat()
	if getattr(record, "business", None) is not None:
		seat.businesses = [record.business]
	opened = set(every_view.pop("operating")) if "operating" in views else set(getattr(record, "operating", None) or ())
	for key in sorted(opened):
		if seat.business.plant_of(key) is None:
			seat.business.open_plant(key, None)
	for key in sorted(getattr(record, "mothballed", None) or ()):
		if seat.business.plant_of(key) is None:
			seat.business.mothball(key, None, "")
	if "techniques_held" not in views and hasattr(record, "done"):
		every_view["techniques_held"] = record.done
	if "techniques_granted" not in views and hasattr(record, "granted"):
		every_view["techniques_granted"] = record.granted
	module = module_harness.build(Ventures, views=every_view, answers=answers, seat=seat, module_id="ventures")
	module.clock.acting_seat = "founder"
	return module
