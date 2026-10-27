"""The projects module for a test: built with `module_harness`, every view it reads answering a neutral default unless the
test gives its own, and its own views wired the way a game wires them.

    module = projects_host.build(tree={"a": {...}}, techniques_held={"x"}, debt_status={"credit_frozen_until": 0, "insolvent_years": 0})
    module._check_already_done("a", node, False, None, True)

A view given as a plain value is that value; as a function, it is called with the view's arguments. A keyed view is
given as a dict or a function of the key. Defaults are the quiet answers (nothing known, nothing owed, nobody short)."""
import types
from typing import Any, Dict

from sim.projects.projects import Projects
from sim.projects import module_spec
from sim.tests import module_harness

OWN_VIEWS = ("start_check", "start_blockers", "start_refusal", "bounty_eligible", "start_hours", "last_start")


def projects_state(**fields: Any) -> types.SimpleNamespace:
	"""The raw `state.projects` the module still mutates in place."""
	values = dict(active={}, done=set(), paid_towards={}, bountied=set(), mothballed=set())
	values.update(fields)
	return types.SimpleNamespace(**values)


def defaults() -> Dict[str, Any]:
	state = projects_state()
	return {
		"tree": lambda node_id: None,
		"techniques_held": state.done, "closures": state.mothballed, "legacy_projects": state,
		"visibility": lambda node_id, memo: True, "visible_to_player": lambda node_id: True,
		"prerequisite_message": lambda missing, memo: "missing prerequisites: " + ", ".join(missing),
		"needs_first": lambda node_id, about_stock: (None, None), "foreign_only": lambda node_id: False,
		"civ_cost_factor": lambda node_id: 1.0, "reopen_fee": lambda node_id: 0.0,
		"is_venture": lambda node_id: False, "running": lambda node_id: False,
		"revenue_estimate": 0.0, "upkeep": 0.0, "living_cost": lambda revenue=None, upkeep=None: 0.0,
		"mine_operating_cost": 0.0, "money_per_labour_hour": 1.0,
		"project_cost": lambda node_id: 0.0, "funding_capacity": 0.0,
		"own_output_claim": lambda node_id: {}, "bounty_price": lambda node_id: 0.0,
		"material_upfront_refusal": lambda node_id: None, "material_pool": lambda material: (material, material),
		"generation": 0.0, "goods_stock": lambda commodity: 0.0,
		"debt_status": {"credit_frozen_until": 0, "insolvent_years": 0}, "credit_limit": 0.0,
		"purchase_remedies_text": lambda: "", "acting_balance": 0.0,
		"standing": {"protection": 0.0, "scandal": 0.0, "bribes_year_to_date": 0.0},
		"state_interest": lambda node: 0.0, "value_weight": {"bribability": 1.0}, "approval_patron": lambda gate: None,
		"hours_available": {"scholar_hands": 0.0, "craft_hands": 0.0, "director_pool": 0.0, "director_committed": 0.0,
		                    "hired_cap": 0.0},
		"market_supply": lambda trade: 1.0, "trade_available": lambda trade: True,
		"staff_advice": lambda kind, deficit: "hire", "training_advice": lambda trade: {
			"trade": trade, "source_trade": None, "hours_each": None, "years": None},
		"training_queue": [], "project_staffing_shortfall": lambda node: None, "staff": {"scholars": 0.0, "artisans": 0.0, "employees": {}},
		"mechanic": lambda name: {}, "techniques_forgotten": {}, "corpus_hedge": (1.0, 0.0, None), "operating": set(),
		"hour_commitments": {"allocations": {}, "trade_hours_used": {}, "unused_reported": {}},
		"hours_you_can_call_on": lambda trade: 0.0, "industry_depth": lambda node_id: 0.0, "resource_throttle": lambda node_id: (1.0, None),
		"material_binding": None, "founder": {"alive": True, "life_left": 10.0, "dead_reason": None, "policy": {}},
		"goal": "goal", "automatic_policy": lambda name: True, "capability_sets": (frozenset(), frozenset(), {}),
		"money_text": lambda amount, grouped=False, short=False: "%d money" % round(amount),
		"plain_number": lambda value, digits=0: format(value, ",.%df" % digits),
		"win_condition_text": lambda node: "the goal is met", "acting_seat": "founder",
		"automation": {"manual": False, "bounty_set": set()}, "society_name": "Testland", "year": 100,
		"horizon_end_year": 1000, "legacy_order": [], "project_limits": {
			"base": 2, "per_director_hours": 2000.0, "per_scholar": 12.0, "per_artisan": 25.0},
		"actor_world": None, "legacy_acting_household": types.SimpleNamespace(bounties_paid=0, employees={}),
		"start_gate_unheld_stock": lambda *arguments: None,
		"start_gate_material_seller": lambda *arguments: None, "start_gate_group_prohibition": lambda *arguments: None,
		"extra_start_checks": lambda *arguments: None,
	}


def build(answers: Dict[str, Any] = None, **views: Any) -> Projects:
	"""The module with `views` (and `answers`, the replies of owners to commands, keyed by command class)."""
	every_view = defaults()
	every_view.update(views)
	if isinstance(every_view["tree"], dict):
		every_view.setdefault("tree_nodes", every_view["tree"])
	every_view.setdefault("tree_nodes", {})
	module = module_harness.build(Projects, views=every_view, answers=answers)
	for name in OWN_VIEWS:
		if name not in views:
			setattr(module.needs, name, module_harness._FakeView(getattr(module, name)))
	return module


def declared_reads() -> tuple:
	return module_spec.MODULE_SPECS[0].reads


def start_phase_module(funding_capacity: float = 1e9, committed_cost: float = 0.0, project_cost: float = 10.0,
                       manual: bool = False, **views: Any) -> Projects:
	"""The module ready to run its start phase: two candidates, every one startable, money in hand and the given room.
	`started` lists what `initialize_project` was asked to begin."""
	state = projects_state()
	arguments = dict(
		legacy_projects=state, tree=lambda node_id: {"name": node_id, "rev": 0.0, "up": 0.0}, legacy_order=["a", "b"],
		funding_capacity=funding_capacity, committed_cost=committed_cost, project_cost=lambda node_id: project_cost,
		automation={"manual": manual, "bounty_set": set()}, revenue_estimate=1e6, acting_balance=1e7, year=0,
		start_check=lambda *call: (True, None),
		project_limits={"base": 5.0, "per_director_hours": 2000.0, "per_scholar": 12.0, "per_artisan": 40.0})
	arguments.update(views)
	module = build(**arguments)
	module.started = []

	def initialize_project(node_id):
		module.started.append(node_id)
		state.active[node_id] = {}
	module.initialize_project = initialize_project
	return module
