"""The hazards module for a test: built with `module_harness`, every view it reads answering a quiet default unless the test
gives its own.

    module = hazards_host.build(techniques_held={"academy"}, civilisation={"id": "rome", "hazards": [...]})
    module.hazard_relief("sack_chance")

A view given as a plain value is that value; as a function, it is called with the view's arguments. A keyed view is given as
a dict or a function of the key. Defaults are the quiet answers: nothing built, nothing owed, one seat, no hazards, nobody
short. The commands the module sends are in `module_harness.sent(module)`. Dice are `random.Random(seed)`."""
import random
from contextlib import contextmanager
from typing import Any, Dict, Optional

from sim.hazards import module_spec
from sim.hazards.module import Hazards
from sim.hazards.state import HazardsSeat, HazardsWorld
from sim.tests import module_harness
from sim.workforce.api import LoseStaff


@contextmanager
def _same_seat(seat_id):
	yield


def defaults(seed: int) -> Dict[str, Any]:
	return {
		"year": 100, "civilisation": {"id": "rome", "hazards": []}, "events_enabled": True,
		"game_random": random.Random(seed), "act_as": _same_seat,
		"money_text": lambda amount, grouped=False, short=False: "%d money" % round(amount),
		"seat_list": {"joined": ["founder"], "playing": ["founder"]}, "ended_seats": [],
		"founder": {"alive": True, "life_left": 30.0, "dead_reason": None, "policy": {}}, "goal": None,
		"automation": {"manual": False, "bounty_set": set()},
		"techniques_held": set(), "techniques_granted": set(), "tree": lambda node_id: None, "tree_nodes": {},
		"visible_to_player": lambda node_id: True, "losable_node_ids": lambda keep_dispersed=True: [],
		"tree_closure": lambda goal_id: set(), "critical_path": lambda goal_id: (0.0, []),
		"hazard_counter_rows": {}, "corpus_hedge": (0.8, 0.4, None), "corpus_nodes": [], "mechanic": lambda name: {},
		"running_mechanics": lambda name: [], "running": lambda node_id: False,
		"start_check": lambda node_id, ignore_trade=False, memo=None, why=True: (True, None),
		"project_cost": lambda node_id: 0.0, "active_projects": {}, "closure_record": lambda node_id: None,
		"closed_by_choice": "manual",
		"civ_diffusion": lambda node_id: 0.0, "diffusible_ids": lambda category: (),
		"diffusion_relief": lambda kind, per_weapon=0.0: 0.0 if kind == "medical" else (1.0, None),
		"counter_supply_gap": lambda node_id, kind, label: (1.0, None), "mine_capacity": {},
		"military_leverage": 0.0, "standing": {"protection": 0.0, "scandal": 0.0, "bribes_year_to_date": 0.0},
		"wage_index": 1.0,
		"money_per_labour_hour": 1.0, "acting_balance": 0.0, "money_real": 1.0, "event_log": [], "price_index": 1.0,
		"partners_in_agent_economy": [], "weather_seed": lambda year, region=None: "seed", "country_strata": lambda country: [],
		"visibility": lambda node_id, memo=None: True, "techniques_forgotten": {}, "fog_of_war": False, "capability_gaps": [],
		"epidemic_risk": {},
	}


def build(seed: int = 1, answers: Optional[Dict[type, Any]] = None, world: Optional[HazardsWorld] = None,
          seat: Optional[HazardsSeat] = None, **views: Any) -> Hazards:
	"""The module with `views` over the quiet defaults, a fresh world and seat state unless given, and `answers`, the
	replies of owners to commands keyed by command class (a shock that takes people finds none lost unless given)."""
	every_view = defaults(seed)
	every_view.update(views)
	answers = {LoseStaff: lambda command: {"people_before": 0.0, "people_after": 0.0}, **(answers or {})}
	return module_harness.build(Hazards, views=every_view, answers=answers, world=world or HazardsWorld(),
	                            seat=seat or HazardsSeat(), module_id="hazards")


def declared_reads() -> tuple:
	return module_spec.MODULE_SPECS[0].reads
